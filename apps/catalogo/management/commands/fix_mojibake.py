from django.core.management.base import BaseCommand
from catalogo.models import Categoria, Producto
from core.models import Usuario
from pedidos.models import Pedido
import re


def _looks_mojibake(s: str) -> bool:
    if not isinstance(s, str) or not s:
        return False
    return any(ch in s for ch in ("Ã", "Â", "�"))


def _fix_text(s: str) -> str:
    if not s:
        return s
    # Intento 1: fue leído como latin-1 cuando era utf-8
    try:
        if _looks_mojibake(s):
            fixed = s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
            if fixed and fixed != s:
                s = fixed
    except Exception:
        pass
    # Intento 2: reemplazos comunes
    replacements = {
        "EnvA-os": "Envíos",
        "InformaciA3n": "Información",
        "UbicaciA3n": "Ubicación",
        "CategorA-as": "Categorías",
        "ContraseA�a": "Contraseña",
        "ElA©ctricas": "Eléctricas",
        "ConstrucciA3n": "Construcción",
    }
    out = s
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def _normalize_phone_ve(raw: str) -> str:
    if not raw:
        return raw
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("58"):
        local = digits[2:]
    else:
        local = digits
    if len(local) == 10:
        return "+58 " + local
    return raw


class Command(BaseCommand):
    help = "Corrige textos con mojibake (acentos rotos) en categorías, productos, usuarios y pedidos."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cambios, no guardar")

    def handle(self, *args, **options):
        dry = options.get("dry_run", False)
        updated = 0

        # Categorías
        for c in Categoria.objects.all():
            original_nombre = c.nombre
            original_desc = c.descripcion or ""
            new_nombre = _fix_text(original_nombre)
            new_desc = _fix_text(original_desc)
            if new_nombre != original_nombre or new_desc != original_desc:
                self.stdout.write(f"Categoria #{c.id}: '{original_nombre}' -> '{new_nombre}'")
                if not dry:
                    c.nombre = new_nombre
                    c.descripcion = new_desc
                    c.save(update_fields=["nombre", "descripcion"])  # type: ignore[arg-type]
                updated += 1

        # Productos
        for p in Producto.objects.all():
            original_nombre = p.nombre
            original_desc = p.descripcion or ""
            new_nombre = _fix_text(original_nombre)
            new_desc = _fix_text(original_desc)
            if new_nombre != original_nombre or new_desc != original_desc:
                self.stdout.write(f"Producto #{p.id}: '{original_nombre}' -> '{new_nombre}'")
                if not dry:
                    p.nombre = new_nombre
                    p.descripcion = new_desc
                    p.save(update_fields=["nombre", "descripcion"])  # type: ignore[arg-type]
                updated += 1

        # Usuarios (perfil + nombres)
        for u in Usuario.objects.select_related("user").all():
            changes = {}
            new_dir = _fix_text(u.direccion or "")
            if new_dir != (u.direccion or ""):
                changes["direccion"] = new_dir
            # Normalizar teléfono si luce VE
            if u.telefono:
                new_tel = _normalize_phone_ve(u.telefono)
                if new_tel != u.telefono:
                    changes["telefono"] = new_tel
            if changes:
                self.stdout.write(f"Usuario #{u.id} actualizado: {list(changes.keys())}")
                if not dry:
                    for k, v in changes.items():
                        setattr(u, k, v)
                    u.save(update_fields=list(changes.keys()))
                updated += 1
            # También nombres del User
            first = u.user.first_name or ""
            last = u.user.last_name or ""
            new_first = _fix_text(first)
            new_last = _fix_text(last)
            if new_first != first or new_last != last:
                self.stdout.write(f"User #{u.user.id} nombre: '{first} {last}' -> '{new_first} {new_last}'")
                if not dry:
                    u.user.first_name = new_first
                    u.user.last_name = new_last
                    u.user.save(update_fields=["first_name", "last_name"])
                updated += 1

        # Pedidos (notas)
        for ped in Pedido.objects.all():
            changes = {}
            if ped.notas_pago:
                new_np = _fix_text(ped.notas_pago)
                if new_np != ped.notas_pago:
                    changes["notas_pago"] = new_np
            if ped.notas_administrador:
                new_na = _fix_text(ped.notas_administrador)
                if new_na != ped.notas_administrador:
                    changes["notas_administrador"] = new_na
            if changes:
                self.stdout.write(f"Pedido #{ped.id} actualizado: {list(changes.keys())}")
                if not dry:
                    for k, v in changes.items():
                        setattr(ped, k, v)
                    ped.save(update_fields=list(changes.keys()))
                updated += 1

        if dry:
            self.stdout.write(self.style.WARNING(f"Dry-run terminado. Registros con cambios: {updated}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Corrección terminada. Registros actualizados: {updated}"))
