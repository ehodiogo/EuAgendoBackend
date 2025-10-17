from .models import Locacao
from rest_framework import serializers

class LocacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locacao
        fields = "__all__"

    def validate_duracao(self, value):
        if value % 15 != 0:
            raise serializers.ValidationError("A duração deve ser um múltiplo de 15 minutos.")
        return value