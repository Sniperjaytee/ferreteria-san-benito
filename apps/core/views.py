from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from urllib.parse import quote
from catalogo.models import Producto, Categoria
from core.models import ConfiguracionMoneda
from django.urls import reverse
from .forms import SignupForm


def index(request):
    productos_destacados = Producto.objects.filter(activo=True, destacado=True).select_related('categoria')[:8]
    destacados_ids = productos_destacados.values_list('id', flat=True)
    productos_recientes = (
        Producto.objects.filter(activo=True)
        .exclude(id__in=destacados_ids)
        .select_related('categoria')
        .order_by('-created_at')[:12]
    )
    categorias = Categoria.objects.filter(activa=True).order_by('orden')[:12]
    return render(request, 'core/index.html', {
        'productos_destacados': productos_destacados,
        'productos_recientes': productos_recientes,
        'categorias': categorias,
    })


def registro(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'core:index'
            messages.success(request, 'Cuenta creada correctamente. ¡Bienvenido!')
            return redirect(next_url)
        else:
            # Mostrar un resumen de errores
            try:
                first_error = next(iter(form.errors.values()))
                if isinstance(first_error, (list, tuple)):
                    first_error = first_error[0]
                messages.error(request, f'Corrige los campos marcados. {first_error}')
            except Exception:
                messages.error(request, 'Corrige los campos marcados en el formulario.')
    else:
        form = SignupForm()
    return render(request, 'core/registro.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def landing(request):
    """Landing para comparar el look de kiuzzu dentro de Django."""
    return render(request, 'core/landing.html')


def ubicacion(request):
    query = getattr(settings, 'MAPS_QUERY', 'San Benito, Venezuela')
    embed_url = f"https://www.google.com/maps?q={quote(query)}&output=embed"
    return render(request, 'core/ubicacion.html', {
        'maps_query': query,
        'maps_embed_url': embed_url,
    })


def preguntas(request):
    return render(request, 'core/preguntas.html')


def envios(request):
    return render(request, 'core/envios.html')


def contacto(request):
    return render(request, 'core/contacto.html')


def acceso_requerido(request):
    """Página intermedia: para acceder a checkout debes registrarte/iniciar sesión."""
    next_url = request.GET.get('next') or reverse('pedidos:checkout')
    return render(request, 'core/acceso_requerido.html', {
        'next': next_url,
    })


def vistas(request):
    links = [
        ('Inicio', 'core:index'),
        ('Productos', 'catalogo:productos_lista'),
        ('Carrito', 'pedidos:carrito_ver'),
        ('Checkout', 'pedidos:checkout'),
        ('Login', 'login'),
        ('Registro', 'core:registro'),
        ('Ubicación', 'core:ubicacion'),
        ('Preguntas frecuentes', 'core:preguntas'),
        ('Envíos', 'core:envios'),
        ('Contacto', 'core:contacto'),
    ]
    return render(request, 'core/vistas.html', {'links': links})


def set_moneda(request):
    """Cambia la moneda activa para mostrar precios en el sitio."""
    # Importación y obtención segura de configuración
    try:
        config = ConfiguracionMoneda.obtener_configuracion()
    except Exception:
        config = None
    moneda = request.GET.get('m') or request.POST.get('m')
    # Accept configured monedas or include EUR as fallback for older configs
    monedas_permitidas = (config.monedas_mostrar or [config.moneda_principal])
    if 'EUR' not in monedas_permitidas:
        monedas_permitidas = monedas_permitidas + ['EUR']

    if config and moneda and moneda in monedas_permitidas:
        request.session['moneda'] = moneda
        request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'core:index'))


@login_required
def perfil(request):
    # Datos básicos del usuario y perfil extendido si existe
    usuario = getattr(request.user, 'usuario', None)
    contexto = {
        'username': request.user.username,
        'nombre_completo': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
        'perfil': usuario,
    }
    return render(request, 'core/perfil.html', contexto)
