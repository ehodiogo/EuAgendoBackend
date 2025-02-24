from django.db import models
from django.contrib.auth.models import User

class Pagamento(models.Model):

    valor = models.FloatField()
    data = models.DateField()
    status = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    plano = models.ForeignKey('plano.Plano', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    hash_mercadopago = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.valor
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'