from django.db import models
from django.contrib.auth.models import User
from django.db.models import TextChoices

class TipoPagamento(TextChoices):
    CARTAO_CREDITO = 'cartao_credito', 'Cartão de Crédito'
    CARTAO_DEBITO = 'cartao_debito', 'Cartão de Débito'
    PIX = 'pix', 'PIX'

class StatusPagamento(TextChoices):
    PENDENTE = 'Pendente', 'Pendente'
    PAGO = 'Pago', 'Pago'
    CANCELADO = 'Cancelado', 'Cancelado'

class Pagamento(models.Model):

    valor = models.FloatField()
    data = models.DateField()
    status = models.CharField(max_length=255, choices=StatusPagamento.choices)
    tipo = models.CharField(max_length=255, choices=TipoPagamento.choices)
    plano = models.ForeignKey('plano.Plano', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    hash_mercadopago = models.CharField(max_length=255, null=True, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return str(self.valor) + ' - ' + self.tipo
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'