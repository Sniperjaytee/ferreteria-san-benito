from django.urls import path
from . import views

urlpatterns = [
    path('carrito/', views.carrito_ver, name='carrito_ver'),
    path('carrito/agregar/', views.carrito_agregar, name='carrito_agregar'),
    path('carrito/actualizar/', views.carrito_actualizar, name='carrito_actualizar'),
    path('carrito/eliminar/', views.carrito_eliminar, name='carrito_eliminar'),
    path('carrito/limpiar/', views.carrito_limpiar, name='carrito_limpiar'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedido/<str:numero_pedido>/', views.pedido_confirmacion, name='pedido_confirmacion'),
]

