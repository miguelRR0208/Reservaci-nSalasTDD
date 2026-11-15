from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from salas.models import Sala


class Reservacion(models.Model):

    class Estado(models.TextChoices):
        VIGENTE = 'VIGENTE', 'Vigente'
        CANCELADA = 'CANCELADA', 'Cancelada'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservaciones',
    )
    sala = models.ForeignKey(
        Sala, on_delete=models.PROTECT, related_name='reservaciones'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    asistentes = models.IntegerField(validators=[MinValueValidator(1)])
    proposito = models.CharField('propósito', max_length=200)
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.VIGENTE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'reservación'
        verbose_name_plural = 'reservaciones'
        ordering = ['-fecha', '-hora_inicio']
        indexes = [models.Index(fields=['sala', 'fecha', 'estado'])]

    def __str__(self):
        return (
            f'{self.sala} {self.fecha:%Y-%m-%d} '
            f'{self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}'
        )
