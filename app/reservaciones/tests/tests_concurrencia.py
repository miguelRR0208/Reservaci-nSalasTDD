import threading
import time as reloj
from datetime import time, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone

from reservaciones import servicios
from reservaciones.models import Reservacion
from salas.models import Sala

disponibilidad_original = servicios.sala_disponible


def disponibilidad_lenta(*args):
    # Deja pasar un momento entre revisar y guardar para que la
    # otra solicitud tenga oportunidad de colarse si no hay bloqueo.
    resultado = disponibilidad_original(*args)
    reloj.sleep(0.3)
    return resultado


class TestReservacionesConcurrentes(TransactionTestCase):
    """IT-01: dos solicitudes al mismo tiempo para la misma sala y horario.

    Se usa TransactionTestCase porque cada hilo necesita su propia
    conexión y ver lo que el otro ya guardó.
    """

    serialized_rollback = True

    def setUp(self):
        self.sala = Sala.objects.get(nombre='Sala B')
        self.usuarios = [
            User.objects.create_user(nombre, password='clave12345')
            for nombre in ('ana', 'beto')
        ]
        self.fecha = timezone.localdate() + timedelta(days=1)

    def reservar(self, usuario, barrera, resultados):
        barrera.wait()
        try:
            servicios.crear_reservacion(
                usuario=usuario,
                sala=self.sala,
                fecha=self.fecha,
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=2,
                proposito='Solicitud que compite por la sala',
            )
            resultados.append('registrada')
        except ValidationError as error:
            resultados.append(error.messages[0])
        finally:
            connection.close()

    def enviar_al_mismo_tiempo(self):
        barrera = threading.Barrier(len(self.usuarios))
        resultados = []
        hilos = [
            threading.Thread(
                target=self.reservar, args=(usuario, barrera, resultados)
            )
            for usuario in self.usuarios
        ]
        with mock.patch.object(
            servicios, 'sala_disponible', side_effect=disponibilidad_lenta
        ):
            for hilo in hilos:
                hilo.start()
            for hilo in hilos:
                hilo.join()
        return resultados

    def test_solo_una_reservacion_queda_vigente(self):
        self.enviar_al_mismo_tiempo()
        vigentes = Reservacion.objects.filter(
            sala=self.sala, fecha=self.fecha,
            estado=Reservacion.Estado.VIGENTE,
        )
        self.assertEqual(vigentes.count(), 1)

    def test_la_segunda_solicitud_recibe_respuesta_controlada(self):
        resultados = self.enviar_al_mismo_tiempo()
        self.assertCountEqual(
            resultados,
            [
                'registrada',
                'La sala no está disponible en el horario solicitado.',
            ],
        )
