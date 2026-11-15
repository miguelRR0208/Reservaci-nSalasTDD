from datetime import time, timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils import timezone

from reservaciones import reglas
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
