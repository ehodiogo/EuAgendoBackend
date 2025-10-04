from django.db import models
import uuid

class Agendamento(models.Model):

    identificador = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True
    )

    servico = models.ForeignKey('servico.Servico', on_delete=models.CASCADE, blank=True, null=True) # pode agendar servico de um funcionario
    locacao = models.ForeignKey('locacao.Locacao', on_delete=models.CASCADE, blank=True, null=True) # pode agendar uma locacao tipo quadra/vaga/sala
    cliente = models.ForeignKey('cliente.Cliente', on_delete=models.CASCADE)
    funcionario = models.ForeignKey('funcionario.Funcionario', on_delete=models.CASCADE, blank=True, null=True)
    data = models.DateField()
    hora = models.TimeField()
    is_continuacao = models.BooleanField(default=False)

    nota_avaliacao = models.IntegerField(default=0)
    descricao_avaliacao = models.TextField(default="")

    compareceu_agendamento = models.BooleanField(default=False)

    def __str__(self):
        servico_nome = self.servico.nome if self.servico else ""
        locacao_nome = self.locacao.nome if self.locacao else ""
        funcionario_nome = self.funcionario.nome if self.funcionario else ""
        return f'{servico_nome or locacao_nome} - {self.cliente} - {funcionario_nome} - {self.data} {self.hora}'

    def save(self, *args, **kwargs):
        if not self.identificador:
            self.identificador = uuid.uuid4().hex[:20].upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'