from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('EXECUTIVE', 'Ejecutivo'),
        ('CLIENT', 'Cliente'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')

    def save(self, *args, **kwargs):
        # Aseguramos que los administradores y ejecutivos puedan entrar al panel admin
        if getattr(self, 'role', None) in ['ADMIN', 'EXECUTIVE']:
            self.is_staff = True
        elif getattr(self, 'is_superuser', False):
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)