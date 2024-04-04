from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.views import View
import psycopg2
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
import requests
from io import BytesIO
from PIL import Image
import tempfile
import os



# 1° PDF OD (relatorio um) -----------------------------------------------------------
class RelatorioView(View):
    template_name = 'relatorio_template.html'

    def get(self, request, *args, **kwargs):
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            host="database-4.cg6rk0mnctnw.us-east-2.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="lepes_dados_FRM"
        )

        # Criar um cursor para executar comandos SQL
        cur = conn.cursor()

        # Adapte a lógica para usar o parâmetro CNPJ na sua consulta SQL
        query1 = f"""
            SELECT UPPER(REGEXP_REPLACE(cadastral_itaborai."nome_ue", '[-–]', '')) AS nome_ue,
                COUNT(DISTINCT cadastral_itaborai.nome_turma) AS qtdTurmasCadastral,
                COUNT(DISTINCT dds_eapi_od."V010013A") AS qtdTurmasEapiOd,
                COUNT(DISTINCT cadastral_itaborai.nome_turma) - COUNT(DISTINCT dds_eapi_od."V010013A") AS turmasFaltantes 
            FROM cadastral_itaborai
            LEFT JOIN dds_eapi_od ON UPPER(REGEXP_REPLACE(cadastral_itaborai."nome_ue", '[-–]', '')) = dds_eapi_od."V010001B"
            WHERE REGEXP_REPLACE(cadastral_itaborai."nome_ue", '[-–]', '') <> 'CIEP V MARIA EUDOCIA SANTA TEREZINHA'
            GROUP BY nome_ue
            ORDER BY turmasFaltantes DESC;
            
            """ 

        # Executar a consulta 1
        cur.execute(query1)

        # Recuperar os resultados da consulta 1
        resultados_query1 = cur.fetchall()

        # Obter os nomes das colunas da consulta 1
        colunas_query1 = [desc[0] for desc in cur.description]

        # Criar DataFrame da consulta 1
        df_query1 = pd.DataFrame(resultados_query1, columns=colunas_query1)

        # Criar um objeto FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Definir a fonte e o tamanho do título
        pdf.set_font("Arial", "B", 16)

        # Adicionar o título
        pdf.cell(0, 10, "Acompanhamento eapi QPDI FGV", ln=True, align='C')

        # Volte à fonte padrão para o restante do conteúdo
        pdf.set_font("Arial", "", 12)

        # Adicionar uma linha abaixo do título
        pdf.set_draw_color(0, 0, 0) 
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Adicionar uma linha em branco entre as queries
        pdf.ln(10)

        # Adicionar um subtítulo
        pdf.cell(0, 10, "Informações para acompanhamento das observações diretas", ln=True, align='C')

        # Adicionar uma linha em branco após o subtítulo
        pdf.ln(10)

        # Adicionar cabeçalhos da tabela
        pdf.set_fill_color(200, 220, 255)  # Cor de fundo para os cabeçalhos
        pdf.set_font("Arial", "B", 7)
        pdf.cell(100, 8, "Escola", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Qtd. Turmas Cadastral", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Qtd. Turmas Eapi Od", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Turmas Faltantes", 1, 1, 'C', 1)

        # Adicionar dados da tabela
        pdf.set_fill_color(255, 255, 255)  # Cor de fundo para as linhas
        pdf.set_font("Arial", "B", 6)
        for index, row in df_query1.iterrows():
            pdf.cell(100, 8, row['nome_ue'], 1)
            pdf.cell(30, 8, str(row['qtdturmascadastral']), 1, 0, 'C')
            pdf.cell(30, 8, str(row['qtdturmaseapiod']), 1, 0, 'C')
            pdf.cell(30, 8, str(row['turmasfaltantes']), 1, 1, 'C')

        
        # Corrigir o nome da variável para torná-lo um identificador válido
        turmas_faltantes = float(row['turmasfaltantes'])  # Assuming the value is already a numeric type

        # Define your color ranges here
        if turmas_faltantes > 0:
            pdf.set_fill_color(50, 100, 0)  # vermelho
        else:
            pdf.set_fill_color(102, 255, 102)  # verde

        pdf.cell(30, 8, str(turmas_faltantes), 1, 1, 'C')

        # Adicionar uma linha em branco após a tabela
        pdf.ln(10)

        # Gere o PDF diretamente como bytes
        # pdf_bytes = bytes(pdf.output(dest='S'))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')


        # Retorne o PDF como uma resposta HTTP
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'filename=relatorio.pdf'

        return response
    


# 2° PDF OD (relatorio dois) -----------------------------------------------------------
class RelatorioViewDois(View):
    template_name = 'relatorio_template.html'

    def get(self, request, *args, **kwargs):
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            host="database-4.cg6rk0mnctnw.us-east-2.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="lepes_dados_FRM"
        )

        # Criar um cursor para executar comandos SQL
        cur = conn.cursor()

        # Adapte a lógica para usar o parâmetro CNPJ na sua consulta SQL
        query2 = f"""
            WITH cadastral_agg AS (
                SELECT 
                    UPPER(REGEXP_REPLACE(c."nome_ue", '[-–]', '')) AS nome_ue,
                    ARRAY_AGG(DISTINCT UPPER(TRANSLATE(c."nome_turma", 'áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ', 'aaaaeeiooouucAAAAEEIOOOUUC'))) AS turmas_cadastral
                FROM cadastral_itaborai c
                WHERE REGEXP_REPLACE(c."nome_ue", '[-–]', '') <> 'CIEP V MARIA EUDOCIA SANTA TEREZINHA'
                GROUP BY nome_ue
            ),
            dds_eapi_od_agg AS (
                SELECT 
                    UPPER(REGEXP_REPLACE(d."V010001B", '[-–]', '')) AS nome_ue,
                    ARRAY_AGG(DISTINCT UPPER(TRANSLATE(d."V010013A", 'áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ', 'aaaaeeiooouucAAAAEEIOOOUUC'))) AS turmas_dds_eapi_od
                FROM dds_eapi_od d
                GROUP BY nome_ue
            )
            SELECT 
                c.nome_ue,
                UNNEST(c.turmas_cadastral) AS turmas_cadastral,
                UNNEST(d.turmas_dds_eapi_od) AS turmas_dds_eapi_od,
                ARRAY(SELECT UNNEST(c.turmas_cadastral) EXCEPT SELECT UNNEST(d.turmas_dds_eapi_od)) AS turmas_faltantes
            FROM cadastral_agg c
            LEFT JOIN dds_eapi_od_agg d ON c.nome_ue = d.nome_ue;

        """ 

        # Executar a consulta 2
        cur.execute(query2)

        # Recuperar os resultados da consulta 2
        resultados_query2 = cur.fetchall()

        # Obter os nomes das colunas da consulta 2
        colunas_query2 = [desc[0] for desc in cur.description]

        # Criar DataFrame da consulta 2
        df_query2 = pd.DataFrame(resultados_query2, columns=colunas_query2)

        # Criar um objeto FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Definir a fonte e o tamanho do título
        pdf.set_font("Arial", "B", 16)

        # Adicionar o título
        pdf.cell(0, 10, "Acompanhamento eapi QPDI FGV", ln=True, align='C')

        # Volte à fonte padrão para o restante do conteúdo
        pdf.set_font("Arial", "", 12)

        # Adicionar uma linha abaixo do título
        pdf.set_draw_color(0, 0, 0) 
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Adicionar uma linha em branco entre as queries
        pdf.ln(10)

        # Adicionar um subtítulo
        pdf.cell(0, 10, "Informações para acompanhamento das observações diretas - turmas faltantes", ln=True, align='C')

        # Adicionar uma linha em branco após o subtítulo
        pdf.ln(10)

        # Adicionar cabeçalhos da tabela
        pdf.set_fill_color(200, 220, 255)  # Cor de fundo para os cabeçalhos
        pdf.set_font("Arial", "B", 7)
        pdf.cell(85, 8, "Escola", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Turmas Cadastral", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Turmas Eapi Od", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Turmas Faltantes", 1, 1, 'C', 1)

        
        # Adicionar dados da tabela
        pdf.set_fill_color(255, 255, 255)  # Cor de fundo para as linhas
        pdf.set_font("Arial", "B", 6)

        lista_escolas = df_query2['nome_ue'].unique()

        i = 0 
        for index, row in df_query2.iterrows():

            if lista_escolas[i] != row['nome_ue']:
                i += 1
            
                # criando outra tabela por escola 
                pdf.ln(10)

                # colocando outro cabecalho para a proxima tabela
                pdf.set_fill_color(200, 220, 255)  
                pdf.set_font("Arial", "B", 7)
                pdf.cell(85, 8, "Escola", 1, 0, 'C', 1)
                pdf.cell(35, 8, "Turmas Cadastral", 1, 0, 'C', 1)
                pdf.cell(35, 8, "Turmas Eapi Od", 1, 0, 'C', 1)
                pdf.cell(35, 8, "Turmas Faltantes", 1, 1, 'C', 1)
            
            # desenhando as celulas da primeira linha
            pdf.cell(85,10, row['nome_ue'], 1)
            pdf.cell(35, 10, str(row['turmas_cadastral']), 1, 0, 'C')
            pdf.cell(35, 10, str(row['turmas_dds_eapi_od']), 1, 0, 'C')
            pdf.cell(35, 10, str(row['turmas_faltantes']), 1, 1, 'C')

        # Adicionar uma linha em branco após a tabela
        pdf.ln(10)

        # Gere o PDF diretamente como bytes
        # pdf_bytes = bytes(pdf.output(dest='S'))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')

        # Retorne o PDF como uma resposta HTTP
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'filename=relatorio.pdf'

        return response



# PDF ED (Entrevista do diretor) -------------------------------------------------------------------------------------------------
class RelatorioViewEd(View):
    template_name = 'relatorio_template.html'

    def get(self, request, *args, **kwargs):
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            host="database-4.cg6rk0mnctnw.us-east-2.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="lepes_dados_FRM"
        )

        # Criar um cursor para executar comandos SQL
        cur = conn.cursor()

        # Adapte a lógica para usar o parâmetro CNPJ na sua consulta SQL
        query3 = f"""
            SELECT
                DISTINCT UPPER (REGEXP_REPLACE(cadastral_itaborai."nome_ue", '[-–]', '')) AS "ed_prevista_cadastral",
                "dds_eapi_ed"."V010001B_D" AS "ed_realizada",
                "dds_eapi_ed"."V010023_D" AS "appliedBy",
                "dds_eapi_ed"."V010024_D" AS "applicationdate"
            FROM cadastral_itaborai
                LEFT JOIN "dds_eapi_ed" ON UPPER(cadastral_itaborai."nome_ue") = "dds_eapi_ed"."V010001B_D";
        """ 

        # Executar a consulta 3
        cur.execute(query3)

        # Recuperar os resultados da consulta 3
        resultados_query3 = cur.fetchall()

        # Obter os nomes das colunas da consulta 3
        colunas_query3 = [desc[0] for desc in cur.description]

        # Criar DataFrame da consulta 3
        df_query3 = pd.DataFrame(resultados_query3, columns=colunas_query3)

        # Criar um objeto FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Definir a fonte e o tamanho do título
        pdf.set_font("Arial", "B", 16)

        # Adicionar o título
        pdf.cell(0, 10, "Acompanhamento eapi QPDI FGV", ln=True, align='C')

        # Volte à fonte padrão para o restante do conteúdo
        pdf.set_font("Arial", "", 12)

        # Adicionar uma linha abaixo do título
        pdf.set_draw_color(0, 0, 0) 
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Adicionar uma linha em branco entre as queries
        pdf.ln(10)

        # Adicionar um subtítulo
        pdf.cell(0, 10, "Informações para acompanhamento das entrevistas do diretor", ln=True, align='C')

        # Adicionar uma linha em branco após o subtítulo
        pdf.ln(10)

        # Adicionar cabeçalhos da tabela
        pdf.set_fill_color(102, 255, 102)  # Cor verde para os cabeçalhos
        pdf.set_font("Arial", "B", 7)
        pdf.cell(65, 8, "Ed. Previstas", 1, 0, 'C', 1)
        pdf.cell(55, 8, "Ed. Realizadas", 1, 0, 'C', 1)
        pdf.cell(45, 8, "Aplicador", 1, 0, 'C', 1)
        pdf.cell(25, 8, "Data de aplicação", 1, 1, 'C', 1)

        # Adicionar dados da tabela
        pdf.set_fill_color(255, 255, 255)  # Cor de fundo para as linhas
        pdf.set_font("Arial", "B", 6)
        for index, row in df_query3.iterrows():
            pdf.cell(65, 8, row['ed_prevista_cadastral'], 1)
            pdf.cell(55, 8, str(row['ed_realizada']), 1, 0, 'C')
            pdf.cell(45, 8, str(row['appliedBy']), 1, 0, 'C')
            pdf.cell(25, 8, str(row['applicationdate']), 1, 1, 'C')


        # Adicionar uma linha em branco após a tabela
        pdf.ln(10)

        # Gere o PDF diretamente como bytes
        # pdf_bytes = bytes(pdf.output(dest='S'))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')

        # Retorne o PDF como uma resposta HTTP
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'filename=relatorio.pdf'

        return response
    



# PDF EP (Entrevista do professor) ------------------------------------------------------------------------------------------------
class RelatorioViewEp(View):
    template_name = 'relatorio_template.html'

    def get(self, request, *args, **kwargs):
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            host="database-4.cg6rk0mnctnw.us-east-2.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="lepes_dados_FRM"
        )

        # Criar um cursor para executar comandos SQL
        cur = conn.cursor()

        # Adapte a lógica para usar o parâmetro CNPJ na sua consulta SQL
        query4 = f"""
            SELECT
                UPPER(REGEXP_REPLACE(cadastral_itaborai."nome_ue", '[-–]', '')) AS "nome_ue",
                UNACCENT(UPPER(cadastral_itaborai."nome_turma")) AS "ep_prevista_cadastral",
                "dds_eapi_ep"."V010013A_P" AS "ep_realizada",
                "dds_eapi_ep"."V010023_P" AS "appliedBy",
                "dds_eapi_ep"."V010024_P" AS "applicationdate"
            FROM cadastral_itaborai
            LEFT JOIN "dds_eapi_ep" ON 
                UPPER(REGEXP_REPLACE(cadastral_itaborai."nome_ue", '[-–]', '')) = "dds_eapi_ep"."V010001B_P" AND
                UNACCENT(UPPER(cadastral_itaborai."nome_turma")) = UNACCENT("dds_eapi_ep"."V010013A_P")
            ORDER BY "nome_ue" ASC;
         """ 

        # Executar a consulta 4
        cur.execute(query4)

        # Recuperar os resultados da consulta 4
        resultados_query4 = cur.fetchall()

        # Obter os nomes das colunas da consulta 4
        colunas_query4 = [desc[0] for desc in cur.description]

        # Criar DataFrame da consulta 4
        df_query4 = pd.DataFrame(resultados_query4, columns=colunas_query4)

        # Criar um objeto FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Definir a fonte e o tamanho do título
        pdf.set_font("Arial", "B", 16)

        # Adicionar o título
        pdf.cell(0, 10, "Acompanhamento eapi QPDI FGV", ln=True, align='C')

        # Volte à fonte padrão para o restante do conteúdo
        pdf.set_font("Arial", "", 12)

        # Adicionar uma linha abaixo do título
        pdf.set_draw_color(0, 0, 0) 
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Adicionar uma linha em branco entre as queries
        pdf.ln(10)

        # Adicionar um subtítulo
        pdf.cell(0, 10, "Informações para acompanhamento das entrevistas do professor", ln=True, align='C')

        # Adicionar uma linha em branco após o subtítulo
        pdf.ln(10)

        # Adicionar cabeçalhos da tabela
        pdf.set_fill_color(255, 165, 0)  # Cor laranja para os cabeçalhos
        pdf.set_font("Arial", "B", 6)
        pdf.cell(55, 8, "Escola", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Ep. Previstas", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Ep. Realizadas", 1, 0, 'C', 1)
        pdf.cell(45, 8, "Aplicador", 1, 0, 'C', 1)
        pdf.cell(20, 8, "Data de aplicação", 1, 1, 'C', 1)

        # Adicionar dados da tabela
        pdf.set_fill_color(255, 255, 255)  # Cor de fundo para as linhas
        pdf.set_font("Arial", "B", 5.5)

        lista_escolas4 = df_query4['nome_ue'].unique()

        i = 0 
        for index, row in df_query4.iterrows():

            if lista_escolas4[i] != row['nome_ue']:
                i += 1
            
                # criando outra tabela por escola 
                pdf.ln(10)

                # colocando outro cabecalho para a proxima tabela
                pdf.set_fill_color(255, 165, 0)
                pdf.set_font("Arial", "B", 6)
                pdf.cell(55, 8, "Escola", 1, 0, 'C', 1)
                pdf.cell(30, 8, "Ep. Previstas", 1, 0, 'C', 1)
                pdf.cell(30, 8, "Ep. Realizadas", 1, 0, 'C', 1)
                pdf.cell(45, 8, "Aplicador", 1, 0, 'C', 1)
                pdf.cell(20, 8, "Data de aplicação", 1, 1, 'C', 1)
            
            # desenhando as celulas da primeira linha
            pdf.cell(55, 8, row['nome_ue'], 1)
            pdf.cell(30, 8, str(row['ep_prevista_cadastral']), 1, 0, 'C')
            pdf.cell(30, 8, str(row['ep_realizada']), 1, 0, 'C')
            pdf.cell(45, 8, str(row['appliedBy']), 1, 0, 'C')
            pdf.cell(20, 8, str(row['applicationdate']), 1, 1, 'C')

        # Adicionar uma linha em branco após a tabela
        pdf.ln(10)


        # Gere o PDF diretamente como bytes
        # pdf_bytes = bytes(pdf.output(dest='S'))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')

        # Retorne o PDF como uma resposta HTTP
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'filename=relatorio.pdf'

        return response
    

