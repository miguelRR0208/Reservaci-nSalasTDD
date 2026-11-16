from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# usuario, contraseña, es administrador
USUARIOS_PRUEBA = [
    ('ana', 'Reserva2026', False),
    ('beto', 'Reserva2026', False),
    ('admin', 'Admin2026', True),
]


class Command(BaseCommand):
    help = 'Crea o restablece los usuarios de prueba del sistema.'

    def handle(self, *args, **opciones):
        for nombre, clave, es_admin in USUARIOS_PRUEBA:
            usuario, _ = User.objects.get_or_create(username=nombre)
            usuario.set_password(clave)
            usuario.is_staff = es_admin
            usuario.is_superuser = es_admin
            usuario.save()
            self.stdout.write(f'Usuario listo: {nombre}')
