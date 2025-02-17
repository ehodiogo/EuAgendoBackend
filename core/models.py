from django.db import models

class Imagem(models.Model):

    imagem = models.ImageField(upload_to='imagens/', null=True, blank=True)
    imagem_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.imagem.url
    
    class Meta:
        verbose_name = 'Imagem'
        verbose_name_plural = 'Imagens'