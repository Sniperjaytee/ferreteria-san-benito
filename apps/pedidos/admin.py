from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.shortcuts import redirect
from .models import Carrito, Pedido, ItemPedido
from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from io import BytesIO
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
except Exception:
    canvas = None
    A4 = None

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
        'estado_pago_display', 'administrador_pago', 'fecha_pago',
        'descargar_factura'
    )
    inlines = [ItemPedidoInline]

    class Media:
        js = ('js/admin-pedidos-reporte.js',)
    # Usar plantilla de changelist personalizada para inyectar el botón directamente
    change_list_template = 'admin/pedidos/pedido/change_list.html'

    fieldsets = (
        ('Información del Pedido', {
            'fields': ('numero_pedido', 'usuario', 'total', 'total_formateado', 'items_count', 'descargar_factura')
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
    # Añadir acción para crear reporte PDF de pedidos seleccionados
    actions += ['crear_reporte_pdf']

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

    # --- PDF factura support ---
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:pedido_id>/factura/', self.admin_site.admin_view(self.factura_view), name='pedidos_pedido_factura'),
        ]
        return custom_urls + urls

    def descargar_factura(self, obj):
        if not obj or not obj.pk:
            return "-"
        url = reverse('admin:pedidos_pedido_factura', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">Descargar factura</a>', url)
    descargar_factura.short_description = 'Factura'

    def factura_view(self, request, pedido_id, *args, **kwargs):
        """Genera un PDF simple de la factura (usa ReportLab si está disponible)."""
        pedido = get_object_or_404(Pedido, pk=pedido_id)

        if canvas is None or A4 is None:
            return HttpResponse('ReportLab no está instalado en el servidor. Instala reportlab para generar PDFs.', status=500)

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Margenes
        x_margin = 50
        y = height - 60

        # Title
        p.setFont('Helvetica-Bold', 20)
        p.drawString(x_margin, y, 'Ferretería San Benito')
        y -= 30

        # Order header
        p.setFont('Helvetica', 10)
        from django.utils import timezone
        fecha_str = timezone.localtime(pedido.fecha_creacion).strftime('%Y-%m-%d %H:%M') if pedido.fecha_creacion else ''
        p.drawString(x_margin, y, f'Fecha: {fecha_str}')
        p.drawRightString(width - x_margin, y, f'Pedido: {pedido.numero_pedido}')
        y -= 20

        # Customer
        p.setFont('Helvetica-Bold', 12)
        p.drawString(x_margin, y, f'Cliente: {pedido.usuario.get_full_name() or pedido.usuario.username}')
        y -= 14
        p.setFont('Helvetica', 10)
        p.drawString(x_margin, y, f'Teléfono: {pedido.telefono_contacto}')
        y -= 14
        p.drawString(x_margin, y, 'Dirección:')
        y -= 12
        text = p.beginText(x_margin, y)
        text.setFont('Helvetica', 10)
        for line in str(pedido.direccion_entrega).splitlines():
            text.textLine(line)
        p.drawText(text)
        y = text.getY() - 10

        # Table header
        p.setFont('Helvetica-Bold', 10)
        p.drawString(x_margin, y, 'Producto')
        p.drawRightString(width - 200, y, 'Cantidad')
        p.drawRightString(width - 120, y, 'Precio')
        p.drawRightString(width - x_margin, y, 'Subtotal')
        y -= 14
        p.setFont('Helvetica', 10)

        # Items
        for item in pedido.items.all():
            if y < 80:
                p.showPage()
                y = height - 60
            p.drawString(x_margin, y, item.producto.nombre)
            p.drawRightString(width - 200, y, str(item.cantidad))
            p.drawRightString(width - 120, y, f'${item.precio_unitario:,.2f}')
            p.drawRightString(width - x_margin, y, f'${item.subtotal:,.2f}')
            y -= 14

        # Totals
        y -= 10
        p.line(x_margin, y, width - x_margin, y)
        y -= 16
        p.setFont('Helvetica-Bold', 11)
        p.drawRightString(width - 140, y, 'Total:')
        p.drawRightString(width - x_margin, y, f'${pedido.total:,.2f}')

        # Finish up
        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        filename = f'factura_{pedido.numero_pedido}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        return response

    def crear_reporte_pdf(self, request, queryset):
        """Genera un PDF tipo 'reporte de ventas' con los pedidos seleccionados.

        El reporte incluye un encabezado con el rango de fechas (pedido más antiguo y más reciente)
        y después la información de cada pedido separada por líneas horizontales.
        """
        if not queryset.exists():
            self.message_user(request, 'No se seleccionaron pedidos para generar el reporte.', level=messages.WARNING)
            return None

        if canvas is None or A4 is None:
            return HttpResponse('ReportLab no está instalado en el servidor. Instala reportlab para generar PDFs.', status=500)

        pedidos = queryset.order_by('fecha_creacion')
        primer = pedidos.first()
        ultimo = pedidos.last()

        from django.utils import timezone
        inicio = timezone.localtime(primer.fecha_creacion) if primer and primer.fecha_creacion else None
        fin = timezone.localtime(ultimo.fecha_creacion) if ultimo and ultimo.fecha_creacion else None

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        x_margin = 50
        y = height - 60

        # Título
        p.setFont('Helvetica-Bold', 18)
        p.drawString(x_margin, y, 'Ferreteria San Benito')
        y -= 26

        # Fecha de reporte
        p.setFont('Helvetica', 11)
        inicio_str = inicio.strftime('%Y-%m-%d %H:%M') if inicio else 'N/A'
        fin_str = fin.strftime('%Y-%m-%d %H:%M') if fin else 'N/A'
        p.drawString(x_margin, y, f'Reporte de: {inicio_str}  -  {fin_str}')
        y -= 14
        p.line(x_margin, y, width - x_margin, y)
        y -= 18

        p.setFont('Helvetica', 10)

        for idx, pedido in enumerate(pedidos):
            if y < 120:
                p.showPage()
                y = height - 60
                p.setFont('Helvetica', 10)

            # Encabezado del pedido
            p.setFont('Helvetica-Bold', 11)
            p.drawString(x_margin, y, f'Pedido: {pedido.numero_pedido}')
            p.setFont('Helvetica', 10)
            p.drawRightString(width - x_margin, y, f'Fecha: {timezone.localtime(pedido.fecha_creacion).strftime("%Y-%m-%d %H:%M") if pedido.fecha_creacion else "N/A"}')
            y -= 14

            p.drawString(x_margin, y, f'Cliente: {pedido.usuario.get_full_name() or pedido.usuario.username}')
            p.drawRightString(width - x_margin, y, f'Total: ${pedido.total:,.2f}')
            y -= 14

            p.drawString(x_margin, y, f'Método pago: {pedido.metodo_pago or "N/A"}    Estado pago: {pedido.estado_pago_display or "N/A"}')
            y -= 14

            # Dirección y contacto
            p.drawString(x_margin, y, f'Teléfono: {pedido.telefono_contacto or "-"}')
            y -= 12
            text = p.beginText(x_margin, y)
            text.setFont('Helvetica', 10)
            dir_text = str(pedido.direccion_entrega or '')
            for line in dir_text.splitlines():
                text.textLine(line)
            p.drawText(text)
            y = text.getY() - 10

            # Items
            p.setFont('Helvetica-Bold', 10)
            p.drawString(x_margin, y, 'Producto')
            p.drawRightString(width - 200, y, 'Cantidad')
            p.drawRightString(width - 120, y, 'Precio')
            p.drawRightString(width - x_margin, y, 'Subtotal')
            y -= 12
            p.setFont('Helvetica', 10)

            for item in pedido.items.all():
                if y < 80:
                    p.showPage()
                    y = height - 60
                p.drawString(x_margin, y, item.producto.nombre)
                p.drawRightString(width - 200, y, str(item.cantidad))
                p.drawRightString(width - 120, y, f'${item.precio_unitario:,.2f}')
                p.drawRightString(width - x_margin, y, f'${item.subtotal:,.2f}')
                y -= 12

            # Línea separadora entre pedidos
            y -= 6
            p.line(x_margin, y, width - x_margin, y)
            y -= 16

        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        filename = f'reporte_pedidos_{inicio_str}_a_{fin_str}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        return response
    crear_reporte_pdf.short_description = 'Crear reporte PDF de pedidos seleccionados'

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario_formateado', 'subtotal_formateado')
    list_filter = ('pedido__estado', 'pedido__fecha_creacion')
    search_fields = ('pedido__numero_pedido', 'producto__nombre')
    readonly_fields = ('precio_unitario_formateado', 'subtotal_formateado')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pedido', 'producto')
