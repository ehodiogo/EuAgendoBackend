from rest_framework import serializers
from cliente.models import Cliente
from core.models import Imagem
from empresa.models import Empresa
from servico.models import Servico
from plano.models import Plano, PlanoUsuario
from django.utils import timezone
from usuario.models import PerfilUsuario
from funcionario.models import Funcionario

class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plano
        fields = ["valor", "nome"]
