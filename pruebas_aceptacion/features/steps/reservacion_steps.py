import threading
from datetime import datetime, timedelta

from behave import given, when, then
from django.contrib.auth.models import User
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from reservaciones.models import Reservacion
from salas.models import Sala

DIAS = {'ayer': -1, 'hoy': 0, 'mañana': 1}


def fecha_de(dia):
    return timezone.localdate() + timedelta(days=DIAS[dia])


def hora(texto):
    return datetime.strptime(texto, '%H:%M').time()


def guardar_sala(nombre, capacidad, activa, ubicacion='Biblioteca'):
    Sala.objects.update_or_create(
        nombre=nombre,
        defaults={
            'ubicacion': ubicacion,
            'capacidad': capacidad,
            'activa': activa,
        },
    )


def escribir(navegador, campo, valor):
    elemento = navegador.find_element(By.NAME, campo)
    elemento.clear()
    elemento.send_keys(valor)


def capturar_horario(context, navegador, dia, inicio, fin):
    fecha = fecha_de(dia).strftime('%Y-%m-%d')
    escribir(navegador, 'fecha', fecha)
    escribir(navegador, 'hora_inicio', inicio)
    escribir(navegador, 'hora_fin', fin)
    context.capturado.update(
        {'fecha': fecha, 'hora_inicio': inicio, 'hora_fin': fin}
    )


def abrir_formulario(context, navegador):
    navegador.get(context.get_url('reservaciones:lista'))
    navegador.find_element(By.ID, 'nueva-reservacion').click()


def textos_de_mensajes(navegador):
    mensajes = navegador.find_elements(By.CLASS_NAME, 'mensaje')
    return [mensaje.text for mensaje in mensajes]


def vigentes_en(sala, dia, inicio, fin):
    return Reservacion.objects.filter(
        sala__nombre=sala,
        fecha=fecha_de(dia),
        hora_inicio=hora(inicio),
        hora_fin=hora(fin),
        estado=Reservacion.Estado.VIGENTE,
    )


@given(u'que existe la sala "{nombre}" en "{ubicacion}" con capacidad '
       u'para {capacidad:d} personas')
def existe_sala_activa(context, nombre, ubicacion, capacidad):
    guardar_sala(nombre, capacidad, True, ubicacion)


@given(u'que existe la sala inactiva "{nombre}" con capacidad para '
       u'{capacidad:d} personas')
def existe_sala_inactiva(context, nombre, capacidad):
    guardar_sala(nombre, capacidad, False)


@given(u'que no existe otra reservación vigente para la sala "{sala}" '
       u'{dia} de {inicio} a {fin}')
def no_existe_reservacion(context, sala, dia, inicio, fin):
    assert not vigentes_en(sala, dia, inicio, fin).exists(), \
        f'Ya existe una reservación vigente para {sala}'


@given(u'que existe una reservación vigente de otro usuario para la sala '
       u'"{sala}" {dia} de {inicio} a {fin}')
def existe_reservacion_ajena(context, sala, dia, inicio, fin):
    otro, _ = User.objects.get_or_create(username='otro_usuario')
    Reservacion.objects.create(
        usuario=otro,
        sala=Sala.objects.get(nombre=sala),
        fecha=fecha_de(dia),
        hora_inicio=hora(inicio),
        hora_fin=hora(fin),
        asistentes=1,
        proposito='Reservación hecha por otra persona',
    )


@when(u'abro el formulario de nueva reservación')
def abro_formulario(context):
    context.reservaciones_antes = Reservacion.objects.count()
    context.capturado = {}
    abrir_formulario(context, context.navegador)


@when(u'capturo la sala "{sala}" para {dia} de {inicio} a {fin}')
def capturo_sala_y_horario(context, sala, dia, inicio, fin):
    lista = Select(context.navegador.find_element(By.NAME, 'sala'))
    lista.select_by_visible_text(sala)
    context.capturado['sala'] = lista.first_selected_option.get_attribute(
        'value'
    )
    capturar_horario(context, context.navegador, dia, inicio, fin)


@when(u'fuerzo la selección de la sala "{sala}" para {dia} de {inicio} '
      u'a {fin}')
def fuerzo_sala(context, sala, dia, inicio, fin):
    # Simula una petición manipulada: agrega a la lista una sala
    # que la página no ofrece y la deja seleccionada.
    sala_id = str(Sala.objects.get(nombre=sala).pk)
    context.navegador.execute_script(
        "const lista = document.getElementsByName('sala')[0];"
        "lista.add(new Option(arguments[1], arguments[0]));"
        "lista.value = arguments[0];",
        sala_id, sala,
    )
    capturar_horario(context, context.navegador, dia, inicio, fin)


@when(u'capturo {asistentes:d} asistentes con el propósito "{proposito}"')
def capturo_asistentes_y_proposito(context, asistentes, proposito):
    escribir(context.navegador, 'asistentes', str(asistentes))
    escribir(context.navegador, 'proposito', proposito)
    context.capturado.update(
        {'asistentes': str(asistentes), 'proposito': proposito}
    )


@when(u'envío el formulario')
def envio_formulario(context):
    context.navegador.find_element(By.ID, 'boton-guardar').click()


@then(u'mi reservación queda registrada con estado "{estado}"')
def reservacion_registrada(context, estado):
    reservacion = Reservacion.objects.filter(
        usuario__username=context.usuario
    ).latest('fecha_creacion')
    assert reservacion.estado == estado, \
        f'Estado esperado {estado} y obtenido {reservacion.estado}'


@then(u'veo el mensaje "{mensaje}"')
def veo_mensaje(context, mensaje):
    obtenidos = textos_de_mensajes(context.navegador)
    assert mensaje in obtenidos, \
        f'Mensaje esperado "{mensaje}" y obtenidos {obtenidos}'


@then(u'en mi lista aparece la reservación de "{sala}" de {inicio} a '
      u'{fin} con estado "{estado}"')
def aparece_en_lista(context, sala, inicio, fin, estado):
    context.navegador.get(context.get_url('reservaciones:lista'))
    tabla = context.navegador.find_element(By.ID, 'tabla-reservaciones')
    filas = [fila.text for fila in tabla.find_elements(By.TAG_NAME, 'tr')]
    buscados = [sala, inicio, fin, estado]
    assert any(all(dato in fila for dato in buscados) for fila in filas), \
        f'No se encontró {buscados} en {filas}'


@then(u'no se registra ninguna reservación nueva')
def no_se_registra(context):
    total = Reservacion.objects.count()
    assert total == context.reservaciones_antes, \
        f'Había {context.reservaciones_antes} reservaciones y ahora {total}'


@then(u'el formulario conserva los datos que capturé')
def conserva_datos(context):
    for campo, esperado in context.capturado.items():
        elemento = context.navegador.find_element(By.NAME, campo)
        obtenido = elemento.get_attribute('value')
        assert obtenido == esperado, \
            f'En {campo} se esperaba "{esperado}" y hay "{obtenido}"'


@then(u'la sala "{sala}" no aparece entre las opciones')
def sala_no_aparece(context, sala):
    lista = Select(context.navegador.find_element(By.NAME, 'sala'))
    opciones = [opcion.text for opcion in lista.options]
    assert sala not in opciones, f'{sala} aparece en {opciones}'


@given(u'en ambos navegadores se captura la sala "{sala}" para {dia} de '
       u'{inicio} a {fin} con {asistentes:d} asistentes')
def captura_en_ambos(context, sala, dia, inicio, fin, asistentes):
    context.reservaciones_antes = Reservacion.objects.count()
    context.navegadores = [context.navegador, context.otro_navegador]
    for navegador in context.navegadores:
        context.capturado = {}
        abrir_formulario(context, navegador)
        Select(navegador.find_element(By.NAME, 'sala')) \
            .select_by_visible_text(sala)
        capturar_horario(context, navegador, dia, inicio, fin)
        escribir(navegador, 'asistentes', str(asistentes))
        escribir(navegador, 'proposito', 'Prueba de solicitudes simultáneas')


@when(u'ambos navegadores envían el formulario al mismo tiempo')
def envian_al_mismo_tiempo(context):
    # La barrera hace que los dos hilos den clic en el mismo instante.
    barrera = threading.Barrier(len(context.navegadores))
    botones = [
        navegador.find_element(By.ID, 'boton-guardar')
        for navegador in context.navegadores
    ]

    def enviar(boton):
        barrera.wait()
        boton.click()

    hilos = [threading.Thread(target=enviar, args=(b,)) for b in botones]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    context.mensajes_por_navegador = [
        textos_de_mensajes(navegador) for navegador in context.navegadores
    ]


@then(u'solo una reservación queda vigente para la sala "{sala}" {dia} de '
      u'{inicio} a {fin}')
def solo_una_vigente(context, sala, dia, inicio, fin):
    total = vigentes_en(sala, dia, inicio, fin).count()
    assert total == 1, f'Se esperaba 1 reservación vigente y hay {total}'


@then(u'un navegador muestra el mensaje "{mensaje}"')
def un_navegador_muestra(context, mensaje):
    con_mensaje = [
        mensajes for mensajes in context.mensajes_por_navegador
        if mensaje in mensajes
    ]
    assert len(con_mensaje) == 1, \
        f'"{mensaje}" no aparece en un solo navegador: ' \
        f'{context.mensajes_por_navegador}'


@then(u'el otro navegador muestra el mensaje "{mensaje}"')
def otro_navegador_muestra(context, mensaje):
    un_navegador_muestra(context, mensaje)
