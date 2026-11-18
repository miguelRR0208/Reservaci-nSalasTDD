# Reservación de salas de estudio

Aplicación web en Django para reservar salas de estudio. Permite registrar una reservación (HU-01) y cancelarla (HU-02). La hice con TDD y BDD: las pruebas unitarias se escribieron antes del código y los criterios de aceptación están automatizados con Behave y Selenium.

## Qué se necesita

- Python 3.12
- Google Chrome para correr los escenarios de Behave (Selenium baja el driver solo)
- Java 17 o más y Apache JMeter 5.6.3, solo para las pruebas de rendimiento

## Cómo está organizado

```
app/                  proyecto Django
  config/             settings y urls
  salas/              modelo Sala y salas iniciales
  reservaciones/      modelo, reglas, servicios, formulario, vistas y plantillas
pruebas_aceptacion/   archivos .feature y steps de Behave
rendimiento/          plan de JMeter, CSV de datos y scripts para revisar resultados
evidencias/           salidas de cada ciclo TDD (falla / pasa) y de los escenarios BDD
reportes/             pruebas, cobertura, flake8, radon, behave y JMeter
BITACORA_TDD.md       bitácora de los ciclos TDD
generar_reportes.py   corre todas las pruebas y revisiones de una vez
```

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\activate        # en Linux o macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

Para trabajar en local no hace falta definir nada, las dos tienen un valor por defecto.

- `DJANGO_SECRET_KEY`: si no se define se usa una llave de desarrollo. Fuera de su máquina conviene poner una propia.
- `DJANGO_DEBUG`: `1` para modo depuración (es el valor por defecto) y `0` para apagarlo.

```powershell
$env:DJANGO_SECRET_KEY = "mi-llave-secreta"
$env:DJANGO_DEBUG = "0"
```

## Base de datos, salas y usuarios

Los comandos de Django se corren dentro de `app/`:

```powershell
cd app
python manage.py migrate
python manage.py crear_usuarios_prueba
```

`migrate` crea la base SQLite y además carga las salas iniciales con una migración de datos: Sala A (4 personas), Sala B (8), Sala C (12) y Sala de mantenimiento (6, inactiva).

`crear_usuarios_prueba` crea los usuarios de prueba. Si ya existen, solo les vuelve a poner su contraseña, así que se puede correr las veces que sea.

| Usuario | Contraseña | Rol |
|---|---|---|
| ana | Reserva2026 | usuario normal |
| beto | Reserva2026 | usuario normal |
| admin | Admin2026 | administrador, puede entrar a `/admin/` |

## Correr la aplicación

```powershell
cd app
python manage.py runserver
```

Queda en http://127.0.0.1:8000/. Si el puerto 8000 está ocupado se puede usar otro, por ejemplo `python manage.py runserver 8010`.

### Para la demostración

1. Entrar como `ana`.
2. En "Nueva reservación" elegir Sala A para mañana de 10:00 a 11:00 con 2 asistentes. Aparece en "Mis reservaciones" como VIGENTE.
3. Intentar el mismo horario en la misma sala: sale el aviso de que la sala no está disponible.
4. Cancelar la reservación desde la lista. Queda CANCELADA con su fecha de cancelación y el horario vuelve a estar libre.
5. Entrar como `beto` y ver que no aparecen las reservaciones de `ana`.

## Generar todos los reportes de una vez

Desde la raíz, con el entorno virtual activo:

```powershell
python generar_reportes.py
```

Corre en orden las pruebas unitarias con coverage, el reporte de cobertura (texto y HTML), flake8, radon y Behave. Cada salida se guarda en `reportes/` con el comando que la generó hasta arriba. Al final enseña qué pasó bien y qué falló. Tarda alrededor de un minuto.

Si no tiene Chrome o no quiere esperar a Selenium, use `python generar_reportes.py --sin-behave`. JMeter no está incluido porque necesita el servidor levantado y la base limpia; eso se explica más abajo.

Si prefiere correr cada cosa por separado, los comandos están en las siguientes secciones.

## Pruebas unitarias

```powershell
cd app
python manage.py test
```

Son 157 pruebas. Además de UT-01 a UT-20 y la de integración IT-01, agregué varias para cubrir límites, ramas y errores. Los casos obligatorios tienen su clave en la descripción de la prueba:

- UT-01, UT-07 a UT-10, UT-13 a UT-17 y UT-20: `reservaciones/tests/tests_servicios.py`
- UT-02 a UT-06: `reservaciones/tests/tests_forms.py`
- UT-11, UT-12, UT-18 y UT-19: `reservaciones/tests/tests_views.py`
- IT-01: `reservaciones/tests/tests_concurrencia.py`

Cuando se corren pruebas el proyecto usa un cifrado de contraseñas rápido (MD5). El normal de Django es lento a propósito y hacía que las pruebas tardaran bastante más. Esto solo aplica con `test` y `behave`.

## Cobertura

```powershell
cd app
coverage run manage.py test
coverage report -m
coverage html
```

Da 100% en líneas y en ramas. El HTML queda en `reportes/cobertura/index.html`.

Dejé fuera de la medición:

- Las migraciones, porque las genera Django. La de salas iniciales igual tiene sus pruebas en `salas/tests/tests_datos_iniciales.py`.
- La carpeta `tests`, porque son las pruebas y no código de la aplicación.
- `config/` y `manage.py`, que son configuración del proyecto y no tienen lógica de negocio.

## PEP 8

Desde la raíz del repositorio:

```powershell
flake8 --count .
```

La configuración está en `.flake8`: líneas de 79 caracteres, complejidad máxima de 10, y deja fuera `.venv` y las migraciones.

## Complejidad ciclomática

```powershell
radon cc . -s -a -e "*/migrations/*" -i ".venv"
radon cc . -s -n C -e "*/migrations/*" -i ".venv"
```

El segundo comando solo enseña lo que tenga complejidad de 11 o más; si no imprime nada, todo está en 10 o menos.

En el enunciado viene `-x '*/migrations/*'`, pero en radon `-x` sirve para otra cosa (la complejidad máxima que se muestra). Para excluir archivos se usa `-e` y para ignorar carpetas `-i`.

## Pruebas de aceptación (Behave + Selenium)

```powershell
cd pruebas_aceptacion
python ..\app\manage.py behave
```

Chrome corre sin ventana. Si quiere ver lo que va haciendo el navegador, ponga antes `$env:HEADLESS = "0"`.

Behave usa su propia base de prueba y la limpia en cada escenario, así que no toca sus datos. Los escenarios están en español y separados por historia:

- `reservaciones.feature`: CA-01 a CA-06
- `cancelaciones.feature`: CA-07 a CA-11

Si en Windows manda la salida a un archivo, ponga antes `$env:PYTHONIOENCODING = "utf-8"` para que no falle con los acentos.

## Pruebas de rendimiento (JMeter)

El plan registra reservaciones con fechas que dependen del día en que se corre, por eso hay que empezar con la base limpia. Si no, la segunda corrida choca con lo que dejó la primera.

```powershell
cd app
Remove-Item db.sqlite3
python manage.py migrate
python manage.py crear_usuarios_prueba
$env:DJANGO_DEBUG = "0"
python manage.py runserver 127.0.0.1:8010 --noreload
```

En otra terminal, desde la raíz:

```powershell
jmeter -n -t rendimiento/plan_reservaciones.jmx -Jpuerto=8010 -l reportes/jmeter/resultados.csv -e -o reportes/jmeter/html
python rendimiento/resumir_resultados.py
python rendimiento/revisar_traslapes.py
```

Con `-Jpuerto` se le dice a JMeter en qué puerto está la aplicación; si no se pone usa el 8000. La carpeta `reportes/jmeter/html` no debe existir antes de correr el plan.

El plan tiene tres grupos:

- PERF-01: 50 usuarios consultan su lista 5 veces cada uno, con subida gradual de 30 s.
- PERF-02: 30 usuarios registran 3 reservaciones cada uno, con subida de 30 s. Los horarios salen de `rendimiento/datos/reservaciones_sin_traslape.csv` para que no se encimen.
- PERF-03: 5 usuarios piden al mismo tiempo la misma sala y horario, y eso se repite 10 veces.

En `reportes/jmeter/` está el reporte HTML, el resumen con muestras, promedio, p90, p95, throughput y errores, la consulta a la base después de PERF-03 y `interpretacion.md`, donde comento los resultados.

## Entregables

- E-01 Repositorio: este repositorio, con su `.gitignore`.
- E-02 README: este archivo.
- E-03 Pruebas unitarias: `app/*/tests/` y `reportes/pruebas_unitarias.txt`.
- E-04 Pruebas BDD: `pruebas_aceptacion/`, `reportes/behave.txt` y `evidencias/bdd/`.
- E-05 Cobertura: `reportes/cobertura/` y `reportes/cobertura.txt`.
- E-06 PEP 8: `reportes/flake8.txt`.
- E-07 Complejidad: `reportes/radon.txt`.
- E-08 JMeter: `rendimiento/` y `reportes/jmeter/`.
- E-09 Bitácora TDD: `BITACORA_TDD.md` y `evidencias/tdd/`.
- E-10 Demostración: ver "Correr la aplicación".
