from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from .models import Empresa
from agendamento.models import Agendamento


@receiver(pre_delete, sender=Empresa)
def deletar_relacionados_empresa(sender, instance, **kwargs):
    try:
        if instance.tipo == 'Serviço':
            agendamentos = Agendamento.objects.filter(funcionario__empresas__id=instance.id)
        else:
            agendamentos = Agendamento.objects.filter(locacao__in=instance.locacoes.all())
        agendamentos.delete()
    except Exception as e:
        print(f"[WARN] Erro ao deletar agendamentos: {e}")

    try:
        for funcionario in instance.funcionarios.all():
            funcionario.delete()
    except Exception as e:
        print(f"[WARN] Erro ao deletar funcionários: {e}")

    try:
        for servico in instance.servicos.all():
            servico.delete()
    except Exception as e:
        print(f"[WARN] Erro ao deletar serviços: {e}")

    try:
        for locacao in instance.locacoes.all():
            locacao.delete()
    except Exception as e:
        print(f"[WARN] Erro ao deletar locações: {e}")


@receiver(post_delete, sender=Empresa)
def deletar_logo_empresa(sender, instance, **kwargs):
    try:
        if instance.logo:
            instance.logo.delete()
            print(f"[INFO] Logo da empresa '{instance.nome}' removida com sucesso.")
    except Exception as e:
        print(f"[WARN] Erro ao deletar logo da empresa '{instance.nome}': {e}")
