from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from reservaciones.models import Reservacion
from salas.models import Sala


class TestModeloReservacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user('ana', password='clave12345')
        self.sala = Sala.objects.get(nombre='Sala B')
        self.manana = date.today() + timedelta(days=1)

    def crear_reservacion(self, **datos):
        valores = {
            'usuario': self.usuario,
            'sala': self.sala,
            'fecha': self.manana,
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudiar para el examen final',
        }
        valores.update(datos)
        return Reservacion(**valores)

    def test_guarda_reservacion_con_estado_vigente(self):
        reservacion = self.crear_reservacion()
        reservacion.full_clean()
        reservacion.save()
        guardada = Reservacion.objects.get(pk=reservacion.pk)
        self.assertEqual(guardada.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(guardada.usuario, self.usuario)
        self.assertEqual(guardada.sala, self.sala)

    def test_registra_fecha_de_creacion_automaticamente(self):
        reservacion = self.crear_reservacion()
        reservacion.save()
        self.assertIsNotNone(reservacion.fecha_creacion)

    def test_fecha_de_cancelacion_vacia_al_crear(self):
        reservacion = self.crear_reservacion()
        reservacion.save()
        self.assertIsNone(reservacion.fecha_cancelacion)

    def test_solo_existen_estados_vigente_y_cancelada(self):
        self.assertEqual(
            set(Reservacion.Estado.values), {'VIGENTE', 'CANCELADA'}
        )

    def test_rechaza_estado_desconocido(self):
        reservacion = self.crear_reservacion(estado='BORRADA')
        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()
        self.assertIn('estado', error.exception.message_dict)

    def test_rechaza_cero_asistentes(self):
        reservacion = self.crear_reservacion(asistentes=0)
        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()
        self.assertIn('asistentes', error.exception.message_dict)

    def test_rechaza_proposito_mayor_a_200_caracteres(self):
        reservacion = self.crear_reservacion(proposito='x' * 201)
        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()
        self.assertIn('proposito', error.exception.message_dict)

    def test_str_muestra_sala_fecha_y_horario(self):
        reservacion = self.crear_reservacion()
        esperado = f'Sala B {self.manana:%Y-%m-%d} 10:00-11:00'
        self.assertEqual(str(reservacion), esperado)

    def test_no_permite_borrar_sala_con_reservaciones(self):
        self.crear_reservacion().save()
        with self.assertRaises(ProtectedError):
            self.sala.delete()

    def test_usuario_puede_consultar_sus_reservaciones(self):
        reservacion = self.crear_reservacion()
        reservacion.save()
        self.assertEqual(list(self.usuario.reservaciones.all()), [reservacion])
