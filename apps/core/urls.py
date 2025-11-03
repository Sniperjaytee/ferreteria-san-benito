from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('acceso/', views.acceso_requerido, name='acceso_requerido'),
    path('perfil/', views.perfil, name='perfil'),
    path('landing/', views.landing, name='landing'),
    path('ubicacion/', views.ubicacion, name='ubicacion'),
    path('preguntas/', views.preguntas, name='preguntas'),
    path('envios/', views.envios, name='envios'),
    path('contacto/', views.contacto, name='contacto'),
    path('vistas/', views.vistas, name='vistas'),
    path('moneda/', views.set_moneda, name='set_moneda'),
]
