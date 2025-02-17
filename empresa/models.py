from django.db import models

class Empresa(models.Model):

    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=100)
    endereco = models.CharField(max_length=100)
    telefone = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)

    servicos = models.ManyToManyField('servico.Servico', related_name='servicos')

    horario_abertura_dia_semana = models.TimeField()
    horario_fechamento_dia_semana = models.TimeField()

    horario_abertura_fim_de_semana = models.TimeField()
    horario_fechamento_fim_de_semana = models.TimeField()

    abre_sabado = models.BooleanField()
    abre_domingo = models.BooleanField()

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'