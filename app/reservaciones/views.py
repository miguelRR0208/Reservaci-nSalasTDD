from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reservaciones import reglas
from reservaciones.forms import ReservacionForm
from reservaciones.servicios import cancelar_reservacion, crear_reservacion


@login_required
def lista_reservaciones(request):
    ahora = timezone.now()
    reservaciones = list(request.user.reservaciones.select_related('sala'))
    for reservacion in reservaciones:
        reservacion.cancelable = reglas.se_puede_cancelar(reservacion, ahora)
    return render(
        request,
        'lista_reservaciones.html',
        {'reservaciones': reservaciones},
    )


@login_required
def nueva_reservacion(request):
    formulario = ReservacionForm(request.POST or None)
    if request.method == 'POST' and formulario.is_valid():
        try:
            crear_reservacion(usuario=request.user, **formulario.cleaned_data)
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            messages.success(
                request, 'La reservación se registró correctamente.'
            )
            return redirect('reservaciones:lista')
    return render(
        request, 'nueva_reservacion.html', {'formulario': formulario}
    )


@login_required
def cancelar(request, pk):
    # Solo se buscan las reservaciones del usuario; si la reservación es
    # de alguien más se responde como si no existiera.
    reservacion = get_object_or_404(request.user.reservaciones, pk=pk)
    if request.method != 'POST':
        return render(
            request, 'cancelar_reservacion.html', {'reservacion': reservacion}
        )
    try:
        cancelar_reservacion(request.user, reservacion)
    except ValidationError as error:
        for mensaje in error.messages:
            messages.error(request, mensaje)
    else:
        messages.success(request, 'La reservación se canceló correctamente.')
    return redirect('reservaciones:lista')
