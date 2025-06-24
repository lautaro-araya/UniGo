from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Reserva, ChatViaje

@receiver(pre_save, sender=Reserva)
def manejar_estado_chat(sender, instance, **kwargs):
    if instance.pk:  # Solo si ya existe
        original = Reserva.objects.get(pk=instance.pk)
        
        # Si la reserva se cancela o completa
        if (original.estado == 'confirmada' and instance.estado != 'confirmada') or instance.estado == 'completada':
            ChatViaje.objects.filter(
                viaje=instance.viaje,
                pasajero=instance.pasajero
            ).update(activo=False)