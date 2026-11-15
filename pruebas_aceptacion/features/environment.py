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
    return webdriver.Chrome(options=opciones)


def before_all(context):
    context.navegador = crear_navegador()
    context.navegador.implicitly_wait(5)


def after_all(context):
    context.navegador.quit()
