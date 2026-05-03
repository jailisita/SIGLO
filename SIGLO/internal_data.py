from decimal import Decimal
from SIGLO.mock_utils import MockModel, MockQuerySet
from SIGLO.mock_auth import MOCK_USERS

# Stages
STAGES = [
    MockModel(id=1, name="Lanzamiento", description="Etapa inicial de lanzamiento comercial."),
    MockModel(id=2, name="Preventa", description="Etapa de preventa con precios especiales."),
    MockModel(id=3, name="Construcción", description="El proyecto se encuentra en construcción."),
    MockModel(id=4, name="Entrega", description="Etapa final de entrega de lotes."),
]

# Lots
LOTS = []
for i in range(1, 21):
    status = 'AVAILABLE'
    if i in [2, 5, 8]: status = 'RESERVED'
    if i in [3, 7, 12]: status = 'SOLD'
    
    LOTS.append(MockModel(
        id=i,
        code=f"LOTE-{i:03d}",
        area_m2=Decimal(str(150 + (i * 5))),
        price=Decimal(str(50000000 + (i * 1000000))),
        status=status,
        stage=STAGES[i % 4],
        latitude=10.4 + (i * 0.001),
        longitude=-75.5 + (i * 0.001),
        description=f"Hermoso lote de {150 + (i * 5)}m2 en etapa {STAGES[i % 4].name}."
    ))

# Purchases and Payments
PURCHASES = [
    MockModel(id=1, client=MOCK_USERS['client'], total_amount=Decimal("60000000"), status='ACTIVE'),
]
PURCHASES[0].lots = MockQuerySet([LOTS[2]]) # LOTE-003 is SOLD

PAYMENTS = [
    MockModel(id=1, purchase=PURCHASES[0], amount=Decimal("10000000"), is_validated=True, payment_date=Decimal("1714759200")), # timestamp approximate
]

# PQRS
PQRS_LIST = [
    MockModel(id=1, client=MOCK_USERS['client'], type='P', message="¿Cuándo inician las obras?", status='OPEN', response="Aún no hay fecha."),
]

def get_mock_queryset(model_name):
    if model_name == 'Stage': return MockQuerySet(STAGES)
    if model_name == 'Lot': return MockQuerySet(LOTS)
    if model_name == 'Purchase': return MockQuerySet(PURCHASES)
    if model_name == 'Payment': return MockQuerySet(PAYMENTS)
    if model_name == 'PQRS': return MockQuerySet(PQRS_LIST)
    if model_name == 'User': return MockQuerySet(list(MOCK_USERS.values()))
    return MockQuerySet([])
