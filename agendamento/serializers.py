from .models import Agendamento
from rest_framework import serializers
from funcionario.serializers import FuncionarioSerializer
from empresa.models import Empresa
from agendamento.models import Agendamento

class AgendamentoSerializer(serializers.ModelSerializer):

    duracao_servico = serializers.SerializerMethodField()
    cliente_nome = serializers.SerializerMethodField()
    funcionario_nome = serializers.SerializerMethodField()
    servico_nome = serializers.SerializerMethodField()
    locacao_nome = serializers.SerializerMethodField()
    duracao_locacao = serializers.SerializerMethodField()
    empresa_nome = serializers.SerializerMethodField()
    preco = serializers.SerializerMethodField()

    def get_duracao_servico(self, obj):
        return obj.servico.duracao if obj.servico else None

    def get_cliente_nome(self, obj):
        return obj.cliente.nome

    def get_funcionario_nome(self, obj):
        return obj.funcionario.nome if obj.funcionario else None

    def get_servico_nome(self, obj):
        return obj.servico.nome if obj.servico else None

    def get_locacao_nome(self, obj):
        return obj.locacao.nome if obj.locacao else None

    def get_duracao_locacao(self, obj):
        return obj.locacao.duracao if obj.locacao else None

    def get_empresa_nome(self, obj):
        if obj.locacao:
            return Empresa.objects.get(locacoes=obj.locacao).nome
        else:
            return Empresa.objects.get(servicos=obj.servico).nome

    def get_preco(self, obj):
        if obj.locacao:
            return obj.locacao.preco
        else:
            return obj.servico.preco

    class Meta:
        model = Agendamento
        fields = "__all__"


class AgendamentoAvaliacaoSerializer(serializers.ModelSerializer):

    duracao_servico = serializers.SerializerMethodField()
    servico_nome = serializers.SerializerMethodField()
    cliente_nome = serializers.SerializerMethodField()
    locacao_nome = serializers.SerializerMethodField()
    funcionario = FuncionarioSerializer()

    def get_duracao_servico(self, obj):
        return obj.servico.duracao if obj.servico else None

    def get_servico_nome(self, obj):
        return obj.servico.nome if obj.servico else None

    def get_cliente_nome(self, obj):
        return obj.cliente.nome

    def get_locacao_nome(self, obj):
        return obj.locacao.nome if obj.locacao else None

    class Meta:
        model = Agendamento
        fields = [
            'id',
            'observacao',
            'duracao_servico',
            'servico_nome',
            'cliente_nome',
            'funcionario',
            'locacao_nome',
            'data',
            'hora',
            'nota_avaliacao',
            'descricao_avaliacao',
            'compareceu_agendamento'
        ]
