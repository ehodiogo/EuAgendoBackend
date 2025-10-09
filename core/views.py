from .models import Imagem
from .serializers import ImagemSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .tasks import enviar_email_contato_task

class ImagemViewSet(viewsets.ModelViewSet):
    queryset = Imagem.objects.all()
    serializer_class = ImagemSerializer


@api_view(['POST'])
def enviar_contato(request):
    nome = request.data.get('nome')
    email = request.data.get('email')
    mensagem = request.data.get('mensagem')

    if not all([nome, email, mensagem]):
        return Response(
            {"erro": "Todos os campos (nome, email, mensagem) são obrigatórios."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        enviar_email_contato_task.delay(nome, email, mensagem)

        return Response(
            {"sucesso": "Mensagem recebida com sucesso. Em breve entraremos em contato."},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"erro": f"Erro interno ao processar sua mensagem: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )