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
from datetime import date
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

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

    @action(detail=False, methods=["get"])
    def filtrar_por_empresa(self, request):
        nome = request.query_params.get("nome", None)
        cnpj = request.query_params.get("cnpj", None)

        if nome:
            empresas = Empresa.objects.filter(nome__icontains=nome)
        elif cnpj:
            empresas = Empresa.objects.filter(cnpj__icontains=cnpj)
        else:
            return Response({"error": "Informe o nome ou CNPJ da empresa."})

        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

class AgendamentoCreateView(APIView):
    def post(self, request, *args, **kwargs):

        id_funcionario = request.data.get("id_funcionario")
        data = request.data.get("data")
        hora = request.data.get("hora")
        cliente_nome = request.data.get("cliente_nome")
        cliente_email = request.data.get("cliente_email")  
        cliente_numero = request.data.get("cliente_numero") 
        servico_nome = request.data.get("servico_nome")

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
            # TODO
            servico = Servico.objects.get(nome=servico_nome) # arrumar para puxar o serviço pelo funcionário
        except Servico.DoesNotExist:
            return Response(
                {"erro": "Serviço não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

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

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(token.key),
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
            agendamentos = Agendamento.objects.filter(data=date.today(), funcionario__empresas__id=empresa_id)
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
