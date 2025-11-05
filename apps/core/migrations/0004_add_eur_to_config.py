# Migration to add EUR to existing ConfiguracionMoneda.monedas_mostrar if missing
from django.db import migrations


def add_eur(apps, schema_editor):
    ConfiguracionMoneda = apps.get_model('core', 'ConfiguracionMoneda')
    try:
        config = ConfiguracionMoneda.objects.first()
        if config:
            mm = config.monedas_mostrar or []
            if 'EUR' not in mm:
                mm.append('EUR')
                config.monedas_mostrar = mm
                config.save()
    except Exception:
        pass


def remove_eur(apps, schema_editor):
    ConfiguracionMoneda = apps.get_model('core', 'ConfiguracionMoneda')
    try:
        config = ConfiguracionMoneda.objects.first()
        if config and config.monedas_mostrar:
            mm = config.monedas_mostrar
            if 'EUR' in mm:
                mm = [m for m in mm if m != 'EUR']
                config.monedas_mostrar = mm
                config.save()
    except Exception:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_add_eur_rate'),
    ]

    operations = [
        migrations.RunPython(add_eur, remove_eur),
    ]
