import uuid
from decimal import Decimal
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalogo.models import Categoria, Producto


CATEGORY_DATA = [
    {
        "name": "Herramientas Eléctricas",
        "slug": "herramientas-electricas",
        "description": "Taladros, esmeriles y equipos eléctricos para trabajos exigentes.",
        "image": None,
    },
    {
        "name": "Herramientas Manuales",
        "slug": "herramientas-manuales",
        "description": "Llaves, destornilladores y kits esenciales para mantenimiento diario.",
        "image": None,
    },
    {
        "name": "Pinturas y Acabados",
        "slug": "pinturas-y-acabados",
        "description": "Pinturas, rodillos y accesorios para renovar interiores y exteriores.",
        "image": None,
    },
    {
        "name": "Seguridad Industrial",
        "slug": "seguridad-industrial",
        "description": "Guantes, lentes, cascos y protección personal para tu equipo.",
        "image": None,
    },
    {
        "name": "Construcción y Obra",
        "slug": "construccion-y-obra",
        "description": "Herramientas y materiales para proyectos de construcción pesados.",
        "image": None,
    },
]


PRODUCT_DATA = [
    {
        "name": "Taladro Percutor 750W",
        "description": "Taladro percutor de 750W con velocidad variable y maletín de transporte.",
        "price": "89.99",
        "image": None,
        "category_slug": "herramientas-electricas",
        "stock": 18,
        "destacado": True,
    },
    {
        "name": "Esmeril Angular 4-1/2\"",
        "description": "Esmeril angular compacto de 900W ideal para cortes y desbastes.",
        "price": "74.50",
        "image": None,
        "category_slug": "herramientas-electricas",
        "stock": 12,
        "destacado": True,
    },
    {
        "name": "Juego de Llaves Combinadas 14 pzs",
        "description": "Set de llaves combinadas en milímetros con acabado cromado pulido.",
        "price": "54.90",
        "image": None,
        "category_slug": "herramientas-manuales",
        "stock": 25,
        "destacado": True,
    },
    {
        "name": "Rodillo Antigoteo 9\"",
        "description": "Rodillo antigoteo con charola incluida, ideal para acabados lisos.",
        "price": "12.80",
        "image": None,
        "category_slug": "pinturas-y-acabados",
        "stock": 40,
        "destacado": False,
    },
    {
        "name": "Casco de Seguridad con Arnés",
        "description": "Casco de seguridad industrial con arnés de 6 puntos y visera intercambiable.",
        "price": "21.30",
        "image": None,
        "category_slug": "seguridad-industrial",
        "stock": 30,
        "destacado": True,
    },
    {
        "name": "Guantes Anticorte Nivel 5",
        "description": "Guantes resistentes a cortes con recubrimiento de nitrilo para mejor agarre.",
        "price": "8.75",
        "image": None,
        "category_slug": "seguridad-industrial",
        "stock": 60,
        "destacado": False,
    },
    {
        "name": "Cortadora de Baldosas 65cm",
        "description": "Cortadora manual con base reforzada y guía de corte ajustable.",
        "price": "129.00",
        "image": None,
        "category_slug": "construccion-y-obra",
        "stock": 9,
        "destacado": True,
    },
    {
        "name": "Carretilla de Acero 130L",
        "description": "Carretilla reforzada con llanta neumática para trabajos de obra pesada.",
        "price": "98.50",
        "image": None,
        "category_slug": "construccion-y-obra",
        "stock": 7,
        "destacado": False,
    },
]


class Command(BaseCommand):
    help = "Puebla la base de datos con categorías y productos demo, incluyendo imágenes."

    def handle(self, *args, **options):
        self.stdout.write("Descargando imágenes y creando categorías...")
        categories = self._create_categories()
        self.stdout.write(self.style.SUCCESS(f"Categorías listas ({len(categories)})"))

        self.stdout.write("Creando productos demo...")
        products = self._create_products(categories)
        self.stdout.write(self.style.SUCCESS(f"Productos listos ({len(products)})"))

    def _create_categories(self):
        created = []
        for order, data in enumerate(CATEGORY_DATA, start=1):
            desired_slug = data.get("slug") or slugify(data["name"])  # slug canónica
            categoria = Categoria.objects.filter(slug=desired_slug).first()
            if not categoria:
                categoria = Categoria(slug=desired_slug)
            categoria.nombre = data["name"]
            categoria.descripcion = data["description"]
            categoria.orden = order

            # imagen: usar fallback confiable con seed por slug si no hay URL
            seed = desired_slug
            self._assign_image(
                instance=categoria,
                field="imagen",
                url=data.get("image"),
                prefix=f"{desired_slug}",
                seed=seed,
            )

            categoria.save()
            created.append(categoria)
        return created

    def _create_products(self, categories):
        created = []
        category_map = {slugify((cat.slug or cat.nombre)): cat for cat in categories}
        for data in PRODUCT_DATA:
            categoria = category_map.get(data["category_slug"])
            if not categoria:
                self.stdout.write(self.style.WARNING(
                    f"Categoría {data['category_slug']} no encontrada, saltando producto {data['name']}"
                ))
                continue

            producto, _ = Producto.objects.get_or_create(
                nombre=data["name"],
                categoria=categoria,
                defaults={"precio": Decimal(data["price"])}
            )

            producto.descripcion = data["description"]
            producto.precio = Decimal(data["price"])
            producto.stock = data.get("stock", 0)
            producto.stock_minimo = max(1, producto.stock // 3) if producto.stock else 5
            producto.destacado = data.get("destacado", False)
            producto.activo = True
            producto.moneda_precio = "USD"

            # imagen: fallback confiable con seed por nombre de producto
            self._assign_image(
                instance=producto,
                field="imagen",
                url=data.get("image"),
                prefix=f"{slugify(producto.nombre)}",
                seed=slugify(producto.nombre),
            )

            producto.save()
            created.append(producto)
        return created

    def _assign_image(self, instance, field, url, prefix, seed: str = "fallback"):
        raw_bytes = None
        if url:
            try:
                raw_bytes = self._download(url)
            except (URLError, HTTPError) as exc:
                self.stdout.write(self.style.WARNING(
                    f"No se pudo descargar {url}: {exc}. Intentando fallback..."
                ))
        if raw_bytes is None:
            # Fallback estable con picsum (siempre entrega imagen)
            fallback_url = f"https://picsum.photos/seed/{slugify(seed)}/1200/800"
            try:
                raw_bytes = self._download(fallback_url)
            except (URLError, HTTPError) as exc:
                self.stdout.write(self.style.ERROR(
                    f"Fallo también el fallback {fallback_url}: {exc}"
                ))
                return

        filename = f"{prefix}-{uuid.uuid4().hex[:8]}.jpg"
        django_file = ContentFile(raw_bytes)
        getattr(instance, field).save(filename, django_file, save=False)

    def _download(self, url):
        with urlopen(url) as response:
            return response.read()
