from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Funcionario

@receiver(pre_delete, sender=Funcionario)
def deletar_foto_funcionario(sender, instance, **kwargs):
    try:
        if instance.foto:
            instance.foto.delete()
    except Exception as e:
        print(f"[WARN] Erro ao deletar foto do funcionário {instance}: {e}")
