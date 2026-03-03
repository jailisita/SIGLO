from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('CLIENT', 'Cliente'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    document_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de Documento")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")

    def is_profile_complete(self):
        """Verifica si el usuario ha completado sus datos básicos."""
        return all([self.first_name, self.last_name, self.document_number])