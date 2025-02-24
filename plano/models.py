from django.db import models

class Plano(models.Model):

    nome = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)
    valor = models.FloatField()
    duracao_em_dias = models.IntegerField()
    quantidade_empresas = models.IntegerField()
    quantidade_funcionarios = models.IntegerField()

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'