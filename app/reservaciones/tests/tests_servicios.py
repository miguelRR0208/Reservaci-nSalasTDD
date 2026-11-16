from datetime import time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from reservaciones.models import Reservacion
from reservaciones.servicios import crear_reservacion
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
