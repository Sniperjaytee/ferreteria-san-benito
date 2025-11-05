from typing import Dict, Optional
from django.conf import settings
from core.models import ConfiguracionMoneda
from catalogo.models import Categoria
try:
    from django.contrib.staticfiles import finders as staticfiles_finders
except Exception:
    staticfiles_finders = None


def _detect_asset(path: str) -> Optional[str]:
    """Return relative static path if asset exists via staticfiles finders."""
    if not staticfiles_finders:
        return None
    try:
        abs_path = staticfiles_finders.find(path)
        return path if abs_path else None
    except Exception:
        return None


def cart(request) -> Dict[str, int]:
    """Provide cart item count, currency info, categories and branding assets."""
    cart = request.session.get('cart', {}) or {}
    try:
        count = sum(int(q) for q in cart.values())
    except Exception:
        count = 0

    config = ConfiguracionMoneda.obtener_configuracion()
    moneda_actual = request.session.get('moneda', config.moneda_principal)
    simbolo = config.simbolos.get(moneda_actual, moneda_actual)

    # Branding assets (logo, favicon) if present in static/img/
    logo_path = (
        _detect_asset('img/logo2.svg')
        or _detect_asset('img/logo2.png')
        or _detect_asset('img/logo2.jpg')
        or _detect_asset('img/logo.svg')
        or _detect_asset('img/logo.png')
        or _detect_asset('img/logo.jpg')
    )
    # Favicon preference order: logo2 (svg/png) -> favicon.svg -> favicon.ico
    favicon_path = (
        _detect_asset('img/logo2.svg')
        or _detect_asset('img/logo2.png')
        or _detect_asset('img/favicon.svg')
        or _detect_asset('img/favicon.ico')
    )

    monedas = config.monedas_mostrar or [config.moneda_principal]
    # Ensure EUR is available in the UI if code was recently added but config predates it
    if 'EUR' not in monedas:
        monedas = monedas + ['EUR']

    simbolos_map = config.simbolos or {}
    # Ensure EUR symbol exists in the map for older configs
    if 'EUR' not in simbolos_map:
        simbolos_map = dict(simbolos_map)
        simbolos_map['EUR'] = '€'

    return {
        'cart_count': count,
        'moneda_actual': moneda_actual,
        'simbolo_moneda': simbolo,
        'monedas_disponibles': monedas,
        'simbolos_map': simbolos_map,
        'categorias_nav': list(Categoria.objects.filter(activa=True).order_by('orden')[:8]),
        'logo_path': logo_path,
        'favicon_path': favicon_path,
        'whatsapp_phone': getattr(settings, 'WHATSAPP_PHONE', ''),
        'whatsapp_link': ('https://wa.me/' + getattr(settings, 'WHATSAPP_PHONE', '').strip()),
    }

