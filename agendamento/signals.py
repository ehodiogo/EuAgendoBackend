# agendamento/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Agendamento
from .tasks import enviar_email_agendamento, enviar_email_lembrete
from datetime import datetime, timedelta
from django.utils import timezone

@receiver(post_save, sender=Agendamento)
def agendamento_criado(sender, instance, created, **kwargs):
    if created:
        print("Agendamento criado")
        enviar_email_agendamento.delay(instance.id)

        hora_agendamento = datetime.combine(instance.data, instance.hora)
        hora_agendamento = timezone.make_aware(hora_agendamento)

        enviar_email_lembrete.apply_async(
            args=[instance.id, 60],
            eta=hora_agendamento - timedelta(hours=1)
        )
        enviar_email_lembrete.apply_async(
            args=[instance.id, 30],
            eta=hora_agendamento - timedelta(minutes=30)
        )
