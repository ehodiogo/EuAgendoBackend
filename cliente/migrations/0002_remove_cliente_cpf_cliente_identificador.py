from django.db import migrations, models
from cliente.models import Cliente
import uuid

def gerar_identificador_unico(apps, schema_editor):
    Cliente = apps.get_model('cliente', 'Cliente')
    for cliente in Cliente.objects.all():
        cliente.identificador = str(uuid.uuid4())[:20]
        cliente.save(update_fields=['identificador'])

class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cliente',
            name='cpf',
        ),
        migrations.AddField(
            model_name='cliente',
            name='identificador',
            field=models.CharField(blank=True, editable=False, max_length=20, unique=True),
        ),
        migrations.RunPython(gerar_identificador_unico, reverse_code=migrations.RunPython.noop),
    ]
