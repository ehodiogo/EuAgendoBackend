from django.core.mail import EmailMessage
from celery import shared_task

EMAIL_REMETENTE="vemagendar@gmail.com"
EMAIL_DESTINATARIO_CONTATO="vemagendar@gmail.com"

@shared_task
def enviar_email_contato_task(nome, email, mensagem):
    assunto = f"📧 Nova Mensagem de Contato de: {nome}"

    mensagem_txt = (
        f"Você recebeu uma nova mensagem através do formulário de contato.\n\n"
        f"Nome: {nome}\n"
        f"E-mail: {email}\n"
        f"----------------------------------------\n"
        f"Mensagem:\n{mensagem}\n"
    )

    mensagem_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; background:#f9f9f9; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
          <h2 style="color:#2c7be5;">Nova Mensagem de Contato</h2>
          <p>Você recebeu uma nova mensagem através do formulário de contato:</p>
          <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
          <p><strong>Nome:</strong> {nome}</p>
          <p><strong>E-mail:</strong> <a href="mailto:{email}" style="color:#2c7be5;">{email}</a></p>
          <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
          <h4 style="color:#555;">Conteúdo da Mensagem:</h4>
          <div style="padding: 15px; background: #f0f0f0; border-radius: 8px; white-space: pre-wrap;">{mensagem}</div>
          <p style="margin-top: 30px; font-size: 0.9em; color: #777;">
            Esta mensagem foi enviada automaticamente pelo formulário de contato.
          </p>
        </div>
      </body>
    </html>
    """

    email_msg = EmailMessage(
        subject=assunto,
        body=mensagem_txt,
        from_email=EMAIL_REMETENTE,
        to=[EMAIL_DESTINATARIO_CONTATO],
        reply_to=[email],
    )
    email_msg.content_subtype = "html"
    email_msg.body = mensagem_html

    email_msg.send(fail_silently=False)
