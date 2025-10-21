from rest_framework import viewsets
from .models import Funcionario
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import FuncionarioSerializer
from agendamento.serializers import AgendamentoSerializer
from empresa.models import Empresa
from rest_framework.views import APIView
from django.utils.dateparse import parse_date
from agendamento.models import Agendamento
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authtoken.models import Token
from django.core.files.base import ContentFile
import os
from core.models import Imagem

class FuncionarioViewSet(viewsets.ModelViewSet):
    serializer_class = FuncionarioSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = [
        "nome",
        "empresas__nome",
    ]

    queryset = Funcionario.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_slug = self.request.query_params.get("empresa_slug")

        empresa = None

        if empresa_slug:
            empresa = Empresa.objects.filter(slug=empresa_slug)

        if empresa:
            queryset = empresa[0].funcionarios.all()

        return queryset

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
                "funcionarios": [{
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
            print("Erro: ", e)
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