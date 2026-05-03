from USERS.decorators import admin_required
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import redirect, render

# from LOTES.models import Lot, Stage
# from PQRS.models import PQRS
# from SALES.models import Payment, Purchase
# from .models import ProjectInfo
from SIGLO.internal_data import get_mock_queryset

Lot = get_mock_queryset('Lot')
Stage = get_mock_queryset('Stage')
PQRS = get_mock_queryset('PQRS')
Purchase = get_mock_queryset('Purchase')
Payment = get_mock_queryset('Payment')
UserMock = get_mock_queryset('User')


def dashboard(request):
    if request.user.is_authenticated:
        role = getattr(request.user, "role", "CLIENT")

        if role in ["ADMIN", "EXECUTIVE"]:
            User = get_user_model()

            users_total = UserMock.count()
            clients_total = UserMock.filter(role="CLIENT").count()
            admins_total = UserMock.filter(role__in=["ADMIN", "EXECUTIVE"]).count()

            lots_total = Lot.count()
            lots_available = Lot.filter(status="AVAILABLE").count()
            lots_sold = Lot.filter(status="SOLD").count()

            purchases_total = Purchase.count()
            total_purchase_amount = (
                Purchase.aggregate(total=Sum("total_amount"))["total"] or 0
            )
            total_paid_amount = (
                Payment.aggregate(total=Sum("amount"))["total"] or 0
            )

            pqrs_total = PQRS.count()
            pqrs_open = PQRS.filter(status="OPEN").count()

            context = {
                "users_total": users_total,
                "clients_total": clients_total,
                "admins_total": admins_total,
                "lots_total": lots_total,
                "lots_available": lots_available,
                "lots_sold": lots_sold,
                "purchases_total": purchases_total,
                "total_purchase_amount": total_purchase_amount,
                "total_paid_amount": total_paid_amount,
                "pqrs_total": pqrs_total,
                "pqrs_open": pqrs_open,
            }
            return render(request, "project_info/admin_dashboard.html", context)

        purchases = Purchase.filter(client=request.user)
        lots_owned_count = purchases.count() # Simplified mock
        total_purchase_amount = (
            purchases.aggregate(total=Sum("total_amount"))["total"] or 0
        )
        total_paid_amount = (
            Payment.filter(purchase__client=request.user).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        balance_total = total_purchase_amount - total_paid_amount

        pqrs_open = PQRS.filter(client=request.user, status="OPEN").count()

        context = {
            "purchases_total": purchases.count(),
            "lots_owned_count": lots_owned_count,
            "total_purchase_amount": total_purchase_amount,
            "total_paid_amount": total_paid_amount,
            "balance_total": balance_total,
            "pqrs_open": pqrs_open,
        }
        return render(request, "project_info/client_dashboard.html", context)

    desired_names = ["Lanzamiento", "Preventa", "Construcción", "Entrega"]
    stages_qs = Stage.filter(name__in=desired_names)
    stage_map = {s.name: s for s in stages_qs}
    stages = [stage_map[name] for name in desired_names if name in stage_map]
    
    # Fallback if no stages found to prevent empty list
    if not stages:
        stages = Stage.all()[:4]
    return render(request, "project_info/dashboard.html", {"stages": stages})


def error_404_view(request, exception):
    return render(request, "404.html", status=404)


@admin_required
def admin_content(request):
    return redirect('dashboard')
