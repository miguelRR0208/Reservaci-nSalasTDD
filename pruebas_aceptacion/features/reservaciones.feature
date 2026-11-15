Característica: Registrar una reservación de sala
    Como usuario autenticado
    Quiero seleccionar una sala disponible y registrar una reservación
    Para asegurar el uso exclusivo de la sala durante un periodo determinado

    Antecedentes:
        Dado que existe la sala "Sala A" en "Biblioteca, planta baja" con capacidad para 4 personas
        Y el usuario "ana" con contraseña "Reserva2026" ha iniciado sesión

    Escenario: CA-01 Registrar una reservación válida
        Dado que no existe otra reservación vigente para la sala "Sala A" mañana de 10:00 a 11:00
        Cuando abro el formulario de nueva reservación
        Y capturo la sala "Sala A" para mañana de 10:00 a 11:00
        Y capturo 3 asistentes con el propósito "Repaso para el examen de cálculo"
        Y envío el formulario
        Entonces mi reservación queda registrada con estado "VIGENTE"
        Y veo el mensaje "La reservación se registró correctamente."
        Y en mi lista aparece la reservación de "Sala A" de 10:00 a 11:00 con estado "VIGENTE"

    Escenario: CA-02 Rechazar una reservación con horario traslapado
        Dado que existe una reservación vigente de otro usuario para la sala "Sala A" mañana de 10:00 a 11:00
        Cuando abro el formulario de nueva reservación
        Y capturo la sala "Sala A" para mañana de 10:30 a 11:30
        Y capturo 2 asistentes con el propósito "Reunión del equipo de proyecto"
        Y envío el formulario
        Entonces no se registra ninguna reservación nueva
        Y veo el mensaje "La sala no está disponible en el horario solicitado."

    Escenario: CA-03 Rechazar una reservación que exceda la capacidad
        Cuando abro el formulario de nueva reservación
        Y capturo la sala "Sala A" para mañana de 10:00 a 11:00
        Y capturo 5 asistentes con el propósito "Sesión de estudio en grupo grande"
        Y envío el formulario
        Entonces no se registra ninguna reservación nueva
        Y veo el mensaje "El número de asistentes supera la capacidad de la sala."
        Y el formulario conserva los datos que capturé

    Esquema del escenario: CA-04 Rechazar una fecha u horario inválidos
        Cuando abro el formulario de nueva reservación
        Y capturo la sala "Sala A" para <dia> de <inicio> a <fin>
        Y capturo 2 asistentes con el propósito "Sesión de estudio de algoritmos"
        Y envío el formulario
        Entonces no se registra ninguna reservación nueva
        Y veo el mensaje "<mensaje>"

        Ejemplos:
            | dia    | inicio | fin   | mensaje                                                |
            | ayer   | 10:00  | 11:00 | La fecha no puede ser anterior al día de hoy.          |
            | mañana | 11:00  | 10:00 | La hora de fin debe ser posterior a la hora de inicio. |
            | mañana | 10:00  | 10:00 | La hora de fin debe ser posterior a la hora de inicio. |

    Escenario: CA-05 Rechazar una sala inactiva
        Dado que existe la sala inactiva "Sala de mantenimiento" con capacidad para 6 personas
        Cuando abro el formulario de nueva reservación
        Entonces la sala "Sala de mantenimiento" no aparece entre las opciones
        Cuando fuerzo la selección de la sala "Sala de mantenimiento" para mañana de 10:00 a 11:00
        Y capturo 2 asistentes con el propósito "Revisión del proyecto final"
        Y envío el formulario
        Entonces no se registra ninguna reservación nueva
        Y veo el mensaje "La sala no se encuentra disponible para reservación."

    Escenario: CA-06 Evitar una doble reservación ante solicitudes concurrentes
        Dado que no existe otra reservación vigente para la sala "Sala A" mañana de 12:00 a 13:00
        Y el usuario "beto" con contraseña "Reserva2026" ha iniciado sesión en otro navegador
        Y en ambos navegadores se captura la sala "Sala A" para mañana de 12:00 a 13:00 con 2 asistentes
        Cuando ambos navegadores envían el formulario al mismo tiempo
        Entonces solo una reservación queda vigente para la sala "Sala A" mañana de 12:00 a 13:00
        Y un navegador muestra el mensaje "La reservación se registró correctamente."
        Y el otro navegador muestra el mensaje "La sala no está disponible en el horario solicitado."
