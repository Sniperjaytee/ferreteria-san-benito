from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('ubicacion/', views.ubicacion, name='ubicacion'),
    path('preguntas/', views.preguntas, name='preguntas'),
    path('envios/', views.envios, name='envios'),
    path('contacto/', views.contacto, name='contacto'),
    path('vistas/', views.vistas, name='vistas'),
    path('moneda/', views.set_moneda, name='set_moneda'),
]
