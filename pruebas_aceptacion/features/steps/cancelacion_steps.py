from datetime import timedelta

from behave import given, when, then
from django.contrib.auth.models import User
from django.utils import timezone
from selenium.webdriver.common.by import By

from navegacion import esperar_nueva_pagina
from utilidades import fecha_de, hora
from reservaciones.disponibilidad import sala_disponible
from reservaciones.models import Reservacion
from salas.models import Sala


def guardar_reservacion(context, sala, fecha, inicio, fin, **extra):
    context.reservacion = Reservacion.objects.create(
        usuario=User.objects.get(username=context.usuario),
        sala=Sala.objects.get(nombre=sala),
        fecha=fecha,
        hora_inicio=inicio,
        hora_fin=fin,
        asistentes=2,
        proposito='Repaso para el examen final',
        **extra,
    )


def url_de_cancelacion(context, reservacion):
    return context.get_url('reservaciones:cancelar', reservacion.pk)


def abrir_lista(context):
    context.navegador.get(context.get_url('reservaciones:lista'))


def confirmar(navegador):
    boton = navegador.find_element(By.ID, 'boton-confirmar')
    boton.click()
    esperar_nueva_pagina(navegador, boton)


def cancelar_desde_lista(context):
    abrir_lista(context)
    enlace = f'cancelar-{context.reservacion.pk}'
    context.navegador.find_element(By.ID, enlace).click()


@given(u'que tengo una reservación vigente de la sala "{sala}" {dia} de '
       u'{inicio} a {fin}')
def tengo_reservacion_vigente(context, sala, dia, inicio, fin):
    guardar_reservacion(context, sala, fecha_de(dia), hora(inicio), hora(fin))


@given(u'que tengo una reservación vigente de la sala "{sala}" que inicia '
       u'dentro de {minutos:d} minutos')
def tengo_reservacion_proxima(context, sala, minutos):
    inicio = timezone.localtime() + timedelta(minutes=minutos)
    fin = inicio + timedelta(hours=1)
    guardar_reservacion(
        context, sala, inicio.date(), inicio.time(), fin.time()
    )


@given(u'que tengo una reservación cancelada de la sala "{sala}" {dia} de '
       u'{inicio} a {fin}')
def tengo_reservacion_cancelada(context, sala, dia, inicio, fin):
    context.fecha_cancelacion = timezone.now() - timedelta(hours=1)
    guardar_reservacion(
        context, sala, fecha_de(dia), hora(inicio), hora(fin),
        estado=Reservacion.Estado.CANCELADA,
        fecha_cancelacion=context.fecha_cancelacion,
    )


@given(u'que cancelé esa reservación desde mi lista')
def cancele_desde_lista(context):
    cancelar_desde_lista(context)
    confirmar(context.navegador)


@when(u'elijo cancelar la reservación desde mi lista')
def elijo_cancelar(context):
    cancelar_desde_lista(context)


@when(u'confirmo la cancelación')
def confirmo_cancelacion(context):
    confirmar(context.navegador)


@when(u'abro mi lista de reservaciones')
def abro_lista(context):
    abrir_lista(context)


@when(u'intento cancelarla abriendo directamente su confirmación')
def cancelo_por_url(context):
    context.navegador.get(url_de_cancelacion(context, context.reservacion))
    confirmar(context.navegador)


@when(u'intento cancelar la reservación del otro usuario modificando la '
      u'petición')
def cancelo_reservacion_ajena(context):
    context.reservacion_ajena = Reservacion.objects.exclude(
        usuario__username=context.usuario
    ).get()
    context.navegador.get(url_de_cancelacion(context, context.reservacion))
    # Simula una petición manipulada: el formulario de confirmación de
    # mi reservación se envía con el número de la reservación ajena.
    context.navegador.execute_script(
        "document.getElementById('formulario-cancelar').action = "
        "arguments[0];",
        url_de_cancelacion(context, context.reservacion_ajena),
    )
    confirmar(context.navegador)


@then(u'mi reservación tiene el estado "{estado}"')
def mi_reservacion_tiene_estado(context, estado):
    context.reservacion.refresh_from_db()
    assert context.reservacion.estado == estado, \
        f'Estado esperado {estado} y obtenido {context.reservacion.estado}'


@then(u'la reservación del otro usuario conserva el estado "{estado}"')
def ajena_conserva_estado(context, estado):
    context.reservacion_ajena.refresh_from_db()
    obtenido = context.reservacion_ajena.estado
    assert obtenido == estado, \
        f'Estado esperado {estado} y obtenido {obtenido}'


@then(u'mi reservación tiene registrada la fecha y hora de cancelación')
def tiene_fecha_cancelacion(context):
    context.reservacion.refresh_from_db()
    assert context.reservacion.fecha_cancelacion is not None, \
        'La reservación no tiene fecha de cancelación'


@then(u'la fecha de cancelación de mi reservación no cambia')
def fecha_cancelacion_no_cambia(context):
    context.reservacion.refresh_from_db()
    obtenida = context.reservacion.fecha_cancelacion
    assert obtenida == context.fecha_cancelacion, \
        f'Se esperaba {context.fecha_cancelacion} y hay {obtenida}'


@then(u'la sala "{sala}" queda disponible {dia} de {inicio} a {fin}')
def sala_queda_disponible(context, sala, dia, inicio, fin):
    sala = Sala.objects.get(nombre=sala)
    assert sala_disponible(sala, fecha_de(dia), hora(inicio), hora(fin)), \
        f'{sala} sigue ocupada {dia} de {inicio} a {fin}'


@then(u'la respuesta no muestra datos de la reservación del otro usuario')
def no_muestra_datos_ajenos(context):
    pagina = context.navegador.page_source
    ajena = context.reservacion_ajena
    for dato in [ajena.proposito, ajena.usuario.username]:
        assert dato not in pagina, f'La página muestra "{dato}"'


@then(u'no aparece la opción para cancelar mi reservación')
def no_aparece_cancelar(context):
    pk = context.reservacion.pk
    context.navegador.find_element(By.ID, f'reservacion-{pk}')
    # Se quita la espera implícita para no aguardar 5 segundos
    # por un enlace que se espera que no exista.
    context.navegador.implicitly_wait(0)
    enlaces = context.navegador.find_elements(By.ID, f'cancelar-{pk}')
    context.navegador.implicitly_wait(5)
    assert not enlaces, 'Aparece la opción para cancelar la reservación'


@then(u'en mi lista aparece la fecha y hora en que la cancelé')
def aparece_fecha_cancelacion(context):
    context.reservacion.refresh_from_db()
    esperada = timezone.localtime(
        context.reservacion.fecha_cancelacion
    ).strftime('%Y-%m-%d %H:%M')
    fila = context.navegador.find_element(
        By.ID, f'reservacion-{context.reservacion.pk}'
    )
    obtenida = fila.find_element(By.CLASS_NAME, 'fecha-cancelacion').text
    assert obtenida == esperada, \
        f'Fecha de cancelación esperada {esperada} y obtenida {obtenida}'
