from behave import given
from django.contrib.auth.models import User
from selenium.webdriver.common.by import By


def iniciar_sesion(context, navegador, usuario, clave):
    if not User.objects.filter(username=usuario).exists():
        User.objects.create_user(usuario, password=clave)
    navegador.get(context.get_url('login'))
    navegador.find_element(By.NAME, 'username').send_keys(usuario)
    navegador.find_element(By.NAME, 'password').send_keys(clave)
    navegador.find_element(By.ID, 'boton-entrar').click()


@given(u'el usuario "{usuario}" con contraseña "{clave}" ha iniciado sesión')
def sesion_iniciada(context, usuario, clave):
    iniciar_sesion(context, context.navegador, usuario, clave)
    context.usuario = usuario


@given(u'el usuario "{usuario}" con contraseña "{clave}" ha iniciado '
       u'sesión en otro navegador')
def sesion_en_otro_navegador(context, usuario, clave):
    context.otro_navegador = context.crear_navegador()
    iniciar_sesion(context, context.otro_navegador, usuario, clave)
