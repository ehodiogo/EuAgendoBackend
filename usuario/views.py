from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import PerfilUsuario
from .serializers import PerfilUsuarioSerializer, LoginSerializer, RegisterSerializer
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from plano.models import PlanoUsuario, Plano
from datetime import datetime, timedelta, date
import pytz
from empresa.serializers import EmpresaSerializer
from empresa.models import Empresa
from agendamento.models import Agendamento

class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            user_plan = PlanoUsuario.objects.filter(usuario=user).first()

            if not user_plan:
                plano, _ = Plano.objects.get_or_create(nome="Free Trial", valor=0, quantidade_empresas=1,
                                                       quantidade_funcionarios=1, duracao_em_dias=7)

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

class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer

    def _get_usuario(self, request):
        access_token = request.query_params.get("usuario_token") or request.data.get("usuario_token")
        token_obj = Token.objects.filter(key=access_token).first()
        if not token_obj:
            return None
        return token_obj.user

    @action(detail=False, methods=["get"], url_path="me")
    def get_me(self, request):
        try:
            usuario = self._get_usuario(request)
            if not usuario:
                return Response({"erro": "Token de acesso inválido."}, status=status.HTTP_400_BAD_REQUEST)

            perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
            serializer = self.get_serializer(perfil)
            return Response(serializer.data)
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["patch"], url_path="settings")
    def update_settings(self, request):
        usuario = self._get_usuario(request)

        if not usuario:
            return Response({"erro": "Token de acesso inválido."}, status=status.HTTP_400_BAD_REQUEST)

        perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
        perfil.receive_email_notifications = request.data.get("receiveEmailNotifications", False)
        perfil.save()
        return Response({"success": True})

    @action(detail=False, methods=["post"], url_path="affiliate-code")
    def regenerate_affiliate_code(self, request):
        usuario = self._get_usuario(request)
        if not usuario:
            return Response({"erro": "Token de acesso inválido."}, status=status.HTTP_400_BAD_REQUEST)

        perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
        perfil.regenerar_codigo_afiliado()
        return Response({"affiliateCode": perfil.codigo_afiliado}, status=status.HTTP_200_OK)

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
