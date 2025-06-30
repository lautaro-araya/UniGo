from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Avg, Q, Count
from .forms import RegistroForm, VehiculoForm, ViajeForm, PerfilUpdateForm, CustomPasswordChangeForm, VehiculoForm2
from .models import Usuario, Vehiculo, Viaje, Reserva, Calificacion, ChatViaje, MensajeChat
from django.views.decorators.cache import never_cache
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_GET

@require_GET
def ver_documento(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)
        if usuario.documento_pdf:
            response = HttpResponse(usuario.documento_pdf, content_type=usuario.documento_tipo)
            response['Content-Disposition'] = f'inline; filename="{usuario.documento_nombre}"'
            return response
        raise Http404("Documento no encontrado")
    except Usuario.DoesNotExist:
        raise Http404("Usuario no encontrado")


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Permitir acceso a superusuarios sin aprobación
            if user.is_superuser:
                login(request, user)
                messages.success(request, f'¡Bienvenido administrador {user.get_full_name()}!')
                return redirect('aprobar_usuarios')  # Redirigir directamente a la vista de aprobación
            
            # Para usuarios normales, verificar aprobación
            if user.aprobado:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.get_full_name()}!')
                next_url = request.GET.get('next', 'inicio')
                return redirect(next_url)
            else:
                messages.error(request, 'Tu cuenta está pendiente de aprobación. Por favor, espera a que un administrador la active.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'core/login.html')

@login_required
def logout_view(request):
    """
    Vista para cerrar sesión
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('login')

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.aprobado = False
            user.save()
            
            if user.tipo_usuario == 'conductor':
                Vehiculo.objects.create(
                    conductor=user,
                    marca=form.cleaned_data['marca_vehiculo'],
                    modelo=form.cleaned_data['modelo_vehiculo'],
                    patente=form.cleaned_data['patente'],
                    año=form.cleaned_data['año_vehiculo'],
                    asientos_disponibles=form.cleaned_data['asientos_vehiculo'] or 4
                )
            
            messages.success(request, '¡Registro exitoso! Tu cuenta está pendiente de aprobación.')
            return redirect('login')
    else:
        form = RegistroForm()
    
    return render(request, 'core/registro.html', {'form': form})

def es_administrador(user):
    return user.is_authenticated and (user.is_superuser or hasattr(user, 'superadministrador'))

@user_passes_test(es_administrador, login_url='login')
def aprobar_usuarios(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        accion = request.POST.get('accion')
        
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            if accion == 'aprobar':
                usuario.aprobado = True
                usuario.save()
                messages.success(request, f'Cuenta de {usuario.get_full_name()} aprobada exitosamente.')
            elif accion == 'rechazar':
                usuario.delete()
                messages.success(request, f'Cuenta de {usuario.get_full_name()} rechazada y eliminada.')
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
        
        return redirect('aprobar_usuarios')
    
    usuarios_pendientes = Usuario.objects.filter(aprobado=False).order_by('fecha_registro')
    return render(request, 'core/aprobar_usuarios.html', {'usuarios_pendientes': usuarios_pendientes})

@login_required
def inicio(request):
    viajes = Viaje.objects.filter(activo=True).order_by('-fecha_hora_salida')
    return render(request, 'core/inicio.html', {'viajes': viajes})

@login_required
def publicar_viaje(request):
    if request.method == 'POST':
        form = ViajeForm(request.POST)
        if form.is_valid():
            viaje = form.save(commit=False)
            viaje.conductor = request.user
            viaje.save()
            return redirect('inicio')
    else:
        form = ViajeForm()
    return render(request, 'core/publicar_viaje.html', {'form': form})

@login_required
def reservar_viaje(request, viaje_id):
    viaje = Viaje.objects.get(id=viaje_id)
    if request.method == 'POST':
        asientos = int(request.POST.get('asientos', 1))
        if viaje.asientos_disponibles >= asientos:
            Reserva.objects.create(
                viaje=viaje,
                pasajero=request.user,
                asientos_reservados=asientos,
                estado='pendiente'
            )
            viaje.asientos_disponibles -= asientos
            viaje.save()
            return redirect('mis_reservas')
    return render(request, 'core/reservar_viaje.html', {'viaje': viaje})


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(
        pasajero=request.user
    ).select_related('viaje', 'viaje__conductor').prefetch_related('viaje__chats__mensajes')
    
    for reserva in reservas:
        # Obtener el chat asociado si existe
        reserva.chat = reserva.viaje.chats.filter(pasajero=request.user).first()
        
        if reserva.chat:
            reserva.tiene_mensajes_no_leidos = reserva.chat.mensajes.filter(
                leido=False, 
                autor=reserva.viaje.conductor
            ).exists()
    
    return render(request, 'core/mis_reservas.html', {'reservas': reservas})

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, pasajero=request.user)
    
    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()
        
        # Liberar los asientos en el viaje
        viaje = reserva.viaje
        viaje.asientos_disponibles += reserva.asientos_reservados
        viaje.save()
        
        messages.success(request, 'Reserva cancelada exitosamente.')
        return redirect('mis_reservas')
    
    return redirect('mis_reservas')

@login_required
def calificar_viaje(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, pasajero=request.user)
    
    if reserva.estado != 'completada' or reserva.calificacion.exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        puntuacion = int(request.POST.get('puntuacion'))
        comentario = request.POST.get('comentario', '')
        
        Calificacion.objects.create(
            viaje=reserva.viaje,
            calificador=request.user,
            calificado=reserva.viaje.conductor,
            puntuacion=puntuacion,
            comentario=comentario
        )
        
        # Actualizar calificación promedio del conductor
        conductor = reserva.viaje.conductor
        calificaciones = Calificacion.objects.filter(calificado=conductor)
        conductor.calificacion = calificaciones.aggregate(Avg('puntuacion'))['puntuacion__avg']
        conductor.save()
        
        messages.success(request, '¡Gracias por calificar este viaje!')
        return redirect('mis_reservas')
    
    return redirect('mis_reservas')

@login_required
def perfil(request):
    user = request.user
    vehiculo = None
    
    if user.tipo_usuario == 'conductor':
        try:
            vehiculo = user.vehiculos.first()  # Asumiendo relación one-to-one o first() si es one-to-many
        except:
            vehiculo = None
    
    # Formulario de actualización de perfil
    perfil_form = PerfilUpdateForm(instance=user)
    password_form = CustomPasswordChangeForm(user=user)
    vehiculo_form = VehiculoForm2(instance=vehiculo) if vehiculo else VehiculoForm2()
    
    context = {
        'perfil_form': perfil_form,
        'password_form': password_form,
        'vehiculo_form': vehiculo_form,
        'vehiculo': vehiculo,
    }
    
    return render(request, 'core/perfil.html', context)

@login_required
def actualizar_perfil(request):
    if request.method == 'POST':
        form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    return redirect('perfil')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante para no desloguear al usuario
            messages.success(request, 'Tu contraseña ha sido cambiada correctamente.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    return redirect('perfil')

@login_required
def actualizar_vehiculo(request):
    if request.user.tipo_usuario != 'conductor':
        return redirect('perfil')
    
    vehiculo = request.user.vehiculos.first() if hasattr(request.user, 'vehiculos') else None
    
    if request.method == 'POST':
        form = VehiculoForm2(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.conductor = request.user
            vehiculo.save()
            messages.success(request, 'La información del vehículo ha sido actualizada.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    return redirect('perfil')


##jajajjajaja
@login_required
def mis_viajes(request):
    viajes = Viaje.objects.filter(conductor=request.user).order_by('-fecha_hora_salida')
    return render(request, 'core/mis_viajes.html', {'viajes': viajes})

@login_required
def editar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id, conductor=request.user)
    
    if request.method == 'POST':
        form = ViajeForm(request.POST, instance=viaje)
        if form.is_valid():
            form.save()
            messages.success(request, 'Viaje actualizado correctamente')
            return redirect('mis_viajes')
        else:
            messages.error(request, 'Error al actualizar el viaje')
    else:
        form = ViajeForm(instance=viaje)
    
    # Para el modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'core/includes/modal_editar_viaje.html', {
            'form': form,
            'viaje': viaje
        })
    
    return render(request, 'core/mis_viajes.html', {
        'form': form,
        'viajes': Viaje.objects.filter(conductor=request.user)
    })

@login_required
def cancelar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id, conductor=request.user)
    
    if request.method == 'POST':
        viaje.activo = False
        viaje.save()
        
        # Cancelar todas las reservas asociadas
        viaje.reservas.update(estado='cancelada')
        
        messages.success(request, 'Viaje cancelado correctamente')
    else:
        messages.error(request, 'Método no permitido')
    
    return redirect('mis_viajes')

@login_required
def ver_reservas_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id, conductor=request.user)
    reservas = viaje.reservas.all().order_by('creado_en')
    
    # Para el modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'core/includes/modal_reservas_viaje.html', {
            'viaje': viaje,
            'reservas': reservas
        })
    
    return redirect('mis_viajes')

@login_required
def confirmar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, viaje__conductor=request.user)
    
    if request.method == 'POST':
        if reserva.estado == 'pendiente':
            reserva.estado = 'confirmada'
            reserva.save()
            messages.success(request, 'Reserva confirmada correctamente')
        else:
            messages.warning(request, 'La reserva ya estaba confirmada o cancelada')
    
    return redirect('mis_viajes')



@login_required
def terminar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id, conductor=request.user)
    
    if request.method == 'POST':
        if viaje.activo:
            viaje.activo = False
            viaje.save()
            
            # Marcar reservas confirmadas como completadas
            viaje.reservas.filter(estado='confirmada').update(estado='completada')
            
            messages.success(request, 'Viaje marcado como completado')
        else:
            messages.warning(request, 'El viaje ya estaba completado o cancelado')
    
    return redirect('mis_viajes')

@login_required
def listar_chats(request):
    # Obtener chats activos donde el usuario es conductor o pasajero
    chats = ChatViaje.objects.filter(
        Q(conductor=request.user) | Q(pasajero=request.user),
        activo=True
    ).select_related('pasajero', 'conductor', 'viaje')
    
    # Preprocesar datos para cada chat
    for chat in chats:
        # Obtener reserva asociada
        chat.reserva = Reserva.objects.filter(
            viaje=chat.viaje,
            pasajero=chat.pasajero
        ).first()
        
        # Verificar mensajes no leídos
        chat.tiene_no_leidos = chat.tiene_mensajes_no_leidos(request.user)
    
    # Filtrar chats que tienen reserva válida
    chats_validos = [chat for chat in chats if chat.reserva]
    
    return render(request, 'core/lista_chats.html', {
        'chats': chats_validos,
        'es_conductor': request.user.tipo_usuario == 'conductor'
    })

@login_required
def ver_chat(request, reserva_id):    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar que el usuario es el pasajero o conductor
    if request.user not in [reserva.pasajero, reserva.viaje.conductor]:
        messages.error(request, "No tienes permiso para acceder a este chat")
        return redirect('mis_reservas')
    
    # Verificar que la reserva está confirmada
    if reserva.estado != 'confirmada':
        messages.error(request, "El chat solo está disponible para reservas confirmadas")
        return redirect('mis_reservas')
    
    # Obtener o crear el chat
    chat, created = ChatViaje.objects.get_or_create(
        viaje=reserva.viaje,
        pasajero=reserva.pasajero,
        defaults={'conductor': reserva.viaje.conductor}
    )
    
    # Marcar mensajes como leídos
    if request.user == reserva.pasajero:
        chat.mensajes.filter(autor=reserva.viaje.conductor, leido=False).update(leido=True)
    else:
        chat.mensajes.filter(autor=reserva.pasajero, leido=False).update(leido=True)
    
    # Enviar mensaje si se envió el formulario
    if request.method == 'POST':
        contenido = request.POST.get('contenido', '').strip()
        if contenido:
            MensajeChat.objects.create(
                chat=chat,
                autor=request.user,
                contenido=contenido
            )
            return redirect('ver_chat', reserva_id=reserva.id)
    
    # Obtener todos los mensajes del chat
    mensajes = chat.mensajes.all()
    
    return render(request, 'core/chat.html', {
        'chat': chat,
        'mensajes': mensajes,
        'reserva': reserva,
        'otro_usuario': reserva.viaje.conductor if request.user == reserva.pasajero else reserva.pasajero
    })

