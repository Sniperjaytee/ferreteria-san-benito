from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal
from catalogo.models import Producto
from .models import Pedido, ItemPedido
from core.models import ConfiguracionMoneda, TasaCambio


def _get_cart(session):
    cart = session.get('cart')
    if cart is None or not isinstance(cart, dict):
        cart = {}
        session['cart'] = cart
    return cart


def carrito_ver(request):
    cart = _get_cart(request.session)
    items = []
    total = Decimal('0.00')
    config = ConfiguracionMoneda.obtener_configuracion()
    moneda_actual = request.session.get('moneda', config.moneda_principal)
    if cart:
        ids = [int(pid) for pid in cart.keys()]
        productos = {p.id: p for p in Producto.objects.filter(id__in=ids)}
        for str_id, qty in cart.items():
            pid = int(str_id)
            producto = productos.get(pid)
            if not producto:
                continue
            qty = int(qty)
            subtotal = producto.precio * qty
            total += subtotal
            # precio convertido para mostrar
            precio_convertido = producto.obtener_precio_en_moneda(moneda_actual)
            items.append({
                'producto': producto,
                'cantidad': qty,
                'subtotal': subtotal,
                'precio_convertido': precio_convertido,
                'subtotal_convertido': precio_convertido * qty,
            })
    total_convertido = sum([i['subtotal_convertido'] for i in items]) if items else Decimal('0.00')
    return render(request, 'pedidos/carrito.html', {
        'items': items,
        'total': total,
        'total_convertido': total_convertido,
    })


@require_POST
def carrito_agregar(request):
    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity', '1')
    try:
        producto = Producto.objects.get(id=int(product_id), activo=True)
        quantity = max(1, int(quantity))
    except Exception:
        messages.error(request, 'Producto inválido.')
        return redirect(request.META.get('HTTP_REFERER', 'core:index'))

    cart = _get_cart(request.session)
    current = int(cart.get(str(product_id), 0))
    nuevo_total = current + quantity
    # Validar stock
    if producto.stock is not None and nuevo_total > producto.stock:
        cart[str(product_id)] = producto.stock
        request.session.modified = True
        messages.warning(request, f'Solo hay {producto.stock} unidades disponibles de {producto.nombre}.')
        return redirect(request.META.get('HTTP_REFERER', 'pedidos:carrito_ver'))
    cart[str(product_id)] = nuevo_total
    request.session.modified = True
    messages.success(request, f'Se añadió {producto.nombre} al carrito.')
    return redirect(request.META.get('HTTP_REFERER', 'pedidos:carrito_ver'))


@require_POST
def carrito_actualizar(request):
    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity', '1')
    cart = _get_cart(request.session)
    if product_id in cart:
        qty = max(0, int(quantity))
        if qty == 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = qty
        request.session.modified = True
    return redirect('pedidos:carrito_ver')


@require_POST
def carrito_eliminar(request):
    product_id = request.POST.get('product_id')
    cart = _get_cart(request.session)
    cart.pop(product_id, None)
    request.session.modified = True
    return redirect('pedidos:carrito_ver')


@require_POST
def carrito_limpiar(request):
    request.session['cart'] = {}
    request.session.modified = True
    return redirect('pedidos:carrito_ver')


@login_required
def checkout(request):
    cart = _get_cart(request.session)
    if not cart:
        messages.info(request, 'Tu carrito está vacío.')
        return redirect('catalogo:productos_lista')

    # Recalcular total y validar productos
    items = []
    total = Decimal('0.00')
    ids = [int(pid) for pid in cart.keys()]
    productos = {p.id: p for p in Producto.objects.filter(id__in=ids, activo=True)}
    for str_id, qty in cart.items():
        pid = int(str_id)
        producto = productos.get(pid)
        if not producto:
            continue
        qty = max(1, int(qty))
        subtotal = producto.precio * qty
        total += subtotal
        items.append({'producto': producto, 'cantidad': qty, 'subtotal': subtotal})

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')
        notas_pago = request.POST.get('notas_pago', '')
        comprobante = request.FILES.get('comprobante_pago')

        pedido = Pedido.objects.create(
            usuario=request.user,
            total=total,
            metodo_pago=metodo_pago,
            notas_pago=notas_pago,
        )
        if comprobante:
            pedido.comprobante_pago = comprobante
            pedido.save()

        for it in items:
            producto = it['producto']
            cantidad = it['cantidad']
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=producto.precio * cantidad,
            )
            try:
                producto.reducir_stock(cantidad)
            except Exception:
                pass

        # Vaciar carrito y redirigir a confirmación
        request.session['cart'] = {}
        request.session.modified = True
        return redirect('pedidos:pedido_confirmacion', numero_pedido=pedido.numero_pedido)

    return render(request, 'pedidos/checkout.html', {
        'items': items,
        'total': total,
    })


@login_required
def pedido_confirmacion(request, numero_pedido):
    pedido = get_object_or_404(Pedido, numero_pedido=numero_pedido, usuario=request.user)
    return render(request, 'pedidos/confirmacion.html', {'pedido': pedido})
