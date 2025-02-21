from django.db import models

class Plano(models.Model):

    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    valor = models.FloatField()
    duracao = models.IntegerField()
    quantidade_servicos = models.IntegerField()
    quantidade_funcionarios = models.IntegerField()
    quantidade_clientes = models.IntegerField()

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'