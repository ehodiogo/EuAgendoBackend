from rest_framework import generics
from .models import Plano
from .serializers import PlanoSerializer

class PlanoListView(generics.ListAPIView):
    queryset = Plano.objects.all()
    serializer_class = PlanoSerializer
