from django.contrib import admin

from salas.models import Sala


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'capacidad', 'activa')
    list_filter = ('activa',)
