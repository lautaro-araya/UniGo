from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Avg
from .forms import RegistroForm, VehiculoForm, ViajeForm
from .models import Usuario, Vehiculo, Viaje, Reserva, Calificacion
from django.contrib import messages
from django.views.decorators.cache import never_cache

@never_cache
def login_view(request):
    """
    Vista para manejar el inicio de sesión de usuarios
    """
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.get_full_name()}!')
            next_url = request.GET.get('next', 'inicio')
            return redirect(next_url)
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
            user.save()
            
            # Si es conductor, crear el vehículo
            if user.tipo_usuario == 'conductor':
                Vehiculo.objects.create(
                    conductor=user,
                    marca=form.cleaned_data['marca_vehiculo'],
                    modelo=form.cleaned_data['modelo_vehiculo'],
                    patente=form.cleaned_data['patente'],
                    año=form.cleaned_data['año_vehiculo'],
                    asientos_disponibles=4  # Valor por defecto
                )
            
            login(request, user)
            messages.success(request, '¡Registro exitoso!')
            return redirect('inicio')
    else:
        form = RegistroForm()
    
    return render(request, 'core/registro.html', {'form': form})

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
def mis_viajes(request):
    viajes = Viaje.objects.filter(conductor=request.user).order_by('-fecha_hora_salida')
    return render(request, 'core/mis_viajes.html', {'viajes': viajes})

@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(pasajero=request.user).order_by('-creado_en')
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