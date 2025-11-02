from typing import Dict
from core.models import ConfiguracionMoneda


def cart(request) -> Dict[str, int]:
    """Provide cart item count and currency info from session to all templates."""
    cart = request.session.get('cart', {}) or {}
    try:
        count = sum(int(q) for q in cart.values())
    except Exception:
        count = 0

    config = ConfiguracionMoneda.obtener_configuracion()
    moneda_actual = request.session.get('moneda', config.moneda_principal)
    simbolo = config.simbolos.get(moneda_actual, moneda_actual)

    return {
        'cart_count': count,
        'moneda_actual': moneda_actual,
        'simbolo_moneda': simbolo,
        'monedas_disponibles': config.monedas_mostrar or [config.moneda_principal],
    }
