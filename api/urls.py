from .views import AgendamentoViewSet, ClienteViewSet, EmpresaViewSet, FuncionarioViewSet, ImagemViewSet, ServicoViewSet, EmpresaServicoViewSet, AgendamentoCreateView
from rest_framework import routers
from django.urls import path

router = routers.DefaultRouter()
router.register(r'agendamento', AgendamentoViewSet)
router.register(r'cliente', ClienteViewSet)
router.register(r'empresa', EmpresaViewSet)
router.register(r'funcionario', FuncionarioViewSet)
router.register(r'imagem', ImagemViewSet)
router.register(r'servico', ServicoViewSet)
router.register(r'empresaservico', EmpresaServicoViewSet, basename='empresaservico')

urlpatterns = router.urls

urlpatterns += [
    path('agendamento/create/', AgendamentoCreateView.as_view(), name='agendamento-create')
]