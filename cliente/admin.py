from django.contrib import admin
from .models import Cliente, PontoClienteEmpresa

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'identificador')
    readonly_fields = ('identificador',)

admin.site.register(PontoClienteEmpresa)