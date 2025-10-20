from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from empresa.models import Empresa
from locacao.models import Locacao
from locacao.serializers import LocacaoSerializer
from plano.models import PlanoUsuario
from agendamento.models import Agendamento
from agendamento.serializers import AgendamentoSerializer
from django.utils.dateparse import parse_date


class LocacoesCriadasUsuarioEmpresaView(APIView):

    def get(self, request, *args, **kwargs):

        usuario_token = request.query_params.get("usuario_token")
        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        token_obj = Token.objects.filter(key=usuario_token).first()
        if not token_obj:
            return Response(
                {"erro": "Token de acesso é inválido ou expirado."}, status=status.HTTP_401_UNAUTHORIZED
            )
        usuario = token_obj.user

        empresa_id = request.query_params.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            empresa = Empresa.objects.get(id=empresa_id, criado_por=usuario)

            locacoes = empresa.locacoes.all()

            return Response(
                {
                    "locacoes": LocacaoSerializer(
                        locacoes, many=True
                    ).data
                },
                status=status.HTTP_200_OK,
            )

        except Empresa.DoesNotExist:
            return Response(
                {"erro": "Empresa não encontrada ou o usuário não tem permissão para acessá-la."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(e)
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CadastrarLocacaoView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        usuario_token = data.get("usuario_token")
        empresa_id = data.get("empresa_id")

        if not usuario_token:
            return Response({"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_obj = Token.objects.get(key=usuario_token)
            usuario = token_obj.user
        except Token.DoesNotExist:
            return Response({"erro": "Token de acesso é inválido."}, status=status.HTTP_401_UNAUTHORIZED)

        if not empresa_id:
            return Response({"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            empresa = Empresa.objects.get(id=empresa_id, criado_por=usuario)
        except Empresa.DoesNotExist:
            return Response({"erro": "Empresa não encontrada ou o usuário não tem permissão."},
                            status=status.HTTP_404_NOT_FOUND)

        locacao_data = {
            'nome': data.get('locacao_nome'),
            'descricao': data.get('locacao_descricao'),
            'duracao': data.get('locacao_duracao'),
            'preco': data.get('locacao_preco'),
            'criado_por': usuario.pk,
            'pontos_resgate': data.get('locacao_pontos_resgate'),
            'pontos_gerados': data.get('locacao_pontos_gerados'),
        }

        uso_plano = PlanoUsuario.objects.get(
            usuario=usuario,
        )

        if uso_plano.plano.quantidade_locacoes == empresa.locacoes.count():
            return Response(
                f'Você extrapolou o limite de locações permitidas a serem criadas.',
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LocacaoSerializer(data=locacao_data)
        if serializer.is_valid():
            locacao_nova = serializer.save()

            empresa.locacoes.add(locacao_nova)
            empresa.save()

            return Response(
                {
                    "mensagem": "Item de locação cadastrado com sucesso!",
                    "id": locacao_nova.id,
                    "locacao": serializer.data
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RemoverLocacaoView(APIView):
    def post(self, request, *args, **kwargs):
        locacao_id = request.data.get("locacao_id")
        if not locacao_id:
            return Response({"erro": "ID da locação é obrigatório."}, status=400)

        try:
            locacao = Locacao.objects.get(id=locacao_id)
            locacao.delete()
            return Response({"mensagem": "Locação removida com sucesso!"}, status=200)
        except Locacao.DoesNotExist:
            return Response({"erro": "Locação não encontrada."}, status=404)

class EditarLocacaoView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        usuario_token = data.get("usuario_token")
        locacao_id = data.get("locacao_id")

        if not usuario_token:
            return Response({"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_obj = Token.objects.get(key=usuario_token)
            usuario = token_obj.user
        except Token.DoesNotExist:
            return Response({"erro": "Token de acesso inválido."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            locacao = Locacao.objects.get(id=locacao_id, criado_por=usuario)
        except Locacao.DoesNotExist:
            return Response({"erro": "Locação não encontrada ou usuário sem permissão."}, status=status.HTTP_404_NOT_FOUND)

        locacao_nome = data.get('locacao_nome')
        locacao_descricao = data.get('locacao_descricao')
        locacao_duracao = data.get('locacao_duracao')
        locacao_preco = data.get('locacao_preco')
        pontos_resgate = data.get('locacao_pontos_resgate')
        pontos_gerados = data.get('locacao_pontos_gerados')

        if locacao_nome != locacao.nome and locacao_nome is not None:
            locacao.nome = locacao_nome

        if locacao_descricao != locacao.descricao and locacao_descricao is not None:
            locacao.descricao = locacao_descricao

        if locacao_duracao != locacao.duracao and locacao_duracao is not None:
            locacao.duracao = locacao_duracao

        if locacao_preco != locacao.preco and locacao_preco is not None:
            locacao.preco = locacao_preco

        if pontos_resgate is not None and pontos_resgate != locacao.pontos_resgate:
            locacao.pontos_resgate = pontos_resgate

        if pontos_gerados is not None and pontos_gerados != locacao.pontos_gerados:
            locacao.pontos_gerados = pontos_gerados

        locacao.save()

        return Response({"mensagem": "Locação atualizada com sucesso!", "locacao": LocacaoSerializer(locacao).data},)

class LocacaoAgendamentoView(APIView):
    def get(self, request, *args, **kwargs):
        id_locacao = request.query_params.get("id_locacao")
        data_str = request.query_params.get(
            "data"
        )

        if not id_locacao or not data_str:
            return Response(
                {"erro": "Os parâmetros 'id_locacao' e 'data' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            locacao = Locacao.objects.get(id=id_locacao)
        except Locacao.DoesNotExist:
            return Response(
                {"erro": "Locação não encontrada."},
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

        agendamentos = Agendamento.objects.filter(locacao=locacao, data=data)

        if not agendamentos:
            return Response(
                [],
                status=status.HTTP_200_OK,
            )

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)