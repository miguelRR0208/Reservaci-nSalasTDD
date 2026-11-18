"""Corre todas las pruebas y revisiones y guarda cada salida en reportes/.

Uso, desde la raíz del repositorio y con el entorno virtual activo:
    python generar_reportes.py
    python generar_reportes.py --sin-behave   (se salta las de Selenium)
"""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
APP = RAIZ / 'app'
REPORTES = RAIZ / 'reportes'
PY = sys.executable
RADON = ['-e', '*/migrations/*', '-i', '.venv']

# Cada paso: archivo de salida, carpeta donde se corre y comandos.
# Cada comando: (texto que se muestra en el reporte, comando real).
PASOS = [
    ('pruebas_unitarias.txt', APP, [
        ('coverage run manage.py test -v 2',
         [PY, '-m', 'coverage', 'run', 'manage.py', 'test', '-v', '2']),
    ]),
    ('cobertura.txt', APP, [
        ('coverage report -m', [PY, '-m', 'coverage', 'report', '-m']),
        ('coverage html', [PY, '-m', 'coverage', 'html']),
    ]),
    ('flake8.txt', RAIZ, [
        ('flake8 --count .', [PY, '-m', 'flake8', '--count', '.']),
    ]),
    ('radon.txt', RAIZ, [
        ('radon cc . -s -a -e "*/migrations/*" -i ".venv"',
         [PY, '-m', 'radon', 'cc', '.', '-s', '-a'] + RADON),
        ('radon cc . -s -n C -e "*/migrations/*" -i ".venv"  '
         '(solo lo que pase de 10; vacío = ninguno)',
         [PY, '-m', 'radon', 'cc', '.', '-s', '-n', 'C'] + RADON),
    ]),
    ('behave.txt', RAIZ / 'pruebas_aceptacion', [
        ('python ../app/manage.py behave',
         [PY, str(APP / 'manage.py'), 'behave']),
    ]),
]


def ejecutar(archivo, carpeta, comandos):
    entorno = dict(os.environ, PYTHONIOENCODING='utf-8')
    todo_bien = True
    with open(REPORTES / archivo, 'w', encoding='utf-8') as salida:
        for texto, comando in comandos:
            salida.write(f'$ {texto}\n\n')
            salida.flush()
            resultado = subprocess.run(
                comando, cwd=carpeta, env=entorno,
                stdout=salida, stderr=subprocess.STDOUT,
            )
            salida.write('\n')
            todo_bien = todo_bien and resultado.returncode == 0
    return todo_bien


def elegir_pasos(argumentos):
    if '--sin-behave' in argumentos:
        return [paso for paso in PASOS if paso[0] != 'behave.txt']
    return PASOS


def mostrar_resumen(resultados):
    print()
    for archivo, bien in resultados:
        print(f'{"OK   " if bien else "FALLÓ"} reportes/{archivo}')


def main():
    REPORTES.mkdir(exist_ok=True)
    resultados = []
    for archivo, carpeta, comandos in elegir_pasos(sys.argv):
        print(f'Generando reportes/{archivo} ...', flush=True)
        resultados.append((archivo, ejecutar(archivo, carpeta, comandos)))
    # coverage deja un .gitignore en la carpeta del HTML que impide
    # subirla al repositorio.
    (REPORTES / 'cobertura' / '.gitignore').unlink(missing_ok=True)
    mostrar_resumen(resultados)
    sys.exit(0 if all(bien for _, bien in resultados) else 1)


if __name__ == '__main__':
    main()
