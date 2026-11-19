from decimal import Decimal

from django.templatetags.static import static

from .models import Product


def photo_url(product):
    assets = {"teclado": "teclado.jpg", "mouse": "mouse.jpg", "laptop": "laptop.jpg"}
    if product.image_url:
        return product.image_url
    filename = assets.get(product.sku)
    return static(f"store/photos/{filename}") if filename else ""


def cart_rows(request):
    cart = request.session.get("cart", {})
    products = Product.objects.filter(pk__in=cart, active=True)
    rows = [
        {"product": product, "quantity": cart[str(product.pk)],
         "subtotal": product.price * cart[str(product.pk)], "photo": photo_url(product)}
        for product in products
    ]
    return rows, sum((row["subtotal"] for row in rows), Decimal("0.00"))


def cart_context(request):
    return {"cart_count": sum(request.session.get("cart", {}).values())}
