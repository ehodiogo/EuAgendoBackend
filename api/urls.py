from .views import AgendamentoViewSet, ClienteViewSet, EmpresaViewSet, FuncionarioViewSet
from .views import ImagemViewSet, ServicoViewSet, EmpresaServicoViewSet, AgendamentoCreateView
from .views import FuncionarioAgendamentoView, LoginView, RegisterView, PasswordRecoveryView
from .views import AgendamentosHojeView, EmpresasUsuarioView, UserView, DashboardView, FinanceiroView
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
    path('agendamento/create', AgendamentoCreateView.as_view(), name='agendamento-create'),
    path('agendamentos_funcionario/', FuncionarioAgendamentoView.as_view(), name='agendamentos_funcionario'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-recovery/', PasswordRecoveryView.as_view(), name='password_recovery'),
    path('agendamentos-hoje/', AgendamentosHojeView.as_view(), name='agendamentos_hoje'),
    path('empresas-usuario/', EmpresasUsuarioView.as_view(), name='empresas_usuario'),
    path('user/', UserView.as_view(), name='user'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('financeiro/', FinanceiroView.as_view(), name='financeiro'),
]