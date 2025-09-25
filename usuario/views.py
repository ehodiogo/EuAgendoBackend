from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import PerfilUsuario
from .serializers import PerfilUsuarioSerializer
from rest_framework.authtoken.models import Token

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
