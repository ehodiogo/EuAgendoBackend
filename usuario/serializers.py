from rest_framework import serializers
from .models import PerfilUsuario

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ["id", "user", "codigo_afiliado", "codigo_usado", "receiveEmailNotifications"]

    receiveEmailNotifications = serializers.BooleanField(source="receive_email_notifications")