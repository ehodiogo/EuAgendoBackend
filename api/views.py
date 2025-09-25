from .serializers import (
    AgendamentoSerializer,
    ClienteSerializer,
    EmpresaSerializer,
    FuncionarioSerializer,
    ImagemSerializer,
    ServicoSerializer,
    EmpresaServicoFuncionarioSerializer,
    ServicoFuncionarioSerializer,
    AgendamentoAvaliacaoSerializer
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
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
import os

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

class AgendamentoAvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoAvaliacaoSerializer
    filter_backends = [DjangoFilterBackend]
    lookup_field = "identificador"

    def get_renderers(self):
        from rest_framework.renderers import JSONRenderer
        return [JSONRenderer()]

    @action(detail=True, methods=["post"], url_path="avaliar")
    def avaliar(self, request, identificador=None):
        agendamento = self.get_object()

        serializer = AgendamentoAvaliacaoSerializer(
            agendamento,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

                plano, _ = Plano.objects.get_or_create(nome="Free Trial", valor=0, quantidade_empresas=1, quantidade_funcionarios=1, duracao_em_dias=7)

                PlanoUsuario.objects.create(
                    usuario=user, plano=plano, expira_em=datetime.now() + timedelta(days=7)
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

        total_funcionarios = empresa.funcionarios.count()

        total_clientes = Agendamento.objects.filter(funcionario__empresas__in=[empresa]) \
        .values('cliente') \
        .distinct() \
        .count()
        
        total_servicos = empresa.servicos.count()

        agendamentos_hoje = Agendamento.objects.filter(
            data=date.today(), funcionario__empresas__in=[empresa], is_continuacao=False
        ).count()

        agendamentos_pendentes = Agendamento.objects.filter(
            data__gte=date.today(),
            funcionario__empresas__in=[empresa],
            is_continuacao=False,
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
            return Response (
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

                transaction = Pagamento.objects.filter(plano__nome=plano_nome, verified=False, usuario=user, status="Pendente").last()

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
                    transaction.is_verified = True
                    transaction.status = StatusPagamento.PAGO
                    transaction.save()

                    user_plan = PlanoUsuario.objects.filter(usuario=user).first()

                    if not user_plan:
                        PlanoUsuario.objects.create(
                            usuario=user, plano=Plano.objects.get(title="Free Trial"), expira_em=datetime.now() + timedelta(days=30)
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
                            t.is_verified = True
                            t.status = StatusPagamento.PAGO
                            t.save()

                            user_plan = PlanoUsuario.objects.filter(usuario=user).first()

                            if not user_plan:
                                PlanoUsuario.objects.create(
                                    usuario=user, plano=Plano.objects.get(title="Free Trial"), expira_em=datetime.now() + timedelta(days=30)
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

class EmpresaCreate(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        nome = request.data.get("nome")
        cnpj = request.data.get("cnpj")
        endereco = request.data.get("endereco")
        bairro = request.data.get("bairro")
        cidade = request.data.get("cidade")
        estado = request.data.get("estado")
        pais = request.data.get("pais")
        telefone = request.data.get("telefone")
        email = request.data.get("email")

        horario_abertura_dia_semana = request.data.get("horario_abertura_dia_semana")
        horario_fechamento_dia_semana = request.data.get("horario_fechamento_dia_semana")

        horario_abertura_fim_semana = request.data.get("horario_abertura_fim_de_semana")
        horario_fechamento_fim_semana = request.data.get("horario_fechamento_fim_de_semana")

        para_almoco = request.data.get("para_almoco")

        if para_almoco == "true":
            para_almoco = True
        else:
            para_almoco = False

        inicio_almoco = request.data.get("inicio_almoco")
        fim_almoco = request.data.get("fim_almoco")

        abre_sabado = request.data.get("abre_sabado")

        if abre_sabado == "true":
            abre_sabado = True
        else:
            abre_sabado = False

        abre_domingo = request.data.get("abre_domingo")

        if abre_domingo == "true":
            abre_domingo = True
        else:
            abre_domingo = False

        logo = request.data.get("logo")

        if not nome or not cnpj or not endereco or not telefone or not email:

            return Response(
                {"erro": "Todos os campos são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )

        try:

            imagem_obj = None
            if isinstance(logo, ContentFile) or hasattr(logo, 'read'):
                base_name, ext = os.path.splitext(logo.name)
                new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"
                imagem_obj = Imagem()
                imagem_obj.imagem.save(new_filename, logo, save=True)
            elif isinstance(logo, str) and logo.startswith("http"):
                imagem_obj = Imagem.objects.create(imagem_url=logo)

            empresa = Empresa.objects.create(
                nome=nome,
                cnpj=cnpj,
                endereco=endereco,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                pais=pais,
                telefone=telefone,
                email=email,
                horario_abertura_dia_semana=horario_abertura_dia_semana,
                horario_fechamento_dia_semana=horario_fechamento_dia_semana,
                horario_abertura_fim_de_semana=horario_abertura_fim_semana,
                horario_fechamento_fim_de_semana=horario_fechamento_fim_semana,
                para_almoco=para_almoco,
                horario_pausa_inicio=inicio_almoco,
                horario_pausa_fim=fim_almoco,
                abre_sabado=abre_sabado,
                abre_domingo=abre_domingo,
                logo=imagem_obj,  
                criado_por=usuario
            )

            usuario.empresas.add(empresa)
            usuario.save()

            imagem_obj.empresa = empresa
            imagem_obj.save()

            return Response(
                {
                    "message": "Empresa criada com sucesso.",
                    "empresa": EmpresaSerializer(empresa).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FuncionarioCreate(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )

        nome = request.data.get("nome")
        foto = request.data.get("foto")

        if not nome:

            return Response(
                {"erro": "Nome é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        empresa_nome = request.data.get("empresa_nome")

        try:    

            imagem_obj = None
            if isinstance(foto, ContentFile) or hasattr(foto, 'read'):
                base_name, ext = os.path.splitext(foto.name)
                new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"
                imagem_obj = Imagem()
                imagem_obj.imagem.save(new_filename, foto, save=True)
            elif isinstance(foto, str) and foto.startswith("http"):
                imagem_obj = Imagem.objects.create(imagem_url=foto)

            funcionario = Funcionario.objects.create(
                nome=nome,
                foto=imagem_obj,
                criado_por=usuario
            )

            if empresa_nome:
                empresa = Empresa.objects.get(nome=empresa_nome)
                imagem_obj.empresa = empresa
                funcionario.empresas.add(empresa)
                funcionario.save()

            imagem_obj.funcionario = funcionario
            imagem_obj.save()

            return Response(
                {
                    "message": "Funcionário criado com sucesso.",
                    "funcionario": FuncionarioSerializer(funcionario).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ServicoCreate(APIView):

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )
        
        nome = request.data.get("nome")
        preco = request.data.get("preco")
        duracao = request.data.get("duracao")

        if not nome or not preco or not duracao:

            return Response(
                {"erro": "Todos os campos são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            servico = Servico.objects.create(
                nome=nome,
                preco=preco,
                duracao=duracao,
                criado_por=usuario,
            )

            return Response(
                {
                    "message": "Serviço criado com sucesso.",
                    "servico": ServicoSerializer(servico).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdicionarFuncionariosEmpresa(APIView):

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )
        
        empresa_nome = request.data.get("empresa_nome")

        if not empresa_nome:

            return Response(
                {"erro": "Nome da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        funcionarios = request.data.get("funcionarios")

        if not funcionarios:

            return Response(
                {"erro": "Funcionários são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:

            empresa = Empresa.objects.get(nome=empresa_nome)

            for funcionario in funcionarios:
                funcionario_obj = Funcionario.objects.get(id=funcionario)
                funcionario_obj.empresas.add(empresa)
                funcionario_obj.save()

            return Response(
                {
                    "message": "Funcionários adicionados com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )
        
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FuncionariosCriadosView(APIView):

    def get(self, request, *args, **kwargs):

        usuario_token = request.query_params.get("usuario_token")
        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user
        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )

        funcionarios = Funcionario.objects.filter(criado_por=usuario)

        if not funcionarios:
            return Response(
                {"erro": "Usuário não possui funcionários cadastrados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empresa_id = request.query_params.get("empresa_id")

        if empresa_id:
            funcionarios = funcionarios.filter(empresas__id=empresa_id)

        return Response(
            {
                "funcionarios": ServicoFuncionarioSerializer(
                    funcionarios, many=True
                ).data
            },
            status=status.HTTP_200_OK,
        )

class AdicionarServicosFuncionario(APIView):

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:   
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )
        
        funcionarios = request.data.get("funcionarios")
        
        servico_nome = request.data.get("servico_nome")
        servico_duracao = request.data.get("servico_duracao")
        servico_valor = request.data.get("servico_valor")
        servico_descricao = request.data.get("servico_descricao")

        if not servico_nome or not servico_duracao or not servico_valor:

            return Response(
                {"erro": "Todos os campos são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        empresa_id = request.data.get("empresa_id")

        if not empresa_id:

            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:

            servico = Servico.objects.create(
                nome=servico_nome,
                duracao=servico_duracao,
                preco=servico_valor,
                descricao=servico_descricao,
                criado_por=usuario
            )

            if funcionarios:

                for funcionario in funcionarios:
                    funcionario_obj = Funcionario.objects.get(id=funcionario)
                    funcionario_obj.servicos.add(servico)
                    funcionario_obj.save()

            empresa = Empresa.objects.get(id=empresa_id)
            empresa.servicos.add(servico)
            empresa.save()

            return Response(
                {
                    "message": "Serviços adicionados com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )
        
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ServicosCriadosUsuarioEmpresaView(APIView):

    def get(self, request, *args, **kwargs):

        usuario_token = request.query_params.get("usuario_token")
        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )
        
        empresa_id = request.query_params.get("empresa_id")

        if not empresa_id:

            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:

            empresa = Empresa.objects.get(id=empresa_id)
            servicos = empresa.servicos.all()

            return Response(
                {
                    "servicos": ServicoSerializer(
                        servicos, many=True
                    ).data
                },
                status=status.HTTP_200_OK,
            )
        
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdicionarServicoFuncionariosView(APIView):

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:   
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )
        
        servico_id = request.data.get("servico_id")

        if not servico_id:

            return Response(
                {"erro": "ID do serviço é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        funcionarios = request.data.get("funcionarios")

        if not funcionarios:

            return Response(
                {"erro": "Funcionários são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:

            servico = Servico.objects.get(id=servico_id)

            for funcionario in funcionarios:
                funcionario_obj = Funcionario.objects.get(id=funcionario)
                funcionario_obj.servicos.add(servico)

            return Response(
                {
                    "message": "Serviços adicionados com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )
    
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RemoverServicoEmpresaView(APIView):

    def post(self, request):

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:   
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )

        servico_id = request.data.get("servico_id")

        if not servico_id:

            return Response(
                {"erro": "ID do serviço é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        empresa_id = request.data.get("empresa_id")

        if not empresa_id:

            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            empresa = Empresa.objects.get(id=empresa_id)
            servico = Servico.objects.get(id=servico_id)
            empresa.servicos.remove(servico)

            for funcionario in empresa.funcionarios.all():
                funcionario.servicos.remove(servico)
                funcionario.save()

            servico.delete()

            return Response(
                {
                    "message": "Serviço removido com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RemoverServicosFuncionarioView(APIView):

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

        servico_id = request.data.get("servico_id")

        if not servico_id:

            return Response(
                {"erro": "ID do serviço é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        funcionarios = request.data.get("funcionarios")

        if not funcionarios:

            return Response(
                {"erro": "Funcionários são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            servico = Servico.objects.get(id=servico_id)

            for funcionario in funcionarios:
                funcionario_obj = Funcionario.objects.get(id=funcionario)
                funcionario_obj.servicos.remove(servico)

            return Response(
                {
                    "message": "Serviços adicionados com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EditarServicoView(APIView):

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
        
        servico_id = request.data.get("servico_id")

        if not servico_id:
            return Response(
                {"erro": "ID do serviço é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        servico_nome = request.data.get("servico_nome")
        servico_duracao = request.data.get("servico_duracao")
        servico_valor = request.data.get("servico_valor")
        servico_descricao = request.data.get("servico_descricao")

        try:

            servico = Servico.objects.get(id=servico_id)

            if servico_nome:
                servico.nome = servico_nome

            if servico_duracao:
                servico.duracao = servico_duracao

            if servico_valor:
                servico.preco = servico_valor

            if servico_descricao:
                servico.descricao = servico_descricao

            servico.save()

            return Response(
                {
                    "message": "Serviço atualizado com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )
        
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EditarEmpresaView(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        nome = request.data.get("nome")
        cnpj = request.data.get("cnpj")
        endereco = request.data.get("endereco")
        bairro = request.data.get("bairro")
        cidade = request.data.get("cidade")
        estado = request.data.get("estado")
        pais = request.data.get("pais")
        telefone = request.data.get("telefone")
        email = request.data.get("email")

        horario_abertura_dia_semana = request.data.get("horario_abertura_dia_semana")
        horario_fechamento_dia_semana = request.data.get("horario_fechamento_dia_semana")

        horario_abertura_fim_semana = request.data.get("horario_abertura_fim_de_semana")
        horario_fechamento_fim_semana = request.data.get("horario_fechamento_fim_de_semana")

        para_almoco = request.data.get("para_almoco")

        if para_almoco == "true":
            para_almoco = True
        else:
            para_almoco = False

        inicio_almoco = request.data.get("inicio_almoco")
        fim_almoco = request.data.get("fim_almoco")

        abre_sabado = request.data.get("abre_sabado")

        if abre_sabado == "true":
            abre_sabado = True
        else:
            abre_sabado = False

        abre_domingo = request.data.get("abre_domingo")

        if abre_domingo == "true":
            abre_domingo = True
        else:
            abre_domingo = False

        logo = request.data.get("logo")

        empresa_id = request.data.get("empresa_id")

        if not nome or not cnpj or not endereco or not telefone or not email or not empresa_id:

            return Response(
                {"erro": "Todos os campos são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST 
            )

        try:

            imagem_obj = None

            if isinstance(logo, ContentFile) or hasattr(logo, "read"):
                base_name, ext = os.path.splitext(logo.name)
                new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"

                imagem_obj, created = Imagem.objects.get_or_create(
                    empresa_id=empresa_id,
                    imagem=f"imagens/{new_filename}",
                )

                if created:
                    imagem_obj.imagem.save(new_filename, logo, save=True)
            elif isinstance(logo, str) and logo.startswith("http"):
                imagem_obj, _ = Imagem.objects.get_or_create(imagem_url=logo, empresa__id=empresa_id)

            empresa = Empresa.objects.get(id=empresa_id)

            if nome != empresa.nome and nome != None:
                empresa.nome = nome

            if cnpj != empresa.cnpj and cnpj != None:
                empresa.cnpj = cnpj

            if endereco != empresa.endereco and endereco != None:
                empresa.endereco = endereco

            if bairro != empresa.bairro and bairro != None:
                empresa.bairro = bairro

            if cidade != empresa.cidade and cidade != None:
                empresa.cidade = cidade

            if estado != empresa.estado and estado != None:
                empresa.estado = estado

            if pais != empresa.pais and pais != None:
                empresa.pais = pais

            if telefone != empresa.telefone and telefone != None:
                empresa.telefone = telefone

            if email != empresa.email and email != None:
                empresa.email = email

            if horario_abertura_dia_semana != empresa.horario_abertura_dia_semana and horario_abertura_dia_semana != None:
                empresa.horario_abertura_dia_semana = horario_abertura_dia_semana

            if horario_fechamento_dia_semana != empresa.horario_fechamento_dia_semana and horario_fechamento_dia_semana != None:
                empresa.horario_fechamento_dia_semana = horario_fechamento_dia_semana

            if horario_abertura_fim_semana != empresa.horario_abertura_fim_de_semana and horario_abertura_fim_semana != None:
                empresa.horario_abertura_fim_de_semana = horario_abertura_fim_semana

            if horario_fechamento_fim_semana != empresa.horario_fechamento_fim_de_semana and horario_fechamento_fim_semana != None:
                empresa.horario_fechamento_fim_de_semana = horario_fechamento_fim_semana

            if para_almoco != empresa.para_almoco and para_almoco != None:
                empresa.para_almoco = para_almoco

            if inicio_almoco != empresa.horario_pausa_inicio and inicio_almoco != None:
                empresa.horario_pausa_inicio = inicio_almoco

            if fim_almoco != empresa.horario_pausa_fim and fim_almoco != None:
                empresa.horario_pausa_fim = fim_almoco

            if abre_sabado != empresa.abre_sabado and abre_sabado != None:
                empresa.abre_sabado = abre_sabado

            if abre_domingo != empresa.abre_domingo and abre_domingo != None:
                empresa.abre_domingo = abre_domingo

            if imagem_obj != empresa.logo and imagem_obj != None:
                empresa.logo = imagem_obj

            empresa.save()

            return Response(
                {
                    "message": "Empresa editada com sucesso.",
                    "empresa": EmpresaSerializer(empresa).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RemoverEmpresaView(APIView):

    def post(self, request):

        empresa_id = request.data.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            empresa = Empresa.objects.get(id=empresa_id)

            for funcionario in empresa.funcionarios.all():
                funcionario.delete()

            for servico in empresa.servicos.all():
                servico.delete()

            for agendamento in Agendamento.objects.filter(funcionario__empresas=empresa):
                agendamento.delete()

            empresa.delete()

            return Response(
                {
                    "message": "Empresa removida com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

class FuncionariosCriadosView(APIView):

    def get(self, request, *args, **kwargs):

        usuario_token = request.query_params.get("usuario_token")
        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user
        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        funcionarios = Funcionario.objects.filter(criado_por=usuario)

        if not funcionarios:
            return Response(
                {"erro": "Usuário não possui funcionários cadastrados."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        return Response(
            {
                "funcionarios" : [ {
                    "id": funcionario.id,
                    "nome": funcionario.nome,
                    "foto_url": funcionario.foto.imagem.url if funcionario.foto else None,
                    "servicos": [
                        {
                            "id": servico.id,
                            "nome": servico.nome,
                            "duracao": servico.duracao,
                        } for servico in funcionario.servicos.all()
                    ],
                } for funcionario in funcionarios]
            }, status=status.HTTP_200_OK
        )

class RemoverFuncionarioView(APIView):

    def post(self, request):

        funcionarios_ids = request.data.get("funcionarios_ids")

        if not funcionarios_ids:
            return Response(
                {"erro": "ID do funcionário é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            funcionarios = Funcionario.objects.filter(id__in=funcionarios_ids)

            if not funcionarios:
                return Response(
                    {"erro": "Funcionários não encontrados."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            for funcionario in funcionarios:

          
                if funcionario.criado_por != usuario:
                    return Response(
                        {"erro": "Usuário não possui permissão para remover esse funcionário."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                funcionario.delete()

            return Response(
                {
                    "message": "Funcionários removidos com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EditarFuncionarioView(APIView):

    def post(self, request):

        funcionario_id = request.data.get("funcionario_id")

        if not funcionario_id:
            return Response(
                {"erro": "ID do funcionário é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        nome = request.data.get("nome")
        foto = request.data.get("foto")

        try:

            funcionario = Funcionario.objects.filter(id=funcionario_id).first()

            if not funcionario:
                return Response(
                    {"erro": "Funcionário não encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
                
            if nome and nome != funcionario.nome:
                funcionario.nome = nome
            if foto and foto != funcionario.foto:
                funcionario.foto = foto

            funcionario.save()

            return Response(
                {
                    "message": "Funcionário editado com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )
            
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RemoverFuncionariosEmpresaView(APIView):

    def post(self, request):

        funcionarios_ids = request.data.get("funcionarios_ids")

        if not funcionarios_ids:
            return Response(
                {"erro": "ID do funcionário é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        empresa_id = request.data.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            funcionarios = Funcionario.objects.filter(id__in=funcionarios_ids)

            if not funcionarios:
                return Response(
                    {"erro": "Funcionários não encontrados."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            empresa = Empresa.objects.get(id=empresa_id)

            if empresa.criado_por != usuario:
                return Response(
                    {"erro": "Usuário não possui permissão para remover esse funcionário."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            for funcionario in funcionarios:

                if funcionario.criado_por != usuario:
                    return Response(
                        {"erro": "Usuário não possui permissão para remover esse funcionário."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                funcionario.empresas.remove(empresa)

            return Response(
                {
                    "message": "Funcionários removidos com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)