"""Resume el reporte HTML de JMeter y lo compara con los criterios.

Uso: python rendimiento/resumir_resultados.py [statistics.json]
"""

import json
import sys
from pathlib import Path

ESTADISTICAS = Path(__file__).resolve().parent.parent / 'reportes' / \
    'jmeter' / 'html' / 'statistics.json'

# escenario: (petición que se evalúa, p95 máximo en ms)
CRITERIOS = {
    'PERF-01': ('PERF-01 Consultar mis reservaciones', 1500),
    'PERF-02': ('PERF-02 Registrar reservación', 2000),
}
ERROR_MAXIMO = 1.0

COLUMNAS = '{:<38} {:>8} {:>9} {:>8} {:>8} {:>8} {:>11} {:>9}'


def fila(nombre, datos):
    return COLUMNAS.format(
        nombre,
        datos['sampleCount'],
        f"{datos['meanResTime']:.1f}",
        f"{datos['pct1ResTime']:.1f}",
        f"{datos['pct2ResTime']:.1f}",
        f"{datos['maxResTime']:.0f}",
        f"{datos['throughput']:.2f}",
        f"{datos['errorPct']:.2f}",
    )


def errores_del_escenario(escenario, estadisticas):
    muestras = errores = 0
    for nombre, datos in estadisticas.items():
        if nombre.startswith(escenario):
            muestras += datos['sampleCount']
            errores += datos['errorCount']
    return 100 * errores / muestras


def evaluar(escenario, estadisticas):
    peticion, p95_maximo = CRITERIOS[escenario]
    p95 = estadisticas[peticion]['pct2ResTime']
    error = errores_del_escenario(escenario, estadisticas)
    cumple = error < ERROR_MAXIMO and p95 <= p95_maximo
    return (
        f'{escenario}: errores {error:.2f}% (< {ERROR_MAXIMO}%), '
        f'p95 de "{peticion}" {p95:.1f} ms (<= {p95_maximo} ms) -> '
        f'{"CUMPLE" if cumple else "NO CUMPLE"}'
    )


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else ESTADISTICAS
    with open(ruta, encoding='utf-8') as archivo:
        estadisticas = json.load(archivo)
    total = estadisticas.pop('Total')
    print('Tiempos en ms, throughput en peticiones por segundo\n')
    print(COLUMNAS.format('Petición', 'Muestras', 'Promedio', 'p90',
                          'p95', 'Máximo', 'Throughput', '% Error'))
    for nombre in sorted(estadisticas):
        print(fila(nombre, estadisticas[nombre]))
    print(fila('Total', total))
    print()
    for escenario in CRITERIOS:
        print(evaluar(escenario, estadisticas))
    print(f'PERF-03: errores '
          f'{errores_del_escenario("PERF-03", estadisticas):.2f}% '
          f'(el resultado en la base se revisa con revisar_traslapes.py)')


if __name__ == '__main__':
    main()
