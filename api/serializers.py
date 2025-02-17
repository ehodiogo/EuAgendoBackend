from rest_framework import serializers
from agendamento.models import Agendamento
from cliente.models import Cliente
from core.models import Imagem
from empresa.models import Empresa
from funcionario.models import Funcionario
from servico.models import Servico

class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = "__all__"


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"


class ImagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Imagem
        fields = "__all__"


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = "__all__"


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = "__all__"


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = "__all__"
