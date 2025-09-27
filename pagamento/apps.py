from django.apps import AppConfig


class PagamentoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pagamento'

    def ready(self):
        import pagamento.signals