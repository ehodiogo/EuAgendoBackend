from .models import Imagem
from .serializers import ImagemSerializer
from rest_framework import viewsets

class ImagemViewSet(viewsets.ModelViewSet):
    queryset = Imagem.objects.all()
    serializer_class = ImagemSerializer