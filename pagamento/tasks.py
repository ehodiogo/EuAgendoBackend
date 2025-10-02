from celery import shared_task
from decouple import config
import mercadopago
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from .models import Pagamento, StatusPagamento, TipoPagamento
from plano.models import PlanoUsuario, Plano

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

            # Email aprovado
            assunto = "✅ Pagamento Aprovado!"
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
            send_mail(assunto, mensagem_txt, EMAIL_REMETENTE, [user.email], html_message=mensagem_html)

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
            raise self.retry(countdown=90)  # 90 segundos = 1.5 minutos

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
