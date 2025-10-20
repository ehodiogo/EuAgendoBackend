from django.db import models
import uuid

from empresa.models import Empresa


class Cliente(models.Model):

    nome = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    telefone = models.CharField(max_length=100)
    identificador = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def save(self, *args, **kwargs):
        if not self.identificador:
            self.identificador = uuid.uuid4().hex[:20].upper()
        super().save(*args, **kwargs)

class PontoClienteEmpresa(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    pontos = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.cliente} - {self.empresa} - {self.pontos}'