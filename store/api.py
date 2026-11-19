from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Order, Product, Purchase


class CatalogPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_staff


class OrderPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.method in SAFE_METHODS
        )


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "sku", "name", "description", "price", "active", "image_url", "ai_labels", "ar_target")


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    total = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "customer", "product", "product_name", "quantity",
                  "unit_price", "total", "status", "created_at")

    def get_fields(self):
        fields = super().get_fields()
        fields["customer"].required = False
        user = self.context["request"].user
        if not user.is_staff:
            for name in ("customer", "status"):
                fields[name].read_only = True
            fields["product"].queryset = Product.objects.filter(active=True)
        return fields

    def validate(self, attrs):
        if self.instance and self.instance.purchase_id and (
            {"customer", "product", "quantity"} & attrs.keys()
        ):
            raise ValidationError("Solo se puede actualizar el estado de un pedido de compra.")
        return attrs

    def create(self, validated_data):
        validated_data.setdefault("customer", self.context["request"].user)
        return super().create(validated_data)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [CatalogPermission]
    lookup_field = "sku"

    def get_queryset(self):
        products = Product.objects.all()
        return products if self.request.user.is_staff else products.filter(active=True)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError("El producto tiene pedidos asociados. Puedes ocultarlo del catálogo.") from exc


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]

    def get_queryset(self):
        orders = Order.objects.select_related("product", "customer").filter(
            Q(purchase__isnull=True) | ~Q(purchase__payment=Purchase.Payment.PENDING)
        )
        if self.request.user.is_staff:
            return orders
        return orders.filter(customer=self.request.user)

    def perform_destroy(self, instance):
        if instance.purchase_id:
            raise ValidationError("Conserva el historial de compra cambiando el estado a Cancelado.")
        instance.delete()
