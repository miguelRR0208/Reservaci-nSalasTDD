Característica: Cancelar una reservación
    Como usuario autenticado propietario de una reservación
    Quiero cancelar una reservación que ya no utilizaré
    Para liberar la sala y permitir que otro usuario pueda reservarla

    Antecedentes:
        Dado que existe la sala "Sala A" en "Biblioteca, planta baja" con capacidad para 4 personas
        Y el usuario "ana" con contraseña "Reserva2026" ha iniciado sesión

    Escenario: CA-07 Cancelar una reservación vigente con anticipación suficiente
        Dado que tengo una reservación vigente de la sala "Sala A" mañana de 10:00 a 11:00
        Cuando elijo cancelar la reservación desde mi lista
        Y confirmo la cancelación
        Entonces mi reservación tiene el estado "CANCELADA"
        Y mi reservación tiene registrada la fecha y hora de cancelación
        Y veo el mensaje "La reservación se canceló correctamente."
        Y la sala "Sala A" queda disponible mañana de 10:00 a 11:00

    Escenario: CA-08 Impedir que un usuario cancele una reservación ajena
        Dado que existe una reservación vigente de otro usuario para la sala "Sala A" mañana de 12:00 a 13:00
        Y que tengo una reservación vigente de la sala "Sala A" mañana de 10:00 a 11:00
        Cuando intento cancelar la reservación del otro usuario modificando la petición
        Entonces veo el mensaje "No se encontró la página solicitada."
        Y la reservación del otro usuario conserva el estado "VIGENTE"
        Y mi reservación tiene el estado "VIGENTE"
        Y la respuesta no muestra datos de la reservación del otro usuario

    Esquema del escenario: CA-09 Impedir la cancelación fuera del periodo permitido
        Dado que tengo una reservación vigente de la sala "Sala A" que inicia dentro de <minutos> minutos
        Cuando abro mi lista de reservaciones
        Entonces no aparece la opción para cancelar mi reservación
        Cuando intento cancelarla abriendo directamente su confirmación
        Entonces mi reservación tiene el estado "VIGENTE"
        Y veo el mensaje "El periodo de cancelación ha concluido."

        Ejemplos:
            | minutos |
            | 60      |
            | 30      |

    Escenario: CA-10 Impedir cancelar nuevamente una reservación cancelada
        Dado que tengo una reservación cancelada de la sala "Sala A" mañana de 10:00 a 11:00
        Cuando abro mi lista de reservaciones
        Entonces no aparece la opción para cancelar mi reservación
        Cuando intento cancelarla abriendo directamente su confirmación
        Entonces mi reservación tiene el estado "CANCELADA"
        Y la fecha de cancelación de mi reservación no cambia
        Y veo el mensaje "La reservación ya fue cancelada."

    Escenario: CA-11 Mantener la trazabilidad de la cancelación
        Dado que tengo una reservación vigente de la sala "Sala A" mañana de 10:00 a 11:00
        Y que cancelé esa reservación desde mi lista
        Cuando abro mi lista de reservaciones
        Entonces en mi lista aparece la reservación de "Sala A" de 10:00 a 11:00 con estado "CANCELADA"
        Y en mi lista aparece la fecha y hora en que la cancelé
