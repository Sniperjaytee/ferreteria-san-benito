from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.shortcuts import redirect
from .models import Carrito, Pedido, ItemPedido
from decimal import Decimal
from django.db.models import Sum

# Register your models here.

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    # Permitir seleccionar producto y cantidad; precios y subtotal, solo lectura
    readonly_fields = ('precio_unitario', 'subtotal_formateado')
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal_formateado')
    show_change_link = True

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'producto', 'cantidad', 'subtotal_formateado', 'created_at')
    list_filter = ('created_at', 'usuario')
    search_fields = ('usuario__username', 'producto__nombre')
    readonly_fields = ('created_at', 'updated_at', 'subtotal_formateado')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'producto')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_pedido', 'usuario', 'total_formateado', 'estado_pago_display', 
        'metodo_pago', 'fecha_creacion', 'comprobante_link'
    )
    list_filter = ('estado_pago', 'estado', 'metodo_pago', 'fecha_creacion')
    search_fields = ('numero_pedido', 'usuario__username', 'usuario__email')
    readonly_fields = (
        'numero_pedido', 'fecha_creacion', 'fecha_actualizacion', 
        'total_formateado', 'items_count', 'comprobante_preview',
        'estado_pago_display', 'administrador_pago', 'fecha_pago'
    )
    inlines = [ItemPedidoInline]

    fieldsets = (
        ('Información del Pedido', {
            'fields': ('numero_pedido', 'usuario', 'total', 'total_formateado', 'items_count')
        }),
        ('Estado del Pedido', {
            'fields': ('estado', 'estado_pago_display', 'metodo_pago')
        }),
        ('Información de Pago', {
            'fields': ('comprobante_pago', 'comprobante_preview', 'notas_pago', 'notas_administrador')
        }),
        ('Verificación de Pago', {
            'fields': ('administrador_pago', 'fecha_pago'),
            'classes': ('collapse',)
        }),
        ('Información de Entrega', {
            'fields': ('direccion_entrega', 'telefono_contacto', 'fecha_entrega')
        }),
        ('Notas Generales', {
            'fields': ('notas',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    actions = ['aprobar_pagos', 'rechazar_pagos', 'marcar_como_procesando', 'marcar_como_completado']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'total' in form.base_fields:
            form.base_fields['total'].required = False
        return form

    def save_model(self, request, obj, form, change):
        # Asegura un valor por defecto para evitar NOT NULL al primer guardado
        if obj.total is None:
            obj.total = Decimal('0.00')
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        # Completar precios y subtotales en items antes de guardar
        if formset.model is ItemPedido:
            for it in instances:
                if it.precio_unitario is None and it.producto:
                    it.precio_unitario = it.producto.precio or Decimal('0.00')
                if it.precio_unitario is not None and it.cantidad:
                    try:
                        it.subtotal = it.precio_unitario * int(it.cantidad)
                    except Exception:
                        it.subtotal = Decimal('0.00')
                it.save()
            for obj_del in formset.deleted_objects:
                obj_del.delete()
        else:
            for inst in instances:
                inst.save()
            for obj_del in formset.deleted_objects:
                obj_del.delete()

        formset.save_m2m()
        # Recalcular total del pedido después de guardar items
        pedido = form.instance
        if isinstance(pedido, Pedido):
            total = pedido.items.aggregate(Sum('subtotal')).get('subtotal__sum') or Decimal('0.00')
            if pedido.total != total:
                pedido.total = total
                pedido.save(update_fields=['total'])
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'administrador_pago').prefetch_related('items')
    
    def comprobante_link(self, obj):
        if obj.comprobante_pago:
            return format_html(
                '<a href="{}" target="_blank">📄 Ver Comprobante</a>',
                obj.comprobante_pago.url
            )
        return "Sin comprobante"
    comprobante_link.short_description = 'Comprobante'
    
    def comprobante_preview(self, obj):
        if obj.comprobante_pago:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.comprobante_pago.url
            )
        return "Sin comprobante"
    comprobante_preview.short_description = 'Vista Previa'
    
    def aprobar_pagos(self, request, queryset):
        """Acción para aprobar pagos seleccionados"""
        count = 0
        for pedido in queryset.filter(estado_pago='verificando'):
            pedido.aprobar_pago(request.user, "Pago verificado desde admin")
            count += 1
        
        if count > 0:
            self.message_user(request, f'{count} pagos aprobados exitosamente.')
        else:
            self.message_user(request, 'No hay pagos pendientes de verificación.', level=messages.WARNING)
    aprobar_pagos.short_description = "✅ Aprobar pagos seleccionados"
    
    def rechazar_pagos(self, request, queryset):
        """Acción para rechazar pagos seleccionados"""
        count = 0
        for pedido in queryset.filter(estado_pago='verificando'):
            pedido.rechazar_pago(request.user, "Pago rechazado - revisar comprobante")
            count += 1
        
        if count > 0:
            self.message_user(request, f'{count} pagos rechazados.')
        else:
            self.message_user(request, 'No hay pagos pendientes de verificación.', level=messages.WARNING)
    rechazar_pagos.short_description = "❌ Rechazar pagos seleccionados"
    
    def marcar_como_procesando(self, request, queryset):
        """Marcar pedidos como en proceso"""
        updated = queryset.filter(estado_pago='pagado').update(estado='procesando')
        self.message_user(request, f'{updated} pedidos marcados como en proceso.')
    marcar_como_procesando.short_description = "🔄 Marcar como en proceso"
    
    def marcar_como_completado(self, request, queryset):
        """Marcar pedidos como completados"""
        updated = queryset.filter(estado='procesando').update(estado='completado')
        self.message_user(request, f'{updated} pedidos marcados como completados.')
    marcar_como_completado.short_description = "✅ Marcar como completado"

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario_formateado', 'subtotal_formateado')
    list_filter = ('pedido__estado', 'pedido__fecha_creacion')
    search_fields = ('pedido__numero_pedido', 'producto__nombre')
    readonly_fields = ('precio_unitario_formateado', 'subtotal_formateado')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pedido', 'producto')
