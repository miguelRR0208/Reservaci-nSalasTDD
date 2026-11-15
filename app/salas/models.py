from django.core.validators import MinValueValidator
from django.db import models


class SalaQuerySet(models.QuerySet):

    def activas(self):
        return self.filter(activa=True)


class Sala(models.Model):
    objects = SalaQuerySet.as_manager()

    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField('ubicación', max_length=150)
    capacidad = models.IntegerField(validators=[MinValueValidator(1)])
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
