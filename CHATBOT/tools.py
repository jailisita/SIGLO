import math
# from LOTES.models import Lot, Stage
from SIGLO.internal_data import get_mock_queryset

Lot = get_mock_queryset('Lot')
Stage = get_mock_queryset('Stage')

def search_lots(price_min=None, price_max=None, status='AVAILABLE', stage_name=None):
    """Filtra lotes por precio, estado y etapa."""
    lots = Lot.all()
    
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

    # Note: MockQuerySet filter is very basic, but it handles standard equality and __in.
    # For price ranges, I'll do a simple iteration for the mock.
    items = lots.items
    if price_min is not None:
        items = [i for i in items if i.price >= price_min]
    if price_max is not None:
        items = [i for i in items if i.price <= price_max]
    if status:
        items = [i for i in items if i.status == status]
    if stage_name:
        items = [i for i in items if stage_name.lower() in i.stage.name.lower()]
    
    results = []
    for lot in items[:10]: # Limitar a 10 resultados para el bot
        results.append({
            "id": lot.id,
            "code": lot.code,
            "price": f"${float(lot.price):,.2f}",
            "status": lot.status, # Simplified
            "stage": lot.stage.name,
            "area": f"{float(lot.area_m2)} m2",
            "buy_url": f"/lotes/buy/{lot.id}/",
            "map_url": f"/lotes/mapa/?lot_id={lot.id}"
        })
    return results

def get_lot_details(lot_id):
    """Obtiene detalles específicos de un lote incluyendo ubicación."""
    lot = Lot.filter(id=int(lot_id)).first()
    if lot:
        return {
            "id": lot.id,
            "code": lot.code,
            "price": f"${float(lot.price):,.2f}",
            "description": lot.description or "Sin descripción disponible.",
            "latitude": lot.latitude,
            "longitude": lot.longitude,
            "status": lot.status,
            "stage": lot.stage.name,
            "area": f"{float(lot.area_m2)} m2",
            "buy_url": f"/lotes/buy/{lot.id}/",
            "map_url": f"/lotes/mapa/?lot_id={lot.id}"
        }
    return {"error": "Lote no encontrado"}

def get_project_stages():
    """Obtiene la lista de etapas del proyecto."""
    stages = Stage.all()
    return [{"id": s.id, "name": s.name, "description": s.description} for s in stages]
