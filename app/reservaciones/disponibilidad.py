from reservaciones.models import Reservacion


def reservaciones_que_se_traslapan(sala, fecha, hora_inicio, hora_fin):
    # Dos horarios chocan si uno empieza antes de que el otro termine
    # y termina después de que el otro empieza. Las canceladas no cuentan.
    return Reservacion.objects.filter(
        sala=sala,
        fecha=fecha,
        estado=Reservacion.Estado.VIGENTE,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    )


def sala_disponible(sala, fecha, hora_inicio, hora_fin):
    return not reservaciones_que_se_traslapan(
        sala, fecha, hora_inicio, hora_fin
    ).exists()
