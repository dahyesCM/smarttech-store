import hashlib
import hmac
import json
import os
import time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Order, Product, Profile, Purchase


class CheckoutTests(TestCase):
    shipping = {
        "full_name": "Cliente de Prueba", "phone": "+51 999 000 111",
        "address": "Avenida de Prueba 123", "country": "Perú", "city": "Lima",
    }

    def setUp(self):
        self.keyboard = Product.objects.create(sku="teclado", name="Teclado", price="189.90")
        self.mouse = Product.objects.create(sku="mouse", name="Mouse", price="79.90")
        self.user = get_user_model().objects.create_user("comprador", password="tienda-test-421")
        self.client = Client(enforce_csrf_checks=True)

    def post(self, url, data, **headers):
        return self.client.post(url, data, HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value, **headers)

    def test_guest_cart_signup_and_purchase(self):
        self.client.get("/")
        response = self.post(reverse("cart-change", args=[self.keyboard.pk]),
                             {"action": "add", "quantity": 2}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.json()["count"], 2)
        self.post(reverse("cart-change", args=[self.mouse.pk]), {"action": "add"})
        self.assertRedirects(self.client.get(reverse("checkout")), "/ingresar/?next=/compra/")
        password = "demo-tienda-481-demo"
        response = self.post(reverse("signup"), {
            **self.shipping, "username": "nueva", "email": "client@example.test",
            "password1": password, "password2": password,
        })
        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(Profile.objects.get(user__username="nueva").city, "Lima")
        self.assertContains(self.client.get(reverse("checkout")), self.shipping["address"])
        reference = self.client.session["checkout_reference"]
        data = {**self.shipping, "reference": reference}
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}):
            first = self.post(reverse("checkout"), data)
            second = self.post(reverse("checkout"), data)
        self.assertEqual(first.url, second.url)
        self.assertContains(self.client.get(first.url), "Compra exitosa")
        self.assertFalse(self.client.session.get("cart"))
        self.assertEqual(Purchase.objects.get().total, Decimal("459.70"))
        self.assertEqual(Order.objects.count(), 2)
        self.assertContains(self.client.get(reverse("history")), "Teclado")
        Product.objects.filter(pk=self.keyboard.pk).update(price="200.00")
        self.assertEqual(Order.objects.get(product=self.keyboard).unit_price, Decimal("189.90"))
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(first.url).status_code, 404)
        self.assertNotContains(self.client.get(reverse("history")), "Teclado")

    def test_stripe_waits_for_signed_confirmation(self):
        self.client.force_login(self.user)
        self.client.get("/")
        self.post(reverse("cart-change", args=[self.mouse.pk]), {"action": "add", "quantity": 1})
        self.client.get(reverse("checkout"))
        reference = self.client.session["checkout_reference"]
        stripe_url = "https://checkout.stripe.com/c/pay/test"
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_fake"}), patch(
            "store.views.payments.create_session",
            return_value={"url": stripe_url, "id": "cs_test_fake", "payment_status": "unpaid"},
        ):
            self.assertRedirects(
                self.post(reverse("checkout"), {**self.shipping, "reference": reference}),
                stripe_url, fetch_redirect_response=False,
            )
        self.assertEqual(Purchase.objects.get().payment, Purchase.Payment.PENDING)
        self.assertEqual(self.client.get(reverse("order-list")).json(), [])
        self.assertNotContains(self.client.get(reverse("history")), "Mouse")
        event = {"type": "checkout.session.completed", "data": {"object": {
            "id": "cs_test_fake", "payment_status": "paid", "client_reference_id": reference,
            "amount_total": 7990, "currency": "pen", "livemode": False,
        }}}
        endpoint = reverse("stripe-webhook")
        secret = "whsec_fake_for_tests"
        timestamp = str(int(time.time()))
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": secret}):
            body = json.dumps(event).encode()
            self.assertEqual(self.client.post(endpoint, body, content_type="application/json").status_code, 400)
            for amount in (1, 7990, 7990):
                event["data"]["object"]["amount_total"] = amount
                body = json.dumps(event).encode()
                signature = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
                response = self.client.post(endpoint, body, content_type="application/json",
                                            HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}")
                self.assertEqual(response.status_code, 200)
                expected = Purchase.Payment.STRIPE_TEST if amount == 7990 else Purchase.Payment.PENDING
                self.assertEqual(Purchase.objects.get().payment, expected)
        self.assertEqual(Order.objects.count(), 1)
        self.assertContains(self.client.get(reverse("receipt", args=[reference])), "Compra exitosa")
        self.assertContains(self.client.get(reverse("history")), "Mouse")
