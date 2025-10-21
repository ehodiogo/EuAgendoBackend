from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'tipo', 'cidade', 'estado', 'criado_por')
    readonly_fields = ('slug',)
    search_fields = ('nome', 'cidade', 'estado', 'slug')
    list_filter = ('tipo', 'cidade', 'estado')