import os
import logging

from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.db import models
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from mailjet_rest import Client

from django.urls import reverse
from .forms import EmailUserCreationForm
from .decorators import admin_required, client_required


logger = logging.getLogger(__name__)


def send_mailjet_email(subject, html_content, to_email, to_name=''):
    mailjet = Client(
        auth=(os.environ.get('MJ_APIKEY_PUBLIC'), os.environ.get('MJ_APIKEY_PRIVATE')),
        version='v3.1'
    )
    data = {
        'Messages': [
            {
                'From': {'Email': settings.DEFAULT_FROM_EMAIL, 'Name': 'SIGLO'},
                'To': [{'Email': to_email, 'Name': to_name}],
                'Subject': subject,
                'HTMLPart': html_content,
            }
        ]
    }
    result = mailjet.send.create(data=data)
    return result


class CustomLoginView(LoginView):
    def form_invalid(self, form):
        username = self.request.POST.get('username')
        User = get_user_model()
        user = User.objects.filter(
            models.Q(email__iexact=username) | models.Q(username__iexact=username)
        ).first()

        if user and not user.is_active:
            form.is_unverified = True
            form._errors = {}
            return self.render_to_response(self.get_context_data(form=form))

        return super().form_invalid(form)


def register_view(request):
    form = EmailUserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.role = "CLIENT"
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        # Obtener el protocolo y dominio de la solicitud actual
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()
        
        activation_link = f"{protocol}://{domain}{reverse('activate_account', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Activa tu cuenta en SIGLO"
        context = {
            'user_name': user.get_full_name() or user.username,
            'activation_link': activation_link,
        }
        html_content = render_to_string('emails/activation_email.html', context)

        try:
            result = send_mailjet_email(
                subject=subject,
                html_content=html_content,
                to_email=user.email,
                to_name=user.get_full_name() or user.username,
            )
            print("Mailjet activacion response:", result.status_code, result.json())
        except Exception as e:
            logger.error(f"ERROR CORREO ACTIVACION: {type(e).__name__}: {e}")
            print(f"ERROR CORREO ACTIVACION: {type(e).__name__}: {e}")

        return render(
            request,
            "users/registration_pending.html",
            {
                "email": user.email,
                "activation_link": activation_link,
                "debug": settings.DEBUG,
            },
        )
    return render(request, "users/register.html", {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        User = get_user_model()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.add_message(
            request, messages.SUCCESS,
            "Tu cuenta ha sido activada correctamente. Ahora puedes iniciar sesión.",
            extra_tags='activated'
        )
        return redirect("login")

    messages.error(request, "El enlace de activación no es válido o ha expirado.")
    return redirect("login")


def custom_password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            users = User.objects.filter(email__iexact=email, is_active=True)

            for user in users:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                html_content = render_to_string('registration/password_reset_email.html', {
                    'user': user,
                    'reset_link': reset_link,
                    'uid': uid,
                    'token': token,
                    'protocol': 'https' if request.is_secure() else 'http',
                    'domain': request.get_host(),
                })

                try:
                    result = send_mailjet_email(
                        subject='Restablece tu contraseña - SIGLO',
                        html_content=html_content,
                        to_email=user.email,
                        to_name=user.get_full_name() or user.username,
                    )
                    print("Mailjet reset response:", result.status_code, result.json())
                except Exception as e:
                    print(f"ERROR RESET EMAIL: {type(e).__name__}: {e}")

            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'registration/password_reset_form.html', {'form': form})


@admin_required
def admin_user_list(request):
    User = get_user_model()
    users = User.objects.all().order_by("date_joined")
    return render(request, "users/admin_user_list.html", {"users": users})


@login_required
def profile_view(request):
    user = request.user

    if request.method == "POST":
        email = request.POST.get("email") or ""
        first_name = request.POST.get("first_name") or ""
        last_name = request.POST.get("last_name") or ""
        current_password = request.POST.get("current_password") or ""
        new_password = request.POST.get("new_password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if email and email != user.email:
            user.email = email

        user.first_name = first_name
        user.last_name = last_name

        if new_password or confirm_password:
            if not current_password or not user.check_password(current_password):
                messages.error(request, "La contraseña actual no es correcta.")
                return render(request, "users/profile.html", {
                    "form": {
                        "email": email or user.email,
                        "first_name": first_name or user.first_name,
                        "last_name": last_name or user.last_name,
                    }
                })
            if new_password != confirm_password:
                messages.error(request, "Las contraseñas nuevas no coinciden.")
                return render(request, "users/profile.html", {
                    "form": {
                        "email": email or user.email,
                        "first_name": first_name or user.first_name,
                        "last_name": last_name or user.last_name,
                    }
                })
            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)

        user.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("profile")

    context = {
        "form": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    }
    return render(request, "users/profile.html", context)


def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect("dashboard")