from cliente.models import PontoClienteEmpresa
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
    cliente_pontos = serializers.SerializerMethodField()
    pontos_para_resgatar = serializers.SerializerMethodField()

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

    def get_pontos_para_resgatar(self, obj):
        if obj.servico:
            return obj.servico.pontos_resgate
        else:
            return obj.locacao.pontos_resgate

    def get_cliente_pontos(self, obj):
        empresa = None

        if obj.servico:
            empresa = Empresa.objects.get(servicos=obj.servico)
        else:
            empresa = Empresa.objects.get(locacoes=obj.locacao)

        pontos_cliente_empresa, _ = PontoClienteEmpresa.objects.get_or_create(
            empresa=empresa,
            cliente=obj.cliente,
        )

        return pontos_cliente_empresa.pontos

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
