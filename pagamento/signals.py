from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pagamento
from .tasks import verificar_pagamento_com_retries

@receiver(post_save, sender=Pagamento)
def iniciar_verificacao_pagamento(sender, instance, created, **kwargs):
    if created:
        verificar_pagamento_com_retries.delay(instance.id)