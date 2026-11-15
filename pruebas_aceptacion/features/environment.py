import os

from selenium import webdriver


def crear_navegador():
    # Por defecto corre sin ventana; con HEADLESS=0 se ve el navegador.
    opciones = webdriver.ChromeOptions()
    if os.environ.get('HEADLESS', '1') == '1':
        opciones.add_argument('--headless=new')
    opciones.add_argument('--window-size=1280,900')
    opciones.add_argument('--no-sandbox')
    opciones.add_argument('--disable-gpu')
    navegador = webdriver.Chrome(options=opciones)
    navegador.implicitly_wait(5)
    return navegador


def before_all(context):
    context.crear_navegador = crear_navegador
    context.navegador = crear_navegador()


def before_scenario(context, scenario):
    context.navegador.delete_all_cookies()
    context.otro_navegador = None


def after_scenario(context, scenario):
    if context.otro_navegador:
        context.otro_navegador.quit()


def after_all(context):
    context.navegador.quit()
