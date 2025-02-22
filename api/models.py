from django.db import models
from django.contrib.auth.models import User

User.add_to_class('empresas', models.ManyToManyField('empresa.Empresa', related_name='users'))