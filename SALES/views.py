import os
import base64
import logging
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from USERS.decorators import admin_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.generic.edit import CreateView
from mailjet_rest import Client

from LOTES.models import Lot
from .models import Payment, Purchase

logger = logging.getLogger(__name__)


def send_mailjet_email(subject, html_content, to_email, to_name='', attachments=None):
    mailjet = Client(
        auth=(os.environ.get('MJ_APIKEY_PUBLIC'), os.environ.get('MJ_APIKEY_PRIVATE')),
        version='v3.1'
    )
    message = {
        'From': {'Email': settings.DEFAULT_FROM_EMAIL, 'Name': 'SIGLO'},
        'To': [{'Email': to_email, 'Name': to_name}],
        'Subject': subject,
        'HTMLPart': html_content,
    }
    if attachments:
        message['Attachments'] = attachments

    result = mailjet.send.create(data={'Messages': [message]})
    return result


def update_lots_status_for_purchase(purchase):
    lots = purchase.lots.all()
    if not lots:
        return

    payments = purchase.payment_set.filter(is_validated=True)
    total_paid = sum((p.amount for p in payments), Decimal("0"))
    sum_lot_prices = sum((l.price or Decimal("0") for l in lots), Decimal("0"))
    contractual_total = purchase.total_amount or sum_lot_prices

    targets = {}
    if sum_lot_prices > Decimal("0"):
        for l in lots:
            price = l.price or Decimal("0")
            targets[l.id] = (price / sum_lot_prices) * contractual_total
    else:
        for l in lots:
            targets[l.id] = Decimal("0")

    total_targets = sum(targets.values(), Decimal("0"))

    if total_paid >= total_targets and total_targets > Decimal("0"):
        for lot in lots:
            lot.status = "SOLD"
            lot.save()
        return

    if total_paid <= Decimal("0"):
        for lot in lots:
            lot.status = "AVAILABLE"
            lot.save()
        return

    remaining = total_paid
    ordered_lots = sorted(lots, key=lambda l: (targets.get(l.id, Decimal("0")), l.id), reverse=True)
    for lot in ordered_lots:
        target = targets.get(lot.id, Decimal("0"))
        if remaining >= target and target > Decimal("0"):
            lot.status = "SOLD"
            remaining -= target
        else:
            lot.status = "RESERVED"
        lot.save()


@login_required
def buy_lot(request, lot_id):
    user = request.user
    # Verificar si el usuario tiene sus datos completos
    if not user.first_name or not user.last_name or not user.email:
        messages.warning(request, "Por favor, completa tu perfil (nombre, apellido y correo) antes de realizar una compra.")
        return redirect('profile')

    lot = get_object_or_404(Lot, id=lot_id, status='AVAILABLE')
    purchase = Purchase.objects.create(client=request.user, total_amount=lot.price)
    purchase.lots.add(lot)
    update_lots_status_for_purchase(purchase)
    return redirect('purchase_detail', purchase_id=purchase.id)


@login_required
def my_purchases_list(request):
    purchases = (
        Purchase.objects.filter(client=request.user)
        .prefetch_related("lots")
        .order_by("-created_at")
    )
    return render(request, "sales/my_purchases_list.html", {"purchases": purchases})


@login_required
def purchase_detail(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, client=request.user)
    payments = purchase.payment_set.all().order_by('-payment_date')
    return render(request, 'sales/purchase_detail.html', {'purchase': purchase, 'payments': payments})


@login_required
def register_payment(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, client=request.user)

    if request.method == "POST":
        amount_raw = request.POST.get('amount')
        context = {'purchase': purchase}

        if amount_raw:
            try:
                amount = Decimal(str(amount_raw))
            except Exception:
                context['error'] = "Monto inválido."
                return render(request, 'sales/register_payment.html', context)

            if amount <= Decimal("0"):
                context['error'] = "El monto debe ser mayor a 0."
                return render(request, 'sales/register_payment.html', context)

            pending = purchase.balance()
            if amount > pending:
                context['error'] = f"El monto excede el saldo pendiente (${pending})."
                return render(request, 'sales/register_payment.html', context)

            payment = Payment.objects.create(purchase=purchase, amount=amount)
            payment.refresh_from_db()
            purchase.refresh_from_db()

            if purchase.client.email:
                subject = "Comprobante de pago - SIGLO"
                payment_date_str = payment.payment_date.strftime("%d/%m/%Y") if payment.payment_date else "Hoy"

                email_context = {
                    'user_name': purchase.client.get_full_name() or purchase.client.username,
                    'purchase_id': purchase.id,
                    'amount': payment.amount,
                    'payment_date': payment_date_str,
                    'balance': purchase.balance(),
                }
                html_content = render_to_string('emails/payment_receipt_email.html', email_context)
                attachments = []

                # QR code
                try:
                    import qrcode
                    qr_data = (
                        f"SIGLO-COMPROBANTE\n"
                        f"Pago: #{payment.id}\n"
                        f"Compra: #{purchase.id}\n"
                        f"Monto: ${payment.amount}\n"
                        f"Fecha: {payment_date_str}"
                    )
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    qr_buffer = BytesIO()
                    img.save(qr_buffer, format="PNG")
                    qr_b64 = base64.b64encode(qr_buffer.getvalue()).decode()
                    qr_buffer.close()
                    attachments.append({
                        'Filename': f'comprobante_qr_{payment.id}.png',
                        'ContentType': 'image/png',
                        'Base64Content': qr_b64,
                    })
                except Exception as e:
                    print(f"QR error: {e}")

                # PDF (Usando fpdf ya que está en requirements.txt)
                try:
                    from fpdf import FPDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt="Comprobante de pago SIGLO", ln=True, align='C')
                    pdf.ln(10)
                    pdf.cell(200, 10, txt=f"Compra: #{purchase.id}", ln=True)
                    pdf.cell(200, 10, txt=f"Cliente: {purchase.client.get_full_name() or purchase.client.email}", ln=True)
                    pdf.cell(200, 10, txt=f"Monto: ${payment.amount}", ln=True)
                    pdf.cell(200, 10, txt=f"Fecha: {payment_date_str}", ln=True)
                    pdf.cell(200, 10, txt=f"Saldo pendiente: ${purchase.balance()}", ln=True)
                    
                    pdf_buffer = BytesIO()
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    pdf_b64 = base64.b64encode(pdf_output).decode()
                    attachments.append({
                        'Filename': f'comprobante_pago_{payment.id}.pdf',
                        'ContentType': 'application/pdf',
                        'Base64Content': pdf_b64,
                    })
                except Exception as e:
                    print(f"PDF error (fpdf): {e}")

                try:
                    result = send_mailjet_email(
                        subject=subject,
                        html_content=html_content,
                        to_email=purchase.client.email,
                        to_name=purchase.client.get_full_name() or purchase.client.username,
                        attachments=attachments,
                    )
                    print("Mailjet pago response:", result.status_code, result.json())
                    messages.add_message(
                        request, messages.SUCCESS,
                        "Pago registrado con éxito. Te hemos enviado el comprobante a tu correo. "
                        "Si no lo encuentras, revisa tu carpeta de SPAM.",
                        extra_tags='payment_success'
                    )
                except Exception as e:
                    print(f"ERROR CORREO PAGO: {type(e).__name__}: {e}")
                    messages.warning(request, "Pago registrado, pero hubo un problema al enviar el correo.")
            else:
                messages.success(request, "Pago registrado con éxito.")

            # update_lots_status_for_purchase(purchase)  # Comentado para que solo el admin valide el estado del lote

        return redirect('purchase_detail', purchase_id=purchase.id)

    return render(request, 'sales/register_payment.html', {'purchase': purchase})


class PaymentCreateView(CreateView):
    model = Payment
    fields = ['purchase', 'amount']
    template_name = 'sales/payment_form.html'
    success_url = '/'


@admin_required
def validate_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.is_validated = True
    payment.save()
    update_lots_status_for_purchase(payment.purchase)
    return redirect("admin_purchase_list")


@admin_required
def admin_purchase_list(request):
    purchases = Purchase.objects.select_related("client").prefetch_related("lots").all().order_by("-created_at")
    return render(request, "sales/admin_purchase_list.html", {"purchases": purchases})


@admin_required
def admin_payment_list(request):
    payments = Payment.objects.select_related("purchase", "purchase__client").all().order_by("-payment_date")
    return render(request, "sales/admin_payment_list.html", {"payments": payments})


@admin_required
def monthly_report(request):
    from fpdf import FPDF
    from django.utils import timezone
    from django.http import HttpResponse
    from decimal import Decimal

    now = timezone.now()
    month_name = now.strftime("%B %Y")
    
    # Obtener pagos validados del mes actual
    payments = Payment.objects.filter(
        payment_date__month=now.month,
        payment_date__year=now.year,
        is_validated=True
    ).select_related('purchase', 'purchase__client')

    total_amount = sum((p.amount for p in payments), Decimal("0"))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Reporte Mensual de Ventas - {month_name}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Fecha", 1)
    pdf.cell(80, 10, "Cliente", 1)
    pdf.cell(40, 10, "Compra #", 1)
    pdf.cell(30, 10, "Monto", 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for p in payments:
        client_name = p.purchase.client.get_full_name() or p.purchase.client.email
        pdf.cell(40, 10, p.payment_date.strftime("%d/%m/%Y"), 1)
        pdf.cell(80, 10, str(client_name)[:40], 1)
        pdf.cell(40, 10, f"#{p.purchase.id}", 1)
        pdf.cell(30, 10, f"${p.amount}", 1)
        pdf.ln()

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(160, 10, "TOTAL RECAUDADO:", 0)
    pdf.cell(30, 10, f"${total_amount}", 0)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{now.strftime("%m_%Y")}.pdf"'
    response.write(pdf.output(dest='S').encode('latin-1'))
    return response


@admin_required
def admin_purchase_create(request):
    User = get_user_model()
    clients = User.objects.filter(role="CLIENT").order_by("email")
    lots = Lot.objects.all().order_by("code")

    if request.method == "POST":
        data = request.POST
        client = get_object_or_404(User, pk=data.get("client"))
        purchase = Purchase.objects.create(client=client, total_amount=data.get("total_amount") or 0)
        selected_lots = data.getlist("lots")
        if selected_lots:
            purchase.lots.set(Lot.objects.filter(pk__in=selected_lots))
            update_lots_status_for_purchase(purchase)
        return redirect("admin_purchase_list")

    context = {
        "clients": clients,
        "lots": lots,
        "form": {"client": "", "lots": [], "total_amount": ""},
        "purchase": None,
    }
    return render(request, "sales/admin_purchase_form.html", context)


@admin_required
def admin_purchase_edit(request, purchase_id):
    User = get_user_model()
    purchase = get_object_or_404(Purchase, pk=purchase_id)
    clients = User.objects.filter(role="CLIENT").order_by("email")
    lots = Lot.objects.all().order_by("code")

    if request.method == "POST":
        data = request.POST
        client = get_object_or_404(User, pk=data.get("client"))
        old_lot_ids = list(purchase.lots.values_list("id", flat=True))
        purchase.client = client
        purchase.total_amount = data.get("total_amount") or 0
        purchase.save()
        selected_lots = data.getlist("lots")
        if selected_lots:
            new_lots_qs = Lot.objects.filter(pk__in=selected_lots)
            purchase.lots.set(new_lots_qs)
            removed_ids = set(old_lot_ids) - set(new_lots_qs.values_list("id", flat=True))
            if removed_ids:
                Lot.objects.filter(id__in=removed_ids).update(status="AVAILABLE")
            update_lots_status_for_purchase(purchase)
        else:
            purchase.lots.clear()
            if old_lot_ids:
                Lot.objects.filter(id__in=old_lot_ids).update(status="AVAILABLE")
        return redirect("admin_purchase_list")

    context = {
        "clients": clients,
        "lots": lots,
        "form": {
            "client": purchase.client.id if purchase.client else "",
            "lots": [lot.id for lot in purchase.lots.all()],
            "total_amount": purchase.total_amount,
        },
        "purchase": purchase,
    }
    return render(request, "sales/admin_purchase_form.html", context)


@admin_required
def admin_payment_create(request):
    purchases = Purchase.objects.select_related("client").all().order_by("-created_at")

    if request.method == "POST":
        data = request.POST
        purchase = get_object_or_404(Purchase, pk=data.get("purchase"))
        try:
            amount = Decimal(str(data.get("amount") or "0"))
        except Exception:
            return render(request, "sales/admin_payment_form.html", {
                "purchases": purchases,
                "form": {"purchase": purchase.id, "amount": data.get("amount")},
                "payment": None,
                "error": "Monto inválido.",
            })
        if amount <= Decimal("0"):
            return render(request, "sales/admin_payment_form.html", {
                "purchases": purchases,
                "form": {"purchase": purchase.id, "amount": data.get("amount")},
                "payment": None,
                "error": "El monto debe ser mayor a 0.",
            })
        if amount > purchase.balance():
            return render(request, "sales/admin_payment_form.html", {
                "purchases": purchases,
                "form": {"purchase": purchase.id, "amount": data.get("amount")},
                "payment": None,
                "error": f"El monto excede el saldo pendiente (${purchase.balance()}).",
            })
        Payment.objects.create(purchase=purchase, amount=amount)
        update_lots_status_for_purchase(purchase)
        return redirect("admin_payment_list")

    context = {
        "purchases": purchases,
        "form": {"purchase": "", "amount": ""},
        "payment": None,
    }
    return render(request, "sales/admin_payment_form.html", context)


@admin_required
def admin_payment_edit(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    purchases = Purchase.objects.select_related("client").all().order_by("-created_at")

    if request.method == "POST":
        data = request.POST
        purchase = get_object_or_404(Purchase, pk=data.get("purchase"))
        try:
            amount = Decimal(str(data.get("amount") or "0"))
        except Exception:
            return render(request, "sales/admin_payment_form.html", {
                "purchases": purchases,
                "form": {"purchase": purchase.id, "amount": data.get("amount")},
                "payment": payment,
                "error": "Monto inválido.",
            })
        
        # Al editar, sumamos el monto actual del pago al balance para validar el nuevo monto
        current_balance = payment.purchase.balance() + payment.amount
        if amount > current_balance:
            return render(request, "sales/admin_payment_form.html", {
                "purchases": purchases,
                "form": {"purchase": purchase.id, "amount": data.get("amount")},
                "payment": payment,
                "error": f"El monto excede el saldo disponible (${current_balance}).",
            })
            
        payment.purchase = purchase
        payment.amount = amount
        payment.save()
        update_lots_status_for_purchase(purchase)
        return redirect("admin_payment_list")

    context = {
        "purchases": purchases,
        "form": {
            "purchase": payment.purchase.id,
            "amount": payment.amount,
        },
        "payment": payment,
    }
    return render(request, "sales/admin_payment_form.html", context)