from .models import Servico
from .serializers import ServicoSerializer
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from funcionario.models import Funcionario
from empresa.models import Empresa

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

        servico_data = {
            "nome": request.data.get("nome"),
            "preco": request.data.get("preco"),
            "duracao": request.data.get("duracao"),
            "criado_por": usuario.pk,
        }

        serializer = ServicoSerializer(data=servico_data)
        if serializer.is_valid():
            servico = serializer.save()
            return Response(
                {
                    "message": "Serviço criado com sucesso.",
                    "servico": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            print(e)
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
            print(e)
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