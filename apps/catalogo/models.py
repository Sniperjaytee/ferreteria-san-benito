from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django.utils.text import slugify
from decimal import Decimal

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Nombre de la categoría (mínimo 2 caracteres)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada de la categoría"
    )
    imagen = models.ImageField(
        upload_to='categorias/',
        blank=True,
        null=True,
        help_text="Imagen representativa de la categoría"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Indica si la categoría está disponible"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización (menor número = mayor prioridad)"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="URL amigable (se genera automáticamente)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['orden', 'nombre']
        indexes = [
            models.Index(fields=['activa', 'orden']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        """Genera automáticamente el slug si no existe"""
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
    @property
    def productos_activos(self):
        """Retorna el número de productos activos en esta categoría"""
        return self.productos.filter(activo=True).count()
    
    @property
    def tiene_productos(self):
        """Verifica si la categoría tiene productos"""
        return self.productos.exists()


class Producto(models.Model):
    MONEDAS = [
        ('USD', 'Dólar Americano (USD)'),
        ('VES', 'Bolívar Venezolano (VES)'),
        ('COP', 'Peso Colombiano (COP)'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text="Nombre del producto (mínimo 3 caracteres)"
    )
    descripcion = models.TextField(
        help_text="Descripción detallada del producto"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio del producto en la moneda base"
    )
    moneda_precio = models.CharField(
        max_length=3,
        choices=MONEDAS,
        default='USD',
        help_text="Moneda del precio base"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='productos',
        help_text="Categoría a la que pertenece el producto"
    )
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad disponible en inventario"
    )
    stock_minimo = models.PositiveIntegerField(
        default=5,
        help_text="Stock mínimo antes de alertar"
    )
    imagen = models.ImageField(
        upload_to='productos/',
        help_text="Imagen principal del producto"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el producto está disponible para venta"
    )
    destacado = models.BooleanField(
        default=False,
        help_text="Producto destacado en la página principal"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL amigable (se genera automáticamente)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-destacado', '-created_at']
        indexes = [
            models.Index(fields=['activo', 'destacado']),
            models.Index(fields=['categoria', 'activo']),
            models.Index(fields=['precio']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        if self.categoria:
            return f"{self.nombre} - {self.categoria.nombre}"
        return self.nombre
    
    def save(self, *args, **kwargs):
        """Genera automáticamente el slug si no existe"""
        if not self.slug and self.nombre and self.categoria:
            self.slug = slugify(f"{self.nombre}-{self.categoria.nombre}")
        super().save(*args, **kwargs)
    
    def obtener_precio_en_moneda(self, moneda_destino):
        """Obtiene el precio del producto en una moneda específica"""
        from core.models import TasaCambio
        
        if self.moneda_precio == moneda_destino:
            return self.precio
        
        tasa = TasaCambio.obtener_tasa(self.moneda_precio, moneda_destino)
        return self.precio * tasa
    
    def obtener_precios_multiple_monedas(self):
        """Retorna los precios en todas las monedas disponibles"""
        from core.models import ConfiguracionMoneda
        
        config = ConfiguracionMoneda.obtener_configuracion()
        precios = {}
        
        for moneda in config.monedas_mostrar:
            precio = self.obtener_precio_en_moneda(moneda)
            simbolo = config.simbolos.get(moneda, moneda)
            precios[moneda] = {
                'precio': precio,
                'simbolo': simbolo,
                'formateado': f"{simbolo}{precio:,.{config.decimales_precision}f}"
            }
        
        return precios
    
    @property
    def precio_formateado(self):
        """Retorna el precio formateado en la moneda base"""
        from core.models import ConfiguracionMoneda
        
        config = ConfiguracionMoneda.obtener_configuracion()
        simbolo = config.simbolos.get(self.moneda_precio, self.moneda_precio)
        try:
            precio_val = self.precio if self.precio is not None else Decimal('0.00')
            return f"{simbolo}{precio_val:,.{config.decimales_precision}f}"
        except Exception:
            return f"{simbolo}0.00"
    
    @property
    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        if self.stock is not None and self.stock_minimo is not None:
            return self.stock <= self.stock_minimo
        return False
    
    @property
    def disponible(self):
        """Verifica si el producto está disponible para venta"""
        if self.stock is not None:
            return self.activo and self.stock > 0
        return self.activo
    
    def reducir_stock(self, cantidad):
        """Reduce el stock del producto"""
        if self.stock is not None and self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        return False
    
    def aumentar_stock(self, cantidad):
        """Aumenta el stock del producto"""
        if self.stock is not None:
            self.stock += cantidad
        else:
            self.stock = cantidad
        self.save()
