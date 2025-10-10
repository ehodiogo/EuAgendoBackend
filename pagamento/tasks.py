from celery import shared_task
from decouple import config
import mercadopago
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMessage, send_mail
from .models import Pagamento, StatusPagamento, TipoPagamento
from plano.models import PlanoUsuario, Plano
from io import BytesIO
from xhtml2pdf import pisa

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

def gerar_nota_pdf_profissional(pagamento):
    logo_url = "https://eu-agendo.s3.us-east-1.amazonaws.com/imagens/logo_VemAgendar_vemagendargmail.com.png"

    html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; color: #333; }}
          .container {{ width: 700px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
          .header {{ text-align: center; margin-bottom: 20px; }}
          .header img {{ width: 180px; }}
          .title {{ text-align: center; color: #2c7be5; font-size: 22px; margin-bottom: 20px; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ padding: 8px 10px; border: 1px solid #ddd; text-align: left; }}
          th {{ background-color: #f2f2f2; }}
          .footer {{ text-align: center; font-size: 12px; color: #777; margin-top: 20px; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <img src="{logo_url}" alt="VemAgendar Logo"/>
          </div>
          <div class="title">Nota Fiscal de Pagamento</div>

          <table>
            <tr><th>Usuário</th><td>{pagamento.usuario.first_name or pagamento.usuario.email}</td></tr>
            <tr><th>Plano</th><td>{pagamento.plano.nome}</td></tr>
            <tr><th>Valor</th><td>R$ {pagamento.valor:.2f}</td></tr>
            <tr><th>Data do Pagamento</th><td>{pagamento.updated_at.strftime('%d/%m/%Y %H:%M')}</td></tr>
            <tr><th>Método de Pagamento</th><td>{pagamento.tipo}</td></tr>
            <tr><th>Status</th><td>{pagamento.status}</td></tr>
          </table>

          <p class="footer">
            Esta nota fiscal é gerada automaticamente pelo sistema <b>VemAgendar</b>.<br>
            🌐 <a href="{SITE_URL}">{SITE_URL}</a>
          </p>
        </div>
      </body>
    </html>
    """
    pdf_file = BytesIO()
    pisa.CreatePDF(html, dest=pdf_file)
    pdf_file.seek(0)
    return pdf_file

@shared_task
def cancelar_plano_usuario(plano_usuario_id):
    from plano.models import PlanoUsuario

    try:
        user_plan = PlanoUsuario.objects.get(id=plano_usuario_id)
        user_plan.active = False
        user_plan.changed_at = timezone.now()
        user_plan.save()
        print(f"Plano do usuário {user_plan.usuario.email} foi cancelado após 30 dias.")
    except PlanoUsuario.DoesNotExist:
        print(f"PlanoUsuario {plano_usuario_id} não encontrado.")

@shared_task(bind=True, max_retries=20)
def verificar_pagamento_com_retries(self, pagamento_id):
    try:
        pagamento = Pagamento.objects.get(id=pagamento_id)

        if config("DEBUG", default=False, cast=bool):
            sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_TEST"))
        else:
            sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_PRD"))

        payment = sdk.payment().search({"external_reference": pagamento.hash_mercadopago})
        results = payment.get("response", {}).get("results", [])

        if not results:
            raise Exception("Nenhum resultado encontrado no Mercado Pago")

        status_mp = results[0]["status"]
        payment_method = results[0]["payment_method_id"]

        if status_mp == "approved":
            pagamento.status = StatusPagamento.PAGO
            pagamento.verified = True
            pagamento.updated_at = timezone.now()

            if payment_method == "credit_card":
                pagamento.payment_method = TipoPagamento.CARTAO_CREDITO
            elif payment_method == "debit_card":
                pagamento.payment_method = TipoPagamento.CARTAO_DEBITO
            else:
                pagamento.payment_method = TipoPagamento.PIX

            pagamento.save()

            user = pagamento.usuario
            user_plan = PlanoUsuario.objects.filter(usuario=user).first()
            if not user_plan:
                user_plan = PlanoUsuario.objects.create(
                    usuario=user,
                    plano=Plano.objects.get(nome="Free Trial"),
                    expira_em=timezone.now() + timedelta(days=30),
                    active=True,
                    changed_at=timezone.now()
                )

            user_plan.plano = pagamento.plano
            user_plan.active = True
            user_plan.changed_at = timezone.now()
            user_plan.expira_em = timezone.now() + timedelta(days=30)
            user_plan.save()

            pdf = gerar_nota_pdf_profissional(pagamento)

            cancelar_plano_usuario.apply_async(
                args=[user_plan.id],
                eta=timezone.now() + timedelta(days=30)
            )

            assunto = "✅ Pagamento Apro vado e Nota Fiscal"
            mensagem_txt = (
                f"Olá {user.first_name or user.email},\n\n"
                f"Seu pagamento do plano {pagamento.plano.nome} foi aprovado com sucesso! 🎉\n"
                f"Agora você já pode aproveitar todos os recursos do seu plano.\n\n"
                f"Acesse sua conta: {SITE_URL}\n\n"
                "Equipe VemAgendar 🚀"
            )
            mensagem_html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color:#333; background:#f9f9f9; padding:20px;">
                <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
                  <h2 style="color:#28a745;">✅ Pagamento Aprovado</h2>
                  <p>Olá <b>{user.first_name or user.email}</b>,</p>
                  <p>Seu pagamento do plano <b>{pagamento.plano.nome}</b> foi aprovado com sucesso! 🎉</p>
                  <p>Agora você já pode aproveitar todos os recursos do seu plano.</p>
                  <div style="margin-top:25px; text-align:center;">
                    <a href="{SITE_URL}" style="background:#2c7be5; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
                      🚀 Acessar Minha Conta
                    </a>
                  </div>
                  {rodape_padrao()}
                </div>
              </body>
            </html>
            """
            email = EmailMessage(
                subject=assunto,
                body=mensagem_html,
                from_email=EMAIL_REMETENTE,
                to=[user.email],
            )
            email.content_subtype = "html"
            email.attach(f"nota_fiscal_{pagamento.id}.pdf", pdf.read(), "application/pdf")
            email.send()

        elif status_mp == "rejected":
            pagamento.status = StatusPagamento.REJEITADO
            pagamento.updated_at = timezone.now()
            pagamento.save()

            # Email rejeitado
            assunto = "❌ Pagamento Rejeitado"
            mensagem_txt = (
                f"Olá {pagamento.usuario.first_name or pagamento.usuario.email},\n\n"
                f"Infelizmente, seu pagamento do plano {pagamento.plano.nome} foi rejeitado.\n"
                f"Tente novamente ou utilize outro método de pagamento.\n\n"
                f"Acesse sua conta: {SITE_URL}\n\n"
                "Equipe VemAgendar 💙"
            )
            mensagem_html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color:#333; background:#f9f9f9; padding:20px;">
                <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
                  <h2 style="color:#dc3545;">❌ Pagamento Rejeitado</h2>
                  <p>Olá <b>{pagamento.usuario.first_name or pagamento.usuario.email}</b>,</p>
                  <p>Infelizmente, seu pagamento do plano <b>{pagamento.plano.nome}</b> foi rejeitado.</p>
                  <p>Tente novamente ou utilize outro método de pagamento.</p>
                  <div style="margin-top:25px; text-align:center;">
                    <a href="{SITE_URL}" style="background:#2c7be5; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
                      💳 Tentar Novamente
                    </a>
                  </div>
                  {rodape_padrao()}
                </div>
              </body>
            </html>
            """
            send_mail(assunto, mensagem_txt, EMAIL_REMETENTE, [pagamento.usuario.email], html_message=mensagem_html)

        else:
            raise self.retry(countdown=90)

    except self.MaxRetriesExceededError:
        assunto = "⏳ Pagamento Pendente"
        mensagem_txt = (
            f"Olá {pagamento.usuario.first_name or pagamento.usuario.email},\n\n"
            f"Seu pagamento do plano {pagamento.plano.nome} ainda não foi aprovado nem rejeitado após várias tentativas.\n"
            f"Por favor, verifique no Mercado Pago se há alguma pendência.\n\n"
            f"Acesse sua conta: {SITE_URL}\n\n"
            "Equipe VemAgendar 💙"
        )
        mensagem_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color:#333; background:#f9f9f9; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
              <h2 style="color:#f59f00;">⏳ Pagamento Pendente</h2>
              <p>Olá <b>{pagamento.usuario.first_name or pagamento.usuario.email}</b>,</p>
              <p>Seu pagamento do plano <b>{pagamento.plano.nome}</b> ainda não foi aprovado nem rejeitado após várias tentativas.</p>
              <p>Por favor, verifique no Mercado Pago se há alguma pendência.</p>
              <div style="margin-top:25px; text-align:center;">
                <a href="{SITE_URL}" style="background:#2c7be5; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
                  🔍 Verificar Pagamento
                </a>
              </div>
              {rodape_padrao()}
            </div>
          </body>
        </html>
        """
        send_mail(assunto, mensagem_txt, EMAIL_REMETENTE, [pagamento.usuario.email], html_message=mensagem_html)

    except Exception as e:
        raise self.retry(exc=e, countdown=90)
