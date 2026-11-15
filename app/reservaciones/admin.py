from django.contrib import admin

from reservaciones.models import Reservacion


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display = (
        'sala', 'fecha', 'hora_inicio', 'hora_fin', 'usuario', 'estado'
    )
    list_filter = ('estado', 'sala')
