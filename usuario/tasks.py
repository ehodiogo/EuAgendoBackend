from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

EMAIL_REMETENTE = "vemagendar@gmail.com"
SITE_URL = "https://vemagendar.com.br"

def rodape_padrao():
    return f"""
        <hr style="margin-top:30px; border:0; border-top:1px solid #ddd;">
        <p style="font-size:13px; color:#777; margin-top:15px;">
            Equipe <b>VemAgendar</b><br>
            ✉ {EMAIL_REMETENTE}<br>
            🌐 <a href="{SITE_URL}" style="color:#2c7be5;">{SITE_URL}</a>
        </p>
    """

@shared_task
def enviar_email_confirmacao_cadastro(user_id):
    try:
        user = User.objects.get(id=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirm_url = f"{SITE_URL}/confirmar-conta/?uid={uid}&token={token}"

        assunto = "🎉 Confirme seu cadastro no VemAgendar"
        mensagem_txt = (
            f"Olá {user.first_name or user.username},\n\n"
            f"Bem-vindo ao VemAgendar! 🎉\n\n"
            f"Para ativar sua conta, confirme seu e-mail clicando no link abaixo:\n"
            f"{confirm_url}\n\n"
            f"Se você não criou esta conta, ignore este e-mail.\n\n"
            f"Equipe VemAgendar 🚀"
        )

        mensagem_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color:#333; background:#f9f9f9; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
              <h2 style="color:#2c7be5;">🎉 Bem-vindo ao VemAgendar!</h2>
              <p>Olá <b>{user.first_name or user.username}</b>,</p>
              <p>Seu cadastro foi realizado com sucesso! Para começar a usar, confirme seu e-mail clicando no botão abaixo:</p>
              <div style="margin-top:25px; text-align:center;">
                <a href="{confirm_url}" style="background:#2c7be5; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
                  ✅ Confirmar E-mail
                </a>
              </div>
              <p style="margin-top:20px;">Se você não criou esta conta, ignore este e-mail.</p>
              {rodape_padrao()}
            </div>
          </body>
        </html>
        """

        send_mail(
            assunto,
            mensagem_txt,
            EMAIL_REMETENTE,
            [user.email],
            html_message=mensagem_html,
            fail_silently=False,
        )

    except Exception as e:
        print(f"Erro ao enviar e-mail de confirmação: {e}")
