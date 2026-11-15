from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from reservaciones.forms import ReservacionForm
from salas.models import Sala


class TestFormularioReservacion(TestCase):

    def setUp(self):
        self.sala = Sala.objects.get(nombre='Sala A')
        self.manana = timezone.localdate() + timedelta(days=1)

    def formulario(self, **cambios):
        datos = {
            'sala': self.sala.pk,
            'fecha': self.manana.strftime('%Y-%m-%d'),
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'asistentes': '3',
            'proposito': 'Estudiar para el examen final',
        }
        datos.update(cambios)
        return ReservacionForm(data=datos)

    def assertCampoInvalido(self, formulario, campo, mensaje=None):
        self.assertFalse(formulario.is_valid())
        self.assertIn(campo, formulario.errors)
        if mensaje:
            self.assertIn(mensaje, formulario.errors[campo])

    def test_acepta_datos_validos(self):
        formulario = self.formulario()
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_todos_los_campos_son_obligatorios(self):
        formulario = ReservacionForm(data={})
        self.assertFalse(formulario.is_valid())
        self.assertEqual(
            set(formulario.errors),
            {'sala', 'fecha', 'hora_inicio', 'hora_fin',
             'asistentes', 'proposito'},
        )

    # Propósito (UT-02)

    def test_rechaza_proposito_menor_a_10_caracteres(self):
        self.assertCampoInvalido(
            self.formulario(proposito='Estudiar'), 'proposito',
            'El propósito debe tener entre 10 y 200 caracteres.',
        )

    def test_rechaza_proposito_corto_rodeado_de_espacios(self):
        self.assertCampoInvalido(
            self.formulario(proposito='     Estudio     '), 'proposito'
        )

    def test_acepta_proposito_de_10_caracteres(self):
        self.assertTrue(self.formulario(proposito='a' * 10).is_valid())

    def test_acepta_proposito_de_200_caracteres(self):
        self.assertTrue(self.formulario(proposito='a' * 200).is_valid())

    def test_rechaza_proposito_de_201_caracteres(self):
        self.assertCampoInvalido(
            self.formulario(proposito='a' * 201), 'proposito',
            'El propósito debe tener entre 10 y 200 caracteres.',
        )

    def test_quita_espacios_al_inicio_y_final_del_proposito(self):
        formulario = self.formulario(proposito='   Repaso de cálculo   ')
        self.assertTrue(formulario.is_valid())
        self.assertEqual(
            formulario.cleaned_data['proposito'], 'Repaso de cálculo'
        )

    # Asistentes (UT-03 y UT-04)

    def test_rechaza_cero_asistentes(self):
        self.assertCampoInvalido(
            self.formulario(asistentes='0'), 'asistentes',
            'Debe haber al menos 1 asistente.',
        )

    def test_rechaza_asistentes_negativos(self):
        self.assertCampoInvalido(
            self.formulario(asistentes='-2'), 'asistentes'
        )

    def test_rechaza_asistentes_con_texto(self):
        self.assertCampoInvalido(
            self.formulario(asistentes='tres'), 'asistentes',
            'Escribe un número entero de asistentes.',
        )

    def test_rechaza_asistentes_con_decimales(self):
        self.assertCampoInvalido(
            self.formulario(asistentes='2.5'), 'asistentes'
        )

    def test_acepta_asistentes_igual_a_capacidad(self):
        self.assertTrue(self.formulario(asistentes='4').is_valid())

    def test_rechaza_asistentes_mayor_a_capacidad(self):
        self.assertCampoInvalido(
            self.formulario(asistentes='5'), 'asistentes',
            'El número de asistentes supera la capacidad de la sala.',
        )

    # Fecha (UT-05)

    def test_rechaza_fecha_pasada(self):
        ayer = timezone.localdate() - timedelta(days=1)
        self.assertCampoInvalido(
            self.formulario(fecha=ayer.strftime('%Y-%m-%d')), 'fecha',
            'La fecha no puede ser anterior al día de hoy.',
        )

    def test_acepta_fecha_de_hoy(self):
        hoy = timezone.localdate().strftime('%Y-%m-%d')
        self.assertTrue(self.formulario(fecha=hoy).is_valid())

    def test_rechaza_fecha_con_formato_incorrecto(self):
        self.assertCampoInvalido(
            self.formulario(fecha='mañana'), 'fecha'
        )

    # Horario (UT-06 y horario institucional)

    def test_rechaza_hora_fin_igual_a_inicio(self):
        self.assertCampoInvalido(
            self.formulario(hora_inicio='10:00', hora_fin='10:00'),
            'hora_fin',
            'La hora de fin debe ser posterior a la hora de inicio.',
        )

    def test_rechaza_hora_fin_antes_de_inicio(self):
        self.assertCampoInvalido(
            self.formulario(hora_inicio='11:00', hora_fin='10:00'),
            'hora_fin',
            'La hora de fin debe ser posterior a la hora de inicio.',
        )

    def test_rechaza_inicio_antes_de_las_08_00(self):
        self.assertCampoInvalido(
            self.formulario(hora_inicio='07:30', hora_fin='08:30'),
            'hora_inicio',
            'La hora de inicio debe estar entre las 08:00 y las 19:00.',
        )

    def test_rechaza_inicio_despues_de_las_19_00(self):
        self.assertCampoInvalido(
            self.formulario(hora_inicio='19:30', hora_fin='20:00'),
            'hora_inicio',
        )

    def test_rechaza_fin_despues_de_las_20_00(self):
        self.assertCampoInvalido(
            self.formulario(hora_inicio='19:00', hora_fin='20:30'),
            'hora_fin',
            'La hora de fin no puede ser posterior a las 20:00.',
        )

    def test_acepta_horario_en_los_limites(self):
        self.assertTrue(
            self.formulario(hora_inicio='08:00', hora_fin='09:00').is_valid()
        )
        self.assertTrue(
            self.formulario(hora_inicio='19:00', hora_fin='20:00').is_valid()
        )

    def test_rechaza_hora_con_formato_incorrecto(self):
        self.assertCampoInvalido(
            self.formulario(hora_inicio='diez'), 'hora_inicio'
        )

    # Sala

    def test_solo_ofrece_salas_activas(self):
        opciones = list(
            self.formulario().fields['sala'].queryset.values_list(
                'nombre', flat=True
            )
        )
        self.assertEqual(opciones, ['Sala A', 'Sala B', 'Sala C'])

    def test_rechaza_sala_inactiva(self):
        inactiva = Sala.objects.get(nombre='Sala de mantenimiento')
        self.assertCampoInvalido(
            self.formulario(sala=inactiva.pk), 'sala',
            'La sala no se encuentra disponible para reservación.',
        )

    def test_rechaza_sala_inexistente(self):
        self.assertCampoInvalido(
            self.formulario(sala=9999), 'sala',
            'La sala no se encuentra disponible para reservación.',
        )
