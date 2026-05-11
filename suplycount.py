import imaplib
import email
import re
import json
import pandas as pd
import json
from reportconverter import string_to_float
import requests
from bs4 import BeautifulSoup
import streamlit as st
import os

def buscar_link(email_usuario, senha_usuario):
    """
    Busca o link de contagem no e-mail utilizando credenciais 
    fornecidas dinamicamente via interface.
    """
    try:
        # Conexão IMAP (Locaweb)
        mail = imaplib.IMAP4_SSL("email-ssl.com.br", 993)
        mail.login(email_usuario, senha_usuario) # Agora usa os parâmetros
        mail.select("inbox")

        # 🔍 Buscar apenas emails do sistema uMov.me
        status, messages = mail.search(None, '(FROM "noreply@umov.me")')
        email_ids = messages[0].split()

        if not email_ids:
            print("Nenhum email encontrado")
            return None # Retorna None em vez de encerrar o programa

        # Pegar o mais recente[cite: 9]
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # 📬 Extrair corpo HTML[cite: 9]
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # 🔗 Extrair link do email usando regex[cite: 9]
        links = re.findall(r'https://[^\s"]+', body)

        if not links:
            print("Nenhum link encontrado no email")
            return None
        
        link = links[0] 
        return link # Retorna o link para ser usado no fluxo principal[cite: 9]

    except Exception as e:
        print(f"Erro ao acessar e-mail: {e}")
        return None

def extrair_produtos(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("Erro ao acessar:", response.status_code)
            return

        soup = BeautifulSoup(response.text, "html.parser")
        produtos = []

        # 🔎 Busca todas as seções que contêm produtos
        secoes = soup.find_all("div", class_="report_table c-table-report")

        for secao in secoes:
            # Pega o título (H3)
            titulo_tag = secao.find("h3")
            if not titulo_tag:
                continue

            nome = titulo_tag.get_text(strip=True)
            
            quantidade = None
            unidade = None

            # Percorre as linhas da tabela dentro da seção
            linhas = secao.find_all("tr")
            for linha in linhas:
                colunas = linha.find_all("td")

                # No seu HTML, a primeira coluna <td> é oculta (ID), 
                # a segunda é o Nome do Campo e a terceira é o Valor.
                if len(colunas) < 3:
                    continue

                # Normaliza o nome do campo (segunda coluna)
                campo = colunas[1].get_text(strip=True).lower()
                
                # Pega o valor (terceira coluna) buscando o span interno se existir
                valor_tag = colunas[2].find("span", class_="valueForExibition")
                if valor_tag:
                    valor = valor_tag.get_text(strip=True)
                else:
                    valor = colunas[2].get_text(strip=True)

                if "quantidade" in campo:
                    quantidade = valor
                elif "unidade" in campo:
                    unidade = valor.upper()

            # Só adiciona se capturou os dados essenciais
            if nome and quantidade:
                produtos.append({
                    "nome": nome,
                    "quantidade": string_to_float(quantidade),
                    "unidade": unidade if unidade else "N/A"
                })

        print(f"{len(produtos)} registros de produtos encontrados")

        # 📦 Salvar JSON
        with open("produtos_contagem.json", "w", encoding="utf-8") as f:
            json.dump(produtos, f, ensure_ascii=False, indent=4)

        print("JSON salvo com sucesso")
        return produtos

    except Exception as e:
        print("Erro detalhado:", e)

def processar_export_csv(caminho_csv):
    """Lê o Cadastro_Itens.csv e retorna a lista de produtos"""
    try:
        df = pd.read_csv(caminho_csv, sep=';', skiprows=1, encoding='utf-8')
        df_contagem = df[df['ATIVO ITEM'] == 1]
        
        produtos = []
        for _, row in df_contagem.iterrows():
            produtos.append({
                "nome": str(row['DESCRIÇÃO ITEM']),
                "unidade": str(row['Unidade de medida']),
                "quantidade": float(row['Quantidade']) if pd.notnull(row['Quantidade']) else 0.0,
                "quantidadeContagem": float(row['QuantidadeContagem']) if pd.notnull(row['QuantidadeContagem']) else 0.0
            })
        return produtos # Retorna uma lista
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        return []

# --- FUNÇÃO DE CONSOLIDAÇÃO CORRIGIDA ---

def obter_contagem_consolidada(email, senha, caminho_csv):
    """
    Consolida dados do CSV e Email. 
    Se o item existir em ambos, a quantidade do Email prevalece.
    """
    total_estoque = {}
    dados_email = []
    dados_csv = []

    # 1. Obter dados do E-mail
    if email and senha:
        link = buscar_link(email, senha)
        if link:
            dados_email = extrair_produtos(link)
    
    if isinstance(dados_email, tuple):
        dados_email = dados_email[0] if (len(dados_email) > 0 and isinstance(dados_email[0], list)) else []
    elif not isinstance(dados_email, list):
        dados_email = []

    # 2. Obter dados do CSV
    if caminho_csv and os.path.exists(caminho_csv):
        dados_csv = processar_export_csv(caminho_csv)
    
    if isinstance(dados_csv, tuple):
        dados_csv = dados_csv[0] if (len(dados_csv) > 0 and isinstance(dados_csv[0], list)) else []
    elif not isinstance(dados_csv, list):
        dados_csv = []

    # 3. Consolidação com Regra de Prioridade
    
    # Passo A: Processar CSV primeiro (Base)
    for item in dados_csv:
        if isinstance(item, dict) and 'nome' in item:
            nome = str(item['nome']).strip()
            try:
                qtd = float(item.get('quantidade', 0))
            except (ValueError, TypeError):
                qtd = 0.0
            
            # Se houver duplicatas dentro do PRÓPRIO CSV, somamos
            if nome in total_estoque:
                total_estoque[nome]['quantidade'] += qtd
            else:
                total_estoque[nome] = item.copy()
                total_estoque[nome]['quantidade'] = qtd

    # Passo B: Processar Email (Prioridade)
    # Criamos um dicionário temporário para o email para somar duplicatas internas do email antes da sobreposição
    estoque_email_temp = {}
    for item in dados_email:
        if isinstance(item, dict) and 'nome' in item:
            nome = str(item['nome']).strip()
            try:
                qtd = float(item.get('quantidade', 0))
            except (ValueError, TypeError):
                qtd = 0.0
                
            if nome in estoque_email_temp:
                estoque_email_temp[nome]['quantidade'] += qtd
            else:
                estoque_email_temp[nome] = item.copy()
                estoque_email_temp[nome]['quantidade'] = qtd

    # Passo C: Sobrepor os dados do CSV com os do Email
    for nome, item_email in estoque_email_temp.items():
        # Isso vai substituir o item do CSV pelo do Email se o nome for igual,
        # ou adicionar o item se ele só existir no Email.
        total_estoque[nome] = item_email

    resultado_final = list(total_estoque.values())
    
    if not resultado_final:
        return None

    with open("produtos_contagem.json", "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=4, ensure_ascii=False)
        
    return resultado_final