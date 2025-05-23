from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inicio', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('publicar-viaje/', views.publicar_viaje, name='publicar_viaje'),
    path('reservar-viaje/<int:viaje_id>/', views.reservar_viaje, name='reservar_viaje'),
    path('mis-viajes/', views.mis_viajes, name='mis_viajes'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar-reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('calificar-viaje/<int:reserva_id>/', views.calificar_viaje, name='calificar_viaje'),
]
