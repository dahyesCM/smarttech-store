from django.contrib import admin
from django.db.models import Q

from .models import Order, Product, Purchase


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "price", "active", "ar_target")
    list_filter = ("active",)
    search_fields = ("name", "sku")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "product", "quantity", "total", "status")
    list_filter = ("status",)
    search_fields = ("customer__username", "product__name")
    readonly_fields = ("unit_price", "total", "created_at", "purchase")
    actions = None

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            Q(purchase__isnull=True) | ~Q(purchase__payment=Purchase.Payment.PENDING)
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.purchase_id:
            return (*self.readonly_fields, "customer", "product", "quantity")
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.purchase_id) and super().has_delete_permission(request, obj)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "total", "payment", "created_at")
    readonly_fields = ("customer", "reference", "total", "payment", "stripe_session",
                       "created_at", "full_name", "phone", "address", "country", "city")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "Gestión de SmartTech Store"
