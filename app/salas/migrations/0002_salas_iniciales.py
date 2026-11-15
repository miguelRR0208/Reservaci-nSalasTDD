from django.db import migrations

SALAS_INICIALES = [
    ('Sala A', 'Biblioteca, planta baja', 4, True),
    ('Sala B', 'Biblioteca, planta baja', 8, True),
    ('Sala C', 'Biblioteca, planta alta', 12, True),
    ('Sala de mantenimiento', 'Biblioteca, planta alta', 6, False),
]


def crear_salas(apps, schema_editor):
    Sala = apps.get_model('salas', 'Sala')
    for nombre, ubicacion, capacidad, activa in SALAS_INICIALES:
        Sala.objects.update_or_create(
            nombre=nombre,
            defaults={
                'ubicacion': ubicacion,
                'capacidad': capacidad,
                'activa': activa,
            },
        )


def borrar_salas(apps, schema_editor):
    Sala = apps.get_model('salas', 'Sala')
    nombres = [sala[0] for sala in SALAS_INICIALES]
    Sala.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('salas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_salas, borrar_salas),
    ]
