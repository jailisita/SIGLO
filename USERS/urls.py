from django.urls import path
from .views import (
    register_view,
    activate_account,
    CustomLoginView,
    logout_view,
    custom_password_reset,
    admin_user_list,
    profile_view,
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', register_view, name='register'),
    path('activar/<uidb64>/<token>/', activate_account, name='activate_account'),
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', custom_password_reset, name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('admin/users/', admin_user_list, name='admin_user_list'),
    path('profile/', profile_view, name='profile'),
]
