from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from PROJECT_INFO.views import error_404_view, error_500_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('PROJECT_INFO.urls')),
    path('accounts/', include('USERS.urls')),
    path('lotes/', include('LOTES.urls')),
    path('pqrs/', include('PQRS.urls')),
    path('sales/', include('SALES.urls')),
    path('chatbot/', include('CHATBOT.urls')),
]

handler404 = error_404_view
handler500 = error_500_view

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
