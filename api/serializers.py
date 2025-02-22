from rest_framework import serializers
from agendamento.models import Agendamento
from cliente.models import Cliente
from core.models import Imagem
from empresa.models import Empresa
from funcionario.models import Funcionario
from servico.models import Servico
from django.contrib.auth import get_user_model, authenticate

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

class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = "__all__"

class EmpresaSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    servicos = serializers.SerializerMethodField()
    funcionarios = serializers.SerializerMethodField()

    def get_logo(self, obj):
        return obj.logo.imagem.url

    def get_servicos(self, obj):
        return [
            {"nome": servico.nome, "preco": servico.preco, "duracao": servico.duracao}
            for servico in obj.servicos.all()
        ]

    def get_funcionarios(self, obj):
        funcionarios = obj.funcionarios.all()
        return [
            {
                "nome": funcionario.nome,
                "foto": funcionario.foto.imagem.url if funcionario.foto else None,
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
        )

class ServicosFuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = 'id', 'nome'

class FuncionarioSerializer(serializers.ModelSerializer):

    foto_url = serializers.SerializerMethodField()

    def get_foto_url(self, obj):
        return obj.foto.imagem.url if obj.foto else None
    
    class Meta:
        model = Funcionario
        fields = "id", "nome", "foto_url"

class ServicoFuncionarioSerializer(serializers.ModelSerializer):

    servicos = ServicosFuncionarioSerializer(many=True)
    foto_url = serializers.SerializerMethodField()

    def get_foto_url(self, obj):
        return obj.foto.imagem.url if obj.foto else None
    
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
