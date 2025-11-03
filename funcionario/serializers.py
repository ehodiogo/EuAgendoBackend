from rest_framework import serializers
from .models import Funcionario
from servico.serializers import ServicosFuncionarioSerializer

class FuncionarioSerializer(serializers.ModelSerializer):
    foto = serializers.SerializerMethodField()

    def get_foto(self, obj):
        return obj.foto.imagem_url.split("AWSAccessKeyId=")[0] if obj.foto else None

    class Meta:
        model = Funcionario
        fields = "id", "nome", "foto"


class ServicoFuncionarioSerializer(serializers.ModelSerializer):
    servicos = ServicosFuncionarioSerializer(many=True)
    foto_url = serializers.SerializerMethodField()

    def get_foto_url(self, obj):
        return obj.foto.imagem_url.split("AWSAccessKeyId=")[0] if obj.foto else None

    class Meta:
        model = Funcionario
        fields = ["id", "nome", "foto_url", "servicos"]