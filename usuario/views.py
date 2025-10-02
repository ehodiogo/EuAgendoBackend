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
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

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
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{SITE_URL}/reset-password/?uid={uid}&token={token}"

            assunto = "🔑 Recuperação de Senha"
            mensagem_txt = (
                f"Olá {user.first_name or user.email},\n\n"
                f"Recebemos uma solicitação para redefinir sua senha.\n"
                f"Para criar uma nova senha, clique no link abaixo:\n\n"
                f"{reset_url}\n\n"
                f"Se você não solicitou a redefinição, apenas ignore este e-mail.\n\n"
                f"Acesse sua conta: {SITE_URL}\n\n"
                "Equipe VemAgendar 🚀"
            )

            mensagem_html = f"""
                <html>
                  <body style="font-family: Arial, sans-serif; color:#333; background:#f9f9f9; padding:20px;">
                    <div style="max-width:600px; margin:auto; background:#fff; padding:25px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
                      <h2 style="color:#2c7be5;">🔑 Recuperação de Senha</h2>
                      <p>Olá <b>{user.first_name or user.email}</b>,</p>
                      <p>Recebemos uma solicitação para redefinir sua senha.</p>
                      <p>Clique no botão abaixo para criar uma nova senha:</p>
                      <div style="margin-top:25px; text-align:center;">
                        <a href="{reset_url}" style="background:#2c7be5; color:#fff; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
                          🔐 Redefinir Senha
                        </a>
                      </div>
                      <p style="margin-top:20px;">Se você não solicitou a redefinição, apenas ignore este e-mail.</p>
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

class ResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not uidb64 or not token or not new_password:
            return Response(
                {"erro": "Parâmetros uid, token e new_password são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception as e:
            return Response({"erro": "UID inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"erro": "Token inválido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"mensagem": "Senha redefinida com sucesso!"},
            status=status.HTTP_200_OK,
        )