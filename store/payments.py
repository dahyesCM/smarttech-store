import hashlib
import hmac
import os
import time

import requests

from .models import Purchase

STRIPE_API = "https://api.stripe.com/v1/checkout/sessions"


def stripe_key():
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    return key if key.startswith(("sk_test_", "rk_test_")) else ""


def create_session(purchase, success_url, cancel_url):
    data = {
        "mode": "payment",
        "payment_method_types[0]": "card",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(purchase.reference),
    }
    for index, order in enumerate(purchase.orders.select_related("product")):
        prefix = f"line_items[{index}]"
        data[f"{prefix}[quantity]"] = order.quantity
        data[f"{prefix}[price_data][currency]"] = "pen"
        data[f"{prefix}[price_data][unit_amount]"] = int(order.unit_price * 100)
        data[f"{prefix}[price_data][product_data][name]"] = order.product.name
    response = requests.post(
        STRIPE_API, data=data, auth=(stripe_key(), ""), timeout=(4, 12),
        headers={"Idempotency-Key": str(purchase.reference)},
    )
    response.raise_for_status()
    return response.json()


def fetch_session(session_id):
    response = requests.get(f"{STRIPE_API}/{session_id}", auth=(stripe_key(), ""), timeout=(4, 12))
    response.raise_for_status()
    return response.json()


def confirm_stripe(purchase, session):
    if (
        session.get("id") == purchase.stripe_session
        and session.get("client_reference_id") == str(purchase.reference)
        and session.get("payment_status") == "paid"
        and session.get("amount_total") == int(purchase.total * 100)
        and session.get("currency") == "pen"
        and session.get("livemode") is False
    ):
        Purchase.objects.filter(pk=purchase.pk, payment=Purchase.Payment.PENDING).update(
            payment=Purchase.Payment.STRIPE_TEST
        )
        purchase.refresh_from_db()


def valid_signature(body, header):
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    values = [part.partition("=") for part in header.split(",")]
    timestamp = next((value for key, _, value in values if key == "t"), "")
    if not secret or not timestamp.isascii() or not timestamp.isdigit() or len(timestamp) > 12:
        return False
    if abs(time.time() - int(timestamp)) > 300:
        return False
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return any(key == "v1" and value.isascii() and hmac.compare_digest(expected, value)
               for key, _, value in values)
