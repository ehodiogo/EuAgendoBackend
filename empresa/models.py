from django.db import models
from django.utils.text import slugify

class Empresa(models.Model):

    nome = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True, editable=False)

    cnpj = models.CharField(max_length=100)
    endereco = models.CharField(max_length=100)
    telefone = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)

    logo = models.ForeignKey('core.Imagem', on_delete=models.CASCADE, related_name='logo', null=True, blank=True)

    servicos = models.ManyToManyField('servico.Servico', related_name='servicos')

    horario_abertura_dia_semana = models.TimeField()
    horario_fechamento_dia_semana = models.TimeField()

    para_almoço = models.BooleanField(default=False)
    horario_pausa_inicio = models.TimeField(null=True, blank=True)
    horario_pausa_fim = models.TimeField(null=True, blank=True)

    horario_abertura_fim_de_semana = models.TimeField(null=True, blank=True)
    horario_fechamento_fim_de_semana = models.TimeField(null=True, blank=True)

    abre_sabado = models.BooleanField()
    abre_domingo = models.BooleanField()

    funcionarios = models.ManyToManyField('funcionario.Funcionario', related_name='empresas')

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super(Empresa, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'