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
from datetime import date, datetime, timedelta
from .tasks import enviar_email_avaliacao

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

    @action(detail=True, methods=["post"], url_path="marcar-compareceu")
    def marcar_compareceu(self, request, identificador=None):
        agendamento = self.get_object()
        if agendamento.compareceu_agendamento:
            return Response(
                {"message": "Agendamento já marcado como compareceu."},
                status=status.HTTP_400_BAD_REQUEST
            )

        agendamento.compareceu_agendamento = True
        agendamento.save()

        enviar_email_avaliacao.delay(agendamento.id, agendamento.cliente.email)

        return Response(
            {"message": "Agendamento marcado como compareceu e e-mail enviado."},
            status=status.HTTP_200_OK
        )

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

    @action(detail=False, methods=["get"], url_path="sem-comparecimento")
    def sem_comparecimento(self, request):
        empresa_id = request.query_params.get("empresa_id")
        if not empresa_id:
            return Response(
                {"erro": "Parâmetro 'empresa_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return Response(
                {"erro": "Empresa não encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        if empresa.tipo == "Serviço":
            agendamentos = Agendamento.objects.filter(
                funcionario__empresas__id=empresa_id,
                compareceu_agendamento=False
            ).order_by('data', 'hora')
        else:
            agendamentos = Agendamento.objects.filter(
                locacao__in=empresa.locacoes.all(),
                compareceu_agendamento=False
            ).order_by('data', 'hora')

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        descricao = request.data.get("descricao")

        if not data or not hora or not cliente_nome or not cliente_email or not cliente_numero:
            return Response({"erro": "Todos os campos são obrigatórios."},
                            status=status.HTTP_400_BAD_REQUEST)

        if id_funcionario and not servico_nome:
            return Response({"erro": "Todos os campos são obrigatórios."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            data_hora = parse_datetime(f"{data}T{hora}:00")
            if not data_hora:
                raise ValueError("Data ou hora inválidos.")
        except ValueError as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        funcionario = None
        servico = None
        locacao = None
        if id_funcionario and servico_nome:
            try:
                funcionario = Funcionario.objects.get(id=id_funcionario)
            except Funcionario.DoesNotExist:
                return Response({"erro": "Funcionário não encontrado."},
                                status=status.HTTP_404_NOT_FOUND)

            try:
                servico = Servico.objects.get(nome=servico_nome, funcionarios=funcionario)
            except Servico.DoesNotExist:
                return Response({"erro": "Serviço não encontrado."},
                                status=status.HTTP_404_NOT_FOUND)
        elif servico_nome:
            try:
                locacao = Locacao.objects.get(nome=servico_nome)
            except Locacao.DoesNotExist:
                return Response({"erro": "Locação não encontrada."},
                                status=status.HTTP_404_NOT_FOUND)

        cliente, _ = Cliente.objects.get_or_create(
            nome=cliente_nome, email=cliente_email, telefone=cliente_numero
        )

        duracao_total = None
        if servico:
            duracao_total = int(servico.duracao)
        elif locacao:
            duracao_total = int(locacao.duracao)

        duracao_minima = int(duracao_minima)
        quantidade_blocos = max(1, duracao_total // duracao_minima)

        horarios = [
            (datetime.combine(data_hora.date(), data_hora.time()) + timedelta(minutes=duracao_minima * i)).time()
            for i in range(quantidade_blocos)
        ]

        for hora_check in horarios:
            conflito = Agendamento.objects.filter(
                data=data_hora.date(),
                hora=hora_check,
                funcionario=funcionario if funcionario else None,
                locacao=locacao if locacao else None
            ).exists()
            if conflito:
                return Response({"erro": f"O horário {hora_check} já está ocupado."},
                                status=status.HTTP_400_BAD_REQUEST)

        agendamentos_criados = []
        for i, hora_create in enumerate(horarios):
            agendamento = Agendamento.objects.create(
                data=data_hora.date(),
                hora=hora_create,
                cliente=cliente,
                funcionario=funcionario,
                servico=servico,
                locacao=locacao,
                is_continuacao=(i > 0),
                observacao=descricao
            )
            agendamentos_criados.append(agendamento)

        agendamento = agendamentos_criados[0]
        return Response({
            "id": agendamento.id,
            "funcionario": funcionario.nome if funcionario else None,
            "data": agendamento.data,
            "hora": agendamento.hora,
            "cliente_nome": cliente.nome,
            "cliente_email": cliente.email,
            "cliente_numero": cliente.telefone,
            "servico_nome": servico.nome if servico else None,
            "locacao_nome": locacao.nome if locacao else None,
            "quantidade_continuacao": len(agendamentos_criados) - 1
        }, status=status.HTTP_201_CREATED)

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