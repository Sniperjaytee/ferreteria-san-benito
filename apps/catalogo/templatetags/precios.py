from decimal import Decimal
from django import template

register = template.Library()


@register.simple_tag
def precio_en_moneda(producto, moneda_destino):
    """Devuelve el precio del producto convertido a la moneda destino.
    Uso en templates:
      {% load precios %}
      {% precio_en_moneda producto "USD" as p %}
    """
    try:
        if not producto or not moneda_destino:
            return Decimal('0.00')
        return producto.obtener_precio_en_moneda(moneda_destino)
    except Exception:
        return Decimal('0.00')

