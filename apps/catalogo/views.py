from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Producto, Categoria


def productos_lista(request):
    q = request.GET.get('q', '').strip()
    categoria_slug = request.GET.get('categoria', '').strip()
    productos = Producto.objects.filter(activo=True)

    if q:
        productos = productos.filter(nombre__icontains=q)
    if categoria_slug:
        productos = productos.filter(categoria__slug=categoria_slug)

    productos = productos.select_related('categoria').order_by('-destacado', '-created_at')
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categorias = Categoria.objects.filter(activa=True).order_by('orden')
    return render(request, 'catalogo/lista.html', {
        'page_obj': page_obj,
        'categorias': categorias,
        'q': q,
        'categoria_slug': categoria_slug,
    })


def productos_por_categoria(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug, activa=True)
    request.GET = request.GET.copy()
    request.GET['categoria'] = slug
    return productos_lista(request)


def producto_detalle(request, slug):
    producto = get_object_or_404(Producto, slug=slug, activo=True)
    relacionados = Producto.objects.filter(activo=True, categoria=producto.categoria).exclude(id=producto.id)[:4]
    return render(request, 'catalogo/detalle.html', {
        'producto': producto,
        'relacionados': relacionados,
    })
