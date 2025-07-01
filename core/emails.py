from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def enviar_notificacion_admin(usuario):
    asunto = f"Nuevo usuario registrado: {usuario.get_full_name()}"
    mensaje = f"""
    Un nuevo usuario se ha registrado en la plataforma:
    
    Nombre: {usuario.get_full_name()}
    Email: {usuario.email}
    RUN: {usuario.run}
    Tipo: {usuario.get_tipo_usuario_display()}
    
    Por favor revisa la solicitud en el panel de administración.
    """
    
    send_mail(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],  # Se envía a ti mismo
        fail_silently=False,
    )

def enviar_notificacion_aprobacion(usuario):
    asunto = "¡Tu cuenta ha sido aprobada!"
    
    # Puedes crear un template HTML en templates/emails/aprobacion.html
    html_message = render_to_string('core/aprobacion.html', {
        'usuario': usuario,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        asunto,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [usuario.email],  # Se envía al usuario
        html_message=html_message,
        fail_silently=False,
    )