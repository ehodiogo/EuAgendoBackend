from .serializers import (
    AgendamentoSerializer,
    ClienteSerializer,
    EmpresaSerializer,
    FuncionarioSerializer,
    ImagemSerializer,
    ServicoSerializer,
    EmpresaServicoFuncionarioSerializer,
)
from agendamento.models import Agendamento
from cliente.models import Cliente
from core.models import Imagem
from empresa.models import Empresa
from funcionario.models import Funcionario
from servico.models import Servico
from rest_framework import viewsets,filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework import status
from django.utils.dateparse import parse_datetime
from django.utils.dateparse import parse_date
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, LoginSerializer
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from datetime import date, timedelta, datetime
import hashlib
from rest_framework.authtoken.models import Token
from django.db.models import Sum
from plano.models import PlanoUsuario, Plano
from pagamento.models import Pagamento
from decouple import config
import mercadopago
import pytz

User = get_user_model()

class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["funcionario"]

    def get_renderers(self):
        """Garante que a API só use JSON, evitando erro de template"""
        from rest_framework.renderers import JSONRenderer
        return [JSONRenderer()]

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class ImagemViewSet(viewsets.ModelViewSet):
    queryset = Imagem.objects.all()
    serializer_class = ImagemSerializer

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=400)

        empresas = Empresa.objects.filter(nome__icontains=termo) | Empresa.objects.filter(cnpj__icontains=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=400)

        empresas = Empresa.objects.filter(nome__icontains=termo) | Empresa.objects.filter(cnpj__icontains=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

class FuncionarioViewSet(viewsets.ModelViewSet):
    serializer_class = FuncionarioSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = [
        "nome",
        "empresas__nome",
        "empresas__cnpj",
    ]

    queryset = Funcionario.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_nome = self.request.query_params.get("empresa_nome")
        empresa_cnpj = self.request.query_params.get("empresa_cnpj")

        empresa = None

        if empresa_nome:
            empresa = Empresa.objects.filter(nome__icontains=empresa_nome)
        if empresa_cnpj:
            empresa = Empresa.objects.filter(cnpj__icontains=empresa_cnpj)

        if empresa:
            queryset = empresa[0].funcionarios.all()

        return queryset

class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer

    def get_queryset(self):
        ids = self.request.query_params.get("ids", None)

        if ids:
            ids = [int(id) for id in ids.split(",")]
            return Servico.objects.filter(id__in=ids) 
        else:
            return (
                Servico.objects.all()
            ) 

class EmpresaServicoViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaServicoFuncionarioSerializer

    def get_queryset(self):
        nome = self.request.query_params.get("empresa_nome", None)
        cnpj = self.request.query_params.get("cnpj", None)

        if nome:
            return Empresa.objects.filter(nome__icontains=nome)
        elif cnpj:
            return Empresa.objects.filter(cnpj__icontains=cnpj)
        else:
            return Empresa.objects.all()

class AgendamentoCreateView(APIView):
    def post(self, request, *args, **kwargs):

        id_funcionario = request.data.get("id_funcionario")
        data = request.data.get("data")
        hora = request.data.get("hora")
        cliente_nome = request.data.get("cliente_nome")
        cliente_email = request.data.get("cliente_email")  
        cliente_numero = request.data.get("cliente_numero") 
        servico_nome = request.data.get("servico_nome")
        duracao_minima = request.data.get("duracao_minima")

        if (
            not id_funcionario
            or not data
            or not hora
            or not cliente_nome
            or not cliente_email
            or not cliente_numero
            or not servico_nome
        ):
            return Response(
                {"erro": "Todos os campos são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data_hora = parse_datetime(f"{data}T{hora}:00")
            if not data_hora:
                raise ValueError("Data ou hora inválidos.")
        except ValueError as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            funcionario = Funcionario.objects.get(id=id_funcionario)
        except Funcionario.DoesNotExist:
            return Response(
                {"erro": "Funcionário não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cliente, created = Cliente.objects.get_or_create(
            nome=cliente_nome, email=cliente_email, telefone=cliente_numero
        )

        try:
            servico = Servico.objects.get(nome=servico_nome, funcionarios=funcionario)
        except Servico.DoesNotExist:
            return Response(
                {"erro": "Serviço não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        if int(servico.duracao) > int(duracao_minima):

            quantia_agendamentos = int(servico.duracao) // int(duracao_minima)

            agendamento = Agendamento.objects.create(
                funcionario=funcionario,
                data=data_hora.date(),
                hora=data_hora.time(),
                cliente=cliente,
                servico=servico,
            )

            for i in range(1, quantia_agendamentos):
                nova_hora = datetime.combine(datetime.today(), data_hora.time()) + timedelta(minutes=int(duracao_minima) * i)
                nova_hora = nova_hora.time()

                agendamento = Agendamento.objects.create(
                    funcionario=funcionario,
                    data=data_hora.date(),
                    hora=nova_hora,
                    cliente=cliente,
                    servico=servico,
                    is_continuacao=True,
                )
        else:

            agendamento = Agendamento.objects.create(
                funcionario=funcionario,
                data=data_hora.date(),
                hora=data_hora.time(),
                cliente=cliente,
                servico=servico,
            )

        return Response(
            {
                "id": agendamento.id,
                "funcionario": funcionario.nome,
                "data": agendamento.data,
                "hora": agendamento.hora,
                "cliente_nome": cliente.nome,
                "cliente_email": cliente.email,
                "cliente_numero": cliente.telefone,
                "servico_nome": servico.nome,
            },
            status=status.HTTP_201_CREATED,
        )

class FuncionarioAgendamentoView(APIView):
    def get(self, request, *args, **kwargs):
        id_funcionario = request.query_params.get("id_funcionario")
        data_str = request.query_params.get(
            "data"
        ) 

        if not id_funcionario or not data_str:
            return Response(
                {"erro": "Os parâmetros 'id_funcionario' e 'data' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            funcionario = Funcionario.objects.get(id=id_funcionario)
        except Funcionario.DoesNotExist:
            return Response(
                {"erro": "Funcionário não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            data = parse_date(data_str)
            if not data:
                raise ValueError("Data inválida.")
        except ValueError:
            return Response(
                {"erro": "Data no formato inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        agendamentos = Agendamento.objects.filter(funcionario=funcionario, data=data)

        if not agendamentos:
            return Response(
                [],
                status=status.HTTP_200_OK,
            )

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            
            user_plan = PlanoUsuario.objects.filter(usuario=user).first()

            if not user_plan:
                PlanoUsuario.objects.create(
                    usuario=user, plano=Plano.objects.get(title="Free Trial"), expira_em=datetime.now() + timedelta(days=7)
                )

                user_plan = PlanoUsuario.objects.filter(usuario=user)

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "username": user.username,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            token, _ = Token.objects.get_or_create(user=user)

            plan = PlanoUsuario.objects.filter(usuario=user).first()

            now_aware = datetime.now(pytz.utc)
            is_expired = False
            if plan.plano.nome != "Free Trial":
                if plan.expira_em.astimezone(pytz.utc) < now_aware:
                    is_expired = True
                    
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(token.key),
                    "is_expired_plan": is_expired,
                    "tempo_restante": plan.expira_em.astimezone(pytz.utc) - now_aware,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordRecoveryView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)

        if not email:
            return Response(
                {"detail": "Email é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            token = default_token_generator.make_token(user)

            reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={token}"

            subject = "Recuperação de senha"
            message = f"Para recuperar sua senha, clique no link abaixo:\n{reset_url}"
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return Response(
                {"detail": "Link de recuperação de senha enviado!"},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuário com este email não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

class AgendamentosHojeView(APIView):

    def get(self, request, *args, **kwargs):

        empresa_id = request.query_params.get("empresa_id")

        if empresa_id:
            agendamentos = Agendamento.objects.filter(data=date.today(), funcionario__empresas__id=empresa_id, is_continuacao=False, hora__gte=datetime.now().time()).order_by('hora')
            serializer = AgendamentoSerializer(agendamentos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
    
        return Response(
            {"erro": "Parâmetro 'empresa_id' é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST,
        )

class EmpresasUsuarioView(APIView):

    def get(self, request, *args, **kwargs):

        access_token = request.query_params.get("usuario_token")

        if not access_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = Token.objects.filter(key=access_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empresas = usuario.empresas.all()
        serializer = EmpresaSerializer(empresas, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class UserView(APIView):

    def get(self, request, *args, **kwargs):
        access_token = request.query_params.get("usuario_token")

        if not access_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_obj = Token.objects.filter(key=access_token).first()
        if not token_obj:
            return Response(
                {"erro": "Token de acesso inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = token_obj.user

        return Response(
            {
                "id": usuario.id,
                "username": usuario.username,
                "email": usuario.email,
                "first_name": usuario.first_name,
                "password": usuario.password,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        access_token = request.data.get("usuario_token")

        if not access_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_obj = Token.objects.filter(key=access_token).first()
        if not token_obj:
            return Response(
                {"erro": "Token de acesso inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = token_obj.user

        usuario.first_name = request.data.get("first_name", usuario.first_name)
        usuario.username = request.data.get("username", usuario.username)
        usuario.email = request.data.get("email", usuario.email)
        usuario.save()

        return Response(
            {"mensagem": "Perfil atualizado com sucesso!"},
            status=status.HTTP_200_OK,
        )

class ChangePasswordView(APIView):
    def post(self, request, *args, **kwargs):
        usuario_token = request.data.get("usuario_token")
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not usuario_token or not current_password or not new_password:
            return Response(
                {"erro": "Token de acesso e senha são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_obj = Token.objects.filter(key=usuario_token).first()
        if not token_obj:
            return Response(
                {"erro": "Token de acesso inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user

        if not user.password == current_password:

            return Response(
                {"erro": "Senha atual incorreta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"mensagem": "Senha alterada com sucesso!"},
            status=status.HTTP_200_OK,
        )

class DashboardView(APIView):

    def get(self, request, *args, **kwargs):
        empresa_id = request.query_params.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "Parâmetro 'empresa_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return Response(
                {"erro": "Empresa não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_funcionarios = Funcionario.objects.filter(empresas=empresa).count()
        total_clientes = Cliente.objects.count()
        total_servicos = Servico.objects.count()

        agendamentos_hoje = Agendamento.objects.filter(
            data=date.today(), funcionario__empresas=empresa, is_continuacao=False
        ).count()

        agendamentos_pendentes = Agendamento.objects.filter(
            data__gte=date.today(), funcionario__empresas=empresa, is_continuacao=False
        ).count()

        dados = {
            "empresa": empresa.nome,
            "total_funcionarios": total_funcionarios,
            "total_clientes": total_clientes,
            "total_servicos": total_servicos,
            "agendamentos_hoje": agendamentos_hoje,
            "agendamentos_pendentes": agendamentos_pendentes,
        }

        return Response(dados, status=status.HTTP_200_OK)

class FinanceiroView(APIView):
    def get(self, request, *args, **kwargs):
        empresa_id = request.query_params.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "Parâmetro 'empresa_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        primeiro_dia_semana = hoje - timedelta(days=hoje.weekday())

        # Total de ganhos
        total_ganhos = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .aggregate(total=Sum("servico__preco"))
            .get("total", 0)
        ) or 0

        # Ganhos por semana
        ganhos_por_semana = (
            Agendamento.objects.filter(
                funcionario__empresas__id=empresa_id, data__gte=primeiro_dia_semana, is_continuacao=False
            )
            .aggregate(total=Sum("servico__preco"))
            .get("total", 0)
        ) or 0

        # Ganhos por mês
        ganhos_por_mes = (
            Agendamento.objects.filter(
                funcionario__empresas__id=empresa_id, data__gte=primeiro_dia_mes, is_continuacao=False
            )
            .aggregate(total=Sum("servico__preco"))
            .get("total", 0)
        ) or 0

        # Funcionário que mais gerou dinheiro
        funcionario_top = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .values("funcionario__nome")
            .annotate(total=Sum("servico__preco"))
            .order_by("-total")
            .first()
        )

        # Serviço mais rentável
        servico_mais_rentavel = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .values("servico__nome")
            .annotate(total=Sum("servico__preco"))
            .order_by("-total")
            .first()
        )

        # Serviço que menos gerou dinheiro
        servico_menos_rentavel = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .values("servico__nome")
            .annotate(total=Sum("servico__preco"))
            .order_by("total")
            .first()
        )

        return Response(
            {
                "total_ganhos": total_ganhos,
                "ganhos_por_semana": ganhos_por_semana,
                "ganhos_por_mes": ganhos_por_mes,
                "funcionario_top": funcionario_top
                or {"funcionario__nome": None, "total": 0},
                "servico_mais_rentavel": servico_mais_rentavel
                or {"servico__nome": None, "total": 0},
                "servico_menos_rentavel": servico_menos_rentavel
                or {"servico__nome": None, "total": 0},
            },
            status=status.HTTP_200_OK,
        )

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

        if not empresas:
            return Response(
                {"erro": "Usuário não possui empresas cadastradas."},
                status=status.HTTP_400_BAD_REQUEST, 
            )

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
                {"erro": "Usuário não possui pagamentos cadastrados."},
                status=status.HTTP_400_BAD_REQUEST,
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
                print("MERCADO_PAGO_ACCESS_TOKEN_TEST", config("MERCADO_PAGO_ACCESS_TOKEN_TEST"))
            else:
                sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_PRD"))

            plan = Plano.objects.get(nome=plano_nome)

            user = Token.objects.filter(key=usuario_token).first().user

            external_reference = hashlib.sha256(f"{user.id}-{plan.id}-{plan.nome}-{user.email}-{datetime.now()}".encode()).hexdigest()

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
                    # TODO: Alterar para URL do frontend
                    "success": 'http://localhost:5173/payment/success/',
                    "failure": 'http://localhost:5173/payment/failure/',
                    "pending": 'http://localhost:5173/payment/pending/',
                },
                "payer": {
                    "email": user.email,
                },
                "external_reference": external_reference,
            }

            result = sdk.preference().create(payment_data)

            print("Result: ", result)

            url = result["response"]['init_point'] 

            return Response({"url": url}, status=status.HTTP_200_OK)

        except Plano.DoesNotExist:
            return Response(
                {"erro": "Plano não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

class PaymentSuccessView(APIView):
    def post(self, request, *args, **kwargs):

        plano_nome = request.data.get("plano_nome")
        usuario_token = request.data.get("usuario_token")

        print("Plano: ", plano_nome)
        print("Token: ", usuario_token)

        if not plano_nome or not usuario_token:
            return Response(
                {"erro": "Plano e token de acesso é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            user = Token.objects.filter(key=usuario_token).first().user

            transaction = Pagamento.objects.filter(plano__nome=plano_nome, verified=False, usuario=user, status="Pendente").last()

            hash_id = transaction.hash_mercadopago

            if config("DEBUG", default=False, cast=bool):
                sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_TEST"))
            else:
                sdk = mercadopago.SDK(config("MERCADO_PAGO_ACCESS_TOKEN_PRD"))

            payment = sdk.payment().search({"external_reference": hash_id})
            print("Payment: ", payment)

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
                transaction.is_verified = True
                transaction.status = StatusPagamento.PAGO
                transaction.save()

                user_plan = PlanoUsuario.objects.filter(usuario=user).first()

                if not user_plan:
                    PlanoUsuario.objects.create(
                        usuario=user, plano=Plano.objects.get(title="Free"), expira_em=datetime.now() + timedelta(days=30)
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

                print("User plan: ", user_plan)

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
                print(payment["response"]["results"][0]["status"])
                print("Not approved")
                return Response(
                    {"message": "Payment not approved"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Pagamento.DoesNotExist:
            return Response(
                {"erro": "Pagamento não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
