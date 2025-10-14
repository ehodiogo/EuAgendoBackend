from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'identificador')  # aparece na tabela
    readonly_fields = ('identificador',)  # aparece no formulário, mas não pode ser editado
