from django.db import models

class Funcionario(models.Model):

    nome = models.CharField(max_length=100)
    foto = models.ForeignKey('core.Imagem', on_delete=models.CASCADE)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'