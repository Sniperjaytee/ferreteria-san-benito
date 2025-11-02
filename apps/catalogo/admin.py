from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Categoria, Producto

# Register your models here.

class ProductoInline(admin.TabularInline):
    model = Producto
    extra = 0
    fields = ('nombre', 'precio', 'moneda_precio', 'stock', 'activo', 'destacado')
    readonly_fields = ('created_at',)
    show_change_link = True

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'productos_activos', 'activa', 'orden', 'created_at')
    list_filter = ('activa', 'created_at')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('activa', 'orden')
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ('created_at', 'updated_at', 'productos_activos', 'imagen_preview')
    inlines = [ProductoInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview')
        }),
        ('Configuración', {
            'fields': ('activa', 'orden')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('productos')
    
    def productos_activos(self, obj):
        count = obj.productos_activos
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: red;">{}</span>',
            count
        )
    productos_activos.short_description = 'Productos Activos'
    
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.imagen.url
            )
        return "Sin imagen"
    imagen_preview.short_description = 'Vista Previa'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_formateado', 'moneda_precio', 'stock', 'stock_status', 'activo', 'destacado', 'created_at')
    list_filter = ('activo', 'destacado', 'categoria', 'moneda_precio', 'created_at')
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')
    list_editable = ('activo', 'destacado', 'stock')
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ('created_at', 'updated_at', 'imagen_preview', 'precio_formateado', 'precios_multiple_monedas')
    filter_horizontal = ()
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion', 'categoria')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'moneda_precio', 'precio_formateado', 'precios_multiple_monedas', 'stock', 'stock_minimo')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview')
        }),
        ('Configuración', {
            'fields': ('activo', 'destacado')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categoria')
    
    def stock_status(self, obj):
        if obj.stock_bajo:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Bajo</span>'
            )
        elif obj.stock == 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ Agotado</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✅ Disponible</span>'
            )
    stock_status.short_description = 'Estado Stock'
    
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.imagen.url
            )
        return "Sin imagen"
    imagen_preview.short_description = 'Vista Previa'
    
    def precio_formateado(self, obj):
        return obj.precio_formateado
    precio_formateado.short_description = 'Precio'
    
    def precios_multiple_monedas(self, obj):
        """Muestra los precios en todas las monedas configuradas"""
        try:
            precios = obj.obtener_precios_multiple_monedas()
            html = []
            for moneda, data in precios.items():
                if moneda != obj.moneda_precio:  # No mostrar la moneda base
                    html.append(f"<strong>{data['formateado']}</strong>")
            
            if html:
                return format_html('<br>'.join(html))
            else:
                return "Configurar tasas de cambio"
        except:
            return "Error en conversión"
    precios_multiple_monedas.short_description = 'Precios en Otras Monedas'
    
    # Acciones personalizadas
    actions = ['marcar_como_destacado', 'marcar_como_no_destacado', 'activar_productos', 'desactivar_productos']
    
    def marcar_como_destacado(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} productos marcados como destacados.')
    marcar_como_destacado.short_description = "Marcar como destacados"
    
    def marcar_como_no_destacado(self, request, queryset):
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} productos desmarcados como destacados.')
    marcar_como_no_destacado.short_description = "Desmarcar como destacados"
    
    def activar_productos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} productos activados.')
    activar_productos.short_description = "Activar productos seleccionados"
    
    def desactivar_productos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} productos desactivados.')
    desactivar_productos.short_description = "Desactivar productos seleccionados"
