from django.urls import path
from .views import (
    my_purchases_list,
    purchase_detail,
    register_payment,
    validate_payment,
    admin_purchase_list,
    admin_payment_list,
    admin_purchase_create,
    admin_purchase_edit,
    admin_payment_create,
    admin_payment_edit,
    monthly_report,
)

urlpatterns = [
    path('mis-compras/', my_purchases_list, name='my_purchases_list'),
    path('detalle/<int:purchase_id>/', purchase_detail, name='purchase_detail'),
    path('pago/<int:purchase_id>/', register_payment, name='register_payment'),
    path('reporte-mensual/', monthly_report, name='monthly_report'),
    
    # Admin Ventas
    path('admin/purchases/', admin_purchase_list, name='admin_purchase_list'),
    path('admin/payments/', admin_payment_list, name='admin_payment_list'),
    path('admin/purchase/create/', admin_purchase_create, name='admin_purchase_create'),
    path('admin/purchase/edit/<int:purchase_id>/', admin_purchase_edit, name='admin_purchase_edit'),
    path('admin/payment/create/', admin_payment_create, name='admin_payment_create'),
    path('admin/payment/edit/<int:payment_id>/', admin_payment_edit, name='admin_payment_edit'),
    path('admin/payment/validate/<int:payment_id>/', validate_payment, name='admin_payment_validate'),
]
