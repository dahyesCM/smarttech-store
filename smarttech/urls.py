from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from store import views
from store.forms import LoginForm
from store.api import OrderViewSet, ProductViewSet
from store.vision import classify

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", views.home, name="home"),
    path("ingresar/", auth_views.LoginView.as_view(authentication_form=LoginForm, redirect_authenticated_user=True), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", views.signup, name="signup"),
    path("perfil/", views.profile, name="profile"),
    path("carrito/", views.cart_page, name="cart"),
    path("carrito/<int:pk>/", views.cart_change, name="cart-change"),
    path("compra/", views.checkout, name="checkout"),
    path("compra/<uuid:reference>/", views.receipt, name="receipt"),
    path("pedidos/", views.history, name="history"),
    path("pagos/stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("admin/", admin.site.urls),
    path("api/classify/", classify, name="classify"),
    path("api/", include(router.urls)),
]
