# Generated by Django 5.1.5 on 2025-03-12 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagem',
            name='imagem',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]
