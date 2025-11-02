from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.productos_lista, name='productos_lista'),
    path('categoria/<slug:slug>/', views.productos_por_categoria, name='productos_por_categoria'),
    path('producto/<slug:slug>/', views.producto_detalle, name='producto_detalle'),
]

