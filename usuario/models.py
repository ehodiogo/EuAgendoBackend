from django.db import models
from django.contrib.auth.models import User
import uuid

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    codigo_afiliado = models.CharField(max_length=8, unique=True, blank=True, null=True)
    codigo_usado = models.CharField(max_length=8, blank=True, null=True)
    receive_email_notifications = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.codigo_afiliado:
            self.codigo_afiliado = self.gerar_codigo_afiliado()
        super().save(*args, **kwargs)

    def gerar_codigo_afiliado(self):
        while True:
            codigo = uuid.uuid4().hex[:8].upper()
            if not PerfilUsuario.objects.filter(codigo_afiliado=codigo).exists():
                return codigo

    def regenerar_codigo_afiliado(self):
        self.codigo_afiliado = self.gerar_codigo_afiliado()
        self.save(update_fields=["codigo_afiliado"])

    def __str__(self):
        return f"{self.user.username} - Afiliado: {self.codigo_afiliado}"
