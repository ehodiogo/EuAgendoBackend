from .models import Cliente, PontoClienteEmpresa
from rest_framework import serializers

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

class PontoClienteSerializer(serializers.ModelSerializer):
    empresa = serializers.SerializerMethodField()
    cliente = serializers.SerializerMethodField()

    def get_empresa(self, obj):
        return obj.empresa.nome

    def get_cliente(self, obj):
        return obj.cliente.nome

    class Meta:
        model = PontoClienteEmpresa
        fields = "__all__"