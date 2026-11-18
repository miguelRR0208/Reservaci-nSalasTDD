# Bitácora TDD

En cada parte del sistema primero escribí la prueba y la corrí para confirmar que fallaba por la razón correcta. Luego escribí lo mínimo para que pasara y, cuando el código quedaba feo, lo limpié y volví a correr todo.

Las salidas de cada corrida, en rojo y en verde, están en `evidencias/tdd/`. En el historial de git también se ve: el commit `test:` de cada parte va antes que su `feat:`.

Con Behave fue parecido. Escribí los `.feature` y los steps, los corrí y fallaron porque todavía no había pantallas (`evidencias/bdd/*_falla.txt`). Después hice las vistas hasta que pasaron (`*_pasa.txt`).

## App salas

**1. Modelo Sala**
Falló con `ImportError` porque `Sala` no existía. Creé el modelo con nombre, ubicación, capacidad y activa, y pasaron las 10 pruebas.
Evidencia: `salas/01` y `salas/02`.

**2. Salas iniciales**
Las pruebas buscaban la Sala A, B, C y la de mantenimiento y daban `DoesNotExist`. Las agregué con una migración de datos usando `update_or_create`, que no duplica nada si la migración se aplica otra vez.
Evidencia: `salas/03` y `salas/04`.

**3. Salas activas**
`Sala.objects.activas()` no existía. Hice un QuerySet propio con ese método y lo puse como manager. Ya con eso, en el formulario solo salen las salas activas y la de mantenimiento queda fuera.
Evidencia: `salas/05` y `salas/06`.

## App reservaciones

**4. Modelo Reservación**
Falló porque no existía el modelo. Los estados VIGENTE y CANCELADA quedaron como `TextChoices`.
Evidencia: `reservaciones/01` y `02`.

**5. Disponibilidad**
Aquí las pruebas pedían una función que dijera si una sala está libre en un horario. Dos casos que cuidé: las reservaciones canceladas no cuentan, y si un horario empieza justo cuando termina otro no es traslape. La consulta de traslapes la dejé en su propia función porque después la volví a usar.
Evidencia: `reservaciones/03` y `04`.

**6. Reglas de negocio**
Probé los valores límite de cada regla: fecha no pasada, inicio de 08:00 a 19:00, fin a más tardar a las 20:00, duración de 30 minutos a 2 horas, capacidad y sala activa. Cada regla quedó en una función chica y los límites como constantes.
Evidencia: `reservaciones/05` y `06`.

**7. Formulario (UT-02 a UT-06)**
El formulario reutiliza las reglas del paso anterior. En la primera versión `clean()` tenía el mismo `try/except` repetido varias veces; al refactorizar lo pasé a `aplicar_regla()`.
Evidencia: `reservaciones/07` y `08`.

**8. Servicio para registrar (UT-01, UT-07 a UT-10)**
`crear_reservacion` valida todo otra vez en el servidor antes de guardar, por si llega una petición que no pasó por el formulario. Las validaciones de fecha y hora terminaron juntas en `validar_horario()`.
Evidencia: `reservaciones/09` y `10`.

**9. Dos solicitudes al mismo tiempo (IT-01)**
La prueba lanza dos hilos que reservan la misma sala y horario a la vez. Falló con `database is locked` de SQLite. Lo resolví leyendo de nuevo la sala con `select_for_update()` dentro de una transacción y configurando la base con `transaction_mode = IMMEDIATE` y `timeout = 20`. Con eso la segunda solicitud se queda esperando, y cuando le toca ya ve la reservación de la primera y la rechaza por no disponible.
Evidencia: `reservaciones/11` y `12`.

**10. Usuarios de prueba**
El comando `crear_usuarios_prueba` no existía. Si el usuario ya está creado, el comando solo le restablece la contraseña, así que se puede correr varias veces.
Evidencia: `reservaciones/13` y `14`.

**11. Vistas de registro y lista (UT-11, UT-12)**
Fallaron con `NoReverseMatch` porque no había URLs. Hice las vistas con `login_required`, plantillas mínimas y el login de Django. Cuando el servicio rechaza una reservación, el formulario conserva lo que el usuario escribió. En la lista agregué `select_related` y así no se hace una consulta por cada fila.
Evidencia: `reservaciones/15` y `16`.

**12. Reglas de cancelación**
Faltaban las reglas de propietario, estado y anticipación de 60 minutos. Probé el límite exacto: a 60 minutos ya no se puede cancelar. Después hice `se_puede_cancelar()` con esas reglas; la usan tanto la lista, que decide si mostrar el enlace, como el servicio que cancela.
Evidencia: `reservaciones/17` y `18`.

**13. Servicio para cancelar (UT-13 a UT-17, UT-20)**
El servicio cambia el estado a CANCELADA y guarda la fecha, sin borrar el registro. Antes de cancelar vuelve a leer la reservación de la base, porque la que trae en memoria podría estar desactualizada. Con UT-20 comprobé que después de cancelar se puede reservar otra vez el mismo horario.
Evidencia: `reservaciones/19` y `20`.

**14. Vista para cancelar (UT-18, UT-19)**
Con GET muestra la confirmación y con POST cancela. La reservación se busca solo entre las del usuario: si alguien cambia el número en la URL para cancelar una ajena, le sale 404 y ni se entera de que existe. Sin token CSRF responde 403.
Evidencia: `reservaciones/21` y `22`.

En los ciclos 12 a 14 guardé solo la salida del archivo de pruebas de cada ciclo. La suite completa la corría al cerrar cada bloque; la última corrida está en `reportes/pruebas_unitarias.txt`.

## Steps de Behave

Al agregar los escenarios de cancelación necesitaba funciones que ya estaban en los steps de reservación (fechas relativas, horas, leer mensajes). Intenté importar un archivo de steps desde otro, pero Behave registraba los pasos dos veces. Terminé moviendo esas funciones a `steps/utilidades.py` y `steps/navegacion.py`.

También tuve que corregir la espera de carga de página. A veces el step revisaba la página antes de que terminara de cargar, y el escenario de los dos navegadores fallaba de vez en cuando.

## Resultado final

Al terminar quedaron 157 pruebas pasando con 100% de cobertura en líneas y ramas. flake8 no marca errores, la complejidad más alta es 7 y los 14 escenarios de Behave pasan.
