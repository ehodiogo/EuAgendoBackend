from .views import AgendamentoViewSet, ClienteViewSet, EmpresaViewSet, FuncionarioViewSet
from .views import ImagemViewSet, ServicoViewSet, EmpresaServicoViewSet, AgendamentoCreateView
from .views import FuncionarioAgendamentoView, LoginView, RegisterView, PasswordRecoveryView
from .views import AgendamentosHojeView, EmpresasUsuarioView, UserView, DashboardView, FinanceiroView
from .views import ChangePasswordView, LimitePlanoUsageView, PagamentosUsuarioView, PagamentoPlanoView
from .views import PaymentSuccessView, EmpresaCreate, FuncionarioCreate, ServicoCreate
from .views import AdicionarFuncionariosEmpresa, FuncionariosCriadosView, AdicionarServicosFuncionario
from .views import ServicosCriadosUsuarioEmpresaView, AdicionarServicoFuncionariosView
from .views import RemoverServicoEmpresaView, RemoverServicosFuncionarioView, EditarServicoView
from .views import PossuiLimiteView, EditarEmpresaView, RemoverEmpresaView, FuncionariosCriadosView
from .views import RemoverFuncionarioView, EditarFuncionarioView, RemoverFuncionariosEmpresaView
from .views import AgendamentoAvaliacaoViewSet
from rest_framework import routers
from django.urls import path

from usuario.views import PerfilUsuarioViewSet

router = routers.DefaultRouter()
router.register(r'agendamento', AgendamentoViewSet)
router.register(r'cliente', ClienteViewSet)
router.register(r'empresa', EmpresaViewSet)
router.register(r'funcionario', FuncionarioViewSet)
router.register(r'imagem', ImagemViewSet)
router.register(r'servico', ServicoViewSet)
router.register(r'empresaservico', EmpresaServicoViewSet, basename='empresaservico')
router.register(r'agendamento-avaliar', AgendamentoAvaliacaoViewSet, basename='agendamentoavaliar')
router.register(r'perfil-usuario', PerfilUsuarioViewSet, basename='perfil-usuario')
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
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('limite-plano-usage/', LimitePlanoUsageView.as_view(), name='limite_plano_usage'),
    path('pagamentos-usuario/', PagamentosUsuarioView.as_view(), name='pagamentos_usuario'),
    path('pagamento-plano/', PagamentoPlanoView.as_view(), name='pagamento_plano'),
    path('payment-success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('empresa-create/', EmpresaCreate.as_view(), name='empresa_create'),
    path('funcionario-create/', FuncionarioCreate.as_view(), name='funcionario_create'),
    path('servico-create/', ServicoCreate.as_view(), name='servico_create'),
    path('adicionar-funcionarios-empresa/', AdicionarFuncionariosEmpresa.as_view(), name='adicionar_funcionarios_empresa'),
    path('funcionarios-criados/', FuncionariosCriadosView.as_view(), name='funcionarios_criados'),
    path('adicionar-servicos-funcionario/', AdicionarServicosFuncionario.as_view(), name='adicionar_servicos_funcionario'),
    path('servicos-criados-usuario-empresa/', ServicosCriadosUsuarioEmpresaView.as_view(), name='servicos_criados_usuario_empresa'),
    path('adicionar-servico-funcionarios/', AdicionarServicoFuncionariosView.as_view(), name='adicionar_servico_funcionarios'),
    path('remover-servico-empresa/', RemoverServicoEmpresaView.as_view(), name='remover_servico_empresa'),
    path('remover-servicos-funcionario/', RemoverServicosFuncionarioView.as_view(), name='remover_servicos_funcionario'),
    path('editar-servico/', EditarServicoView.as_view(), name='editar_servico'),
    path('possui-limite/', PossuiLimiteView.as_view(), name='possui_limite'),
    path('editar-empresa/', EditarEmpresaView.as_view(), name='editar_empresa'),
    path('remover-empresa/', RemoverEmpresaView.as_view(), name='remover_empresa'),
    path('funcionarios-usuario/', FuncionariosCriadosView.as_view(), name='funcionarios_criados'),
    path('remover-funcionarios/', RemoverFuncionarioView.as_view(), name='remover_funcionario'),
    path('editar-funcionario/', EditarFuncionarioView.as_view(), name='editar_funcionario'),
    path('remover-funcionarios-empresa/', RemoverFuncionariosEmpresaView.as_view(), name='remover_funcionarios_empresa'),
]