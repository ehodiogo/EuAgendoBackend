from django.db import models
import uuid

class Agendamento(models.Model):

    identificador = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True
    )

    servico = models.ForeignKey('servico.Servico', on_delete=models.CASCADE)
    cliente = models.ForeignKey('cliente.Cliente', on_delete=models.CASCADE)
    funcionario = models.ForeignKey('funcionario.Funcionario', on_delete=models.CASCADE)
    data = models.DateField()
    hora = models.TimeField()
    is_continuacao = models.BooleanField(default=False)

    nota_avaliacao = models.IntegerField(default=0)
    descricao_avaliacao = models.TextField(default="")

    compareceu_agendamento = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.servico} - {self.cliente} - {self.funcionario} - {self.data} - {self.hora}'

    def save(self, *args, **kwargs):
        if not self.identificador:
            self.identificador = uuid.uuid4().hex[:20].upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'