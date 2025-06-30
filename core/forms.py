from django import forms
import re
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Vehiculo, Viaje
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

def validate_file_size(value):
    limit = 5 * 1024 * 1024  # 5MB
    if value.size > limit:
        raise ValidationError('El archivo es demasiado grande. Tamaño máximo: 5MB.')

class RegistroForm(UserCreationForm):
    tipo_usuario = forms.ChoiceField(
        choices=Usuario.TIPO_USUARIO_CHOICES,
        widget=forms.RadioSelect,
        label="Tipo de usuario"
    )
    
    # Campos solo para conductores
    marca_vehiculo = forms.CharField(
        max_length=50,
        required=False,
        label="Marca del vehículo"
    )
    modelo_vehiculo = forms.CharField(
        max_length=50,
        required=False,
        label="Modelo del vehículo"
    )
    patente = forms.CharField(
        max_length=10,
        required=False,
        label="Patente"
    )
    año_vehiculo = forms.IntegerField(
        required=False,
        label="Año del vehículo",
        min_value=1990,
        max_value=2025
    )
    color_vehiculo = forms.CharField(
        label="Color del vehículo",
        max_length=30,
        required=False
    )
    
    asientos_vehiculo = forms.IntegerField(
        required=False,
        label="Numero de asientos vehículo",
        min_value=4,
        max_value=10, 
        initial=4
    )

    documento = forms.FileField(
        label="Documento de identificación",
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size,  # Validador de tamaño que creamos antes
        ]
    )
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'run',  'tipo_usuario', 
                 'telefono', 'universidad', 'password1', 'password2', 'documento',
                 'marca_vehiculo', 'modelo_vehiculo', 'patente', 'año_vehiculo', 'color_vehiculo', 'asientos_vehiculo']
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')
        if tipo_usuario == 'conductor':
            if not cleaned_data.get('marca_vehiculo'):
                self.add_error('marca_vehiculo', 'Este campo es obligatorio para conductores')
            if not cleaned_data.get('modelo_vehiculo'):
                self.add_error('modelo_vehiculo', 'Este campo es obligatorio para conductores')
            if not cleaned_data.get('patente'):
                self.add_error('patente', 'Este campo es obligatorio para conductores')
            if not cleaned_data.get('año_vehiculo'):
                self.add_error('año_vehiculo', 'Este campo es obligatorio para conductores')
        return cleaned_data
    
    def clean_run(self):
        rut = self.cleaned_data.get('run', '').strip().upper()

        if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
            raise ValidationError("El RUT debe tener el formato XX.XXX.XXX-Z. Ej: 20.123.456-7")

        rut_sin_puntos = rut.replace('.', '')
        cuerpo, dv = rut_sin_puntos.split('-')

        if not self.validar_dv(cuerpo, dv):
            raise ValidationError("El dígito verificador del RUT no es válido.")

        return rut  

    def validar_dv(self, rut_num, dv_input):
        suma = 0
        multiplo = 2

        for c in reversed(rut_num):
            suma += int(c) * multiplo
            multiplo = multiplo + 1 if multiplo < 7 else 2

        resto = 11 - (suma % 11)
        dv_esperado = {
            11: "0",
            10: "K"
        }.get(resto, str(resto))

        return dv_input.upper() == dv_esperado
    
    def clean_patente(self):
        patente = self.cleaned_data.get('patente')
        if patente and Vehiculo.objects.filter(patente=patente).exists():
            raise forms.ValidationError("Esta patente ya está registrada")
        return patente

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['marca', 'modelo', 'año', 'patente', 'color', 'asientos_disponibles']

class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = ['vehiculo', 'origen', 'destino', 'fecha_hora_salida', 'asientos_disponibles', 'precio_por_pasajero', 'descripcion']
        widgets = {
            'fecha_hora_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telefono', 'universidad']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'universidad': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class VehiculoForm2(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['marca', 'modelo', 'año', 'patente', 'color', 'asientos_disponibles']
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            'patente': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'asientos_disponibles': forms.NumberInput(attrs={'class': 'form-control'}),
        }