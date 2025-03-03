# Generated by Django 5.1.5 on 2025-03-01 16:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funcionario', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionario',
            name='criado_por',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='funcionarios_criados', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
