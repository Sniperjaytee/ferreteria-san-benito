from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import re

from .models import Usuario


TelefonoVzlaValidator = RegexValidator(
    # Aceptar +58 con espacios opcionales y dígitos; normalizamos en clean_telefono
    regex=r"^\+?58[ \d]{10,}$",
    message="El número de teléfono debe ser de Venezuela (+58) y contener 10 dígitos.",
)


class SignupForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150, required=False)
    last_name = forms.CharField(label="Apellido", max_length=150, required=False)
    email = forms.EmailField(label="Correo electrónico", required=True)
    cedula = forms.CharField(label="Cédula", max_length=10, required=True,
                             help_text="Solo números, sin puntos ni guiones")
    telefono = forms.CharField(
        label="Teléfono",
        help_text="Formato: +58 4127715553",
        validators=[TelefonoVzlaValidator],
        required=True,
        max_length=16,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "cedula", "telefono", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.first_name = self.cleaned_data.get("first_name", "").strip()
        user.last_name = self.cleaned_data.get("last_name", "").strip()
        # Asegurar que sean usuarios estándar
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        if commit:
            user.save()
            # Crear/actualizar perfil Usuario
            Usuario.objects.update_or_create(
                user=user,
                defaults={
                    "cedula": self.cleaned_data["cedula"].strip(),
                    "telefono": self.cleaned_data["telefono"].strip(),
                },
            )
        return user

    def clean_cedula(self):
        ced = (self.cleaned_data.get("cedula") or "").strip()
        if not ced.isdigit():
            raise forms.ValidationError("Solo números, sin puntos ni guiones.")
        if len(ced) < 7:
            raise forms.ValidationError("La cédula debe tener al menos 7 dígitos.")
        if len(ced) > 10:
            raise forms.ValidationError("La cédula no puede exceder 10 dígitos.")
        if Usuario.objects.filter(cedula=ced).exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return ced

    def clean_telefono(self):
        raw = (self.cleaned_data.get("telefono") or "").strip()
        # Mantener sólo dígitos para validar longitud
        digits = re.sub(r"\D", "", raw)
        # Aceptar con o sin +58, pero forzar formato final '+58 1234567890'
        if digits.startswith("58"):
            local = digits[2:]
        elif raw.startswith("+58"):
            # por si viene mal segmentado
            local = digits
            if local.startswith("58"):
                local = local[2:]
        else:
            local = digits
        if len(local) != 10:
            raise forms.ValidationError("Debe contener 10 dígitos luego del código +58.")
        return "+58 " + local
