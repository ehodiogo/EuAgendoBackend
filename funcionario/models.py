from django.db import models
from django.contrib.auth.models import User
class Funcionario(models.Model):

    nome = models.CharField(max_length=200)
    foto = models.ForeignKey('core.Imagem', on_delete=models.CASCADE, null=True, blank=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='funcionarios_criados')

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'