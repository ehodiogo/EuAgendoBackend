from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Cliente, PontoClienteEmpresa

@receiver(pre_delete, sender=Cliente)
def deletar_pontos_cliente(sender, instance, **kwargs):
    try:
        PontoClienteEmpresa.objects.filter(cliente=instance).delete()
    except Exception as e:
        print(f"[WARN] Erro ao deletar pontos do cliente {instance}: {e}")
