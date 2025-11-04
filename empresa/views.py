from rest_framework import viewsets, status
from rest_framework.decorators import action
from funcionario.models import Funcionario
from locacao.models import Locacao
from servico.models import Servico
from .models import Empresa
from .serializers import EmpresaSerializer, EmpresaServicoFuncionarioSerializer
from agendamento.models import Agendamento
from rest_framework.views import APIView
from datetime import date, timedelta
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
from core.models import Imagem
import os
import json
from plano.models import Plano, PlanoUsuario

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        empresas = Empresa.objects.filter(slug=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

class EmpresaServicoViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaServicoFuncionarioSerializer

    def get_queryset(self):
        empresa_slug = self.request.query_params.get("empresa_slug", None)

        if empresa_slug:
            return Empresa.objects.filter(slug=empresa_slug)
        else:
            return Empresa.objects.all()

class FinanceiroView(APIView):
    def get(self, request, *args, **kwargs):
        empresa_id = request.query_params.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "Parâmetro 'empresa_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        primeiro_dia_semana = hoje - timedelta(days=hoje.weekday())


        empresa = Empresa.objects.get(id=empresa_id)

        if empresa.tipo == "Locação":
            total_ganhos = (
                               Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
                               .aggregate(total=Sum("locacao__preco"))
                               .get("total", 0)
                           ) or 0

            ganhos_por_semana = (
                                    Agendamento.objects.filter(
                                        funcionario__empresas__id=empresa_id,
                                        data__gte=primeiro_dia_semana,
                                        is_continuacao=False,
                                    )
                                    .aggregate(total=Sum("locacao__preco"))
                                    .get("total", 0)
                                ) or 0

            ganhos_por_mes = (
                                 Agendamento.objects.filter(
                                     funcionario__empresas__id=empresa_id,
                                     data__gte=primeiro_dia_mes,
                                     is_continuacao=False,
                                 )
                                 .aggregate(total=Sum("locacao__preco"))
                                 .get("total", 0)
                             ) or 0
        else:

            total_ganhos = (
                Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
                .aggregate(total=Sum("servico__preco"))
                .get("total", 0)
            ) or 0

            # Ganhos por semana
            ganhos_por_semana = (
                Agendamento.objects.filter(
                    funcionario__empresas__id=empresa_id, data__gte=primeiro_dia_semana, is_continuacao=False
                )
                .aggregate(total=Sum("servico__preco"))
                .get("total", 0)
            ) or 0

            # Ganhos por mês
            ganhos_por_mes = (
                Agendamento.objects.filter(
                    funcionario__empresas__id=empresa_id, data__gte=primeiro_dia_mes, is_continuacao=False
                )
                .aggregate(total=Sum("servico__preco"))
                .get("total", 0)
            ) or 0

        # Funcionário que mais gerou dinheiro
        funcionario_top = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .values("funcionario__nome")
            .annotate(total=Sum("servico__preco"))
            .order_by("-total")
            .first()
        )

        # Serviço mais rentável
        servico_mais_rentavel = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .values("servico__nome")
            .annotate(total=Sum("servico__preco"))
            .order_by("-total")
            .first()
        )

        # Serviço que menos gerou dinheiro
        servico_menos_rentavel = (
            Agendamento.objects.filter(funcionario__empresas__id=empresa_id, is_continuacao=False)
            .values("servico__nome")
            .annotate(total=Sum("servico__preco"))
            .order_by("total")
            .first()
        )

        locacao_mais_rentavel = (
            Agendamento.objects.filter(locacao__in=empresa.locacoes.all(), is_continuacao=False)
            .values("locacao__nome")
            .annotate(total=Sum("locacao__preco"))
            .order_by("-total")
            .first()
        )

        locacao_menos_rentavel = (
            Agendamento.objects.filter(locacao__in=empresa.locacoes.all(), is_continuacao=False)
            .values("locacao__nome")
            .annotate(total=Sum("locacao__preco"))
            .order_by("total")
            .first()
        )

        return Response(
            {
                "tipo": empresa.tipo,
                "total_ganhos": total_ganhos,
                "ganhos_por_semana": ganhos_por_semana,
                "ganhos_por_mes": ganhos_por_mes,
                "funcionario_top": funcionario_top
                or {"funcionario__nome": None, "total": 0},
                "servico_mais_rentavel": servico_mais_rentavel
                or {"servico__nome": None, "total": 0},
                "servico_menos_rentavel": servico_menos_rentavel
                or {"servico__nome": None, "total": 0},

                "locacao_mais_rentavel": locacao_mais_rentavel,
                "locacao_menos_rentavel": locacao_menos_rentavel,
            },
            status=status.HTTP_200_OK,
        )

class PrototipoCreate(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):

        usuario_token = request.query_params.get("usuario_token")
        if not usuario_token:
            return Response({"erro": "Token de acesso é obrigatório."}, status=400)

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        empresas_criadas = usuario.empresas.count()
        funcionarios_empresas = [
            {"empresa": empresa.nome, "total_funcionarios": empresa.funcionarios.count()}
            for empresa in usuario.empresas.all()
            if empresa.tipo == "Serviço"
        ]
        locacoes_empresas = [
            {"empresa": empresa.nome, "total_locativos": empresa.locacoes.count()}
            for empresa in usuario.empresas.all()
            if empresa.tipo == "Locação"
        ]

        plano_usuario = PlanoUsuario.objects.filter(usuario=usuario).first()

        return Response(
                {
                    "limites": {
                        "funcionarios_criados": funcionarios_empresas,
                        "empresas_criadas": empresas_criadas,
                        "locacoes_criadas": locacoes_empresas,
                        "limite_empresas": plano_usuario.plano.quantidade_empresas,
                        "limite_funcionarios": plano_usuario.plano.quantidade_funcionarios,
                        "limite_locacoes": plano_usuario.plano.quantidade_locacoes
                    }
                }
            )

    def post(self, request):
        try:
            usuario_token = request.data.get("usuario_token")
            if not usuario_token:
                return Response({"erro": "Token de acesso é obrigatório."}, status=400)

            usuario = Token.objects.filter(key=usuario_token).first().user

            if not usuario:
                return Response(
                    {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
                )

            empresa_id = request.data.get("empresa_id")
            nome = request.data.get("nome")
            tipo = request.data.get("tipo")
            endereco = request.data.get("endereco")
            bairro = request.data.get("bairro")
            cidade = request.data.get("cidade")
            pais = request.data.get("pais")
            estado = request.data.get("estado")
            telefone = request.data.get("telefone")
            email = request.data.get("email")
            horario_abertura_dia_semana = request.data.get("horario_abertura_dia_semana")
            horario_fechamento_dia_semana = request.data.get("horario_fechamento_dia_semana")
            abre_sabado = request.data.get("abre_sabado")
            abre_domingo = request.data.get("abre_domingo")
            para_almoco = request.data.get("para_almoco")
            horario_pausa_inicio = request.data.get("horario_pausa_inicio")
            horario_pausa_fim = request.data.get("horario_pausa_fim")
            is_online = request.data.get("is_online")
            acao = request.data.get("acao")

            logo = request.FILES.get("logo") or request.data.get("logo")
            logo_obj = None
            if logo:
                if isinstance(logo, ContentFile) or hasattr(logo, 'read'):
                    base_name, ext = os.path.splitext(logo.name)
                    new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"
                    logo_obj = Imagem()
                    logo_obj.imagem.save(new_filename, logo, save=True)
                elif isinstance(logo, str) and logo.startswith("http"):
                    logo_obj = Imagem.objects.create(imagem_url=logo)

            servicos = []
            servicos_json_str = request.data.get("servicos_json")
            if servicos_json_str:
                try:
                    servicos = json.loads(servicos_json_str)
                except json.JSONDecodeError:
                    return Response({"erro": "JSON de serviços inválido."}, status=400)

            funcionarios = []
            funcionarios_json_str = request.data.get("funcionarios_json")
            if funcionarios_json_str:
                try:
                    funcionarios = json.loads(funcionarios_json_str)
                except json.JSONDecodeError:
                    return Response({"erro": "JSON de funcionários inválido."}, status=400)

            for idx, f in enumerate(funcionarios):
                file_field_name = f"funcionario_foto_{idx}"
                foto = request.FILES.get(file_field_name)
                if not foto:
                    foto = f.get("foto") or None
                foto_obj = None

                if foto:
                    if hasattr(foto, 'read'):
                        base_name, ext = os.path.splitext(foto.name)
                        new_filename = f"{base_name}_{f.get('nome')}_{usuario_token}{ext}"
                        foto_obj = Imagem()
                        foto_obj.imagem.save(new_filename, foto, save=True)
                        f["foto"] = foto_obj.imagem.url
                    elif isinstance(foto, str) and foto.startswith("http"):
                        foto_obj = Imagem.objects.create(imagem_url=foto)
                        f["foto"] = foto_obj.imagem_url

            locacoes = []
            locacoes_json_str = request.data.get("locacoes_json")
            if locacoes_json_str:
                try:
                    locacoes = json.loads(locacoes_json_str)
                except json.JSONDecodeError:
                    return Response({"erro": "JSON de locações inválido."}, status=400)

            plano_usuario = PlanoUsuario.objects.filter(usuario=usuario).first()

            if abre_sabado == 'false':
                abre_sabado = False
            else:
                abre_sabado = True

            if abre_domingo == 'false':
                abre_domingo = False
            else:
                abre_domingo = True

            if is_online == 'false':
                is_online = False
            else:
                is_online = True

            if para_almoco == 'false':
                para_almoco = False
            else:
                para_almoco = True

            if acao == 'cadastrar':

                empresas_criadas = usuario.empresas.count()

                if empresas_criadas >= plano_usuario.plano.quantidade_empresas:
                    return Response({"erro": "Você não possui mais limite!"}, status=400)

                empresa = Empresa.objects.create(
                    criado_por=usuario,
                    nome=nome,
                    tipo=tipo,
                    endereco=endereco,
                    bairro=bairro,
                    cidade=cidade,
                    pais=pais,
                    estado=estado,
                    telefone=telefone,
                    email=email,
                    horario_abertura_dia_semana=horario_abertura_dia_semana,
                    horario_fechamento_dia_semana=horario_fechamento_dia_semana,
                    abre_sabado=abre_sabado,
                    abre_domingo=abre_domingo,
                    para_almoco=para_almoco,
                    horario_pausa_inicio=horario_pausa_inicio if horario_pausa_inicio != "null" else None,
                    horario_pausa_fim=horario_pausa_fim if horario_pausa_fim != "null" else None,
                    is_online=is_online,
                    logo=logo_obj,
                )
                usuario.empresas.add(empresa)
                usuario.save()

                if tipo == "Serviço":
                    if len(funcionarios) > plano_usuario.plano.quantidade_funcionarios:
                        return Response({"erro": "Você irá atingir o limite de funcionários do seu plano."}, status=400)
                elif tipo == "Locação":
                    if len(locacoes) > plano_usuario.plano.quantidade_locacoes:
                        return Response({"erro": "Você irá atingir o limite de locações do seu plano."}, status=400)

                serv_objs = []
                func_objs = []
                loc_objs = []
                if tipo == "Serviço" and servicos:
                    for s in servicos:
                        serv = Servico.objects.create(
                            nome=s.get("nome"),
                            descricao=s.get("descricao"),
                            preco=s.get("preco"),
                            duracao=s.get("duracao"),
                            criado_por=usuario,
                        )
                        serv_objs.append(serv)

                        if s.get("funcionarios"):
                            for f in s.get("funcionarios"):
                                serv.funcionarios.add(Funcionario.objects.get(id=f))

                        serv.save()

                    for serv in serv_objs:
                        empresa.servicos.add(serv)
                    empresa.save()

                if tipo == "Serviço" and funcionarios:
                    for idx, f in enumerate(funcionarios):
                        foto_obj = None
                        file_field_name = f"funcionario_foto_{idx}"
                        foto = request.FILES.get(file_field_name) or f.get("foto")

                        if foto:
                            if hasattr(foto, "read"):
                                base_name, ext = os.path.splitext(foto.name)
                                new_filename = f"{base_name}_{f.get('nome')}_{usuario.username}{ext}"
                                foto_obj = Imagem()
                                foto_obj.imagem.save(new_filename, foto, save=True)
                            elif isinstance(foto, str) and foto.startswith("http"):
                                foto_obj = Imagem.objects.create(imagem_url=foto)

                        func = Funcionario.objects.create(
                            nome=f.get("nome"),
                            foto=foto_obj,
                            criado_por=usuario,
                        )
                        func_objs.append(func)

                    for func in func_objs:
                        empresa.funcionarios.add(func)
                    empresa.save()

                if tipo == "Locação" and locacoes:
                    for l in locacoes:
                        loc = Locacao.objects.create(
                            nome=l.get("nome"),
                            descricao=l.get("descricao"),
                            preco=l.get("preco"),
                            criado_por=usuario
                        )
                        loc_objs.append(loc)

                    for loc in loc_objs:
                        empresa.locacoes.add(loc)
                    empresa.save()

            elif acao == 'editar':
                empresa = Empresa.objects.get(id=empresa_id)
                empresa.nome = nome
                empresa.tipo = tipo
                empresa.endereco = endereco
                empresa.bairro = bairro
                empresa.cidade = cidade
                empresa.pais = pais
                empresa.estado = estado
                empresa.telefone = telefone
                empresa.email = email
                empresa.horario_abertura_dia_semana = horario_abertura_dia_semana
                empresa.horario_fechamento_dia_semana = horario_fechamento_dia_semana
                empresa.abre_sabado = abre_sabado
                empresa.abre_domingo = abre_domingo
                empresa.para_almoco = para_almoco
                empresa.horario_pausa_inicio = horario_pausa_inicio if horario_pausa_inicio != "null" else None
                empresa.horario_pausa_fim = horario_pausa_fim if horario_pausa_fim != "null" else None
                empresa.is_online = is_online

                if logo_obj:
                    empresa.logo = logo_obj

                empresa.save()

                funcionarios_criados = empresa.funcionarios.count()

                locacoes_criadas = empresa.locacoes.count()

                if empresa.tipo == "Serviço":

                    novos_funcionarios = [f for f in funcionarios if not f.get("id")]

                    func_objs = []
                    serv_objs = []


                    if len(novos_funcionarios) > 0:
                        total_pos_criacao = funcionarios_criados + len(novos_funcionarios)
                        if total_pos_criacao > plano_usuario.plano.quantidade_funcionarios:
                            return Response(

                                {"erro": "Você atingiu o limite de funcionários do seu plano."},

                                status=400

                            )

                        for f in novos_funcionarios:
                            foto_obj = None
                            foto_field = f.get("foto")
                            if foto_field:
                                if hasattr(foto_field, "read"):
                                    base_name, ext = os.path.splitext(foto_field.name)
                                    new_filename = f"{base_name}_{f.get('nome')}_{usuario_token}{ext}"
                                    foto_obj = Imagem()
                                    foto_obj.imagem.save(new_filename, foto_field, save=True)
                                elif isinstance(foto_field, str) and foto_field.startswith("http"):
                                    foto_obj = Imagem.objects.create(imagem_url=foto_field)

                            func = Funcionario.objects.create(
                                nome=f.get("nome"),
                                foto=foto_obj,
                                criado_por=usuario,
                            )
                            func_objs.append(func)

                    for f in funcionarios:

                        if f.get("id"):
                            funcionario = Funcionario.objects.filter(id=f["id"]).first()
                            if funcionario:
                                foto_field = f.get("foto")
                                foto_obj = funcionario.foto
                                if foto_field and hasattr(foto_field, "read"):
                                    base_name, ext = os.path.splitext(foto_field.name)
                                    new_filename = f"{base_name}_{f.get('nome')}_{usuario_token}{ext}"
                                    foto_obj = Imagem()
                                    foto_obj.imagem.save(new_filename, foto_field, save=True)
                                funcionario.nome = f.get("nome")
                                funcionario.foto = foto_obj
                                funcionario.save()

                    if func_objs:
                        for func in func_objs:
                            empresa.funcionarios.add(func)

                        empresa.save()

                    novos_servicos = [s for s in servicos if not s.get("id")]
                    if len(novos_servicos) > 0:
                        for s in novos_servicos:
                            serv = Servico.objects.create(
                                criado_por=usuario,
                                nome=s.get("nome"),
                                descricao=s.get("descricao"),
                                preco=s.get("preco"),
                                duracao=s.get("duracao"),
                                pontos_gerados=s.get("pontos_gerados"),
                                pontos_resgate=s.get("pontos_resgate"),
                            )
                            serv_objs.append(serv)

                            if s.get("funcionarios"):
                                for f in s.get("funcionarios"):
                                    serv.funcionarios.add(Funcionario.objects.get(id=f))
                            serv.save()

                    for s in servicos:
                        if s.get("id"):
                            servico = Servico.objects.filter(id=s["id"]).first()
                            if servico:
                                servico.nome = s.get("nome")
                                servico.descricao = s.get("descricao")
                                servico.preco = s.get("preco")
                                servico.duracao = s.get("duracao")
                                servico.pontos_gerados = s.get("pontos_gerados")
                                servico.pontos_resgate = s.get("pontos_resgate")
                                servico.save()

                                if s.get("funcionarios"):
                                    for f in s.get("funcionarios"):
                                        servico.funcionarios.add(Funcionario.objects.get(id=f))
                                else:
                                    if servico.funcionarios.all():
                                        for func in servico.funcionarios.all():
                                            servico.funcionarios.remove(func)

                                servico.save()

                    if serv_objs:
                        for serv in serv_objs:
                            empresa.servicos.add(serv)
                        empresa.save()

                    ids_enviados_func = [f.get("id") for f in funcionarios if f.get("id")]
                    ids_recem_criados = [f.id for f in func_objs]
                    ids_totais_validos = ids_enviados_func + ids_recem_criados

                    funcionarios_removidos = empresa.funcionarios.exclude(id__in=ids_totais_validos)

                    for func_rem in funcionarios_removidos:
                        empresa.funcionarios.remove(func_rem)

                    funcionarios_removidos.delete()

                    ids_enviados_serv = [s.get("id") for s in servicos if s.get("id")]
                    ids_recem_criados = [s.id for s in serv_objs]
                    ids_totais_validos = ids_enviados_serv + ids_recem_criados

                    servicos_removidos = empresa.servicos.exclude(id__in=ids_totais_validos)

                    for serv_rem in servicos_removidos:
                        empresa.servicos.remove(serv_rem)

                    servicos_removidos.delete()

                else:

                    novas_locacoes = [l for l in locacoes if not l.get("id")]
                    loc_objs = []

                    if len(novas_locacoes) > 0:
                        total_pos_criacao = locacoes_criadas + len(novas_locacoes)
                        if total_pos_criacao > plano_usuario.plano.quantidade_locacoes:
                            return Response(
                                {"erro": "Você atingiu o limite de locações do seu plano."},
                                status=400

                            )

                        for l in novas_locacoes:
                            loc = Locacao.objects.create(
                                nome=l.get("nome"),
                                descricao=l.get("descricao"),
                                duracao=l.get("duracao"),
                                preco=l.get("preco"),
                                pontos_gerados=l.get("pontos_gerados"),
                                pontos_resgate=l.get("pontos_resgate"),
                                criado_por=usuario,

                            )
                            loc_objs.append(loc)

                    for l in locacoes:

                        if l.get("id"):
                            locacao = Locacao.objects.filter(id=l["id"]).first()
                            if locacao:
                                locacao.nome = l.get("nome")
                                locacao.descricao = l.get("descricao")
                                locacao.preco = l.get("preco")
                                locacao.duracao = l.get("duracao")
                                locacao.pontos_gerados = l.get("pontos_gerados")
                                locacao.pontos_resgate = l.get("pontos_resgate")
                                locacao.save()

                    if loc_objs:
                        for loc in loc_objs:
                            empresa.locacoes.add(loc)
                        empresa.save()

                    ids_enviados_loc = [l.get("id") for l in locacoes if l.get("id")]
                    locacoes_removidas = empresa.locacoes.exclude(id__in=ids_enviados_loc)

                    for loc_rem in locacoes_removidas:
                        empresa.locacoes.remove(loc_rem)

                    locacoes_removidas.delete()

            elif acao == 'excluir':

                empresa_id = request.data.get("empresa_id")

                empresa = Empresa.objects.get(id=empresa_id)
                empresa.delete()

                return Response(
                    {
                        "Empresa removida com sucesso"
                    }, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "erro": "Ação desconhecida",
                    }, status=status.HTTP_400_BAD_REQUEST
                )

            response_data = {
                "success": True,
                "nome": nome,
                "tipo": tipo,
                "endereco": endereco,
                "bairro": bairro,
                "cidade": cidade,
                "pais": pais,
                "estado": estado,
                "telefone": telefone,
                "email": email,
                "horario_abertura_dia_semana": horario_abertura_dia_semana,
                "horario_fechamento_dia_semana": horario_fechamento_dia_semana,
                "abre_sabado": abre_sabado,
                "abre_domingo": abre_domingo,
                "para_almoco": para_almoco,
                "horario_pausa_inicio": horario_pausa_inicio,
                "horario_pausa_fim": horario_pausa_fim,
                "is_online": is_online,
                "acao": acao,
                "logo": logo_obj.imagem_url,
                "servicos": servicos,
                "funcionarios": funcionarios,
                "locacoes": locacoes,
            }

            return Response(response_data, status=200)

        except Exception as e:
            print(e)
            return Response(
                {
                    "Erro:", str(e),
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmpresaCreate(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        nome = request.data.get("nome")
        tipo = request.data.get("tipo")
        endereco = request.data.get("endereco")
        bairro = request.data.get("bairro")
        cidade = request.data.get("cidade")
        estado = request.data.get("estado")
        pais = request.data.get("pais")
        telefone = request.data.get("telefone")
        email = request.data.get("email")
        is_online = request.data.get("is_online")

        horario_abertura_dia_semana = request.data.get("horario_abertura_dia_semana")
        horario_fechamento_dia_semana = request.data.get("horario_fechamento_dia_semana")

        horario_abertura_fim_semana = request.data.get("horario_abertura_fim_de_semana") or None
        horario_fechamento_fim_semana = request.data.get("horario_fechamento_fim_de_semana") or None

        para_almoco = request.data.get("para_almoco")

        if para_almoco == "true":
            para_almoco = True
        else:
            para_almoco = False

        inicio_almoco = request.data.get("horario_pausa_inicio") or None
        fim_almoco = request.data.get("horario_pausa_fim") or None

        abre_sabado = request.data.get("abre_sabado")

        if abre_sabado == "true":
            abre_sabado = True
        else:
            abre_sabado = False

        abre_domingo = request.data.get("abre_domingo")

        if abre_domingo == "true":
            abre_domingo = True
        else:
            abre_domingo = False

        if is_online == "true":
            is_online = True
        else:
            is_online = False

        logo = request.data.get("logo")

        if not nome or not endereco or not telefone or not email or not tipo:
            return Response(
                {"erro": "Todos os campos são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            print("Sem usuário")
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            imagem_obj = None
            if isinstance(logo, ContentFile) or hasattr(logo, 'read'):
                base_name, ext = os.path.splitext(logo.name)
                new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"
                imagem_obj = Imagem()
                imagem_obj.imagem.save(new_filename, logo, save=True)
            elif isinstance(logo, str) and logo.startswith("http"):
                imagem_obj = Imagem.objects.create(imagem_url=logo)

            empresa = Empresa.objects.create(
                nome=nome,
                tipo=tipo,
                endereco=endereco,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                pais=pais,
                telefone=telefone,
                email=email,
                horario_abertura_dia_semana=horario_abertura_dia_semana,
                horario_fechamento_dia_semana=horario_fechamento_dia_semana,
                horario_abertura_fim_de_semana=horario_abertura_fim_semana,
                horario_fechamento_fim_de_semana=horario_fechamento_fim_semana,
                para_almoco=para_almoco,
                horario_pausa_inicio=inicio_almoco,
                horario_pausa_fim=fim_almoco,
                abre_sabado=abre_sabado,
                abre_domingo=abre_domingo,
                logo=imagem_obj,
                criado_por=usuario,
                is_online=is_online,
            )

            usuario.empresas.add(empresa)
            usuario.save()

            imagem_obj.empresa = empresa
            imagem_obj.save()

            return Response(
                {
                    "message": "Empresa criada com sucesso.",
                    "empresa": EmpresaSerializer(empresa).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print("Exception", e)
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EditarEmpresaView(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        nome = request.data.get("nome")
        tipo = request.data.get("tipo")
        endereco = request.data.get("endereco")
        bairro = request.data.get("bairro")
        cidade = request.data.get("cidade")
        estado = request.data.get("estado")
        pais = request.data.get("pais")
        telefone = request.data.get("telefone")
        email = request.data.get("email")
        is_online = request.data.get("is_online")

        horario_abertura_dia_semana = request.data.get("horario_abertura_dia_semana")
        horario_fechamento_dia_semana = request.data.get("horario_fechamento_dia_semana")

        horario_abertura_fim_semana = request.data.get("horario_abertura_fim_de_semana") or None
        horario_fechamento_fim_semana = request.data.get("horario_fechamento_fim_de_semana") or None

        para_almoco = request.data.get("para_almoco")

        if para_almoco == "true":
            para_almoco = True
        else:
            para_almoco = False

        inicio_almoco = request.data.get("horario_pausa_inicio") or None
        fim_almoco = request.data.get("horario_pausa_fim") or None

        abre_sabado = request.data.get("abre_sabado")

        if abre_sabado == "true":
            abre_sabado = True
        else:
            abre_sabado = False

        abre_domingo = request.data.get("abre_domingo")

        if abre_domingo == "true":
            abre_domingo = True
        else:
            abre_domingo = False

        logo = request.data.get("logo")

        empresa_id = request.data.get("empresa_id")

        if not nome or not endereco or not telefone or not email or not empresa_id or not tipo:

            return Response(
                {"erro": "Todos os campos são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            imagem_obj = None

            if isinstance(logo, ContentFile) or hasattr(logo, "read"):
                base_name, ext = os.path.splitext(logo.name)
                new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"

                imagem_obj, created = Imagem.objects.get_or_create(
                    empresa_id=empresa_id,
                    imagem=f"imagens/{new_filename}",
                )

                if created:
                    imagem_obj.imagem.save(new_filename, logo, save=True)
            elif isinstance(logo, str) and logo.startswith("http"):
                imagem_obj, _ = Imagem.objects.get_or_create(imagem_url=logo, empresa__id=empresa_id)

            empresa = Empresa.objects.get(id=empresa_id)

            if nome != empresa.nome and nome != None:
                empresa.nome = nome

            if tipo != empresa.tipo and tipo != None:
                empresa.tipo = tipo

            if endereco != empresa.endereco and endereco != None:
                empresa.endereco = endereco

            if bairro != empresa.bairro and bairro != None:
                empresa.bairro = bairro

            if cidade != empresa.cidade and cidade != None:
                empresa.cidade = cidade

            if estado != empresa.estado and estado != None:
                empresa.estado = estado

            if pais != empresa.pais and pais != None:
                empresa.pais = pais

            if telefone != empresa.telefone and telefone != None:
                empresa.telefone = telefone

            if email != empresa.email and email != None:
                empresa.email = email

            if horario_abertura_dia_semana != empresa.horario_abertura_dia_semana and horario_abertura_dia_semana != None:
                empresa.horario_abertura_dia_semana = horario_abertura_dia_semana

            if horario_fechamento_dia_semana != empresa.horario_fechamento_dia_semana and horario_fechamento_dia_semana != None:
                empresa.horario_fechamento_dia_semana = horario_fechamento_dia_semana

            if horario_abertura_fim_semana != empresa.horario_abertura_fim_de_semana and horario_abertura_fim_semana != None:
                empresa.horario_abertura_fim_de_semana = horario_abertura_fim_semana

            if horario_fechamento_fim_semana != empresa.horario_fechamento_fim_de_semana and horario_fechamento_fim_semana != None:
                empresa.horario_fechamento_fim_de_semana = horario_fechamento_fim_semana

            if para_almoco != empresa.para_almoco and para_almoco != None:
                empresa.para_almoco = para_almoco

            if inicio_almoco != empresa.horario_pausa_inicio and inicio_almoco != None:
                empresa.horario_pausa_inicio = inicio_almoco

            if fim_almoco != empresa.horario_pausa_fim and fim_almoco != None:
                empresa.horario_pausa_fim = fim_almoco

            if abre_sabado != empresa.abre_sabado and abre_sabado != None:
                empresa.abre_sabado = abre_sabado

            if abre_domingo != empresa.abre_domingo and abre_domingo != None:
                empresa.abre_domingo = abre_domingo

            if imagem_obj != empresa.logo and imagem_obj != None:
                empresa.logo = imagem_obj

            if is_online != empresa.is_online and is_online != None:
                empresa.is_online = is_online

            empresa.save()

            return Response(
                {
                    "message": "Empresa editada com sucesso.",
                    "empresa": EmpresaSerializer(empresa).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RemoverEmpresaView(APIView):

    def post(self, request):

        empresa_id = request.data.get("empresa_id")

        if not empresa_id:
            return Response(
                {"erro": "ID da empresa é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_token = request.data.get("usuario_token")

        if not usuario_token:
            return Response(
                {"erro": "Token de acesso é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario = Token.objects.filter(key=usuario_token).first().user

        if not usuario:
            return Response(
                {"erro": "Token de acesso é inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            empresa = Empresa.objects.get(id=empresa_id)

            for funcionario in empresa.funcionarios.all():
                funcionario.delete()

            for servico in empresa.servicos.all():
                servico.delete()

            for agendamento in Agendamento.objects.filter(funcionario__empresas=empresa):
                agendamento.delete()

            empresa.delete()

            return Response(
                {
                    "message": "Empresa removida com sucesso.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)
