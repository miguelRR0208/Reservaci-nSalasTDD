"""Revisa la base de datos después de las pruebas de rendimiento.

Uso: python rendimiento/revisar_traslapes.py [ruta de la base]
"""

import sqlite3
import sys
from pathlib import Path

BASE_POR_DEFECTO = Path(__file__).resolve().parent.parent / 'app' / \
    'db.sqlite3'

TRASLAPES = """
SELECT a.id, b.id, s.nombre, a.fecha,
       a.hora_inicio, a.hora_fin, b.hora_inicio, b.hora_fin
FROM reservaciones_reservacion a
JOIN reservaciones_reservacion b
  ON a.sala_id = b.sala_id
 AND a.fecha = b.fecha
 AND a.id < b.id
 AND a.hora_inicio < b.hora_fin
 AND b.hora_inicio < a.hora_fin
JOIN salas_sala s ON s.id = a.sala_id
WHERE a.estado = 'VIGENTE' AND b.estado = 'VIGENTE'
"""

POR_PROPOSITO = """
SELECT proposito, estado, COUNT(*)
FROM reservaciones_reservacion
GROUP BY proposito, estado
ORDER BY proposito
"""

CONFLICTOS = """
SELECT s.nombre, r.fecha, r.hora_inicio, r.hora_fin, COUNT(*),
       GROUP_CONCAT(u.username)
FROM reservaciones_reservacion r
JOIN salas_sala s ON s.id = r.sala_id
JOIN auth_user u ON u.id = r.usuario_id
WHERE r.proposito = 'Prueba de concurrencia PERF-03'
  AND r.estado = 'VIGENTE'
GROUP BY s.nombre, r.fecha, r.hora_inicio, r.hora_fin
ORDER BY r.hora_inicio
"""


def mostrar(titulo, consulta, conexion):
    print(f'-- {titulo}')
    print(consulta.strip())
    filas = conexion.execute(consulta).fetchall()
    for fila in filas:
        print(' | '.join(str(valor) for valor in fila))
    print(f'({len(filas)} filas)\n')
    return filas


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else BASE_POR_DEFECTO
    with sqlite3.connect(ruta) as conexion:
        mostrar('Reservaciones por propósito y estado', POR_PROPOSITO,
                conexion)
        mostrar('Reservaciones vigentes de PERF-03 por horario', CONFLICTOS,
                conexion)
        traslapes = mostrar('Reservaciones vigentes traslapadas', TRASLAPES,
                            conexion)
    print('Sin traslapes' if not traslapes else 'HAY TRASLAPES')


if __name__ == '__main__':
    main()
