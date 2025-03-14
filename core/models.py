from django.db import models
from django.core.files.storage import default_storage


class Imagem(models.Model):
    imagem = models.FileField(upload_to="imagens/", null=True, blank=True)
    imagem_url = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.imagem:
            self.imagem_url = self.imagem.url.split("AWSAccessKeyId=")[0]
        if "AWSAccessKeyId=" in self.imagem_url:
            self.imagem_url = self.imagem_url.split("AWSAccessKeyId=")[0]
            super().save(update_fields=["imagem_url"])

    def __str__(self):
        return self.imagem_url or "Sem imagem"

    def delete(self, *args, **kwargs):
        if self.imagem:
            storage = self.imagem.storage or default_storage
            if storage.exists(self.imagem.name):
                storage.delete(self.imagem.name)

        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Imagem"
        verbose_name_plural = "Imagens"
