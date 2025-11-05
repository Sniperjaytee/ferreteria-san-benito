from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone
from .models import Usuario, TasaCambio, ConfiguracionMoneda

# Register your models here.

class UsuarioInline(admin.StackedInline):
    model = Usuario
    can_delete = False
    verbose_name_plural = 'Información Adicional'
    fields = ('cedula', 'telefono', 'direccion', 'fecha_nacimiento', 'es_empleado')
    readonly_fields = ('created_at',)

class UsuarioAdmin(UserAdmin):
    inlines = (UsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_cedula', 'get_es_empleado')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'usuario__es_empleado')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'usuario__cedula')
    
    def get_cedula(self, obj):
        try:
            return obj.usuario.cedula
        except Usuario.DoesNotExist:
            return "Sin cédula"
    get_cedula.short_description = 'Cédula'
    
    def get_es_empleado(self, obj):
        try:
            return obj.usuario.es_empleado
        except Usuario.DoesNotExist:
            return False
    get_es_empleado.short_description = 'Es Empleado'
    get_es_empleado.boolean = True

# Desregistrar el UserAdmin por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)

# Registrar también el modelo Usuario directamente
@admin.register(Usuario)
class UsuarioDirectAdmin(admin.ModelAdmin):
    list_display = ('user', 'cedula', 'telefono', 'es_empleado', 'created_at')
    list_filter = ('es_empleado', 'created_at')
    search_fields = ('cedula', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'cedula')
        }),
        ('Información Personal', {
            'fields': ('telefono', 'direccion', 'fecha_nacimiento')
        }),
        ('Información Laboral', {
            'fields': ('es_empleado',)
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = (
        'moneda_origen', 'moneda_destino', 'tasa_formateada', 
        'activa', 'fecha_actualizacion', 'actualizada_por'
    )
    list_filter = ('activa', 'moneda_origen', 'moneda_destino', 'fecha_actualizacion')
    search_fields = ('moneda_origen', 'moneda_destino', 'notas')
    list_editable = ('activa',)
    readonly_fields = ('fecha_actualizacion', 'actualizada_por')
    
    fieldsets = (
        ('Información de la Tasa', {
            'fields': ('moneda_origen', 'moneda_destino', 'tasa')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Información Adicional', {
            'fields': ('notas',)
        }),
        ('Auditoría', {
            'fields': ('fecha_actualizacion', 'actualizada_por'),
            'classes': ('collapse',)
        }),
    )
    # Usar plantilla personalizada para mostrar las 3 tarjetas de monedas
    change_list_template = 'admin/core/tasa_cambio/change_list.html'
    # Añadir CSS/JS personalizados
    class Media:
        css = {
            'all': ('css/admin-tasas.css',)
        }
    
    actions = ['activar_tasas', 'desactivar_tasas', 'crear_tasas_bidireccionales']

    def changelist_view(self, request, extra_context=None):
        """Inyecta en el contexto las tasas relativas al USD para mostrar las 3 tarjetas."""
        extra_context = extra_context or {}
        monedas = ['VES', 'COP', 'EUR']
        tasas = {}
        tasas_list = []
        for m in monedas:
            tasa_obj = TasaCambio.objects.filter(moneda_origen='USD', moneda_destino=m, activa=True).first()
            if tasa_obj:
                tasas[m] = {
                    'valor': tasa_obj.tasa,
                    'obj': tasa_obj
                }
                tasas_list.append({'codigo': m, 'valor': tasa_obj.tasa, 'obj': tasa_obj})
            else:
                tasas[m] = None
                tasas_list.append({'codigo': m, 'valor': None, 'obj': None})

        extra_context['tasas_resumen_usd'] = tasas
        extra_context['tasas_resumen_list'] = tasas_list
        # símbolos desde la configuración
        try:
            config = ConfiguracionMoneda.obtener_configuracion()
            extra_context['simbolos'] = config.simbolos
        except Exception:
            extra_context['simbolos'] = {'USD': '$', 'VES': 'Bs', 'COP': '$', 'EUR': '€'}
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('editar-directo/<str:moneda>/', self.admin_site.admin_view(self.editar_directo_view), name='tasa_editar_directo'),
        ]
        return custom + urls

    def editar_directo_view(self, request, moneda=None):
        """Vista simple para editar la tasa respecto a 1 USD para la moneda indicada."""
        from django.shortcuts import render, redirect
        from django.contrib import messages

        moneda = moneda or request.GET.get('moneda')
        if moneda not in dict(TasaCambio.MONEDAS).keys():
            messages.error(request, 'Moneda no válida')
            from django.urls import reverse
            return redirect(reverse('admin:core_tasacambio_changelist'))

        # Buscar tasa USD -> moneda
        tasa = TasaCambio.objects.filter(moneda_origen='USD', moneda_destino=moneda).first()

        if request.method == 'POST':
            valor = request.POST.get('valor')
            try:
                from decimal import Decimal
                v = Decimal(valor)
                if v <= 0:
                    raise ValueError()
            except Exception:
                messages.error(request, 'Valor inválido. Debe ser un número mayor que cero.')
                return redirect(request.path)

            # Crear o actualizar tasa USD -> moneda
            tasa_obj, created = TasaCambio.objects.update_or_create(
                moneda_origen='USD',
                moneda_destino=moneda,
                defaults={
                    'tasa': v,
                    'activa': True,
                    'actualizada_por': request.user,
                }
            )

            # Asegurar tasa inversa también existe (recíproca)
            try:
                if v != 0:
                    tasa_inv_val = (Decimal('1.0') / v).quantize(Decimal('0.000001'))
                else:
                    tasa_inv_val = None
            except Exception:
                tasa_inv_val = None

            if tasa_inv_val:
                TasaCambio.objects.update_or_create(
                    moneda_origen=moneda,
                    moneda_destino='USD',
                    defaults={
                        'tasa': tasa_inv_val,
                        'activa': True,
                        'actualizada_por': request.user,
                    }
                )

            messages.success(request, f'Tasa USD→{moneda} guardada: 1 USD = {v} {moneda}')
            from django.urls import reverse
            return redirect(reverse('admin:core_tasacambio_changelist'))

        simbolo = moneda
        try:
            config = ConfiguracionMoneda.obtener_configuracion()
            simbolo = config.simbolos.get(moneda, moneda)
        except Exception:
            pass

        return render(request, 'admin/core/tasa_cambio/edit_direct.html', {
            'moneda': moneda,
            'tasa': tasa,
            'simbolo': simbolo,
        })

    def save_model(self, request, obj, form, change):
        """Asegura que se actualice actualizada_por y que exista la tasa USD<->otra moneda."""
        # actualizar quien modificó
        obj.actualizada_por = request.user
        super().save_model(request, obj, form, change)

        # Si se guardó una tasa que involucra USD, asegurar la tasa recíproca exista
        try:
            from decimal import Decimal, getcontext
            getcontext().prec = 12
            if obj.moneda_origen == 'USD' and obj.moneda_destino != 'USD':
                # crear/actualizar inversa
                if obj.tasa and obj.tasa != Decimal('0'):
                    inv = (Decimal('1') / obj.tasa).quantize(Decimal('0.000001'))
                    TasaCambio.objects.update_or_create(
                        moneda_origen=obj.moneda_destino,
                        moneda_destino='USD',
                        defaults={'tasa': inv, 'activa': obj.activa, 'actualizada_por': request.user}
                    )
            elif obj.moneda_destino == 'USD' and obj.moneda_origen != 'USD':
                # crear/actualizar USD->origen
                if obj.tasa and obj.tasa != Decimal('0'):
                    inv = (Decimal('1') / obj.tasa).quantize(Decimal('0.000001'))
                    TasaCambio.objects.update_or_create(
                        moneda_origen='USD',
                        moneda_destino=obj.moneda_origen,
                        defaults={'tasa': inv, 'activa': obj.activa, 'actualizada_por': request.user}
                    )
        except Exception:
            # No bloquear en caso de error al crear inversa
            pass

    def get_changeform_initial_data(self, request):
        """Prefill add form using GET params moneda_origen and moneda_destino (used when clicking tarjetas)."""
        initial = super().get_changeform_initial_data(request) or {}
        moneda_origen = request.GET.get('moneda_origen')
        moneda_destino = request.GET.get('moneda_destino')
        if moneda_origen:
            initial['moneda_origen'] = moneda_origen
        if moneda_destino:
            initial['moneda_destino'] = moneda_destino
        return initial
    
    def tasa_formateada(self, obj):
        """Muestra la tasa formateada con colores"""
        if obj.activa:
            return format_html(
                '<span style="color: green; font-weight: bold;">1 {} = {}</span>',
                obj.moneda_origen, obj.tasa
            )
        else:
            return format_html(
                '<span style="color: red;">1 {} = {}</span>',
                obj.moneda_origen, obj.tasa
            )
    tasa_formateada.short_description = 'Tasa de Cambio'
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que actualizó la tasa"""
        if not change:  # Si es nuevo
            obj.actualizada_por = request.user
        elif obj.actualizada_por != request.user:  # Si cambió el usuario
            obj.actualizada_por = request.user
        super().save_model(request, obj, form, change)
    
    def activar_tasas(self, request, queryset):
        """Activa las tasas seleccionadas"""
        updated = queryset.update(activa=True)
        self.message_user(request, f'{updated} tasas activadas.')
    activar_tasas.short_description = "✅ Activar tasas seleccionadas"
    
    def desactivar_tasas(self, request, queryset):
        """Desactiva las tasas seleccionadas"""
        updated = queryset.update(activa=False)
        self.message_user(request, f'{updated} tasas desactivadas.')
    desactivar_tasas.short_description = "❌ Desactivar tasas seleccionadas"
    
    def crear_tasas_bidireccionales(self, request, queryset):
        """Crea tasas bidireccionales para las seleccionadas"""
        count = 0
        for tasa in queryset:
            # Crear tasa inversa si no existe
            tasa_inversa, created = TasaCambio.objects.get_or_create(
                moneda_origen=tasa.moneda_destino,
                moneda_destino=tasa.moneda_origen,
                defaults={
                    'tasa': 1 / tasa.tasa,
                    'activa': tasa.activa,
                    'actualizada_por': request.user,
                    'notas': f'Tasa inversa de {tasa}'
                }
            )
            if created:
                count += 1
        
        self.message_user(request, f'{count} tasas bidireccionales creadas.')
    crear_tasas_bidireccionales.short_description = "🔄 Crear tasas bidireccionales"


@admin.register(ConfiguracionMoneda)
class ConfiguracionMonedaAdmin(admin.ModelAdmin):
    list_display = (
        'moneda_principal', 'mostrar_multiple_monedas', 
        'monedas_mostrar_display', 'decimales_precision'
    )
    readonly_fields = ('monedas_mostrar_display', 'simbolos_display')
    
    fieldsets = (
        ('Configuración Principal', {
            'fields': ('moneda_principal', 'mostrar_multiple_monedas')
        }),
        ('Monedas a Mostrar', {
            'fields': ('monedas_mostrar', 'monedas_mostrar_display')
        }),
        ('Formato', {
            'fields': ('decimales_precision', 'simbolos_monedas', 'simbolos_display')
        }),
    )
    
    def monedas_mostrar_display(self, obj):
        """Muestra las monedas a mostrar de forma legible"""
        if obj.monedas_mostrar:
            return ', '.join(obj.monedas_mostrar)
        return "Sin monedas configuradas"
    monedas_mostrar_display.short_description = 'Monedas Configuradas'
    
    def simbolos_display(self, obj):
        """Muestra los símbolos de monedas de forma legible"""
        if obj.simbolos_monedas:
            simbolos = []
            for moneda, simbolo in obj.simbolos_monedas.items():
                simbolos.append(f"{moneda}: {simbolo}")
            return format_html('<br>'.join(simbolos))
        return "Sin símbolos configurados"
    simbolos_display.short_description = 'Símbolos Configurados'
    
    def has_add_permission(self, request):
        """Solo permite una configuración"""
        return not ConfiguracionMoneda.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """No permite eliminar la configuración"""
        return False
    
    actions = ['resetear_configuracion', 'aplicar_configuracion_venezuela']
    
    def resetear_configuracion(self, request, queryset):
        """Resetea la configuración a valores por defecto"""
        for config in queryset:
            config.moneda_principal = 'USD'
            config.mostrar_multiple_monedas = True
            config.monedas_mostrar = ['USD', 'VES', 'COP']
            config.decimales_precision = 2
            config.simbolos_monedas = {
                'USD': '$',
                'VES': 'Bs',
                'COP': '$'
            }
            config.save()
        
        self.message_user(request, 'Configuración reseteada a valores por defecto.')
    resetear_configuracion.short_description = "🔄 Resetear configuración"
    
    def aplicar_configuracion_venezuela(self, request, queryset):
        """Aplica configuración específica para Venezuela"""
        for config in queryset:
            config.moneda_principal = 'USD'
            config.mostrar_multiple_monedas = True
            config.monedas_mostrar = ['USD', 'VES', 'COP']
            config.decimales_precision = 2
            config.simbolos_monedas = {
                'USD': '$',
                'VES': 'Bs',
                'COP': '$'
            }
            config.save()
        
        # Crear tasas de cambio por defecto si no existen
        tasas_por_defecto = [
            ('USD', 'VES', 36.50),  # 1 USD = 36.50 VES (ejemplo)
            ('USD', 'COP', 4100.00),  # 1 USD = 4100.00 COP (ejemplo)
            ('VES', 'COP', 112.33),  # 1 VES = 112.33 COP (ejemplo)
        ]
        
        count = 0
        for origen, destino, tasa in tasas_por_defecto:
            tasa_obj, created = TasaCambio.objects.get_or_create(
                moneda_origen=origen,
                moneda_destino=destino,
                defaults={
                    'tasa': tasa,
                    'activa': True,
                    'actualizada_por': request.user,
                    'notas': 'Tasa por defecto para Venezuela'
                }
            )
            if created:
                count += 1
        
        self.message_user(request, f'Configuración de Venezuela aplicada. {count} tasas de cambio creadas.')
    aplicar_configuracion_venezuela.short_description = "🇻🇪 Aplicar configuración Venezuela"
