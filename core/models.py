from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import os
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

def user_pdf_upload_path(instance, filename):
    # Guarda el archivo en: media/users/<user_id>/documento.pdf
    return os.path.join('users', str(instance.id), 'documento.pdf')

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('conductor', 'Conductor'),
        ('pasajero', 'Pasajero'),
    ]
    
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='pasajero')
    run = models.CharField(max_length=12)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    universidad = models.CharField(max_length=100, blank=True, null=True)
    calificacion = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=5.0
    )
    aprobado = models.BooleanField(default=False, verbose_name="Cuenta aprobada")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    documento_pdf = models.BinaryField(null=True, blank=True, editable=True)
    documento_nombre = models.CharField(max_length=255, null=True, blank=True)
    documento_tipo = models.CharField(max_length=100, null=True, blank=True)
    documento_size = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.tipo_usuario})"

class Vehiculo(models.Model):
    conductor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='vehiculos')
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.PositiveIntegerField()
    patente = models.CharField(max_length=10, unique=True)
    color = models.CharField(max_length=30)
    asientos_disponibles = models.PositiveIntegerField(default=1)

    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente})"

class Viaje(models.Model):
    conductor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='viajes_conductor')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='viajes')
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    fecha_hora_salida = models.DateTimeField()
    asientos_disponibles = models.PositiveIntegerField()
    precio_por_pasajero = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"De {self.origen} a {self.destino} - {self.fecha_hora_salida.strftime('%d/%m/%Y %H:%M')}"

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='reservas')
    pasajero = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas_pasajero')
    asientos_reservados = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Reserva de {self.pasajero} para viaje {self.viaje.id}"

class Calificacion(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='calificaciones')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_hechas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_recibidas')
    puntuacion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('viaje', 'calificador', 'calificado')
    
    def __str__(self):
        return f"{self.puntuacion} estrellas de {self.calificador} a {self.calificado}"

User = get_user_model()

class ChatViaje(models.Model):
    viaje = models.ForeignKey('Viaje', on_delete=models.CASCADE, related_name='chats')
    pasajero = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_como_pasajero')
    conductor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_como_conductor')
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('viaje', 'pasajero')

    def tiene_mensajes_no_leidos(self, usuario):
        """Verifica si hay mensajes no leídos para el usuario"""
        if usuario.tipo_usuario == 'pasajero':
            return self.mensajes.filter(leido=False, autor=self.conductor).exists()
        return False

class MensajeChat(models.Model):
    chat = models.ForeignKey(ChatViaje, on_delete=models.CASCADE, related_name='mensajes')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado_en']