from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from reservaciones.models import Reservacion
from reservaciones.servicios import cancelar_reservacion, crear_reservacion
from salas.models import Sala


class TestCrearReservacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user('ana', password='clave12345')
        self.sala = Sala.objects.get(nombre='Sala A')
        self.manana = timezone.localdate() + timedelta(days=1)

    def crear(self, **cambios):
        datos = {
            'usuario': self.usuario,
            'sala': self.sala,
            'fecha': self.manana,
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudiar para el examen final',
        }
        datos.update(cambios)
        return crear_reservacion(**datos)

    def assertRechaza(self, mensaje, **cambios):
        antes = Reservacion.objects.count()
        with self.assertRaisesMessage(ValidationError, mensaje):
            self.crear(**cambios)
        self.assertEqual(Reservacion.objects.count(), antes)

    # UT-01

    def test_registra_reservacion_valida_como_vigente(self):
        reservacion = self.crear()
        guardada = Reservacion.objects.get(pk=reservacion.pk)
        self.assertEqual(guardada.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(guardada.usuario, self.usuario)
        self.assertEqual(guardada.sala, self.sala)
        self.assertEqual(guardada.asistentes, 3)

    # UT-04

    def test_rechaza_asistentes_mayor_a_capacidad(self):
        self.assertRechaza(
            'El número de asistentes supera la capacidad de la sala.',
            asistentes=5,
        )

    # UT-07

    def test_rechaza_duracion_menor_a_30_minutos(self):
        self.assertRechaza(
            'La reservación debe durar entre 30 minutos y 2 horas.',
            hora_inicio=time(10, 0), hora_fin=time(10, 20),
        )

    def test_rechaza_duracion_mayor_a_2_horas(self):
        self.assertRechaza(
            'La reservación debe durar entre 30 minutos y 2 horas.',
            hora_inicio=time(10, 0), hora_fin=time(12, 30),
        )

    def test_acepta_duraciones_limite(self):
        self.crear(hora_inicio=time(8, 0), hora_fin=time(8, 30))
        self.crear(hora_inicio=time(9, 0), hora_fin=time(11, 0))
        self.assertEqual(Reservacion.objects.count(), 2)

    # UT-08

    def test_rechaza_traslape_parcial(self):
        self.crear()
        self.assertRechaza(
            'La sala no está disponible en el horario solicitado.',
            hora_inicio=time(10, 30), hora_fin=time(11, 30),
        )

    def test_rechaza_horario_contenido(self):
        self.crear(hora_inicio=time(10, 0), hora_fin=time(12, 0))
        self.assertRechaza(
            'La sala no está disponible en el horario solicitado.',
            hora_inicio=time(10, 30), hora_fin=time(11, 30),
        )

    def test_rechaza_traslape_total(self):
        self.crear()
        self.assertRechaza(
            'La sala no está disponible en el horario solicitado.'
        )

    # UT-09

    def test_permite_horarios_adyacentes(self):
        primera = self.crear(hora_inicio=time(10, 0), hora_fin=time(11, 0))
        segunda = self.crear(hora_inicio=time(11, 0), hora_fin=time(12, 0))
        for reservacion in (primera, segunda):
            reservacion.refresh_from_db()
            self.assertEqual(reservacion.estado, Reservacion.Estado.VIGENTE)

    # UT-10

    def test_ignora_reservaciones_canceladas(self):
        cancelada = self.crear()
        cancelada.estado = Reservacion.Estado.CANCELADA
        cancelada.save()
        nueva = self.crear()
        self.assertEqual(nueva.estado, Reservacion.Estado.VIGENTE)

    # Reglas que también revisa el formulario, por si alguien
    # llama al servicio sin pasar por él.

    def test_rechaza_sala_inactiva(self):
        self.assertRechaza(
            'La sala no se encuentra disponible para reservación.',
            sala=Sala.objects.get(nombre='Sala de mantenimiento'),
        )

    def test_revisa_sala_actualizada_en_base_de_datos(self):
        Sala.objects.filter(pk=self.sala.pk).update(activa=False)
        self.assertRechaza(
            'La sala no se encuentra disponible para reservación.'
        )

    def test_rechaza_fecha_pasada(self):
        self.assertRechaza(
            'La fecha no puede ser anterior al día de hoy.',
            fecha=timezone.localdate() - timedelta(days=1),
        )

    def test_rechaza_inicio_fuera_de_horario(self):
        self.assertRechaza(
            'La hora de inicio debe estar entre las 08:00 y las 19:00.',
            hora_inicio=time(7, 0), hora_fin=time(8, 0),
        )

    def test_rechaza_fin_no_posterior_al_inicio(self):
        self.assertRechaza(
            'La hora de fin debe ser posterior a la hora de inicio.',
            hora_inicio=time(11, 0), hora_fin=time(10, 0),
        )


class TestCancelarReservacion(TestCase):

    def setUp(self):
        self.ana = User.objects.create_user('ana', password='clave12345')
        self.beto = User.objects.create_user('beto', password='clave12345')
        self.reservacion = Reservacion.objects.create(
            usuario=self.ana,
            sala=Sala.objects.get(nombre='Sala A'),
            fecha=date(2030, 5, 10),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito='Repaso para el examen final',
        )

    def momento(self, hora, minuto):
        return timezone.make_aware(datetime(2030, 5, 10, hora, minuto))

    def cancelar(self, usuario=None, ahora=None):
        return cancelar_reservacion(
            usuario or self.ana,
            self.reservacion,
            ahora or self.momento(8, 0),
        )

    def assertSigueVigente(self):
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.Estado.VIGENTE)
        self.assertIsNone(self.reservacion.fecha_cancelacion)

    def assertPeriodoConcluido(self, ahora):
        with self.assertRaisesMessage(
            ValidationError, 'El periodo de cancelación ha concluido.'
        ):
            self.cancelar(ahora=ahora)
        self.assertSigueVigente()

    # UT-13

    def test_cancela_reservacion_propia_vigente_y_a_tiempo(self):
        self.cancelar()
        self.reservacion.refresh_from_db()
        self.assertEqual(
            self.reservacion.estado, Reservacion.Estado.CANCELADA
        )
        self.assertEqual(
            self.reservacion.fecha_cancelacion, self.momento(8, 0)
        )

    def test_usa_la_hora_actual_si_no_se_indica(self):
        antes = timezone.now()
        cancelar_reservacion(self.ana, self.reservacion)
        self.reservacion.refresh_from_db()
        self.assertTrue(
            antes <= self.reservacion.fecha_cancelacion <= timezone.now()
        )

    def test_no_elimina_la_reservacion(self):
        self.cancelar()
        self.assertTrue(
            Reservacion.objects.filter(pk=self.reservacion.pk).exists()
        )

    # UT-14

    def test_rechaza_cancelar_reservacion_ajena(self):
        with self.assertRaises(PermissionDenied):
            self.cancelar(usuario=self.beto)
        self.assertSigueVigente()

    # UT-15

    def test_rechaza_cancelar_con_60_minutos_exactos(self):
        self.assertPeriodoConcluido(self.momento(9, 0))

    # UT-16

    def test_rechaza_cancelar_con_menos_de_60_minutos(self):
        self.assertPeriodoConcluido(self.momento(9, 30))

    # UT-17

    def test_rechaza_segunda_cancelacion_sin_cambiar_la_fecha(self):
        self.cancelar(ahora=self.momento(8, 0))
        with self.assertRaisesMessage(
            ValidationError, 'La reservación ya fue cancelada.'
        ):
            self.cancelar(ahora=self.momento(8, 30))
        self.reservacion.refresh_from_db()
        self.assertEqual(
            self.reservacion.fecha_cancelacion, self.momento(8, 0)
        )

    def test_revisa_el_estado_guardado_en_base_de_datos(self):
        copia_vieja = Reservacion.objects.get(pk=self.reservacion.pk)
        self.cancelar()
        with self.assertRaisesMessage(
            ValidationError, 'La reservación ya fue cancelada.'
        ):
            cancelar_reservacion(self.ana, copia_vieja, self.momento(8, 30))


class TestCancelarYVolverAReservar(TestCase):

    # UT-20

    def test_horario_cancelado_se_puede_reservar_de_nuevo(self):
        usuario = User.objects.create_user('ana', password='clave12345')
        datos = {
            'usuario': usuario,
            'sala': Sala.objects.get(nombre='Sala A'),
            'fecha': timezone.localdate() + timedelta(days=1),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudiar para el examen final',
        }
        primera = crear_reservacion(**datos)
        cancelar_reservacion(usuario, primera)
        segunda = crear_reservacion(**datos)
        self.assertEqual(segunda.estado, Reservacion.Estado.VIGENTE)
        primera.refresh_from_db()
        self.assertEqual(primera.estado, Reservacion.Estado.CANCELADA)
