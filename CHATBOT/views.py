import json
import os
import logging
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from .tools import search_lots, get_lot_details, get_project_stages

# Cargar variables de entorno explícitamente
load_dotenv()

logger = logging.getLogger(__name__)

# Configurar el cliente Hugging Face
HF_TOKEN = os.environ.get("HUGGINGFACE_API_KEY", "")

# Modelo Llama 3.1 8B Instruct es el recomendado para Tool Calling en HF
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct" 

# Definir las herramientas (tools)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_lots",
            "description": "Busca lotes disponibles por precio o etapa. Úsalo cuando el usuario pregunte por disponibilidad general.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price_min": {"type": "number", "description": "Precio mínimo."},
                    "price_max": {"type": "number", "description": "Precio máximo."},
                    "status": {"type": "string", "enum": ["AVAILABLE", "RESERVED", "SOLD"]},
                    "stage_name": {"type": "string", "description": "Nombre de la etapa (ej: Lanzamiento)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_lot_details",
            "description": "Obtiene info detallada y links de un lote específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lot_id": {"type": "integer"}
                },
                "required": ["lot_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_stages",
            "description": "Lista las etapas del proyecto inmobiliario.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

def try_parse_tool_call(content):
    """Intenta extraer una llamada a función si el modelo la envió como JSON en el texto."""
    if not content:
        return None
    try:
        # Buscar el bloque JSON más externo
        content = content.strip()
        if content.startswith('{') and content.endswith('}'):
            data = json.loads(content)
        else:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                return None
        
        # Normalizar al formato de OpenAI/HF
        # Caso 1: {"name": "...", "arguments": {...}}
        if "name" in data and ("arguments" in data or "args" in data):
            args = data.get("arguments") or data.get("args")
            return [{
                "id": "manual_call_" + os.urandom(4).hex(),
                "type": "function",
                "function": {
                    "name": data["name"],
                    "arguments": json.dumps(args) if isinstance(args, dict) else args
                }
            }]
        # Caso 2: {"type": "function", "function": {"name": "...", "arguments": {...}}}
        elif "function" in data and isinstance(data["function"], dict) and "name" in data["function"]:
             args = data["function"].get("arguments") or data["function"].get("args")
             return [{
                "id": "manual_call_" + os.urandom(4).hex(),
                "type": "function",
                "function": {
                    "name": data["function"]["name"],
                    "arguments": json.dumps(args) if isinstance(args, dict) else args
                }
            }]
    except:
        pass
    return None

@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Solo se permiten peticiones POST"}, status=405)
    
    try:
        if not HF_TOKEN:
            return JsonResponse({
                "response": "¡Hola! Para que pueda ayudarte, necesitas configurar tu HUGGINGFACE_API_KEY en el archivo .env.",
                "history": []
            })

        client = InferenceClient(api_key=HF_TOKEN)
        
        data = json.loads(request.body)
        user_message = data.get('message', '')
        history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({"error": "Mensaje vacío"}, status=400)

        # Preparar mensajes
        messages = [
            {
                "role": "system", 
                "content": (
                    "Eres el Asistente Experto de SIGLO. Tu misión es VENDER lotes. "
                    "SIEMPRE que el usuario pregunte por lotes, precios, etapas o disponibilidad, "
                    "DEBES usar tus herramientas (search_lots, get_lot_details o get_project_stages) INMEDIATAMENTE. "
                    "REGLA CRÍTICA DE ENLACES: Al mostrar un enlace, asegúrate de cerrar siempre el paréntesis. "
                    "Ejemplo: [Ver en el Mapa](/lotes/mapa/?lot_id=1). "
                    "No respondas con JSON. Si no especifican filtros, busca los lotes disponibles generales. "
                    "Si el usuario menciona números o precios, procésalos correctamente para llamar a search_lots o get_lot_details. "
                    "Sé persuasivo, profesional y siempre incluye enlaces al mapa o de compra cuando los obtengas."
                )
            }
        ]
        
        clean_history = [msg for msg in history if not str(msg.get('content', '')).startswith('Ocurrió un error')]
        for msg in clean_history[-6:]:
            messages.append(msg)
            
        messages.append({"role": "user", "content": user_message})

        # Primera llamada para detectar herramientas
        try:
            response = client.chat_completion(
                model=MODEL_ID,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=500,
                temperature=0.1
            )
        except Exception as api_err:
            logger.error(f"Error de API Hugging Face: {str(api_err)}")
            # Fallback a un modelo que soporte bien el español si falla el principal
            response = client.chat_completion(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=messages,
                max_tokens=500
            )
  
        response_message = response.choices[0].message
        # Aseguramos el acceso a tool_calls tanto si es objeto como si es dict
        tool_calls = getattr(response_message, 'tool_calls', None)
        if tool_calls is None and isinstance(response_message, dict):
            tool_calls = response_message.get('tool_calls')

        # Si tool_calls es None pero el contenido parece JSON, intentamos parsearlo manualmente
        msg_content = getattr(response_message, 'content', '')
        if msg_content is None and isinstance(response_message, dict):
            msg_content = response_message.get('content', '')
            
        if not tool_calls and msg_content:
            tool_calls = try_parse_tool_call(msg_content)

        if tool_calls:
            # Añadimos la respuesta del modelo (la llamada) al historial
            # Hugging Face espera diccionarios en el historial
            if hasattr(response_message, 'model_dump'):
                messages.append(response_message.model_dump())
            elif not isinstance(response_message, dict):
                # Conversión manual si no tiene model_dump
                messages.append({
                    "role": "assistant",
                    "content": msg_content,
                    "tool_calls": tool_calls
                })
            else:
                messages.append(response_message)
            
            available_functions = {
                "search_lots": search_lots,
                "get_lot_details": get_lot_details,
                "get_project_stages": get_project_stages,
            }

            for tool_call in tool_calls:
                # Extraer nombre y argumentos de forma segura (funciona para objetos o diccionarios)
                if hasattr(tool_call, 'function'):
                    function_name = tool_call.function.name
                    args_raw = tool_call.function.arguments
                    tc_id = tool_call.id
                else:
                    # Caso de diccionario (manual de try_parse_tool_call)
                    tc_func = tool_call.get('function', {})
                    function_name = tc_func.get('name')
                    args_raw = tc_func.get('arguments')
                    tc_id = tool_call.get('id')

                if function_name not in available_functions:
                    continue
                    
                function_to_call = available_functions[function_name]
                # Los argumentos pueden venir como dict o string JSON
                function_args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                
                # Ejecutar función real
                function_response = function_to_call(**function_args)
                
                messages.append({
                    "tool_call_id": tc_id or ("tc_" + os.urandom(4).hex()),
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response),
                })

            # Segunda llamada para redactar la respuesta final con los datos obtenidos
            # IMPORTANTE: Desactivamos tools en la segunda llamada para obligar al modelo a redactar
            try:
                second_response = client.chat_completion(
                    model=MODEL_ID,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7,
                    tools=None, # Desactivar herramientas para la respuesta final
                )
            except:
                second_response = client.chat_completion(
                    model="microsoft/Phi-3-mini-4k-instruct",
                    messages=messages,
                    max_tokens=500
                )
            final_content = second_response.choices[0].message.content
        else:
            final_content = response_message.content

        # Si por algún motivo la respuesta sigue pareciendo JSON, forzamos una limpieza
        if final_content and final_content.strip().startswith('{') and '"name"' in final_content:
             final_content = "He procesado tu solicitud. Tenemos varias opciones disponibles para ti. ¿Te gustaría ver los detalles de algún lote en particular?"

        return JsonResponse({
            "response": final_content,
            "history": clean_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": final_content}
            ]
        })

    except Exception as e:
        logger.exception("Excepción en Chatbot")
        return JsonResponse({
            "response": f"Ocurrió un error al procesar tu solicitud. Intenta de nuevo: {str(e)}",
            "history": history
        })
