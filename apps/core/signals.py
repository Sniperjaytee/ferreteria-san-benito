from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def merge_cart_on_login(sender, user, request, **kwargs):
    """Al iniciar sesión, fusiona el carrito de sesión con el carrito en DB.

    - Pasa items de session['cart'] a pedidos.Carrito del usuario.
    - Vuelve a generar session['cart'] desde la DB para persistencia multi-sesión.
    """
    try:
        from pedidos.models import Carrito
        from catalogo.models import Producto
    except Exception:
        return

    session_cart = request.session.get('cart', {}) or {}

    # Volcar sesión -> DB
    for pid_str, qty in session_cart.items():
        try:
            pid = int(pid_str)
            qty = max(1, int(qty))
        except Exception:
            continue
        # Verificar existencia del producto
        try:
            Producto.objects.only('id').get(id=pid, activo=True)
        except Exception:
            continue
        item, created = Carrito.objects.get_or_create(usuario=user, producto_id=pid, defaults={'cantidad': qty})
        if not created:
            item.cantidad = max(item.cantidad or 0, 0) + qty
            item.save(update_fields=['cantidad'])

    # Regenerar sesión a partir de DB
    nuevos = {}
    for item in Carrito.objects.filter(usuario=user).select_related('producto'):
        try:
            nuevos[str(item.producto_id)] = int(item.cantidad)
        except Exception:
            continue
    request.session['cart'] = nuevos
    request.session.modified = True

