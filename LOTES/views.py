from USERS.decorators import admin_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

# from .models import Lot, Stage, LotImage
from SIGLO.internal_data import get_mock_queryset

Lot = get_mock_queryset('Lot')
Stage = get_mock_queryset('Stage')
LotImage = get_mock_queryset('LotImage')


def lot_list(request):
    lots = Lot.all() # order_by mocked
    stages = Stage.all()
    return render(request, "lotes/list.html", {"lots": lots, "stages": stages})


def map_view(request):
    lots = Lot.all()
    return render(request, "lotes/map.html", {"lots": lots})


def lot_list_api(request):
    lots = Lot.all()
    data = []
    for lot in lots:
        data.append(
            {
                "id": lot.id,
                "code": lot.code,
                "area_m2": float(lot.area_m2),
                "price": float(lot.price),
                "status": lot.status,
                "stage": lot.stage.name if lot.stage else "",
                "latitude": float(lot.latitude) if lot.latitude else None,
                "longitude": float(lot.longitude) if lot.longitude else None,
            }
        )
    return JsonResponse({"results": data})


@admin_required
def admin_lot_list(request):
    # from SALES.models import Purchase, Payment
    Purchase = get_mock_queryset('Purchase')
    Payment = get_mock_queryset('Payment')
    lots = Lot.all()
    
    # Attach recent payment info for each lot
    for lot in lots:
        if lot.status in ['RESERVED', 'SOLD']:
            # Find the most recent purchase that includes this lot
            purchase = Purchase.filter(lots=lot).first()
            if purchase:
                # Get the most recent payment for this purchase
                recent_payment = Payment.filter(purchase=purchase).first()
                lot.recent_payment = recent_payment
                lot.associated_purchase = purchase
        else:
            lot.recent_payment = None
            lot.associated_purchase = None

    return render(request, "lotes/admin_lot_list.html", {"lots": lots})


@admin_required
def admin_stage_list(request):
    stages = Stage.all()
    return render(request, "lotes/admin_stage_list.html", {"stages": stages})


@admin_required
def admin_lot_create(request):
    if request.method == "POST":
        data = request.POST
        files = request.FILES
        stage = get_object_or_404(Stage, pk=data.get("stage"))
        lot = Lot(
            code=data.get("code"),
            area_m2=data.get("area_m2") or 0,
            price=data.get("price") or 0,
            stage=stage,
            status=data.get("status") or "AVAILABLE",
            latitude=data.get("latitude") or 0,
            longitude=data.get("longitude") or 0,
            description=data.get("description") or "",
        )
        image_file = files.get("image")
        if image_file:
            lot.image = image_file
        lot.save()
        gallery_files = files.getlist("images")
        if gallery_files:
            for f in gallery_files:
                if f:
                    LotImage.objects.create(lot=lot, image=f)
        return redirect("admin_lot_list")

    stages = Stage.objects.all().order_by("name")
    context = {
        "form": {
            "code": "",
            "area_m2": "",
            "price": "",
            "stage": "",
            "status": "AVAILABLE",
            "latitude": "",
            "longitude": "",
            "description": "",
        },
        "stages": stages,
        "lot": None,
    }
    return render(request, "lotes/admin_lot_form.html", context)


@admin_required
def admin_lot_edit(request, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id)

    if request.method == "POST":
        data = request.POST
        files = request.FILES
        stage = get_object_or_404(Stage, pk=data.get("stage"))
        lot.code = data.get("code")
        lot.area_m2 = data.get("area_m2") or 0
        lot.price = data.get("price") or 0
        lot.stage = stage
        lot.status = data.get("status") or lot.status
        lot.latitude = data.get("latitude") or 0
        lot.longitude = data.get("longitude") or 0
        lot.description = data.get("description") or ""
        delete_ids = data.getlist("delete_images")
        if delete_ids:
            images_to_delete = LotImage.objects.filter(lot=lot, id__in=delete_ids)
            for img in images_to_delete:
                if img.image:
                    img.image.delete(save=False)
                img.delete()
        image_file = files.get("image")
        delete_main = data.get("delete_main_image")
        if image_file:
            if lot.image:
                lot.image.delete(save=False)
            lot.image = image_file
        elif delete_main:
            if lot.image:
                lot.image.delete(save=False)
            lot.image = None
        lot.save()
        gallery_files = files.getlist("images")
        if gallery_files:
            for f in gallery_files:
                if f:
                    LotImage.objects.create(lot=lot, image=f)
        return redirect("admin_lot_list")

    stages = Stage.objects.all().order_by("name")
    context = {
        "form": {
            "code": lot.code,
            "area_m2": lot.area_m2,
            "price": lot.price,
            "stage": lot.stage.id if lot.stage else "",
            "status": lot.status,
            "latitude": lot.latitude,
            "longitude": lot.longitude,
            "description": lot.description,
        },
        "stages": stages,
        "lot": lot,
    }
    return render(request, "lotes/admin_lot_form.html", context)


@admin_required
def admin_stage_create(request):
    if request.method == "POST":
        data = request.POST
        Stage.objects.create(
            name=data.get("name"),
            description=data.get("description"),
        )
        return redirect("admin_stage_list")

    context = {
        "form": {
            "name": "",
            "description": "",
        },
        "stage": None,
    }
    return render(request, "lotes/admin_stage_form.html", context)


@admin_required
def admin_stage_edit(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)

    if request.method == "POST":
        data = request.POST
        stage.name = data.get("name")
        stage.description = data.get("description")
        stage.save()
        return redirect("admin_stage_list")

    context = {
        "form": {
            "name": stage.name,
            "description": stage.description,
        },
        "stage": stage,
    }
    return render(request, "lotes/admin_stage_form.html", context)
