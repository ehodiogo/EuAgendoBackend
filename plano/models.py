from django.db import models
from django.contrib.auth.models import User

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

class PlanoUsuario(models.Model):

    plano = models.ForeignKey(Plano, on_delete=models.CASCADE)
    adquirido_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.plano.nome
    
    class Meta:
        verbose_name = 'Plano do Usuário'
        verbose_name_plural = 'Planos dos Usuários'