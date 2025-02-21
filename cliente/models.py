from django.db import models

class Cliente(models.Model):

    nome = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    telefone = models.CharField(max_length=100)
    cpf = models.CharField(max_length=100, null=True, blank=True, unique=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'