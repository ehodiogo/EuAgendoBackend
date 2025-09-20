from rest_framework import serializers
from agendamento.models import Agendamento
from cliente.models import Cliente
from core.models import Imagem
from empresa.models import Empresa
from funcionario.models import Funcionario
from servico.models import Servico
from django.contrib.auth import get_user_model, authenticate
from plano.models import Plano, PlanoUsuario
from django.utils import timezone

class AgendamentoSerializer(serializers.ModelSerializer):

    duracao_servico = serializers.SerializerMethodField()

    def get_duracao_servico(self, obj):
        return obj.servico.duracao

    class Meta:
        model = Agendamento
        fields = "__all__"

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

class ImagemSerializer(serializers.ModelSerializer):

    imagem_url = serializers.SerializerMethodField()

    def get_imagem_url(self, obj):
        return obj.imagem.url.split("AWSAccessKeyId=")[0]

    class Meta:
        model = Imagem
        fields = "imagem", "imagem_url"

class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = "__all__"

class EmpresaSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    servicos = serializers.SerializerMethodField()
    funcionarios = serializers.SerializerMethodField()
    assinatura_ativa = serializers.SerializerMethodField()
    assinatura_vencimento = serializers.SerializerMethodField()

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
            return obj.logo.imagem.url.split("AWSAccessKeyId=")[0]
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

    class Meta:
        model = Empresa
        fields = (
            "id",
            "nome",
            "cnpj",
            "endereco",
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
            "para_almoço",
            "horario_pausa_inicio",
            "horario_pausa_fim",
            "funcionarios",
            "assinatura_ativa",
            "assinatura_vencimento",
        )

class ServicosFuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = 'id', 'nome', 'preco', 'duracao'

class FuncionarioSerializer(serializers.ModelSerializer):

    foto = serializers.SerializerMethodField()

    def get_foto(self, obj):
        return obj.foto.imagem.url.split("AWSAccessKeyId=")[0] if obj.foto else None
    
    class Meta:
        model = Funcionario
        fields = "id", "nome", "foto"

class ServicoFuncionarioSerializer(serializers.ModelSerializer):

    servicos = ServicosFuncionarioSerializer(many=True)
    foto_url = serializers.SerializerMethodField()

    def get_foto_url(self, obj):
        return obj.foto.imagem.url.split("AWSAccessKeyId=")[0] if obj.foto else None
    
    class Meta:
        model = Funcionario
        fields = ["id", "nome", "foto_url", "servicos"]

class EmpresaServicoFuncionarioSerializer(serializers.ModelSerializer):

    funcionarios = ServicoFuncionarioSerializer(many=True)

    class Meta:
        model = Empresa
        fields = ['nome', 'cnpj', 'funcionarios']

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if user:
            return {"user": user}
        raise serializers.ValidationError("Credenciais inválidas.")

class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plano
        fields = ["valor", "nome"]
