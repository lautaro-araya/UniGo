from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inicio', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('publicar-viaje/', views.publicar_viaje, name='publicar_viaje'),
    path('reservar-viaje/<int:viaje_id>/', views.reservar_viaje, name='reservar_viaje'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar-reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('calificar-viaje/<int:reserva_id>/', views.calificar_viaje, name='calificar_viaje'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/actualizar/', views.actualizar_perfil, name='actualizar_perfil'),
    path('perfil/cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('perfil/vehiculo/', views.actualizar_vehiculo, name='actualizar_vehiculo'),
    ###
    path('mis-viajes/', views.mis_viajes, name='mis_viajes'),
    path('viaje/editar/<int:viaje_id>/', views.editar_viaje, name='editar_viaje'),
    path('viaje/cancelar/<int:viaje_id>/', views.cancelar_viaje, name='cancelar_viaje'),
    path('viaje/reservas/<int:viaje_id>/', views.ver_reservas_viaje, name='ver_reservas_viaje'),
    path('reserva/confirmar/<int:reserva_id>/', views.confirmar_reserva, name='confirmar_reserva'),
    path('viaje/terminar/<int:viaje_id>/', views.terminar_viaje, name='terminar_viaje'),
    path('chats/', views.listar_chats, name='lista_chats'),
    path('chat/<int:reserva_id>/', views.ver_chat, name='ver_chat'),
    path('aprobar-usuarios/', views.aprobar_usuarios, name='aprobar_usuarios'),
    path('ver-documento/<int:user_id>/', views.ver_documento, name='ver_documento'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)