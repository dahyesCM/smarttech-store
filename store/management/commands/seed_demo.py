from django.core.management.base import BaseCommand

from store.models import Product


class Command(BaseCommand):
    help = "Crea productos de demostración sin modificar los existentes."

    def handle(self, *args, **options):
        products = [
            ("teclado", "Teclado mecánico", "Formato compacto de 75 % con conexión USB-C.",
             "189.90", "computer keyboard, keypad", "SmartTechKeyboard"),
            ("mouse", "Mouse inalámbrico", "Sensor óptico y conexión por receptor USB.",
             "79.90", "mouse, computer mouse", ""),
            ("laptop", "Laptop de 14 pulgadas", "Pantalla Full HD y almacenamiento SSD.",
             "2499.00", "laptop, laptop computer, notebook, notebook computer", "SmartTechLaptop"),
        ]
        for sku, name, description, price, labels, target in products:
            Product.objects.get_or_create(sku=sku, defaults={
                "name": name, "description": description, "price": price,
                "ai_labels": labels, "ar_target": target,
            })
        self.stdout.write(self.style.SUCCESS("Catálogo de demostración disponible."))
