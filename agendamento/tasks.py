from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime
from .models import Agendamento

EMAIL_REMETENTE = "vemagendar@gmail.com"
SITE_URL = "https://vemagendar.com.br"

def formatar_data_br(data):
    return data.strftime("%d/%m/%Y")


def formatar_hora_br(hora):
    return hora.strftime("%H:%M")


def gerar_link_cancelamento(agendamento):
    return f"{SITE_URL}/cancelar/{agendamento.identificador}/"


def rodape_empresa(empresa):
    return f"""
          <hr style="margin-top:30px; border:0; border-top:1px solid #ddd;">
          <p style="font-size:13px; color:#777; margin-top:15px;">
            <b>{empresa.nome if empresa else "Empresa não informada"}</b><br>
            {empresa.endereco_completo() if empresa else ""}<br>
            📞 {empresa.telefone if empresa else ""}<br>
            ✉ {empresa.email if empresa else ""}<br>
            🌐 <a href="{SITE_URL}" style="color:#2c7be5;">{SITE_URL}</a>
          </p>
    """

@shared_task
def enviar_email_agendamento(agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)
    empresa = agendamento.servico.servicos.first()

    assunto = "🎉 Seu agendamento foi confirmado!"
    mensagem_txt = (
        f"Olá {agendamento.cliente},\n\n"
        f"Temos uma ótima notícia! Seu agendamento para *{agendamento.servico}* foi confirmado.\n\n"
        f"📅 Data: {formatar_data_br(agendamento.data)}\n"
        f"⏰ Hora: {formatar_hora_br(agendamento.hora)}\n\n"
        f"Caso precise cancelar, use o link abaixo:\n{gerar_link_cancelamento(agendamento)}\n\n"
        f"Equipe {empresa.nome if empresa else 'da empresa'} agradece a sua confiança! 🙌"
    )

    mensagem_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; background:#f9f9f9; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
          <h2 style="color:#2c7be5;">🎉 Agendamento Confirmado</h2>
          <p>Olá <b>{agendamento.cliente}</b>,</p>
          <p>Seu agendamento foi confirmado com sucesso! Aqui estão os detalhes:</p>
          <table style="margin-top:15px;">
            <tr><td>📌 <b>Serviço:</b></td><td>{agendamento.servico}</td></tr>
            <tr><td>📅 <b>Data:</b></td><td>{formatar_data_br(agendamento.data)}</td></tr>
            <tr><td>⏰ <b>Hora:</b></td><td>{formatar_hora_br(agendamento.hora)}</td></tr>
          </table>
          <div style="margin-top:25px; text-align:center;">
            <a href="{gerar_link_cancelamento(agendamento)}" style="background:#d9534f; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
              ❌ Cancelar Agendamento
            </a>
          </div>
          <p style="margin-top:20px; text-align:center;">Aguardamos você com alegria! 🙌</p>
          {rodape_empresa(empresa)}
        </div>
      </body>
    </html>
    """

    send_mail(
        assunto,
        mensagem_txt,
        EMAIL_REMETENTE,
        [agendamento.cliente.email],
        html_message=mensagem_html,
    )

@shared_task
def enviar_email_lembrete(agendamento_id, minutos):
    agendamento = Agendamento.objects.get(id=agendamento_id)
    empresa = agendamento.servico.empresas.first()

    agora = timezone.now()
    agendamento_datetime = timezone.make_aware(
        datetime.combine(agendamento.data, agendamento.hora)
    )
    diferenca = (agendamento_datetime - agora).total_seconds() / 60
    if diferenca <= 0:
        return

    assunto = f"⏰ Lembrete: seu agendamento é em {minutos} minutos"

    mensagem_txt = (
        f"Olá {agendamento.cliente},\n\n"
        f"Está chegando a hora! Seu agendamento para *{agendamento.servico}* "
        f"acontece em {minutos} minutos.\n\n"
        f"📅 {formatar_data_br(agendamento.data)} - ⏰ {formatar_hora_br(agendamento.hora)}\n\n"
        f"Estamos te esperando! 🚀\n\n"
        f"Caso precise cancelar, use o link abaixo:\n{gerar_link_cancelamento(agendamento)}"
    )

    mensagem_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; background:#f9f9f9; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
          <h2 style="color:#f59f00;">⏰ Está quase na hora!</h2>
          <p>Olá <b>{agendamento.cliente}</b>,</p>
          <p>Este é um lembrete: seu agendamento acontece em <b>{minutos} minutos</b>!</p>
          <table style="margin-top:15px;">
            <tr><td>📌 <b>Serviço:</b></td><td>{agendamento.servico}</td></tr>
            <tr><td>📅 <b>Data:</b></td><td>{formatar_data_br(agendamento.data)}</td></tr>
            <tr><td>⏰ <b>Hora:</b></td><td>{formatar_hora_br(agendamento.hora)}</td></tr>
          </table>
          <div style="margin-top:25px; text-align:center;">
            <a href="{gerar_link_cancelamento(agendamento)}" style="background:#d9534f; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
              ❌ Cancelar Agendamento
            </a>
          </div>
          <p style="margin-top:20px; text-align:center;">Estamos te esperando com alegria! 🚀</p>
          {rodape_empresa(empresa)}
        </div>
      </body>
    </html>
    """

    send_mail(
        assunto,
        mensagem_txt,
        EMAIL_REMETENTE,
        [agendamento.cliente.email],
        html_message=mensagem_html,
    )
