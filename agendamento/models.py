from django.db import models

class Agendamento(models.Model):

    servico = models.ForeignKey('servico.Servico', on_delete=models.CASCADE)
    cliente = models.ForeignKey('cliente.Cliente', on_delete=models.CASCADE)
    funcionario = models.ForeignKey('funcionario.Funcionario', on_delete=models.CASCADE)
    data = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        return f'{self.servico} - {self.cliente} - {self.funcionario} - {self.data} - {self.hora}'
    
    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'