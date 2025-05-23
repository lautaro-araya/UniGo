from django.contrib import admin
from .models import Vehiculo, Viaje, Usuario, Reserva, Calificacion

admin.site.register(Viaje)
admin.site.register(Vehiculo)
admin.site.register(Usuario)
admin.site.register(Reserva)
admin.site.register(Calificacion)

