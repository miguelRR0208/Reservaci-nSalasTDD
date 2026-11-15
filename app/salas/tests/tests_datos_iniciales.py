from django.test import TestCase

from salas.models import Sala


class TestDatosInicialesSalas(TestCase):
    """Las salas del examen deben existir solo con correr las migraciones."""

    SALAS_ESPERADAS = [
        ('Sala A', 'Biblioteca, planta baja', 4, True),
        ('Sala B', 'Biblioteca, planta baja', 8, True),
        ('Sala C', 'Biblioteca, planta alta', 12, True),
        ('Sala de mantenimiento', 'Biblioteca, planta alta', 6, False),
    ]

    def test_existen_las_cuatro_salas_iniciales(self):
        nombres = [sala[0] for sala in self.SALAS_ESPERADAS]
        self.assertEqual(Sala.objects.filter(nombre__in=nombres).count(), 4)

    def test_salas_iniciales_tienen_datos_correctos(self):
        for nombre, ubicacion, capacidad, activa in self.SALAS_ESPERADAS:
            with self.subTest(sala=nombre):
                sala = Sala.objects.get(nombre=nombre)
                self.assertEqual(sala.ubicacion, ubicacion)
                self.assertEqual(sala.capacidad, capacidad)
                self.assertEqual(sala.activa, activa)
