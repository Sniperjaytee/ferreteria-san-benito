from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from catalogo.models import Producto, Categoria
from core.models import ConfiguracionMoneda


def index(request):
    productos_destacados = Producto.objects.filter(activo=True, destacado=True)[:8]
    categorias = Categoria.objects.filter(activa=True).order_by('orden')[:8]
    return render(request, 'core/index.html', {
        'productos_destacados': productos_destacados,
        'categorias': categorias,
    })


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            next_url = request.GET.get('next') or 'core:index'
            return redirect(next_url)
    else:
        form = UserCreationForm()
    return render(request, 'core/registro.html', {'form': form})


def landing(request):
    """Landing para comparar el look de kiuzzu dentro de Django."""
    return render(request, 'core/landing.html')


def ubicacion(request):
    return render(request, 'core/ubicacion.html')


def preguntas(request):
    return render(request, 'core/preguntas.html')


def envios(request):
    return render(request, 'core/envios.html')


def contacto(request):
    return render(request, 'core/contacto.html')


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
    if config and moneda and moneda in (config.monedas_mostrar or [config.moneda_principal]):
        request.session['moneda'] = moneda
        request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'core:index'))
