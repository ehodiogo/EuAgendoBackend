from .serializers import AgendamentoSerializer, ClienteSerializer, EmpresaSerializer, FuncionarioSerializer, ImagemSerializer, ServicoSerializer
from agendamento.models import Agendamento
from cliente.models import Cliente
from core.models import Imagem
from empresa.models import Empresa
from funcionario.models import Funcionario
from servico.models import Servico
from rest_framework import viewsets,filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class ImagemViewSet(viewsets.ModelViewSet):
    queryset = Imagem.objects.all()
    serializer_class = ImagemSerializer


class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=400)

        empresas = Empresa.objects.filter(nome__icontains=termo) | Empresa.objects.filter(cnpj__icontains=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=400)

        empresas = Empresa.objects.filter(nome__icontains=termo) | Empresa.objects.filter(cnpj__icontains=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)


class FuncionarioViewSet(viewsets.ModelViewSet):
    serializer_class = FuncionarioSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = [
        "nome",
        "empresas__nome",
        "empresas__cnpj",
    ]

    queryset = Funcionario.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_nome = self.request.query_params.get("empresa_nome")
        empresa_cnpj = self.request.query_params.get("empresa_cnpj")

        if empresa_nome:
            queryset = queryset.filter(empresas__nome__icontains=empresa_nome)
        if empresa_cnpj:
            queryset = queryset.filter(empresas__cnpj__icontains=empresa_cnpj)

        return queryset


class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
