from empresa.models import Empresa
from locacao.models import Locacao
from .models import Agendamento
from .serializers import AgendamentoSerializer, AgendamentoAvaliacaoSerializer
from rest_framework import viewsets
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from django.utils.dateparse import parse_datetime
from funcionario.models import Funcionario
from cliente.models import Cliente
from servico.models import Servico
from rest_framework.response import Response
from rest_framework import status
from datetime import date, datetime

class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["funcionario"]

    def get_renderers(self):
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

        if id_funcionario and not servico_nome:
            return Response(
                {"erro": "Todos os campos são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not data
            or not hora
            or not cliente_nome
            or not cliente_email
            or not cliente_numero
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

        funcionario = None
        servico = None
        if id_funcionario and servico_nome:
            try:
                funcionario = Funcionario.objects.get(id=id_funcionario)
            except Funcionario.DoesNotExist:
                return Response(
                    {"erro": "Funcionário não encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                servico = Servico.objects.get(nome=servico_nome, funcionarios=funcionario)
            except Servico.DoesNotExist:
                return Response(
                    {"erro": "Serviço não encontrado."}, status=status.HTTP_404_NOT_FOUND
                )

        cliente, created = Cliente.objects.get_or_create(
            nome=cliente_nome, email=cliente_email, telefone=cliente_numero
        )

        locacao = None
        if servico_nome and not id_funcionario:
            locacao = Locacao.objects.get(nome=servico_nome)

        agendamento = None
        if servico:
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

        if locacao:
            if int(locacao.duracao) > int(duracao_minima):

                quantia_agendamentos = int(locacao.duracao) // int(duracao_minima)

                agendamento = Agendamento.objects.create(
                    data=data_hora.date(),
                    hora=data_hora.time(),
                    cliente=cliente,
                    locacao=locacao,
                )

                for i in range(1, quantia_agendamentos):
                    nova_hora = datetime.combine(datetime.today(), data_hora.time()) + timedelta(
                        minutes=int(duracao_minima) * i)
                    nova_hora = nova_hora.time()

                    agendamento = Agendamento.objects.create(
                        data=data_hora.date(),
                        hora=nova_hora,
                        cliente=cliente,
                        locacao=locacao,
                        is_continuacao=True,
                    )
            else:

                agendamento = Agendamento.objects.create(
                    data=data_hora.date(),
                    hora=data_hora.time(),
                    cliente=cliente,
                    locacao=locacao,
                )

        return Response(
            {
                "id": agendamento.id,
                "funcionario": funcionario.nome if funcionario else None,
                "data": agendamento.data,
                "hora": agendamento.hora,
                "cliente_nome": cliente.nome,
                "cliente_email": cliente.email,
                "cliente_numero": cliente.telefone,
                "servico_nome": servico.nome if servico else None,
                "locacao_nome": locacao.nome if locacao else None,
            },
            status=status.HTTP_201_CREATED,
        )


class AgendamentosHojeView(APIView):

    def get(self, request, *args, **kwargs):
        empresa_id = request.query_params.get("empresa_id")

        if empresa_id:
            empresa = Empresa.objects.get(id=empresa_id)

            if empresa.tipo == "Serviço":
                agendamentos = Agendamento.objects.filter(data=date.today(), funcionario__empresas__id=empresa_id,
                                                          is_continuacao=False, hora__gte=datetime.now().time()).order_by(
                    'hora')
            else:
                agendamentos = Agendamento.objects.filter(locacao__in=empresa.locacoes.all(), is_continuacao=False, data=date.today(), hora__gte=datetime.now().time()).order_by(
                    'hora'
                )
            serializer = AgendamentoSerializer(agendamentos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"erro": "Parâmetro 'empresa_id' é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AgendamentoDetailView(APIView):
    serializer_class = AgendamentoAvaliacaoSerializer

    def get(self, request, identificador, *args, **kwargs):
        try:
            agendamento = Agendamento.objects.get(identificador=identificador)
        except Agendamento.DoesNotExist:
            return Response({"detail": "Agendamento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AgendamentoAvaliacaoSerializer(agendamento)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AgendamentoCancelarView(APIView):

    def post(self, request, identificador, *args, **kwargs):
        try:
            agendamento = Agendamento.objects.get(identificador=identificador)
        except Agendamento.DoesNotExist:
            return Response({"detail": "Agendamento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        agendamento.delete()

        # TODO: enviar email p empres ae p cliente
        return Response({"detail": "Agendamento cancelado com sucesso."}, status=status.HTTP_200_OK)