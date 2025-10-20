from rest_framework import viewsets, status
from .models import Cliente, PontoClienteEmpresa
from .serializers import ClienteSerializer, PontoClienteSerializer
from django.shortcuts import get_object_or_404
from agendamento.models import Agendamento
from rest_framework.decorators import api_view
from rest_framework.response import Response
from agendamento.serializers import AgendamentoSerializer
from .serializers import ClienteSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

@api_view(['GET'])
def agendamentos_por_cliente(request, identificador_cliente):
    try:
        cliente = Cliente.objects.get(identificador=identificador_cliente)
    except Cliente.DoesNotExist:
        return Response({'error': 'Cliente não encontrado'}, status=404)

    agendamentos = Agendamento.objects.filter(cliente=cliente)
    serializer = AgendamentoSerializer(agendamentos, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def cliente_detalhe(request, identificador):
    """Retorna os dados do cliente pelo identificador."""
    try:
        cliente = Cliente.objects.get(identificador=identificador)
    except Cliente.DoesNotExist:
        return Response({'detail': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ClienteSerializer(cliente)
    return Response(serializer.data)

@api_view(['GET'])
def pontos_cliente(request, identificador):
    try:
        cliente = Cliente.objects.get(identificador=identificador)
    except Cliente.DoesNotExist:
        return Response({'detail': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    pontos_cliente = PontoClienteEmpresa.objects.filter(cliente=cliente)
    serializer = PontoClienteSerializer(pontos_cliente, many=True)
    return Response(serializer.data)