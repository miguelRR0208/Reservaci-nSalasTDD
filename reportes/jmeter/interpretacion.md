# Interpretación de las pruebas de rendimiento

## Condiciones de la ejecución

- Apache JMeter 5.6.3 en modo consola (sin interfaz gráfica).
- La aplicación corrió con `runserver` de Django en `127.0.0.1:8010` con `DJANGO_DEBUG=0`, sobre SQLite.
- Antes de ejecutar se borró la base, se migró (lo que carga las salas iniciales) y se crearon los usuarios con `crear_usuarios_prueba`.
- JMeter y la aplicación corrieron en la misma computadora.
- Los grupos se ejecutan uno tras otro: PERF-02, PERF-03 y al final PERF-01. Dejé PERF-01 al último porque para entonces cada usuario ya tiene alrededor de 50 reservaciones en su lista.
- Cada usuario virtual inicia sesión una sola vez, como `ana` o `beto` de forma alternada, y después repite sus iteraciones con la misma sesión.
- Todas las peticiones POST envían el token CSRF que se extrae de la página anterior.

## Resultados frente a los criterios

| Escenario | Carga | Errores | p95 | Criterio | Resultado |
|---|---|---|---|---|---|
| PERF-01 | 50 usuarios, subida de 30 s, 5 iteraciones (250 consultas) | 0 % | 13.9 ms | < 1 % y p95 <= 1500 ms | Cumple |
| PERF-02 | 30 usuarios, subida de 30 s, 3 iteraciones (90 registros) | 0 % | 12.0 ms | < 1 % y p95 <= 2000 ms | Cumple |
| PERF-03 | 5 usuarios a la vez, 10 repeticiones del conflicto (50 solicitudes) | 0 % | 82.9 ms | Nunca dos vigentes traslapadas | Cumple |

El detalle por petición (muestras, promedio, p90, p95, throughput y % de errores) está en `resumen_resultados.txt`. El reporte completo está en `html/index.html`.

### PERF-02

Los 90 POST respondieron con redirección a la lista, y en la base quedaron 90 reservaciones vigentes. Los datos salen de `rendimiento/datos/reservaciones_sin_traslape.csv`: 3 salas, 10 horarios de una hora y 3 días distintos, sin ninguna combinación repetida.

### PERF-03

En cada repetición los 5 usuarios esperan en un temporizador de sincronización y envían el POST al mismo tiempo, con la misma sala y el mismo horario.

En las 10 repeticiones el resultado fue siempre el mismo: una solicitud se registró (302) y las otras 4 recibieron el mensaje "La sala no está disponible en el horario solicitado.". En total fueron 10 registradas y 40 rechazadas.

En la consulta a la base de datos (`consulta_traslapes.txt`) se ve que:

- Cada horario del conflicto tiene 1 sola reservación vigente.
- La consulta que cruza la tabla consigo misma para buscar reservaciones vigentes traslapadas en la misma sala y fecha regresa 0 filas.

## Cuellos de botella observados

### Inicio de sesión

Es la petición más lenta, entre 440 y 980 ms. No es un problema de la aplicación: Django guarda las contraseñas con PBKDF2, que es lento a propósito, y cada inicio de sesión gasta casi un segundo de CPU. Cuando varios usuarios entran al mismo tiempo, como en PERF-03, el tiempo sube. Como en el plan cada usuario inicia sesión una sola vez, esto no afecta a las consultas ni a los registros.
### Escrituras simultáneas en SQLite

Un registro solo tarda unos 10 ms (PERF-02). Cuando llegan 5 juntos (PERF-03), el promedio sube a 44 ms y el máximo a 92 ms. Esto pasa porque SQLite solo deja escribir a uno a la vez, y como las transacciones de reservación se abren en modo `IMMEDIATE`, las demás esperan su turno. Es la misma espera que evita los traslapes. Si hubiera muchos más usuarios escribiendo a la vez, convendría cambiar a PostgreSQL o una base parecida.
### Lista de reservaciones

Se mantuvo entre 10 y 21 ms con alrededor de 50 reservaciones por usuario. La lista y sus salas se traen en una sola consulta con `select_related`.

## Limitaciones

- El generador de carga y la aplicación compartieron la misma computadora, así que compitieron por la CPU.
- `runserver` es el servidor de desarrollo de Django. En producción se usaría un servidor como gunicorn o waitress detrás de un proxy.
- Los tiempos sirven para comparar los escenarios entre sí, no como una medida de producción.
