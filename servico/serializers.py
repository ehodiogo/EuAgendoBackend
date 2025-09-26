from .models import Servico
from rest_framework import serializers

class ServicosFuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = 'id', 'nome', 'preco', 'duracao', 'descricao'


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = "__all__"
