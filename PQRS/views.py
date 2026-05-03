from django.template.loader import render_to_string
from USERS.views import send_mailjet_email
from USERS.decorators import admin_required, client_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

# from .models import PQRS
from SIGLO.internal_data import get_mock_queryset

PQRS = get_mock_queryset('PQRS')


class PQRSCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PQRS
    fields = ['type', 'message']
    template_name = 'pqrs/pqrs_form.html'
    success_url = reverse_lazy('mypqrs_list')

    def test_func(self):
        return getattr(self.request.user, 'role', None) == 'CLIENT'

    def form_valid(self, form):
        form.instance.client = self.request.user
        response = super().form_valid(form)
        
        # Notificar al cliente sobre la creación de la PQRS
        subject = f"Hemos recibido tu {self.get_type_display(form.instance.type)}"
        context = {
            'user_name': self.request.user.get_full_name() or self.request.user.username,
            'pqrs_type': self.get_type_display(form.instance.type),
            'message': form.instance.message,
        }
        html_content = render_to_string('emails/pqrs_created_email.html', context)
        
        try:
            send_mailjet_email(
                subject=subject,
                html_content=html_content,
                to_email=self.request.user.email,
                to_name=self.request.user.get_full_name() or self.request.user.username,
            )
            messages.success(
                self.request, 
                "Solicitud registrada. Te hemos enviado un correo de confirmación. "
                "Si no lo encuentras, revisa tu carpeta de SPAM."
            )
        except Exception as e:
            print(f"Error enviando correo de creación de PQRS: {e}")
            messages.success(self.request, "Solicitud registrada correctamente.")
            
        return response

    def get_type_display(self, type_code):
        types = {
            'P': 'Petición',
            'Q': 'Queja',
            'R': 'Reclamo',
            'S': 'Sugerencia',
        }
        return types.get(type_code, 'Solicitud')


@client_required
def my_pqrs_list(request):
    items = PQRS.filter(client=request.user)
    return render(request, 'pqrs/my_pqrs_list.html', {'items': items})


@admin_required
def admin_pqrs_list(request):
    items = PQRS.all()
    return render(request, "pqrs/admin_pqrs_list.html", {"items": items})


@admin_required
def admin_pqrs_edit(request, pqrs_id):
    pq = get_object_or_404(PQRS, pk=pqrs_id)

    if request.method == "POST":
        data = request.POST
        old_status = pq.status
        old_response = pq.response
        
        pq.type = data.get("type") or pq.type
        pq.message = data.get("message") or pq.message
        pq.status = data.get("status") or pq.status
        pq.response = data.get("response") or pq.response
        pq.save()
        
        # Notificar al cliente si hay cambios importantes
        if pq.response != old_response or pq.status != old_status:
            subject = f"Actualización en tu {pq.get_type_display()}"
            context = {
                'user_name': pq.client.get_full_name() or pq.client.username,
                'pqrs_type': pq.get_type_display(),
                'status': pq.get_status_display(),
                'response': pq.response,
                'is_closed': pq.status == 'CLOSED'
            }
            html_content = render_to_string('emails/pqrs_updated_email.html', context)
            
            try:
                send_mailjet_email(
                    subject=subject,
                    html_content=html_content,
                    to_email=pq.client.email,
                    to_name=pq.client.get_full_name() or pq.client.username,
                )
                messages.success(request, f"Respuesta enviada correctamente al cliente {pq.client.username}.")
            except Exception as e:
                print(f"Error enviando correo de actualización de PQRS: {e}")
                messages.warning(request, "Cambios guardados, pero hubo un error al enviar la notificación por correo.")
        else:
            messages.success(request, "Cambios guardados correctamente.")

        return redirect("admin_pqrs_list")

    context = {
        "pq": pq,
        "form": {
            "type": pq.type,
            "message": pq.message,
            "status": pq.status,
            "response": pq.response,
        },
    }
    return render(request, "pqrs/admin_pqrs_form.html", context)
