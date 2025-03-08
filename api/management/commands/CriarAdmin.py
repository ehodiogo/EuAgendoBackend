import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        nome = os.environ.get("DJANGO_SUPERUSER_NAME")
        senha = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")

        if not User.objects.filter(username=nome).exists():
            User.objects.create_superuser(nome, email, senha)
            print(f"Usuário {nome} criado com sucesso")
        else:
            print(f"Usuário {nome} já existe")
            