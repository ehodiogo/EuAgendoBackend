from rest_framework.views import APIView
from plano.models import PlanoUsuario, Plano
from .models import Pagamento
from decouple import config
import mercadopago
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from funcionario.models import Funcionario
import hashlib
from datetime import datetime, timedelta

class LimitePlanoUsageView(APIView):

    def get(self, request, *args, **kwargs):

        usuario_token = request.query_params.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plano = PlanoUsuario.objects.filter(usuario=usuario).first()

        if not plano:
            return Response(
                {"erro": "Usuário não possui plano cadastrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empresas = usuario.empresas.all()

        return Response(
            {
                "plano_ativo": plano.plano.nome,
                "expira_em": plano.expira_em,
                "quantia_empresas_criadas": empresas.count(),
                "limite_empresas": plano.plano.quantidade_empresas,
                "limite_funcionarios": plano.plano.quantidade_funcionarios,
                "funcionarios_por_empresa": [
                    {"empresa": empresa.nome, "total_funcionarios": empresa.funcionarios.count()}
                    for empresa in empresas
                ]
            },
            status=status.HTTP_200_OK,
        )


class PagamentosUsuarioView(APIView):

    def get(self, request, *args, **kwargs):

        usuario_token = request.query_params.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pagamentos = usuario.pagamento_set.all()

        if not pagamentos:
            return Response(
                {
                    "pagamentos": [],
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "pagamentos": [
                    {
                        "valor": pagamento.valor,
                        "data": pagamento.data,
                        "status": pagamento.status,
                        "tipo": pagamento.tipo,
                        "plano": pagamento.plano.nome,
                    }
                    for pagamento in pagamentos
                ]
            },
            status=status.HTTP_200_OK,
        )


class PagamentoPlanoView(APIView):
    def post(self, request, *args, **kwargs):

        plano_nome = request.data.get("plano_nome")
        usuario_token = request.data.get("usuario_token")

        if not plano_nome or not usuario_token:
            return Response(
                {"erro": "Plano e token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            if config("DEBUG", default=False, cast=bool):
                sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_TEST"))
            else:
                sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_PRD"))

            plan = Plano.objects.get(nome=plano_nome)

            user = Token.objects.filter(key=usuario_token).first().user

            external_reference = hashlib.sha256(
                f"{user.id}-{plan.id}-{plan.nome}-{user.email}-{datetime.now()}".encode()).hexdigest()

            from pagamento.models import StatusPagamento

            Pagamento.objects.create(
                plano=plan,
                valor=float(plan.valor),
                status=StatusPagamento.PENDENTE,
                data=datetime.now(),
                tipo="",
                hash_mercadopago=external_reference,
                updated_at=datetime.now(),
                usuario=user,
            )

            payment_data = {
                "items": [
                    {
                        "id": plan.id,
                        "title": f"Contratação do {plan.nome}",
                        "quantity": 1,
                        "unit_price": float(plan.valor),
                        "currency_id": "BRL",
                        "description": f"Você está adquirindo o {plan.nome}! ",
                    }
                ],
                "back_urls": {
                    "success": 'https://vemagendar.com.br/payment/success/',
                    "failure": 'https://vemagendar.com.br/payment/failure/',
                    "pending": 'https://vemagendar.com.br/payment/pending/',
                },
                "payer": {
                    "email": user.email,
                },
                "external_reference": external_reference,
            }
            result = sdk.preference().create(payment_data)

            url = result["response"]['init_point']

            return Response({"url": url}, status=status.HTTP_200_OK)

        except Plano.DoesNotExist:
            return Response(
                {"erro": "Plano não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )


class PaymentSuccessView(APIView):
    def post(self, request, *args, **kwargs):

        print("Post payment success", request.data)

        plano_nome = request.data.get("plano_nome")
        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Plano e token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if plano_nome:

            try:

                user = Token.objects.filter(key=usuario_token).first().user

                transaction = Pagamento.objects.filter(plano__nome=plano_nome, verified=False, usuario=user,
                                                       status="Pendente").last()

                hash_id = transaction.hash_mercadopago

                if config("DEBUG", default=False, cast=bool):
                    sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_TEST"))
                else:
                    sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_PRD"))

                payment = sdk.payment().search({"external_reference": hash_id})

                if payment["response"]["results"][0]["status"] == "approved":
                    transaction.status = "approved"

                    payment_method = payment["response"]["results"][0]["payment_method_id"]

                    from pagamento.models import TipoPagamento
                    if payment_method == "credit_card":
                        transaction.payment_method = TipoPagamento.CARTAO_CREDITO
                    elif payment_method == "debit_card":
                        transaction.payment_method = TipoPagamento.CARTAO_DEBITO
                    else:
                        transaction.payment_method = TipoPagamento.PIX

                    from pagamento.models import StatusPagamento

                    transaction.updated_at = datetime.now()
                    transaction.verified = True
                    transaction.status = StatusPagamento.PAGO
                    transaction.save()

                    user_plan = PlanoUsuario.objects.filter(usuario=user).first()

                    if not user_plan:
                        PlanoUsuario.objects.create(
                            usuario=user, plano=Plano.objects.get(nome="Free Trial"),
                            expira_em=datetime.now() + timedelta(days=30)
                        )

                        user_plan = PlanoUsuario.objects.filter(usuario=user)

                    else:
                        user_plan = user_plan

                    user_plan.plan = transaction.plano
                    user_plan.active = True
                    user_plan.changed_at = datetime.now()
                    user_plan.expira_em = datetime.now() + timedelta(
                        days=30
                    )
                    user_plan.save()

                    return Response(
                        {"message": "Payment approved. You are now subscribed"},
                        status=status.HTTP_200_OK,
                    )
                elif payment["response"]["results"][0]["status"] == "rejected":
                    return Response(
                        {"message": "Payment rejected"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return Response(
                        {"message": "Payment not approved"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Pagamento.DoesNotExist:
                return Response(
                    {"erro": "Pagamento não encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:
            print("Sem plano nome")

            try:
                from pagamento.models import StatusPagamento

                user = Token.objects.filter(key=usuario_token).first().user

                transaction = Pagamento.objects.filter(verified=False, usuario=user, status=StatusPagamento.PENDENTE)

                print("Transacao ", transaction)

                for t in transaction:
                    hash_id = t.hash_mercadopago

                    if config("DEBUG", default=False, cast=bool):
                        sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_TEST"))
                    else:
                        sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_PRD"))

                    payment = sdk.payment().search({"external_reference": hash_id})

                    print("Payment", payment)

                    try:

                        if payment["response"]["results"][0]["status"] == "approved":

                            print("Aprovado")

                            payment_method = payment["response"]["results"][0]["payment_method_id"]

                            from pagamento.models import TipoPagamento
                            if payment_method == "credit_card":
                                t.payment_method = TipoPagamento.CARTAO_CREDITO
                            elif payment_method == "debit_card":
                                t.payment_method = TipoPagamento.CARTAO_DEBITO
                            else:
                                t.payment_method = TipoPagamento.PIX

                            t.updated_at = datetime.now()
                            t.verified = True
                            t.status = StatusPagamento.PAGO
                            t.save()

                            user_plan = PlanoUsuario.objects.filter(usuario=user).first()

                            if not user_plan:
                                PlanoUsuario.objects.create(
                                    usuario=user, plano=Plano.objects.get(nome="Free Trial"),
                                    expira_em=datetime.now() + timedelta(days=30)
                                )

                                user_plan = PlanoUsuario.objects.filter(usuario=user)

                            else:
                                user_plan = user_plan

                            user_plan.plan = t.plano
                            user_plan.active = True
                            user_plan.changed_at = datetime.now()
                            user_plan.expira_em = datetime.now() + timedelta(
                                days=30
                            )
                            user_plan.save()

                            return Response(
                                {"message": "Payment approved. You are now subscribed"},
                                status=status.HTTP_200_OK,
                            )
                        print("Não aprovado")
                    except Exception as e:
                        print(e)

            except Pagamento.DoesNotExist:
                return Response(
                    {"erro": "Pagamento não encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )


class PossuiLimiteView(APIView):

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        acao_realizada = request.data.get("acao_realizada")

        if not acao_realizada:
            return Response(
                {"erro": "Ação realizada é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        possui_limite = False

        plano_usuario = PlanoUsuario.objects.filter(usuario=usuario).first()

        if plano_usuario:
            plano_usuario = plano_usuario.plano

        if acao_realizada == "criar_empresa":

            if usuario.empresas.count() >= plano_usuario.quantidade_empresas:
                possui_limite = False
            else:
                possui_limite = True

        if acao_realizada == "criar_funcionario":

            quantia_funcionarios = Funcionario.objects.filter(criado_por=usuario).count()

            if quantia_funcionarios >= plano_usuario.quantidade_funcionarios:
                possui_limite = False
            else:
                possui_limite = True

        return Response(
            {
                "possui_limite": possui_limite,
            },
            status=status.HTTP_201_CREATED,
        )
