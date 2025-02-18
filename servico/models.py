from django.db import models

class Servico(models.Model):

    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    duracao = models.DurationField()
    preco = models.DecimalField(max_digits=5, decimal_places=2)

    funcionarios = models.ManyToManyField('funcionario.Funcionario', related_name='servicos')

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'