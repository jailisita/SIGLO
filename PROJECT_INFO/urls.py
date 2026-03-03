from django.urls import path
from .views import dashboard, admin_content, download_monthly_report

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin/content/', admin_content, name='admin_content'),
    path('reporte-mensual/', download_monthly_report, name='download_monthly_report'),
]
