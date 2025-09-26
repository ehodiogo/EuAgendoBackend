from .models import Agendamento
from rest_framework import serializers
from funcionario.serializers import FuncionarioSerializer

class AgendamentoSerializer(serializers.ModelSerializer):

    duracao_servico = serializers.SerializerMethodField()
    cliente_nome = serializers.SerializerMethodField()
    funcionario_nome = serializers.SerializerMethodField()
    servico_nome = serializers.SerializerMethodField()

    def get_duracao_servico(self, obj):
        return obj.servico.duracao

    def get_cliente_nome(self, obj):
        return obj.cliente.nome

    def get_funcionario_nome(self, obj):
        return obj.funcionario.nome

    def get_servico_nome(self, obj):
        return obj.servico.nome

    class Meta:
        model = Agendamento
        fields = "__all__"


class AgendamentoAvaliacaoSerializer(serializers.ModelSerializer):

    duracao_servico = serializers.SerializerMethodField()
    servico_nome = serializers.SerializerMethodField()
    cliente_nome = serializers.SerializerMethodField()
    funcionario = FuncionarioSerializer()

    def get_duracao_servico(self, obj):
        return obj.servico.duracao

    def get_servico_nome(self, obj):
        return obj.servico.nome

    def get_cliente_nome(self, obj):
        return obj.cliente.nome

    class Meta:
        model = Agendamento
        fields = [
            'id',
            'duracao_servico',
            'servico_nome',
            'cliente_nome',
            'funcionario',
            'data',
            'hora',
            'nota_avaliacao',
            'descricao_avaliacao',
            'compareceu_agendamento'
        ]
