from django.core.exceptions import ValidationError
from django.db import transaction

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
