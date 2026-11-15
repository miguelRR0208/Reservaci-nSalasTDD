from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from reservaciones.disponibilidad import (
    reservaciones_que_se_traslapan,
    sala_disponible,
)
from reservaciones.models import Reservacion
from salas.models import Sala


class TestDisponibilidad(TestCase):
    """La reservación existente siempre es de 10:00 a 11:00 en Sala B."""

    def setUp(self):
        self.usuario = User.objects.create_user('ana', password='clave12345')
        self.sala = Sala.objects.get(nombre='Sala B')
        self.fecha = date.today() + timedelta(days=1)
        self.existente = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=self.fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito='Reservación que ya existe',
        )

    def disponible(self, inicio, fin, sala=None, fecha=None):
        return sala_disponible(
            sala or self.sala, fecha or self.fecha, inicio, fin
        )

    def test_detecta_traslape_parcial_al_final(self):
        self.assertFalse(self.disponible(time(10, 30), time(11, 30)))

    def test_detecta_traslape_parcial_al_inicio(self):
        self.assertFalse(self.disponible(time(9, 30), time(10, 30)))

    def test_detecta_horario_contenido_en_el_existente(self):
        self.assertFalse(self.disponible(time(10, 15), time(10, 45)))

    def test_detecta_horario_que_contiene_al_existente(self):
        self.assertFalse(self.disponible(time(9, 0), time(12, 0)))

    def test_detecta_horario_identico(self):
        self.assertFalse(self.disponible(time(10, 0), time(11, 0)))

    def test_permite_horario_adyacente_posterior(self):
        self.assertTrue(self.disponible(time(11, 0), time(12, 0)))

    def test_permite_horario_adyacente_anterior(self):
        self.assertTrue(self.disponible(time(9, 0), time(10, 0)))

    def test_permite_mismo_horario_en_otra_sala(self):
        otra_sala = Sala.objects.get(nombre='Sala C')
        self.assertTrue(
            self.disponible(time(10, 0), time(11, 0), sala=otra_sala)
        )

    def test_permite_mismo_horario_en_otra_fecha(self):
        otra_fecha = self.fecha + timedelta(days=1)
        self.assertTrue(
            self.disponible(time(10, 0), time(11, 0), fecha=otra_fecha)
        )

    def test_ignora_reservaciones_canceladas(self):
        self.existente.estado = Reservacion.Estado.CANCELADA
        self.existente.save()
        self.assertTrue(self.disponible(time(10, 0), time(11, 0)))

    def test_regresa_las_reservaciones_que_chocan(self):
        traslapadas = reservaciones_que_se_traslapan(
            self.sala, self.fecha, time(10, 30), time(11, 30)
        )
        self.assertEqual(list(traslapadas), [self.existente])
