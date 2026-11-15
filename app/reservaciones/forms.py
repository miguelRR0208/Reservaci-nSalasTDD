from django import forms
from django.core.exceptions import ValidationError

from reservaciones import reglas
from reservaciones.models import Reservacion
from salas.models import Sala

FORMATO_FECHA = '%Y-%m-%d'
FORMATO_HORA = '%H:%M'


class ReservacionForm(forms.ModelForm):
    sala = forms.ModelChoiceField(
        queryset=Sala.objects.activas(),
        error_messages={
            'invalid_choice':
                'La sala no se encuentra disponible para reservación.',
        },
    )
    fecha = forms.DateField(
        input_formats=[FORMATO_FECHA],
        widget=forms.DateInput(
            format=FORMATO_FECHA, attrs={'placeholder': 'AAAA-MM-DD'}
        ),
        validators=[reglas.validar_fecha_no_pasada],
    )
    hora_inicio = forms.TimeField(
        label='Hora de inicio',
        input_formats=[FORMATO_HORA],
        widget=forms.TimeInput(
            format=FORMATO_HORA, attrs={'placeholder': 'HH:MM'}
        ),
        validators=[reglas.validar_hora_inicio],
    )
    hora_fin = forms.TimeField(
        label='Hora de fin',
        input_formats=[FORMATO_HORA],
        widget=forms.TimeInput(
            format=FORMATO_HORA, attrs={'placeholder': 'HH:MM'}
        ),
    )
    asistentes = forms.IntegerField(
        min_value=1,
        error_messages={
            'invalid': 'Escribe un número entero de asistentes.',
            'min_value': 'Debe haber al menos 1 asistente.',
        },
    )
    proposito = forms.CharField(
        label='Propósito',
        min_length=10,
        max_length=200,
        error_messages={
            'min_length': 'El propósito debe tener entre 10 y 200 caracteres.',
            'max_length': 'El propósito debe tener entre 10 y 200 caracteres.',
        },
    )

    class Meta:
        model = Reservacion
        fields = [
            'sala', 'fecha', 'hora_inicio', 'hora_fin',
            'asistentes', 'proposito',
        ]

    def clean(self):
        datos = super().clean()
        inicio = datos.get('hora_inicio')
        fin = datos.get('hora_fin')
        if inicio is not None and fin is not None:
            self.aplicar_regla(
                'hora_fin', reglas.validar_hora_fin, inicio, fin
            )
        sala = datos.get('sala')
        asistentes = datos.get('asistentes')
        if sala is not None and asistentes is not None:
            self.aplicar_regla(
                'asistentes', reglas.validar_capacidad, sala, asistentes
            )
        return datos

    def aplicar_regla(self, campo, regla, *valores):
        # Si la regla falla, el mensaje se muestra junto al campo indicado.
        try:
            regla(*valores)
        except ValidationError as error:
            self.add_error(campo, error)
