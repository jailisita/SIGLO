import math
from LOTES.models import Lot, Stage
from django.db.models import Q
from django.urls import reverse

def search_lots(price_min=None, price_max=None, status='AVAILABLE', stage_name=None):
    """Filtra lotes por precio, estado y etapa."""
    lots = Lot.objects.all()
    
    # Manejar valores de tipo "inf" o NaN que el LLM pueda enviar
    def clean_price(price):
        if price is None:
            return None
        try:
            # Si es string "inf" o float('inf'), lo tratamos como None para no filtrar ese límite
            if isinstance(price, (int, float)) and not math.isfinite(price):
                return None
            if isinstance(price, str) and price.lower() in ['inf', 'infinity', 'nan']:
                return None
            return float(price)
        except (ValueError, TypeError):
            return None

    price_min = clean_price(price_min)
    price_max = clean_price(price_max)

    if price_min is not None:
        lots = lots.filter(price__gte=price_min)
    if price_max is not None:
        lots = lots.filter(price__lte=price_max)
    if status:
        lots = lots.filter(status=status)
    if stage_name:
        lots = lots.filter(stage__name__icontains=stage_name)
    
    results = []
    for lot in lots[:10]: # Limitar a 10 resultados para el bot
        results.append({
            "id": lot.id,
            "code": lot.code,
            "price": f"${float(lot.price):,.2f}",
            "status": lot.get_status_display(),
            "stage": lot.stage.name,
            "area": f"{float(lot.area_m2)} m2",
            "buy_url": f"/lotes/buy/{lot.id}/",
            "map_url": f"/lotes/mapa/?lot_id={lot.id}"
        })
    return results

def get_lot_details(lot_id):
    """Obtiene detalles específicos de un lote incluyendo ubicación."""
    try:
        lot = Lot.objects.get(id=lot_id)
        return {
            "id": lot.id,
            "code": lot.code,
            "price": f"${float(lot.price):,.2f}",
            "description": lot.description or "Sin descripción disponible.",
            "latitude": lot.latitude,
            "longitude": lot.longitude,
            "status": lot.get_status_display(),
            "stage": lot.stage.name,
            "area": f"{float(lot.area_m2)} m2",
            "buy_url": f"/lotes/buy/{lot.id}/",
            "map_url": f"/lotes/mapa/?lot_id={lot.id}"
        }
    except Lot.DoesNotExist:
        return {"error": "Lote no encontrado"}

def get_project_stages():
    """Obtiene la lista de etapas del proyecto."""
    stages = Stage.objects.all()
    return [{"id": s.id, "name": s.name, "description": s.description} for s in stages]
