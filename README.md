<div align="center">

# SIGLO
**Sistema de Gestión de Lotes y Operaciones**

Aplicación web desarrollada con Django para gestionar lotes, ventas, usuarios y atención al cliente.


---

## Módulos

| Módulo | Descripción |
|--------|-------------|
| `LOTES/` | Gestión de lotes (núcleo del negocio) |
| `SALES/` | Ventas y transacciones comerciales |
| `USERS/` | Autenticación y gestión de usuarios |
| `PQRS/` | Peticiones, Quejas, Reclamos y Sugerencias |
| `CHATBOT/` | Asistente automático con IA (Hugging Face) |

---

## Stack

 **Backend:** Python · Django 6.0 · Django REST Framework <br>
 **Base de datos:** PostgreSQL <br>
 **Almacenamiento:** Cloudinary <br>
 **Correo:** Mailjet <br>
 **Servidor:** Gunicorn + Whitenoise <br>
 **Extras:** JWT, QR codes, exportación PDF

---

## Instalación

```bash
git clone https://github.com/emilymontec/SIGLO.git
cd SIGLO
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz:

```env
DATABASE_URL=postgres://usuario:password@localhost:5432/siglo_db
MJ_APIKEY_PUBLIC=...
MJ_APIKEY_PRIVATE=...
CLOUDINARY_NAME=...
CLOUDINARY_KEY=...
CLOUDINARY_SECRET=...
HUGGINGFACE_API_KEY=...
```

Luego:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Despliegue

El proyecto incluye un `Procfile` para plataformas como Heroku, Railway o Render:

```
web: gunicorn SIGLO.wsgi
```

---
## Para más información

[Documentación (descargar pdf)](https://github.com/emilymontec/SIGLO/raw/main/documentation.pdf)

</div>
