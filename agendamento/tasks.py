from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime
from .models import Agendamento


@shared_task
def enviar_email_agendamento(agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)

    assunto = "✅ Agendamento Confirmado"
    mensagem_txt = (
        f"Olá {agendamento.cliente},\n\n"
        f"Seu agendamento para *{agendamento.servico}* foi confirmado!\n"
        f"📅 Data: {agendamento.data}\n"
        f"⏰ Hora: {agendamento.hora}\n\n"
        "Obrigado por escolher nossos serviços!"
    )

    mensagem_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color:#2c7be5;">Agendamento Confirmado</h2>
        <p>Olá <b>{agendamento.cliente}</b>,</p>
        <p>Seu agendamento foi confirmado com sucesso:</p>
        <ul>
          <li><b>Serviço:</b> {agendamento.servico}</li>
          <li><b>Data:</b> {agendamento.data}</li>
          <li><b>Hora:</b> {agendamento.hora}</li>
        </ul>
        <p style="margin-top:20px;">✔ Obrigado por escolher nossos serviços!</p>
      </body>
    </html>
    """

    send_mail(
        assunto,
        mensagem_txt,
        "vemagendar@gmail.com",
        [agendamento.cliente.email],
        html_message=mensagem_html,
    )


@shared_task
def enviar_email_lembrete(agendamento_id, minutos):
    agendamento = Agendamento.objects.get(id=agendamento_id)

    agora = timezone.now()
    agendamento_datetime = timezone.make_aware(
        datetime.combine(agendamento.data, agendamento.hora)
    )
    diferenca = (agendamento_datetime - agora).total_seconds() / 60

    # Evita enviar lembrete se já estiver muito próximo
    if minutos == 60 and diferenca < 60:
        return
    if minutos == 30 and diferenca < 30:
        return

    assunto = f"⏰ Lembrete: seu agendamento é em {minutos} minutos"
    mensagem_txt = (
        f"Olá {agendamento.cliente},\n\n"
        f"Este é um lembrete de que seu agendamento para *{agendamento.servico}* "
        f"acontece em {minutos} minutos.\n"
        f"📅 Data: {agendamento.data}\n"
        f"⏰ Hora: {agendamento.hora}\n\n"
        "Estamos te esperando!"
    )

    mensagem_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color:#f59f00;">Lembrete de Agendamento</h2>
        <p>Olá <b>{agendamento.cliente}</b>,</p>
        <p>Seu agendamento acontece em <b>{minutos} minutos</b>:</p>
        <ul>
          <li><b>Serviço:</b> {agendamento.servico}</li>
          <li><b>Data:</b> {agendamento.data}</li>
          <li><b>Hora:</b> {agendamento.hora}</li>
        </ul>
        <p style="margin-top:20px;">Estamos te esperando! 🚀</p>
      </body>
    </html>
    """

    send_mail(
        assunto,
        mensagem_txt,
        "vemagendar@gmail.com",
        [agendamento.cliente.email],
        html_message=mensagem_html,
    )
