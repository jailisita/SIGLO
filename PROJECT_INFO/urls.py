from django.urls import path
from .views import dashboard, admin_content
from USERS.views import admin_user_list

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin/content/', admin_content, name='admin_content'),
    path('panel/usuarios/', admin_user_list, name='admin_user_list_panel'),
]
