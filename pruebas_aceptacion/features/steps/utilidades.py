from datetime import datetime, timedelta

from django.utils import timezone
from selenium.webdriver.common.by import By

DIAS = {'ayer': -1, 'hoy': 0, 'mañana': 1}


def fecha_de(dia):
    return timezone.localdate() + timedelta(days=DIAS[dia])


def hora(texto):
    return datetime.strptime(texto, '%H:%M').time()


def textos_de_mensajes(navegador):
    mensajes = navegador.find_elements(By.CLASS_NAME, 'mensaje')
    return [mensaje.text for mensaje in mensajes]
