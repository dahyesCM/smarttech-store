from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import RegexValidator

from .models import Profile


class ShippingForm(forms.ModelForm):
    phone = forms.CharField(
        label="Número de celular", max_length=25,
        validators=[RegexValidator(r"^\+?[0-9 ()-]{7,25}$", "Escribe un número de celular válido.")],
    )

    class Meta:
        model = Profile
        fields = ("full_name", "phone", "address", "country", "city")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, autocomplete in {
            "full_name": "name", "phone": "tel", "address": "street-address",
            "country": "country-name", "city": "address-level2",
        }.items():
            self.fields[name].widget.attrs["autocomplete"] = autocomplete
        placeholders = {
            "full_name": "Ej. María Martínez", "phone": "Ej. +51 999 000 111",
            "address": "Calle, número, distrito y referencia", "country": "Ej. Perú", "city": "Ej. Lima",
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs["placeholder"] = placeholder
        self.fields["phone"].widget.attrs["inputmode"] = "tel"


class SignupForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico")

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario o correo electrónico"
        self.fields["username"].widget.attrs["placeholder"] = "Tu usuario o correo"

    def clean(self):
        identifier = self.cleaned_data.get("username", "")
        if "@" in identifier:
            users = get_user_model().objects
            if not users.filter(username=identifier).exists():
                names = list(users.filter(email__iexact=identifier).values_list("username", flat=True)[:2])
                if len(names) == 1:
                    self.cleaned_data["username"] = names[0]
        return super().clean()
