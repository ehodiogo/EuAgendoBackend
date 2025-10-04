from django.db import models
from django.contrib.auth.models import User

class Locacao(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    duracao = models.CharField(max_length=100, null=True, blank=True, help_text="Em minutos")
    preco = models.DecimalField(max_digits=5, decimal_places=2)

    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locacoes_criadas')

    pontos_resgate = models.IntegerField(blank=True, null=True)
    pontos_gerados = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Locação'
        verbose_name_plural = 'Locações'