
from servico.views import ServicoViewSet, ServicoCreate, ServicosCriadosUsuarioEmpresaView, RemoverServicoEmpresaView
from servico.views import AdicionarServicoFuncionariosView, AdicionarServicosFuncionario, RemoverServicosFuncionarioView, EditarServicoView
from empresa.views import EmpresaViewSet, EmpresaServicoViewSet, FinanceiroView, EmpresaCreate, EditarEmpresaView, RemoverEmpresaView, PrototipoCreate
from core.views import ImagemViewSet, enviar_contato
from cliente.views import ClienteViewSet, cliente_detalhe, agendamentos_por_cliente, pontos_cliente
from agendamento.views import AgendamentoAvaliacaoViewSet, AgendamentoViewSet, AgendamentoCreateView, AgendamentosHojeView, AgendamentoDetailView, AgendamentoCancelarView
from funcionario.views import FuncionarioViewSet, FuncionarioAgendamentoView, FuncionariosCriadosView, RemoverFuncionarioView, EditarFuncionarioView
from funcionario.views import FuncionarioCreate, AdicionarFuncionariosEmpresa, RemoverFuncionariosEmpresaView
from usuario.views import PerfilUsuarioViewSet, RegisterView, LoginView, PasswordRecoveryView, EmpresasUsuarioView
from usuario.views import UserView, ChangePasswordView, DashboardView, ResetPasswordView, ConfirmEmailView
from pagamento.views import PagamentoPlanoView, LimitePlanoUsageView, PagamentosUsuarioView, PaymentSuccessView, PossuiLimiteView
from locacao.views import LocacoesCriadasUsuarioEmpresaView, CadastrarLocacaoView, RemoverLocacaoView, EditarLocacaoView, LocacaoAgendamentoView
from plano.views import PlanoListView

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
router.register(r'agendamento-avaliar', AgendamentoAvaliacaoViewSet, basename='agendamentoavaliar')
router.register(r'perfil-usuario', PerfilUsuarioViewSet, basename='perfil-usuario')
urlpatterns = router.urls

urlpatterns += [
    path('agendamento/create', AgendamentoCreateView.as_view(), name='agendamento-create'),
    path('agendamentos_funcionario/', FuncionarioAgendamentoView.as_view(), name='agendamentos_funcionario'),
    path('agendamentos_locacao/', LocacaoAgendamentoView.as_view(), name='agendamentos_locacao'),
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
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('planos/', PlanoListView.as_view(), name='planos'),
    path('agendamento/detalhe/<str:identificador>/', AgendamentoDetailView.as_view(), name='agendamento-detail'),
    path('agendamento/<str:identificador>/cancelar/', AgendamentoCancelarView.as_view(), name='agendamento-cancelar'),
    path('locacoes-criadas-usuario-empresa/', LocacoesCriadasUsuarioEmpresaView.as_view(), name='locacoes_criadas_usuario_empresa'),
    path('cadastrar-locacao/', CadastrarLocacaoView.as_view(), name='cadastrar_locacao'),
    path('remover-locacao/', RemoverLocacaoView.as_view(), name='remover_locacao'),
    path('editar-locacao/', EditarLocacaoView.as_view(), name='editar_locacao'),
    path('confirmar-conta/', ConfirmEmailView.as_view(), name='confirmar-conta'),
    path('contato/enviar/', enviar_contato, name='enviar_contato'),
    path('clientes/<str:identificador_cliente>/agendamentos/', agendamentos_por_cliente, name='agendamentos_por_cliente'),
    path('clientes/<str:identificador>/', cliente_detalhe, name='cliente_detalhe'),
    path('cliente/<str:identificador>/pontos', pontos_cliente, name='pontos_cliente'),
    path('empresa-salvar/', PrototipoCreate.as_view(), name='empresa_salvar'),

]