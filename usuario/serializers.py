from rest_framework import serializers
from .models import PerfilUsuario
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    codigo_usado = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "codigo_usado"]

    def create(self, validated_data):
        codigo_usado = validated_data.pop("codigo_usado", None)

        user = User.objects.create_user(**validated_data)

        perfil = PerfilUsuario.objects.get(user=user)
        if codigo_usado:
            perfil.codigo_usado = codigo_usado
            perfil.save()

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if user:
            return {"user": user}
        raise serializers.ValidationError("Credenciais inválidas.")

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ["id", "user", "codigo_afiliado", "codigo_usado", "receiveEmailNotifications"]

    receiveEmailNotifications = serializers.BooleanField(source="receive_email_notifications")