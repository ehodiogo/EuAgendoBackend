from rest_framework import serializers
from .models import Imagem

class ImagemSerializer(serializers.ModelSerializer):

    imagem_url = serializers.SerializerMethodField()

    def get_imagem_url(self, obj):
        return obj.imagem.url.split("AWSAccessKeyId=")[0]

    class Meta:
        model = Imagem
        fields = "imagem", "imagem_url"