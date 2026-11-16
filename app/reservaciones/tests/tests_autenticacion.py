from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class TestAutenticacion(TestCase):

    def setUp(self):
        User.objects.create_user('ana', password='Reserva2026')

    def test_pagina_de_login_usa_su_plantilla(self):
        respuesta = self.client.get(reverse('login'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'registration/login.html')
        self.assertContains(respuesta, 'id="boton-entrar"')

    def test_login_valido_lleva_a_mis_reservaciones(self):
        respuesta = self.client.post(
            reverse('login'),
            {'username': 'ana', 'password': 'Reserva2026'},
        )
        self.assertRedirects(respuesta, reverse('reservaciones:lista'))

    def test_login_invalido_muestra_mensaje(self):
        respuesta = self.client.post(
            reverse('login'),
            {'username': 'ana', 'password': 'equivocada'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'class="mensaje"')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cerrar_sesion_regresa_al_login(self):
        self.client.login(username='ana', password='Reserva2026')
        respuesta = self.client.post(reverse('logout'))
        self.assertRedirects(respuesta, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_raiz_del_sitio_lleva_a_mis_reservaciones(self):
        respuesta = self.client.get('/')
        self.assertRedirects(
            respuesta, reverse('reservaciones:lista'),
            fetch_redirect_response=False,
        )
