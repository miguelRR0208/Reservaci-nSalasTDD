from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from reservaciones.models import Reservacion
from salas.models import Sala


class BaseVistas(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user('ana', password='Reserva2026')
        self.otro = User.objects.create_user('beto', password='Reserva2026')
        self.sala = Sala.objects.get(nombre='Sala A')
        self.manana = timezone.localdate() + timedelta(days=1)
        self.url_lista = reverse('reservaciones:lista')
        self.url_nueva = reverse('reservaciones:nueva')

    def entrar(self):
        self.client.login(username='ana', password='Reserva2026')

    def datos(self, **cambios):
        datos = {
            'sala': self.sala.pk,
            'fecha': self.manana.strftime('%Y-%m-%d'),
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'asistentes': '3',
            'proposito': 'Estudiar para el examen final',
        }
        datos.update(cambios)
        return datos

    def reservacion_de(self, usuario, **cambios):
        valores = {
            'usuario': usuario,
            'sala': self.sala,
            'fecha': self.manana,
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 2,
            'proposito': 'Reservación ya registrada',
        }
        valores.update(cambios)
        return Reservacion.objects.create(**valores)


class TestVistaNuevaReservacion(BaseVistas):

    # UT-11

    def test_usuario_anonimo_es_enviado_al_login(self):
        respuesta = self.client.get(self.url_nueva)
        self.assertRedirects(
            respuesta, f'{reverse("login")}?next={self.url_nueva}'
        )

    def test_post_anonimo_no_registra_nada(self):
        respuesta = self.client.post(self.url_nueva, self.datos())
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Reservacion.objects.exists())

    def test_muestra_formulario_con_salas_activas(self):
        self.entrar()
        respuesta = self.client.get(self.url_nueva)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'nueva_reservacion.html')
        self.assertContains(respuesta, 'Sala A')
        self.assertNotContains(respuesta, 'Sala de mantenimiento')
        self.assertContains(respuesta, 'id="boton-guardar"')

    # UT-12

    def test_post_valido_registra_y_redirige_con_mensaje(self):
        self.entrar()
        respuesta = self.client.post(
            self.url_nueva, self.datos(), follow=True
        )
        self.assertRedirects(respuesta, self.url_lista)
        self.assertContains(
            respuesta, 'La reservación se registró correctamente.'
        )
        reservacion = Reservacion.objects.get()
        self.assertEqual(reservacion.usuario, self.usuario)
        self.assertEqual(reservacion.estado, Reservacion.Estado.VIGENTE)

    def test_post_invalido_conserva_datos_y_muestra_error(self):
        self.entrar()
        respuesta = self.client.post(
            self.url_nueva, self.datos(proposito='Corto')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta, 'El propósito debe tener entre 10 y 200 caracteres.'
        )
        self.assertContains(respuesta, 'value="Corto"')
        self.assertContains(respuesta, 'value="10:00"')
        self.assertFalse(Reservacion.objects.exists())

    def test_post_traslapado_muestra_que_la_sala_no_esta_disponible(self):
        self.reservacion_de(self.otro)
        self.entrar()
        respuesta = self.client.post(
            self.url_nueva,
            self.datos(hora_inicio='10:30', hora_fin='11:30'),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta, 'La sala no está disponible en el horario solicitado.'
        )
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_post_con_duracion_invalida_muestra_error_del_servicio(self):
        self.entrar()
        respuesta = self.client.post(
            self.url_nueva,
            self.datos(hora_inicio='10:00', hora_fin='13:00'),
        )
        self.assertContains(
            respuesta, 'La reservación debe durar entre 30 minutos y 2 horas.'
        )
        self.assertFalse(Reservacion.objects.exists())

    def test_post_sin_token_csrf_es_rechazado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.login(username='ana', password='Reserva2026')
        respuesta = cliente.post(self.url_nueva, self.datos())
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Reservacion.objects.exists())


class TestVistaListaReservaciones(BaseVistas):

    def test_usuario_anonimo_es_enviado_al_login(self):
        respuesta = self.client.get(self.url_lista)
        self.assertRedirects(
            respuesta, f'{reverse("login")}?next={self.url_lista}'
        )

    def test_muestra_las_reservaciones_del_usuario(self):
        self.reservacion_de(self.usuario, proposito='Mi sesión de estudio')
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertTemplateUsed(respuesta, 'lista_reservaciones.html')
        self.assertContains(respuesta, 'id="tabla-reservaciones"')
        self.assertContains(respuesta, 'Mi sesión de estudio')
        self.assertContains(respuesta, 'VIGENTE')

    def test_no_muestra_reservaciones_de_otros_usuarios(self):
        self.reservacion_de(self.otro, proposito='Sesión privada de beto')
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertNotContains(respuesta, 'Sesión privada de beto')

    def test_avisa_cuando_no_hay_reservaciones(self):
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, 'Todavía no tienes reservaciones.')

    def test_tiene_enlace_para_nueva_reservacion(self):
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, 'id="nueva-reservacion"')
        self.assertContains(respuesta, f'href="{self.url_nueva}"')

    def test_muestra_enlace_para_cancelar_cuando_se_puede(self):
        reservacion = self.reservacion_de(self.usuario)
        url = reverse('reservaciones:cancelar', args=[reservacion.pk])
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, f'id="cancelar-{reservacion.pk}"')
        self.assertContains(respuesta, f'href="{url}"')

    def test_no_muestra_enlace_para_cancelar_una_cancelada(self):
        reservacion = self.reservacion_de(
            self.usuario,
            estado=Reservacion.Estado.CANCELADA,
            fecha_cancelacion=timezone.now(),
        )
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertNotContains(respuesta, f'id="cancelar-{reservacion.pk}"')

    def test_no_muestra_enlace_si_falta_una_hora_o_menos(self):
        inicio = timezone.localtime() + timedelta(minutes=30)
        reservacion = self.reservacion_de(
            self.usuario, fecha=inicio.date(), hora_inicio=inicio.time()
        )
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertNotContains(respuesta, f'id="cancelar-{reservacion.pk}"')

    def test_muestra_fecha_y_hora_de_cancelacion(self):
        cancelada_el = timezone.make_aware(datetime(2030, 5, 9, 18, 45))
        self.reservacion_de(
            self.usuario,
            estado=Reservacion.Estado.CANCELADA,
            fecha_cancelacion=cancelada_el,
        )
        self.entrar()
        respuesta = self.client.get(self.url_lista)
        self.assertContains(respuesta, 'CANCELADA')
        self.assertContains(
            respuesta, '<td class="fecha-cancelacion">2030-05-09 18:45</td>',
            html=True,
        )


class TestVistaCancelarReservacion(BaseVistas):

    def setUp(self):
        super().setUp()
        self.reservacion = self.reservacion_de(self.usuario)
        self.url = self.url_de(self.reservacion)

    def url_de(self, reservacion):
        return reverse('reservaciones:cancelar', args=[reservacion.pk])

    def estado_de(self, reservacion):
        reservacion.refresh_from_db()
        return reservacion.estado

    # UT-18

    def test_get_anonimo_es_enviado_al_login(self):
        respuesta = self.client.get(self.url)
        self.assertRedirects(respuesta, f'{reverse("login")}?next={self.url}')

    def test_post_anonimo_no_cancela(self):
        respuesta = self.client.post(self.url)
        self.assertRedirects(respuesta, f'{reverse("login")}?next={self.url}')
        self.assertEqual(
            self.estado_de(self.reservacion), Reservacion.Estado.VIGENTE
        )

    def test_get_muestra_la_confirmacion_sin_cancelar(self):
        self.entrar()
        respuesta = self.client.get(self.url)
        self.assertTemplateUsed(respuesta, 'cancelar_reservacion.html')
        self.assertContains(respuesta, 'id="formulario-cancelar"')
        self.assertContains(respuesta, 'id="boton-confirmar"')
        self.assertContains(respuesta, 'Reservación ya registrada')
        self.assertEqual(
            self.estado_de(self.reservacion), Reservacion.Estado.VIGENTE
        )

    def test_post_cancela_y_redirige_con_mensaje(self):
        self.entrar()
        respuesta = self.client.post(self.url, follow=True)
        self.assertRedirects(respuesta, self.url_lista)
        self.assertContains(
            respuesta, 'La reservación se canceló correctamente.'
        )
        self.assertEqual(
            self.estado_de(self.reservacion), Reservacion.Estado.CANCELADA
        )

    # UT-19

    def test_post_a_reservacion_ajena_responde_404_sin_cambios(self):
        ajena = self.reservacion_de(
            self.otro,
            hora_inicio=time(12, 0),
            hora_fin=time(13, 0),
            proposito='Sesión privada de beto',
        )
        self.entrar()
        respuesta = self.client.post(self.url_de(ajena))
        self.assertContains(
            respuesta, 'No se encontró la página solicitada.',
            status_code=404,
        )
        self.assertNotContains(
            respuesta, 'Sesión privada de beto', status_code=404
        )
        self.assertEqual(self.estado_de(ajena), Reservacion.Estado.VIGENTE)

    def test_get_a_reservacion_ajena_responde_404(self):
        ajena = self.reservacion_de(
            self.otro, hora_inicio=time(12, 0), hora_fin=time(13, 0)
        )
        self.entrar()
        respuesta = self.client.get(self.url_de(ajena))
        self.assertEqual(respuesta.status_code, 404)

    def test_reservacion_inexistente_responde_404(self):
        self.entrar()
        respuesta = self.client.post(
            reverse('reservaciones:cancelar', args=[9999])
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_post_fuera_de_periodo_muestra_mensaje(self):
        inicio = timezone.localtime() + timedelta(minutes=30)
        proxima = self.reservacion_de(
            self.usuario,
            fecha=inicio.date(),
            hora_inicio=inicio.time(),
            proposito='Reservación que empieza pronto',
        )
        self.entrar()
        respuesta = self.client.post(self.url_de(proxima), follow=True)
        self.assertRedirects(respuesta, self.url_lista)
        self.assertContains(
            respuesta, 'El periodo de cancelación ha concluido.'
        )
        self.assertEqual(self.estado_de(proxima), Reservacion.Estado.VIGENTE)

    def test_post_a_reservacion_cancelada_muestra_mensaje(self):
        cancelada_el = timezone.now() - timedelta(hours=1)
        Reservacion.objects.filter(pk=self.reservacion.pk).update(
            estado=Reservacion.Estado.CANCELADA,
            fecha_cancelacion=cancelada_el,
        )
        self.entrar()
        respuesta = self.client.post(self.url, follow=True)
        self.assertContains(respuesta, 'La reservación ya fue cancelada.')
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.fecha_cancelacion, cancelada_el)

    def test_post_sin_token_csrf_es_rechazado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.login(username='ana', password='Reserva2026')
        respuesta = cliente.post(self.url)
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(
            self.estado_de(self.reservacion), Reservacion.Estado.VIGENTE
        )
