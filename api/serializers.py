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

    logo = serializers.SerializerMethodField()
    servicos = serializers.SerializerMethodField()

    def get_logo(self, obj):
        return obj.logo.imagem.url
    
    def get_servicos(self, obj):
        return [
            f"{servico.nome} - R${servico.preco} - {servico.duracao}"
            for servico in obj.servicos.all()
        ]
    
    class Meta:
        model = Empresa
        fields = "nome", "cnpj", "endereco", "telefone", "email", "logo", "servicos", "horario_abertura_dia_semana", "horario_fechamento_dia_semana", "horario_abertura_fim_de_semana", "horario_fechamento_fim_de_semana", "abre_sabado", "abre_domingo"


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = "__all__"


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = "__all__"
