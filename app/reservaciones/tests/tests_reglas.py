from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase
from django.utils import timezone

from reservaciones import reglas
from reservaciones.models import Reservacion
from salas.models import Sala


class TestReglaFecha(SimpleTestCase):

    def test_acepta_fecha_de_hoy(self):
        reglas.validar_fecha_no_pasada(timezone.localdate())

    def test_acepta_fecha_futura(self):
        reglas.validar_fecha_no_pasada(
            timezone.localdate() + timedelta(days=30)
        )

    def test_rechaza_fecha_de_ayer(self):
        ayer = timezone.localdate() - timedelta(days=1)
        with self.assertRaisesMessage(
            ValidationError, 'La fecha no puede ser anterior al día de hoy.'
        ):
            reglas.validar_fecha_no_pasada(ayer)


class TestReglaHoraInicio(SimpleTestCase):

    def test_acepta_limites_08_00_y_19_00(self):
        reglas.validar_hora_inicio(time(8, 0))
        reglas.validar_hora_inicio(time(19, 0))

    def test_rechaza_antes_de_las_08_00(self):
        with self.assertRaisesMessage(
            ValidationError,
            'La hora de inicio debe estar entre las 08:00 y las 19:00.',
        ):
            reglas.validar_hora_inicio(time(7, 59))

    def test_rechaza_despues_de_las_19_00(self):
        with self.assertRaises(ValidationError):
            reglas.validar_hora_inicio(time(19, 1))


class TestReglaHoraFin(SimpleTestCase):

    def test_acepta_fin_posterior_al_inicio(self):
        reglas.validar_hora_fin(time(10, 0), time(10, 30))

    def test_acepta_fin_a_las_20_00(self):
        reglas.validar_hora_fin(time(19, 0), time(20, 0))

    def test_rechaza_fin_igual_al_inicio(self):
        with self.assertRaisesMessage(
            ValidationError,
            'La hora de fin debe ser posterior a la hora de inicio.',
        ):
            reglas.validar_hora_fin(time(10, 0), time(10, 0))

    def test_rechaza_fin_anterior_al_inicio(self):
        with self.assertRaises(ValidationError):
            reglas.validar_hora_fin(time(11, 0), time(10, 0))

    def test_rechaza_fin_despues_de_las_20_00(self):
        with self.assertRaisesMessage(
            ValidationError,
            'La hora de fin no puede ser posterior a las 20:00.',
        ):
            reglas.validar_hora_fin(time(19, 0), time(20, 1))


class TestReglaDuracion(SimpleTestCase):

    def test_acepta_30_minutos_exactos(self):
        reglas.validar_duracion(time(10, 0), time(10, 30))

    def test_acepta_2_horas_exactas(self):
        reglas.validar_duracion(time(10, 0), time(12, 0))

    def test_rechaza_menos_de_30_minutos(self):
        with self.assertRaisesMessage(
            ValidationError,
            'La reservación debe durar entre 30 minutos y 2 horas.',
        ):
            reglas.validar_duracion(time(10, 0), time(10, 29))

    def test_rechaza_mas_de_2_horas(self):
        with self.assertRaises(ValidationError):
            reglas.validar_duracion(time(10, 0), time(12, 1))


class TestReglaCapacidad(SimpleTestCase):

    def setUp(self):
        self.sala = Sala(nombre='Sala A', capacidad=4)

    def test_acepta_asistentes_igual_a_capacidad(self):
        reglas.validar_capacidad(self.sala, 4)

    def test_rechaza_asistentes_mayor_a_capacidad(self):
        with self.assertRaisesMessage(
            ValidationError,
            'El número de asistentes supera la capacidad de la sala.',
        ):
            reglas.validar_capacidad(self.sala, 5)


class TestReglaSalaActiva(SimpleTestCase):

    def test_acepta_sala_activa(self):
        reglas.validar_sala_activa(Sala(nombre='Sala A', activa=True))

    def test_rechaza_sala_inactiva(self):
        with self.assertRaisesMessage(
            ValidationError,
            'La sala no se encuentra disponible para reservación.',
        ):
            reglas.validar_sala_activa(Sala(nombre='Sala X', activa=False))


class TestReglasCancelacion(SimpleTestCase):

    def setUp(self):
        self.reservacion = Reservacion(
            usuario_id=1,
            fecha=date(2030, 5, 10),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            estado=Reservacion.Estado.VIGENTE,
        )

    def momento(self, hora, minuto):
        return timezone.make_aware(datetime(2030, 5, 10, hora, minuto))

    def test_inicio_junta_fecha_y_hora_en_la_zona_local(self):
        self.assertEqual(
            reglas.inicio_de(self.reservacion), self.momento(10, 0)
        )

    def test_acepta_al_propietario(self):
        reglas.validar_propietario(self.reservacion, User(pk=1))

    def test_rechaza_a_otro_usuario(self):
        with self.assertRaises(PermissionDenied):
            reglas.validar_propietario(self.reservacion, User(pk=2))

    def test_acepta_reservacion_vigente(self):
        reglas.validar_vigente(self.reservacion)

    def test_rechaza_reservacion_cancelada(self):
        self.reservacion.estado = Reservacion.Estado.CANCELADA
        with self.assertRaisesMessage(
            ValidationError, 'La reservación ya fue cancelada.'
        ):
            reglas.validar_vigente(self.reservacion)

    def test_acepta_cancelar_con_mas_de_60_minutos(self):
        reglas.validar_anticipacion_cancelacion(
            self.reservacion, self.momento(8, 59)
        )

    def assertPeriodoConcluido(self, ahora):
        with self.assertRaisesMessage(
            ValidationError, 'El periodo de cancelación ha concluido.'
        ):
            reglas.validar_anticipacion_cancelacion(self.reservacion, ahora)

    def test_rechaza_cancelar_con_60_minutos_exactos(self):
        self.assertPeriodoConcluido(self.momento(9, 0))

    def test_rechaza_cancelar_con_menos_de_60_minutos(self):
        self.assertPeriodoConcluido(self.momento(9, 30))

    def test_rechaza_cancelar_una_reservacion_ya_iniciada(self):
        self.assertPeriodoConcluido(self.momento(10, 30))

    def test_se_puede_cancelar_si_esta_vigente_y_a_tiempo(self):
        self.assertTrue(
            reglas.se_puede_cancelar(self.reservacion, self.momento(8, 0))
        )

    def test_no_se_puede_cancelar_si_ya_esta_cancelada(self):
        self.reservacion.estado = Reservacion.Estado.CANCELADA
        self.assertFalse(
            reglas.se_puede_cancelar(self.reservacion, self.momento(8, 0))
        )

    def test_no_se_puede_cancelar_si_ya_no_hay_tiempo(self):
        self.assertFalse(
            reglas.se_puede_cancelar(self.reservacion, self.momento(9, 0))
        )
