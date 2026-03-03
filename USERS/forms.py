from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "document_number", "phone_number")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombres"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellidos"}),
            "document_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Documento de Identidad"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = True


class EmailUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tucorreo@ejemplo.com"}),
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get("email")
        user.username = email
        user.email = email
        if commit:
            user.save()
        return user

