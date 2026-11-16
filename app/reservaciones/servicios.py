from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from reservaciones import reglas
from reservaciones.disponibilidad import sala_disponible
from reservaciones.models import Reservacion
from salas.models import Sala


def validar_horario(fecha, hora_inicio, hora_fin):
    reglas.validar_fecha_no_pasada(fecha)
    reglas.validar_hora_inicio(hora_inicio)
    reglas.validar_hora_fin(hora_inicio, hora_fin)
    reglas.validar_duracion(hora_inicio, hora_fin)


def crear_reservacion(usuario, sala, fecha, hora_inicio, hora_fin,
                      asistentes, proposito):
    validar_horario(fecha, hora_inicio, hora_fin)
    with transaction.atomic():
        # Se vuelve a leer la sala dentro de la transacción para usar
        # sus datos actuales y bloquearla mientras se revisa el horario.
        sala = Sala.objects.select_for_update().get(pk=sala.pk)
        reglas.validar_sala_activa(sala)
        reglas.validar_capacidad(sala, asistentes)
        if not sala_disponible(sala, fecha, hora_inicio, hora_fin):
            raise ValidationError(
                'La sala no está disponible en el horario solicitado.',
                code='horario_ocupado',
            )
        return Reservacion.objects.create(
            usuario=usuario,
            sala=sala,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            asistentes=asistentes,
            proposito=proposito,
        )


def cancelar_reservacion(usuario, reservacion, ahora=None):
    ahora = ahora or timezone.now()
    with transaction.atomic():
        # Se vuelve a leer para revisar el estado guardado y no el que
        # tenía el objeto cuando se cargó.
        reservacion = Reservacion.objects.select_for_update().get(
            pk=reservacion.pk
        )
        reglas.validar_propietario(reservacion, usuario)
        reglas.validar_vigente(reservacion)
        reglas.validar_anticipacion_cancelacion(reservacion, ahora)
        reservacion.estado = Reservacion.Estado.CANCELADA
        reservacion.fecha_cancelacion = ahora
        reservacion.save(update_fields=['estado', 'fecha_cancelacion'])
    return reservacion
