from USERS.decorators import admin_required
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import redirect, render

from LOTES.models import Lot, Stage
from PQRS.models import PQRS
from SALES.models import Payment, Purchase
from .models import ProjectInfo


def dashboard(request):
    if request.user.is_authenticated:
        role = getattr(request.user, "role", "CLIENT")

        if role in ["ADMIN", "EXECUTIVE"]:
            User = get_user_model()

            users_total = User.objects.count()
            clients_total = User.objects.filter(role="CLIENT").count()
            admins_total = User.objects.filter(role__in=["ADMIN", "EXECUTIVE"]).count()

            lots_total = Lot.objects.count()
            lots_available = Lot.objects.filter(status="AVAILABLE").count()
            lots_sold = Lot.objects.filter(status="SOLD").count()

            purchases_total = Purchase.objects.count()
            total_purchase_amount = (
                Purchase.objects.aggregate(total=Sum("total_amount"))["total"] or 0
            )
            total_paid_amount = (
                Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
            )

            pqrs_total = PQRS.objects.count()
            pqrs_open = PQRS.objects.filter(status="OPEN").count()

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

        purchases = Purchase.objects.filter(client=request.user)
        lots_owned_count = purchases.values("lots").distinct().count()
        total_purchase_amount = (
            purchases.aggregate(total=Sum("total_amount"))["total"] or 0
        )
        total_paid_amount = (
            Payment.objects.filter(purchase__client=request.user).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        balance_total = total_purchase_amount - total_paid_amount

        pqrs_open = PQRS.objects.filter(client=request.user, status="OPEN").count()

        context = {
            "purchases_total": purchases.count(),
            "lots_owned_count": lots_owned_count,
            "total_purchase_amount": total_purchase_amount,
            "total_paid_amount": total_paid_amount,
            "balance_total": balance_total,
            "pqrs_open": pqrs_open,
        }
        return render(request, "project_info/client_dashboard.html", context)

<<<<<<< HEAD
    stages = Stage.objects.all()
=======
    desired_names = ["Lanzamiento", "Preventa", "Construcción", "Entrega"]
    stages_qs = Stage.objects.filter(name__in=desired_names)
    stage_map = {s.name: s for s in stages_qs}
    stages = [stage_map[name] for name in desired_names if name in stage_map]
    
    # Fallback if no stages found to prevent empty list
    if not stages:
        stages = Stage.objects.all()[:4]
        
>>>>>>> 8075e104d53d3e3e8143cd782142fc340434df23
    return render(request, "project_info/dashboard.html", {"stages": stages})


def error_404_view(request, exception):
    return render(request, "404.html", status=404)


@admin_required
def admin_content(request):
    return redirect('dashboard')
