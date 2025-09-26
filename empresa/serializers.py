from .models import Empresa
from rest_framework import serializers
from funcionario.serializers import ServicoFuncionarioSerializer
from plano.models import PlanoUsuario
from django.utils import timezone

class EmpresaSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    servicos = serializers.SerializerMethodField()
    funcionarios = serializers.SerializerMethodField()
    assinatura_ativa = serializers.SerializerMethodField()
    assinatura_vencimento = serializers.SerializerMethodField()
    endereco = serializers.SerializerMethodField()

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
        print("Servicos ", obj.servicos.all())
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

    def get_endereco(self, obj):
        return obj.endereco_completo()

    class Meta:
        model = Empresa
        fields = (
            "id",
            "nome",
            "cnpj",
            "endereco",
            "bairro",
            "cidade",
            "estado",
            "pais",
            "telefone",
            "email",
            "logo",
            "servicos",
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
        )


class EmpresaServicoFuncionarioSerializer(serializers.ModelSerializer):

    funcionarios = ServicoFuncionarioSerializer(many=True)

    class Meta:
        model = Empresa
        fields = ['nome', 'cnpj', 'funcionarios']