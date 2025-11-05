from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.utils.text import slugify
from decimal import Decimal

# Create your models here.

class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(
        max_length=10,
        unique=True,
        validators=[MinLengthValidator(7)],
    )
    telefono = models.CharField(
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+58 \d{10}$',
                message="El número de teléfono debe tener el formato: +58 4127715553"
            )
        ]
    )
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    es_empleado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.cedula})"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        """Retorna el email del usuario"""
        return self.user.email


class TasaCambio(models.Model):
    MONEDAS = [
        ('USD', 'Dólar Americano (USD)'),
        ('VES', 'Bolívar Venezolano (VES)'),
        ('COP', 'Peso Colombiano (COP)'),
        ('EUR', 'Euro (EUR)'),
    ]
    
    moneda_origen = models.CharField(
        max_length=3,
        choices=MONEDAS,
        help_text="Moneda de origen"
    )
    moneda_destino = models.CharField(
        max_length=3,
        choices=MONEDAS,
        help_text="Moneda de destino"
    )
    tasa = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="Tasa de cambio (1 unidad de origen = X unidades de destino)"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Indica si esta tasa está activa"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que actualizó la tasa"
    )
    notas = models.TextField(
        blank=True,
        help_text="Notas sobre la tasa de cambio"
    )
    
    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        unique_together = ['moneda_origen', 'moneda_destino']
        ordering = ['moneda_origen', 'moneda_destino']
    
    def __str__(self):
        return f"1 {self.moneda_origen} = {self.tasa} {self.moneda_destino}"
    
    @classmethod
    def obtener_tasa(cls, moneda_origen, moneda_destino):
        """Obtiene la tasa de cambio entre dos monedas"""
        if moneda_origen == moneda_destino:
            return Decimal('1.000000')
        
        # Buscar tasa directa
        tasa = cls.objects.filter(
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            activa=True
        ).first()
        
        if tasa:
            return tasa.tasa
        
        # Buscar tasa inversa
        tasa_inversa = cls.objects.filter(
            moneda_origen=moneda_destino,
            moneda_destino=moneda_origen,
            activa=True
        ).first()
        
        if tasa_inversa:
            return Decimal('1') / tasa_inversa.tasa
        
        # Si no hay tasa directa ni inversa, retornar 1 (no se puede convertir)
        return Decimal('1.000000')
    
    @classmethod
    def convertir_moneda(cls, monto, moneda_origen, moneda_destino):
        """Convierte un monto de una moneda a otra"""
        if moneda_origen == moneda_destino:
            return monto
        
        tasa = cls.obtener_tasa(moneda_origen, moneda_destino)
        return monto * tasa


class ConfiguracionMoneda(models.Model):
    MONEDA_BASE = 'USD'
    MONEDAS_DISPONIBLES = [
        ('USD', 'Dólar Americano (USD)'),
        ('VES', 'Bolívar Venezolano (VES)'),
        ('COP', 'Peso Colombiano (COP)'),
        ('EUR', 'Euro (EUR)'),
    ]
    
    moneda_principal = models.CharField(
        max_length=3,
        choices=MONEDAS_DISPONIBLES,
        default=MONEDA_BASE,
        help_text="Moneda principal del sistema"
    )
    mostrar_multiple_monedas = models.BooleanField(
        default=True,
        help_text="Mostrar precios en múltiples monedas"
    )
    monedas_mostrar = models.JSONField(
        default=list,
        help_text="Lista de monedas a mostrar (ej: ['USD', 'VES', 'COP'])"
    )
    decimales_precision = models.PositiveIntegerField(
        default=2,
        help_text="Número de decimales para mostrar precios"
    )
    simbolos_monedas = models.JSONField(
        default=dict,
        help_text="Símbolos de monedas (ej: {'USD': '$', 'VES': 'Bs', 'COP': '$'})"
    )
    
    class Meta:
        verbose_name = "Configuración de Moneda"
        verbose_name_plural = "Configuraciones de Moneda"
    
    def __str__(self):
        return f"Configuración - Moneda Principal: {self.moneda_principal}"
    
    @classmethod
    def obtener_configuracion(cls):
        """Obtiene la configuración actual o crea una por defecto"""
        config, created = cls.objects.get_or_create(
            defaults={
                'moneda_principal': cls.MONEDA_BASE,
                'mostrar_multiple_monedas': True,
                'monedas_mostrar': ['USD', 'VES', 'COP', 'EUR'],
                'decimales_precision': 2,
                'simbolos_monedas': {
                    'USD': '$',
                    'VES': 'Bs',
                    'COP': '$',
                    'EUR': '€'
                }
            }
        )
        return config
    
    @property
    def simbolos(self):
        """Retorna los símbolos de monedas"""
        return self.simbolos_monedas or {
            'USD': '$',
            'VES': 'Bs',
            'COP': '$',
            'EUR': '€'
        }
