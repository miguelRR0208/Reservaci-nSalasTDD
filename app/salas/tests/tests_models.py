from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from salas.models import Sala


class TestModeloSala(TestCase):

    def crear_sala(self, **datos):
        valores = {
            'nombre': 'Sala de prueba',
            'ubicacion': 'Edificio de pruebas',
            'capacidad': 5,
        }
        valores.update(datos)
        return Sala(**valores)

    def test_guarda_sala_con_datos_validos(self):
        sala = self.crear_sala()
        sala.full_clean()
        sala.save()
        guardada = Sala.objects.get(nombre='Sala de prueba')
        self.assertEqual(guardada.ubicacion, 'Edificio de pruebas')
        self.assertEqual(guardada.capacidad, 5)

    def test_sala_es_activa_por_defecto(self):
        sala = self.crear_sala()
        sala.save()
        self.assertTrue(sala.activa)

    def test_str_regresa_nombre(self):
        sala = self.crear_sala(nombre='Sala Z')
        self.assertEqual(str(sala), 'Sala Z')

    def test_nombre_es_requerido(self):
        sala = self.crear_sala(nombre='')
        with self.assertRaises(ValidationError) as error:
            sala.full_clean()
        self.assertIn('nombre', error.exception.message_dict)

    def test_ubicacion_es_requerida(self):
        sala = self.crear_sala(ubicacion='')
        with self.assertRaises(ValidationError) as error:
            sala.full_clean()
        self.assertIn('ubicacion', error.exception.message_dict)

    def test_nombre_no_excede_100_caracteres(self):
        sala = self.crear_sala(nombre='x' * 101)
        with self.assertRaises(ValidationError) as error:
            sala.full_clean()
        self.assertIn('nombre', error.exception.message_dict)

    def test_capacidad_cero_no_es_valida(self):
        sala = self.crear_sala(capacidad=0)
        with self.assertRaises(ValidationError) as error:
            sala.full_clean()
        self.assertIn('capacidad', error.exception.message_dict)

    def test_capacidad_negativa_no_es_valida(self):
        sala = self.crear_sala(capacidad=-3)
        with self.assertRaises(ValidationError) as error:
            sala.full_clean()
        self.assertIn('capacidad', error.exception.message_dict)

    def test_capacidad_uno_es_valida(self):
        sala = self.crear_sala(capacidad=1)
        sala.full_clean()

    def test_nombre_no_se_puede_repetir(self):
        self.crear_sala(nombre='Repetida').save()
        with self.assertRaises(IntegrityError):
            self.crear_sala(nombre='Repetida').save()


class TestSalasActivas(TestCase):

    def test_activas_solo_regresa_salas_activas(self):
        Sala.objects.create(
            nombre='Sala apagada', ubicacion='Sótano',
            capacidad=3, activa=False,
        )
        activas = Sala.objects.activas()
        self.assertTrue(all(sala.activa for sala in activas))
        self.assertFalse(activas.filter(nombre='Sala apagada').exists())

    def test_activas_incluye_salas_iniciales_activas(self):
        nombres = list(
            Sala.objects.activas().values_list('nombre', flat=True)
        )
        self.assertEqual(nombres, ['Sala A', 'Sala B', 'Sala C'])
