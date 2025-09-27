from celery import shared_task
from decouple import config
import mercadopago
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from .models import Pagamento, StatusPagamento, TipoPagamento
from plano.models import PlanoUsuario, Plano

@shared_task(bind=True, max_retries=10)
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

            user_plan.plan = pagamento.plano
            user_plan.active = True
            user_plan.changed_at = timezone.now()
            user_plan.expira_em = timezone.now() + timedelta(days=30)
            user_plan.save()

            send_mail(
                "Pagamento Aprovado",
                f"Olá {user.email}, seu pagamento do plano {pagamento.plano.nome} foi aprovado.",
                None,
                [user.email]
            )

        elif status_mp == "rejected":
            pagamento.status = StatusPagamento.REJEITADO
            pagamento.updated_at = timezone.now()
            pagamento.save()

            # Envia email de rejeição
            send_mail(
                "Pagamento Rejeitado",
                f"Olá {pagamento.usuario.email}, seu pagamento do plano {pagamento.plano.nome} foi rejeitado.",
                None,
                [pagamento.usuario.email]
            )
        else:
            raise self.retry(countdown=180)  # 180 segundos = 3 minutos

    except self.MaxRetriesExceededError:
        send_mail(
            "Pagamento Pendente",
            f"Olá {pagamento.usuario.email}, seu pagamento do plano {pagamento.plano.nome} não foi aprovado nem rejeitado após várias tentativas. Por favor, verifique no Mercado Pago.",
            None,
            [pagamento.usuario.email]
        )
    except Exception as e:
        raise self.retry(exc=e, countdown=180)
