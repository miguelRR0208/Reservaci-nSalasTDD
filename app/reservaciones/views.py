from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from reservaciones.forms import ReservacionForm
from reservaciones.servicios import crear_reservacion


@login_required
def lista_reservaciones(request):
    reservaciones = request.user.reservaciones.select_related('sala')
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
