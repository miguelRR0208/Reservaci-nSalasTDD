from io import StringIO

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase


class TestComandoUsuariosDePrueba(TestCase):

    def ejecutar(self):
        salida = StringIO()
        call_command('crear_usuarios_prueba', stdout=salida)
        return salida.getvalue()

    def test_crea_usuarios_que_pueden_iniciar_sesion(self):
        self.ejecutar()
        for usuario, clave in [('ana', 'Reserva2026'),
                               ('beto', 'Reserva2026'),
                               ('admin', 'Admin2026')]:
            with self.subTest(usuario=usuario):
                self.assertIsNotNone(
                    authenticate(username=usuario, password=clave)
                )

    def test_admin_es_superusuario(self):
        self.ejecutar()
        admin = User.objects.get(username='admin')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_usuarios_normales_no_son_administradores(self):
        self.ejecutar()
        ana = User.objects.get(username='ana')
        self.assertFalse(ana.is_staff)
        self.assertFalse(ana.is_superuser)

    def test_ejecutarlo_dos_veces_no_duplica_usuarios(self):
        self.ejecutar()
        self.ejecutar()
        self.assertEqual(
            User.objects.filter(username__in=['ana', 'beto', 'admin'])
            .count(),
            3,
        )

    def test_restablece_la_contrasena_si_fue_cambiada(self):
        self.ejecutar()
        ana = User.objects.get(username='ana')
        ana.set_password('otra-clave-123')
        ana.save()
        self.ejecutar()
        self.assertIsNotNone(
            authenticate(username='ana', password='Reserva2026')
        )

    def test_informa_los_usuarios_listos(self):
        salida = self.ejecutar()
        self.assertIn('Usuario listo: ana', salida)
        self.assertIn('Usuario listo: beto', salida)
        self.assertIn('Usuario listo: admin', salida)
