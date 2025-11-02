from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.

class Carrito(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carrito_items',
        help_text="Usuario propietario del carrito"
    )
    producto = models.ForeignKey(
        'catalogo.Producto',
        on_delete=models.CASCADE,
        help_text="Producto en el carrito"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Cantidad del producto"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item del Carrito"
        verbose_name_plural = "Items del Carrito"
        unique_together = ['usuario', 'producto']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['usuario', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre} (x{self.cantidad})"
    
    @property
    def subtotal(self):
        """Calcula el subtotal de este item"""
        if self.producto and self.producto.precio:
            return self.producto.precio * self.cantidad
        return Decimal('0.00')
    
    @property
    def subtotal_formateado(self):
        """Retorna el subtotal formateado"""
        return f"${self.subtotal:,.2f}"


class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    ESTADOS_PAGO = [
        ('pendiente', 'Pendiente de Pago'),
        ('verificando', 'Verificando Pago'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Pago Rechazado'),
    ]
    
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('pago_movil', 'Pago Móvil'),
        ('zelle', 'Zelle'),
        ('paypal', 'PayPal'),
        ('binance', 'Binance Pay'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
    ]
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pedidos',
        help_text="Usuario que realizó el pedido"
    )
    numero_pedido = models.CharField(
        max_length=20,
        unique=True,
        help_text="Número único del pedido"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total del pedido"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente',
        help_text="Estado actual del pedido"
    )
    estado_pago = models.CharField(
        max_length=20,
        choices=ESTADOS_PAGO,
        default='pendiente',
        help_text="Estado del pago"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default='efectivo',
        help_text="Método de pago seleccionado"
    )
    comprobante_pago = models.ImageField(
        upload_to='comprobantes/',
        blank=True,
        null=True,
        help_text="Comprobante de transferencia/pago móvil"
    )
    notas_pago = models.TextField(
        blank=True,
        help_text="Notas del usuario sobre el pago"
    )
    notas_administrador = models.TextField(
        blank=True,
        help_text="Notas del administrador sobre el pago"
    )
    administrador_pago = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_verificados',
        help_text="Administrador que verificó el pago"
    )
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se verificó el pago"
    )
    direccion_entrega = models.TextField(
        help_text="Dirección de entrega"
    )
    telefono_contacto = models.CharField(
        max_length=16,
        help_text="Teléfono de contacto para la entrega"
    )
    notas = models.TextField(
        blank=True,
        help_text="Notas adicionales del pedido"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_entrega = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha programada de entrega"
    )
    
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['estado_pago', 'fecha_creacion']),
            models.Index(fields=['estado', 'fecha_creacion']),
            models.Index(fields=['numero_pedido']),
        ]
    
    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.usuario.username}"
    
    def save(self, *args, **kwargs):
        """Genera automáticamente el número de pedido si no existe"""
        if not self.numero_pedido:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            self.numero_pedido = f"PED-{timestamp}"
        super().save(*args, **kwargs)
    
    @property
    def total_formateado(self):
        """Retorna el total formateado"""
        try:
            total = self.total if self.total is not None else Decimal('0.00')
            return f"${total:,.2f}"
        except Exception:
            return "$0.00"
    
    @property
    def items_count(self):
        """Retorna el número de items en el pedido"""
        return self.items.count()
    
    @property
    def estado_display(self):
        """Retorna el estado con emoji"""
        estados_emoji = {
            'pendiente': '⏳ Pendiente',
            'procesando': '🔄 En Proceso',
            'completado': '✅ Completado',
            'cancelado': '❌ Cancelado',
        }
        return estados_emoji.get(self.estado, self.estado)
    
    @property
    def estado_pago_display(self):
        """Retorna el estado del pago con emoji"""
        estados_pago_emoji = {
            'pendiente': '⏳ Pendiente de Pago',
            'verificando': '🔍 Verificando Pago',
            'pagado': '✅ Pago Verificado',
            'rechazado': '❌ Pago Rechazado',
        }
        return estados_pago_emoji.get(self.estado_pago, self.estado_pago)
    
    def aprobar_pago(self, administrador, notas=None):
        """Aprueba el pago del pedido"""
        from django.utils import timezone
        self.estado_pago = 'pagado'
        self.administrador_pago = administrador
        self.fecha_pago = timezone.now()
        if notas:
            self.notas_administrador = notas
        # Si el pago se aprueba, el pedido pasa a procesando
        if self.estado == 'pendiente':
            self.estado = 'procesando'
        self.save()
    
    def rechazar_pago(self, administrador, notas=None):
        """Rechaza el pago del pedido"""
        self.estado_pago = 'rechazado'
        self.administrador_pago = administrador
        if notas:
            self.notas_administrador = notas
        self.save()


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Pedido al que pertenece este item"
    )
    producto = models.ForeignKey(
        'catalogo.Producto',
        on_delete=models.CASCADE,
        help_text="Producto del pedido"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cantidad del producto"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del producto al momento del pedido"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Subtotal de este item (cantidad × precio)"
    )
    
    class Meta:
        verbose_name = "Item del Pedido"
        verbose_name_plural = "Items del Pedido"
        ordering = ['id']
        indexes = [
            models.Index(fields=['pedido', 'producto']),
        ]
    
    def __str__(self):
        return f"{self.pedido.numero_pedido} - {self.producto.nombre} (x{self.cantidad})"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal"""
        if self.precio_unitario and self.cantidad:
            self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
    
    @property
    def precio_unitario_formateado(self):
        """Retorna el precio unitario formateado"""
        try:
            val = self.precio_unitario if self.precio_unitario is not None else Decimal('0.00')
            return f"${val:,.2f}"
        except Exception:
            return "$0.00"
    
    @property
    def subtotal_formateado(self):
        """Retorna el subtotal formateado"""
        try:
            val = self.subtotal if self.subtotal is not None else Decimal('0.00')
            return f"${val:,.2f}"
        except Exception:
            return "$0.00"
