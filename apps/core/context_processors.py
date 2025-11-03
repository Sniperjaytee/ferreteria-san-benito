from typing import Dict, Optional
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
        _detect_asset('img/logo.svg')
        or _detect_asset('img/logo.png')
        or _detect_asset('img/logo.jpg')
    )
    favicon_path = _detect_asset('img/favicon.ico')

    return {
        'cart_count': count,
        'moneda_actual': moneda_actual,
        'simbolo_moneda': simbolo,
        'monedas_disponibles': config.monedas_mostrar or [config.moneda_principal],
        'simbolos_map': config.simbolos,
        'categorias_nav': list(Categoria.objects.filter(activa=True).order_by('orden')[:8]),
        'logo_path': logo_path,
        'favicon_path': favicon_path,
    }
