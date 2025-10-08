from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import Empresa
from .serializers import EmpresaSerializer, EmpresaServicoFuncionarioSerializer
from agendamento.models import Agendamento
from rest_framework.views import APIView
from datetime import date, timedelta
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
from core.models import Imagem
import os

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=400)

        empresas = Empresa.objects.filter(nome__icontains=termo) | Empresa.objects.filter(cnpj__icontains=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip().lower()
        if not termo:
            return Response({"erro": "Parâmetro 'q' é obrigatório."}, status=400)

        empresas = Empresa.objects.filter(nome__icontains=termo) | Empresa.objects.filter(cnpj__icontains=termo)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

class EmpresaServicoViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaServicoFuncionarioSerializer

    def get_queryset(self):
        nome = self.request.query_params.get("empresa_nome", None)
        cnpj = self.request.query_params.get("cnpj", None)

        if nome:
            return Empresa.objects.filter(nome_=nome)
        elif cnpj:
            return Empresa.objects.filter(cnpj=cnpj)
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


class EmpresaCreate(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        nome = request.data.get("nome")
        cnpj = request.data.get("cnpj")
        tipo = request.data.get("tipo")
        endereco = request.data.get("endereco")
        bairro = request.data.get("bairro")
        cidade = request.data.get("cidade")
        estado = request.data.get("estado")
        pais = request.data.get("pais")
        telefone = request.data.get("telefone")
        email = request.data.get("email")

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

        if not nome or not cnpj or not endereco or not telefone or not email or not tipo:
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
            if isinstance(logo, ContentFile) or hasattr(logo, 'read'):
                base_name, ext = os.path.splitext(logo.name)
                new_filename = f"{base_name}_{nome}_{usuario.username}{ext}"
                imagem_obj = Imagem()
                imagem_obj.imagem.save(new_filename, logo, save=True)
            elif isinstance(logo, str) and logo.startswith("http"):
                imagem_obj = Imagem.objects.create(imagem_url=logo)

            empresa = Empresa.objects.create(
                nome=nome,
                cnpj=cnpj,
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
                criado_por=usuario
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
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EditarEmpresaView(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):

        nome = request.data.get("nome")
        cnpj = request.data.get("cnpj")
        tipo = request.data.get("tipo")
        endereco = request.data.get("endereco")
        bairro = request.data.get("bairro")
        cidade = request.data.get("cidade")
        estado = request.data.get("estado")
        pais = request.data.get("pais")
        telefone = request.data.get("telefone")
        email = request.data.get("email")

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

        if not nome or not cnpj or not endereco or not telefone or not email or not empresa_id or not tipo:

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

            if cnpj != empresa.cnpj and cnpj != None:
                empresa.cnpj = cnpj

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
