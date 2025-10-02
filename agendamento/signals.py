# agendamento/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Agendamento
from .tasks import enviar_email_agendamento, enviar_email_lembrete, enviar_email_agendamento_empresa
from datetime import datetime, timedelta
from django.utils import timezone

@receiver(post_save, sender=Agendamento)
def agendamento_criado(sender, instance, created, **kwargs):
    if created:
        enviar_email_agendamento.delay(instance.id)
        enviar_email_agendamento_empresa.delay(instance.id)

        hora_agendamento = datetime.combine(instance.data, instance.hora)
        hora_agendamento = timezone.make_aware(hora_agendamento)

        agora = timezone.now()
        diferenca_total = (hora_agendamento - agora).total_seconds() / 60

        eta_60 = hora_agendamento - timedelta(minutes=60)
        if eta_60 > agora:
            enviar_email_lembrete.apply_async(
                args=[instance.id, 60],
                eta=eta_60
            )

        eta_30 = hora_agendamento - timedelta(minutes=30)
        if eta_30 > agora:
            enviar_email_lembrete.apply_async(
                args=[instance.id, 30],
                eta=eta_30
            )
