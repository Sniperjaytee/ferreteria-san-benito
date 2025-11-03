from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Importar las rutas del app "core" desde el directorio apps/
    # settings.py ya agrega BASE_DIR/apps al sys.path, por lo que el módulo es "core.urls"
    path('', include(('core.urls', 'core'))),
    path('catalogo/', include(('catalogo.urls', 'catalogo'))),
    path('pedidos/', include(('pedidos.urls', 'pedidos'))),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
