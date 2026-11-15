from datetime import time

from django.core.exceptions import ValidationError
from django.utils import timezone

PRIMERA_HORA_INICIO = time(8, 0)
ULTIMA_HORA_INICIO = time(19, 0)
HORA_CIERRE = time(20, 0)
DURACION_MINIMA = 30
DURACION_MAXIMA = 120


def validar_fecha_no_pasada(fecha):
    if fecha < timezone.localdate():
        raise ValidationError(
            'La fecha no puede ser anterior al día de hoy.',
            code='fecha_pasada',
        )


def validar_hora_inicio(hora_inicio):
    if not PRIMERA_HORA_INICIO <= hora_inicio <= ULTIMA_HORA_INICIO:
        raise ValidationError(
            'La hora de inicio debe estar entre las 08:00 y las 19:00.',
            code='hora_inicio_fuera_de_horario',
        )


def validar_hora_fin(hora_inicio, hora_fin):
    if hora_fin <= hora_inicio:
        raise ValidationError(
            'La hora de fin debe ser posterior a la hora de inicio.',
            code='hora_fin_no_posterior',
        )
    if hora_fin > HORA_CIERRE:
        raise ValidationError(
            'La hora de fin no puede ser posterior a las 20:00.',
            code='hora_fin_fuera_de_horario',
        )


def minutos_entre(hora_inicio, hora_fin):
    return (
        (hora_fin.hour * 60 + hora_fin.minute)
        - (hora_inicio.hour * 60 + hora_inicio.minute)
    )


def validar_duracion(hora_inicio, hora_fin):
    duracion = minutos_entre(hora_inicio, hora_fin)
    if not DURACION_MINIMA <= duracion <= DURACION_MAXIMA:
        raise ValidationError(
            'La reservación debe durar entre 30 minutos y 2 horas.',
            code='duracion_invalida',
        )


def validar_capacidad(sala, asistentes):
    if asistentes > sala.capacidad:
        raise ValidationError(
            'El número de asistentes supera la capacidad de la sala.',
            code='capacidad_excedida',
        )


def validar_sala_activa(sala):
    if not sala.activa:
        raise ValidationError(
            'La sala no se encuentra disponible para reservación.',
            code='sala_inactiva',
        )
