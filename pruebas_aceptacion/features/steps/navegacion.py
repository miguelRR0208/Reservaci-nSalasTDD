from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait


def esperar_nueva_pagina(navegador, elemento):
    # Espera a que el navegador deje la página actual después del clic.
    # Chrome a veces avisa con un error genérico en lugar de decir que
    # el elemento ya no existe, así que cualquier error cuenta como cambio.
    def pagina_cambio(_):
        try:
            elemento.is_enabled()
        except WebDriverException:
            return True
        return False

    WebDriverWait(navegador, 10).until(pagina_cambio)
