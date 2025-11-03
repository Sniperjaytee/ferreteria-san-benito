from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalogo.models import Categoria, Producto


class Command(BaseCommand):
    help = "Limpia categorías no canónicas y reasigna productos a slugs canónicos."

    CANONICAL = {
        'herramientas-electricas': 'Herramientas Eléctricas',
        'herramientas-manuales': 'Herramientas Manuales',
        'pinturas-y-acabados': 'Pinturas y Acabados',
        'seguridad-industrial': 'Seguridad Industrial',
        'construccion-y-obra': 'Construcción y Obra',
    }

    RULES = [
        ('herramientas-electricas', ('electric', 'elactr', 'electr', 'elacct', 'elctr')),
        ('herramientas-manuales', ('manual', 'herramientas')),
        ('pinturas-y-acabados', ('pintur', 'acab')),
        ('seguridad-industrial', ('segurid', 'industrial')),
        ('construccion-y-obra', ('construcc', 'obra')),
    ]

    DEFAULT_TARGET = 'herramientas-manuales'

    def handle(self, *args, **options):
        # Asegurar categorías canónicas
        canon_objs = {}
        for slug, name in self.CANONICAL.items():
            cat, _ = Categoria.objects.get_or_create(slug=slug, defaults={'nombre': name, 'descripcion': name, 'orden': 0})
            if not cat.nombre:
                cat.nombre = name
                cat.save(update_fields=['nombre'])
            canon_objs[slug] = cat

        moved = 0
        removed = 0

        def pick_target(cat):
            s = (cat.slug or slugify(cat.nombre or '')).lower()
            n = (cat.nombre or '').lower()
            # Casos explícitos molestos
            if s in ('11', 'categoria-prueba-1'):
                return self.DEFAULT_TARGET
            for target, keys in self.RULES:
                if any(k in s for k in keys) or any(k in n for k in keys):
                    return target
            return None

        for cat in list(Categoria.objects.all()):
            if cat.slug in self.CANONICAL:
                continue
            target = pick_target(cat)
            if not target:
                # si no cumple heurística, saltar
                continue
            target_cat = canon_objs[target]
            moved += Producto.objects.filter(categoria=cat).update(categoria=target_cat)
            cat.delete()
            removed += 1

        self.stdout.write(self.style.SUCCESS(f"Productos movidos: {moved}"))
        self.stdout.write(self.style.SUCCESS(f"Categorías eliminadas: {removed}"))
        self.stdout.write(self.style.SUCCESS(f"Categorías restantes: {Categoria.objects.count()}"))

