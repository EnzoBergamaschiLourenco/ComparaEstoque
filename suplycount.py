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
import csv

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
                    "quantidadeContagem": string_to_float(quantidade),
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
    """Lê o Cadastro_Itens.csv e retorna a lista de produtos de forma robusta"""
    try:
        # Se for um arquivo do Streamlit, precisamos garantir que o ponteiro esteja no início
        if hasattr(caminho_csv, 'seek'):
            caminho_csv.seek(0)

        df = None
        # Tenta UTF-8
        try:
            df = pd.read_csv(caminho_csv, sep=';', skiprows=1, encoding='utf-8')
        except Exception:
            # Se falhar, reseta o ponteiro e tenta Latin-1
            if hasattr(caminho_csv, 'seek'):
                caminho_csv.seek(0)
            df = pd.read_csv(caminho_csv, sep=None, skiprows=1, encoding='latin-1')

        if df is None or df.empty:
            print("Erro: DataFrame vazio após leitura do CSV.")
            return []

        # Limpar nomes das colunas (remove espaços e caracteres invisíveis como o BOM)
        df.columns = [str(col).replace('\ufeff', '').strip() for col in df.columns]

        # Filtro Robusto para ATIVO ITEM (trata 1, "1", 1.0)
        # Usamos errors='coerce' para transformar lixo em NaN e fillna(0) para segurança
        df['ATIVO ITEM'] = pd.to_numeric(df['ATIVO ITEM'], errors='coerce').fillna(0).astype(int)
        
        # Filtramos apenas os ativos (1)
        df_contagem = df[df['ATIVO ITEM'] == 1].copy()
        
        produtos = []
        for _, row in df_contagem.iterrows():
            nome_item = str(row.get('DESCRIÇÃO ITEM', '')).strip()
            
            # Pula itens sem nome ou marcados como "Padrão"
            if not nome_item or nome_item.lower() == 'padrão':
                continue

            def safe_float(val):
                if pd.isna(val) or str(val).strip() == '':
                    return 0.0
                try:
                    return float(str(val).replace(',', '.'))
                except:
                    return 0.0

            produtos.append({
                "nome": nome_item,
                "unidade": str(row.get('Unidade de medida', 'UN')),
                "quantidade": safe_float(row.get('Quantidade')),
                "quantidadeContagem": safe_float(row.get('QuantidadeContagem'))
            })
        
        print(f"Sucesso: {len(produtos)} itens ativos carregados.")
        return produtos

    except Exception as e:
        st.error(f"Erro ao processar CSV no site: {e}")
        return []

def obter_contagem_consolidada(email, senha, caminho_csv):
    total_estoque = {}
    dados_email = []
    dados_csv = []

    # 1. Obter dados do E-mail
    if email and senha:
        link = buscar_link(email, senha)
        if link:
            dados_email = extrair_produtos(link)
    
    # Normalização de dados_email
    if not isinstance(dados_email, list):
        dados_email = []

    # 2. Obter dados do CSV
    if caminho_csv:
        # Se for um caminho de arquivo, verifica se existe. Se for objeto (Streamlit), lê direto.
        if isinstance(caminho_csv, str) and os.path.exists(caminho_csv):
            dados_csv = processar_export_csv(caminho_csv)
        elif not isinstance(caminho_csv, str):
             dados_csv = processar_export_csv(caminho_csv)
    
    if not isinstance(dados_csv, list):
        dados_csv = []

    # 3. Consolidação (CSV como base, Email tem prioridade)
    # Passo A: Processar CSV
    for item in dados_csv:
        nome = item['nome']
        total_estoque[nome] = item.copy()

    # Passo B: Processar Email e Sobrepor
    for item in dados_email:
        nome = item['nome']
        total_estoque[nome] = item.copy()

    resultado_final = list(total_estoque.values())
    
    if not resultado_final:
        return None

    # 4. Exportação para CSV final
    arquivo_saida = "produtos_consolidado.csv"
    with open(arquivo_saida, mode="w", encoding="latin-1", errors="replace", newline="") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Descrição', 'Quantidade'])
        for item in resultado_final:
            # Formata para padrão brasileiro (vírgula decimal) para o convert_report ler
            qtd = str(item.get('quantidade', 0.0)).replace('.', ',')
            writer.writerow([item['nome'], qtd])
            
    return arquivo_saida