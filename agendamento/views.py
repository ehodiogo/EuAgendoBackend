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


class AgendamentosHojeView(APIView):

    def get(self, request, *args, **kwargs):
        empresa_id = request.query_params.get("empresa_id")

        if empresa_id:
            agendamentos = Agendamento.objects.filter(data=date.today(), funcionario__empresas__id=empresa_id,
                                                      is_continuacao=False, hora__gte=datetime.now().time()).order_by(
                'hora')
            serializer = AgendamentoSerializer(agendamentos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"erro": "Parâmetro 'empresa_id' é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST,
        )
