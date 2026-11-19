import json
from uuid import uuid4

import requests
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from . import payments
from .cart import cart_rows, photo_url
from .forms import ShippingForm, SignupForm
from .models import Order, Product, Profile, Purchase


def home(request):
    products = [{"item": product, "photo": photo_url(product)}
                for product in Product.objects.filter(active=True)]
    return render(request, "store/home.html", {"products": products})


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("profile")
    data = request.POST if request.method == "POST" else None
    form, shipping = SignupForm(data), ShippingForm(data)
    if request.method == "POST" and all([form.is_valid(), shipping.is_valid()]):
        with transaction.atomic():
            user = form.save()
            profile = shipping.save(commit=False)
            profile.user = user
            profile.save()
        login(request, user)
        return redirect("cart" if request.session.get("cart") else "profile")
    return render(request, "registration/signup.html", {"form": form, "shipping": shipping})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    details = Profile.objects.filter(user=request.user).first()
    form = ShippingForm(request.POST if request.method == "POST" else None, instance=details)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.user = request.user
        saved.save()
        messages.success(request, "Guardamos tus datos de entrega.")
        return redirect("profile")
    return render(request, "store/profile.html", {"form": form, "profile": details})


def cart_page(request):
    rows, total = cart_rows(request)
    return render(request, "store/cart.html", {"rows": rows, "total": total})


@require_POST
def cart_change(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = request.session.get("cart", {})
    key = str(product.pk)
    action = request.POST.get("action")
    if action == "remove":
        cart.pop(key, None)
    elif action in {"add", "update"} and product.active:
        try:
            quantity = int(request.POST.get("quantity", "1"))
            if not 1 <= quantity <= 99:
                raise ValueError
        except ValueError:
            return JsonResponse({"detail": "Elige una cantidad del 1 al 99."}, status=400)
        cart[key] = min(99, cart.get(key, 0) + quantity) if action == "add" else quantity
    else:
        return JsonResponse({"detail": "Este producto ya no está disponible."}, status=400)
    request.session["cart"] = cart
    request.session.pop("checkout_reference", None)
    if request.headers.get("Accept") == "application/json":
        result = {"count": sum(cart.values()), "name": product.name}
        if action != "add":
            rows, total = cart_rows(request)
            result.update(
                count=sum(row["quantity"] for row in rows), total=str(total),
                subtotal=str(product.price * cart.get(key, 0)),
            )
        return JsonResponse(result)
    return redirect("cart")


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request):
    rows, total = cart_rows(request)
    if not rows:
        return redirect("cart")

    reference = request.session.get("checkout_reference")
    if not reference:
        reference = request.session["checkout_reference"] = str(uuid4())
    stripe = bool(payments.stripe_key())
    data = request.POST if request.method == "POST" else None
    details = Profile.objects.filter(user=request.user).first()
    form = ShippingForm(data, instance=details)
    if request.method == "POST" and form.is_valid():
        if request.POST.get("reference") != reference:
            messages.error(request, "El carrito cambió. Revisa el resumen antes de continuar.")
            return redirect("checkout")
        with transaction.atomic():
            purchase, created = Purchase.objects.get_or_create(
                customer=request.user, reference=reference,
                defaults={**form.cleaned_data, "total": total,
                          "payment": Purchase.Payment.PENDING if stripe else Purchase.Payment.DEMO},
            )
            if created:
                Order.objects.bulk_create([
                    Order(customer=request.user, purchase=purchase, product=row["product"],
                          quantity=row["quantity"], unit_price=row["product"].price)
                    for row in rows
                ])
        if purchase.payment != Purchase.Payment.PENDING:
            return redirect("receipt", reference=reference)
        if not stripe:
            form.add_error(None, "El pago con tarjeta no está disponible en este momento.")
        else:
            try:
                success = request.build_absolute_uri(reverse("receipt", args=[reference]))
                cancel = request.build_absolute_uri(reverse("checkout"))
                session = (payments.fetch_session(purchase.stripe_session) if purchase.stripe_session
                           else payments.create_session(purchase, success, cancel))
                if session.get("status") == "expired":
                    request.session.pop("checkout_reference", None)
                    messages.error(request, "La sesión de Stripe venció. Puedes iniciar un pago nuevo.")
                    return redirect("checkout")
                if session.get("payment_status") == "paid":
                    return redirect("receipt", reference=reference)
                if not session.get("url") or not session["url"].startswith("https://checkout.stripe.com/"):
                    raise ValueError("Sesión de pago no disponible")
                Purchase.objects.filter(pk=purchase.pk).update(stripe_session=session["id"])
                return redirect(session["url"])
            except (requests.RequestException, KeyError, ValueError):
                form.add_error(None, "No se pudo abrir el pago con tarjeta. Intenta de nuevo.")
    return render(request, "store/checkout.html",
                  {"form": form, "rows": rows, "total": total, "stripe": stripe, "reference": reference})


@login_required
def receipt(request, reference):
    purchase = get_object_or_404(Purchase, reference=reference, customer=request.user)
    if purchase.payment == Purchase.Payment.PENDING and purchase.stripe_session and payments.stripe_key():
        try:
            payments.confirm_stripe(purchase, payments.fetch_session(purchase.stripe_session))
        except (requests.RequestException, ValueError):
            pass
    if purchase.payment != Purchase.Payment.PENDING and request.session.get("checkout_reference") == str(reference):
        request.session.pop("cart", None)
        request.session.pop("checkout_reference", None)
    return render(request, "store/receipt.html", {"purchase": purchase})


@login_required
def history(request):
    purchases = Purchase.objects.filter(customer=request.user).exclude(payment=Purchase.Payment.PENDING)
    purchases = purchases.prefetch_related("orders__product")
    older = Order.objects.filter(customer=request.user, purchase__isnull=True).select_related("product")
    return render(request, "store/history.html", {"purchases": purchases, "older": older})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not payments.valid_signature(request.body, request.headers.get("Stripe-Signature", "")):
        return HttpResponse(status=400)
    try:
        event = json.loads(request.body)
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            purchase = Purchase.objects.filter(stripe_session=session["id"]).first()
            if purchase:
                payments.confirm_stripe(purchase, session)
    except (KeyError, ValueError, TypeError):
        return HttpResponse(status=400)
    return HttpResponse(status=200)
