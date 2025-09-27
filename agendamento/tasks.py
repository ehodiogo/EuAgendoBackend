# agendamento/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Agendamento

@shared_task
def enviar_email_agendamento(agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)
    assunto = "Agendamento Confirmado"
    mensagem = f"Olá {agendamento.cliente}, seu agendamento para {agendamento.servico} foi confirmado em {agendamento.data} às {agendamento.hora}."
    send_mail(assunto, mensagem, None, [agendamento.cliente.email])

@shared_task
def enviar_email_lembrete(agendamento_id, minutos):
    agendamento = Agendamento.objects.get(id=agendamento_id)
    assunto = f"Lembrete de Agendamento ({minutos} minutos)"
    mensagem = f"Olá {agendamento.cliente}, seu agendamento para {agendamento.servico} é em {minutos} minutos ({agendamento.data} às {agendamento.hora})."
    send_mail(assunto, mensagem, None, [agendamento.cliente.email])