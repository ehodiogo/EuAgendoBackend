from django.db import models

class Pagamento(models.Model):

    valor = models.FloatField()
    data = models.DateField()
    status = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    plano = models.ForeignKey('plano.Plano', on_delete=models.CASCADE)
    empresa = models.ForeignKey('empresa.Empresa', on_delete=models.CASCADE)

    def __str__(self):
        return self.valor
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'