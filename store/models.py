from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    sku = models.SlugField(unique=True, max_length=40)
    name = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción")
    price = models.DecimalField("precio", max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    active = models.BooleanField("visible", default=True)
    image_url = models.URLField("URL de foto", max_length=500, blank=True)
    ai_labels = models.CharField("etiquetas de IA", max_length=300, blank=True,
                                 help_text="Etiquetas en inglés separadas por comas.")
    ar_target = models.SlugField("marcador de RA", max_length=60, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "producto"

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmado"
        DELIVERED = "delivered", "Entregado"
        CANCELLED = "cancelled", "Cancelado"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                 verbose_name="cliente")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="producto")
    purchase = models.ForeignKey("Purchase", null=True, blank=True, editable=False,
                                 on_delete=models.PROTECT, related_name="orders")
    quantity = models.PositiveIntegerField("cantidad", validators=[MinValueValidator(1)])
    unit_price = models.DecimalField("precio unitario", max_digits=10, decimal_places=2,
                                     editable=False)
    status = models.CharField("estado", max_length=10, choices=Status, default=Status.PENDING)
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pedido"

    @property
    def total(self):
        return self.quantity * self.unit_price

    def save(self, **kwargs):
        if self._state.adding or (
            self.pk and type(self).objects.exclude(product_id=self.product_id).filter(pk=self.pk).exists()
        ):
            self.unit_price = self.product.price
        super().save(**kwargs)

    def __str__(self):
        return f"Pedido #{self.pk}"


class ShippingDetails(models.Model):
    full_name = models.CharField("nombre completo", max_length=120)
    phone = models.CharField("número de celular", max_length=25)
    address = models.CharField("dirección", max_length=220)
    country = models.CharField("país", max_length=75)
    city = models.CharField("ciudad", max_length=75)

    class Meta:
        abstract = True


class Profile(ShippingDetails):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Purchase(ShippingDetails):
    class Payment(models.TextChoices):
        PENDING = "pending", "Pendiente"
        DEMO = "demo", "Pago simulado"
        STRIPE_TEST = "stripe_test", "Stripe · prueba"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reference = models.UUIDField(unique=True, editable=False)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    payment = models.CharField(max_length=12, choices=Payment, default=Payment.PENDING)
    stripe_session = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Compra #{self.pk}"
