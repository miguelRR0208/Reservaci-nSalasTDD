from datetime import datetime, time, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from reservaciones.models import Reservacion

PRIMERA_HORA_INICIO = time(8, 0)
ULTIMA_HORA_INICIO = time(19, 0)
HORA_CIERRE = time(20, 0)
DURACION_MINIMA = 30
DURACION_MAXIMA = 120
ANTICIPACION_CANCELACION = timedelta(minutes=60)


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


def inicio_de(reservacion):
    return timezone.make_aware(
        datetime.combine(reservacion.fecha, reservacion.hora_inicio)
    )


def validar_propietario(reservacion, usuario):
    if reservacion.usuario_id != usuario.pk:
        raise PermissionDenied('La reservación pertenece a otro usuario.')


def validar_vigente(reservacion):
    if reservacion.estado != Reservacion.Estado.VIGENTE:
        raise ValidationError(
            'La reservación ya fue cancelada.', code='ya_cancelada'
        )


def validar_anticipacion_cancelacion(reservacion, ahora):
    if inicio_de(reservacion) - ahora <= ANTICIPACION_CANCELACION:
        raise ValidationError(
            'El periodo de cancelación ha concluido.',
            code='periodo_concluido',
        )


def se_puede_cancelar(reservacion, ahora):
    try:
        validar_vigente(reservacion)
        validar_anticipacion_cancelacion(reservacion, ahora)
    except ValidationError:
        return False
    return True
