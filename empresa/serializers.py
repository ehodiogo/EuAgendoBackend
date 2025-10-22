from locacao.serializers import LocacaoSerializer
from .models import Empresa
from rest_framework import serializers
from funcionario.serializers import ServicoFuncionarioSerializer
from plano.models import PlanoUsuario
from django.utils import timezone
from agendamento.models import Agendamento
from django.db.models import Avg

class EmpresaSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    servicos = serializers.SerializerMethodField()
    locacoes = serializers.SerializerMethodField()
    funcionarios = serializers.SerializerMethodField()
    assinatura_ativa = serializers.SerializerMethodField()
    assinatura_vencimento = serializers.SerializerMethodField()
    avaliacoes_empresa = serializers.SerializerMethodField()
    nota_empresa = serializers.SerializerMethodField()

    def get_assinatura_ativa(self, obj):

        user = obj.users.first()

        assinatura = PlanoUsuario.objects.filter(usuario=user).first()

        if assinatura:
            minutos_restantes = (assinatura.expira_em - timezone.now()).total_seconds() / 60
            horas_restantes = minutos_restantes / 60

            if horas_restantes < 0:
                return False

            return True

        return False

    def get_assinatura_vencimento(self, obj):

        user = obj.users.first()

        assinatura = PlanoUsuario.objects.filter(usuario=user).first()

        if assinatura:
            minutos_restantes = (assinatura.expira_em - timezone.now()).total_seconds() / 60
            horas_restantes = minutos_restantes / 60

            return horas_restantes

        return None

    def get_logo(self, obj):
        if obj.logo:
            if obj.logo.imagem and obj.logo.imagem.name:
                return obj.logo.imagem.url.split("AWSAccessKeyId=")[0]
            if obj.logo.imagem_url:
                return obj.logo.imagem_url
        return None

    def get_servicos(self, obj):
        return [
            {"nome": servico.nome, "preco": servico.preco, "duracao": servico.duracao}
            for servico in obj.servicos.all()
        ]

    def get_funcionarios(self, obj):
        funcionarios = obj.funcionarios.all()
        return [
            {
                "id": funcionario.id,
                "nome": funcionario.nome,
                "foto": funcionario.foto.imagem.url if funcionario.foto else None or funcionario.foto.imagem_url if funcionario.foto else None,
            }
            for funcionario in funcionarios
        ]

    def get_locacoes(self, obj):
        return [
            {"nome": locacao.nome, "preco": locacao.preco, "duracao": locacao.duracao}
            for locacao in obj.locacoes.all()
        ]

    def get_avaliacoes_empresa(self, obj):
        if obj.tipo == 'Serviço':
            return Agendamento.objects.filter(funcionario__empresas__id=obj.id, is_continuacao=False, nota_avaliacao__isnull=False).count()
        else:
            return Agendamento.objects.filter(locacao__in=obj.locacoes.all(), is_continuacao=False, nota_avaliacao__isnull=False).count()


    def get_nota_empresa(self, obj):
        if obj.tipo == 'Serviço':
            resultado = Agendamento.objects.filter(
                funcionario__empresas__id=obj.id,
                is_continuacao=False,
                nota_avaliacao__isnull=False
            ).aggregate(media=Avg('nota_avaliacao'))

            return resultado['media'] or 0
        else:
            resultado = Agendamento.objects.filter(
                locacao__in=obj.locacoes.all(),
                is_continuacao=False,
                nota_avaliacao__isnull=False
            ).aggregate(media=Avg('nota_avaliacao'))

            return resultado['media'] or 0


    class Meta:
        model = Empresa
        fields = (
            "id",
            "nome",
            "slug",
            "tipo",
            "endereco",
            "bairro",
            "cidade",
            "estado",
            "pais",
            "telefone",
            "email",
            "logo",
            "servicos",
            "locacoes",
            "horario_abertura_dia_semana",
            "horario_fechamento_dia_semana",
            "horario_abertura_fim_de_semana",
            "horario_fechamento_fim_de_semana",
            "abre_sabado",
            "abre_domingo",
            "para_almoco",
            "horario_pausa_inicio",
            "horario_pausa_fim",
            "funcionarios",
            "assinatura_ativa",
            "assinatura_vencimento",
            'nota_empresa',
            'avaliacoes_empresa',
            'is_online'
        )


class EmpresaServicoFuncionarioSerializer(serializers.ModelSerializer):

    funcionarios = ServicoFuncionarioSerializer(many=True)
    locacoes = LocacaoSerializer(many=True)

    class Meta:
        model = Empresa
        fields = ['nome', 'funcionarios', 'locacoes', 'tipo', 'slug']
