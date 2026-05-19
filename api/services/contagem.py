"""
Serviço de Contagem de Estoque
Consolida dados de contagem de múltiplas fontes
"""

import imaplib
import email
import re
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Tuple
import io

from ..models import ItemEstoque, DadosContagem
from ..utils.conversao import string_to_float, safe_float
from ..config import IMAP_HOST, IMAP_PORT


def buscar_link(email_usuario: str, senha_usuario: str) -> Optional[str]:
    """
    Busca o link de contagem no e-mail utilizando credenciais fornecidas.
    Retorna: URL ou None
    """
    try:
        # Conexão IMAP (Locaweb)
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(email_usuario, senha_usuario)
        mail.select("inbox")

        # 🔍 Buscar apenas emails do sistema uMov.me
        status, messages = mail.search(None, '(FROM "noreply@umov.me")')
        email_ids = messages[0].split()

        if not email_ids:
            print("❌ Nenhum email encontrado")
            return None

        # Pegar o mais recente
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # 📬 Extrair corpo HTML
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # 🔗 Extrair link do email usando regex
        links = re.findall(r'https://[^\s"]+', body)

        if not links:
            print("❌ Nenhum link encontrado no email")
            return None

        link = links[0]
        print(f"✅ Link encontrado: {link[:50]}...")
        return link

    except Exception as e:
        print(f"❌ Erro ao acessar e-mail: {e}")
        return None


def extrair_produtos(url: str) -> Optional[List[ItemEstoque]]:
    """
    Extrai produtos de uma URL de contagem (web scraping).
    Retorna: Lista de ItemEstoque ou None
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"❌ Erro ao acessar: {response.status_code}")
            return None

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

                if len(colunas) < 3:
                    continue

                # Normaliza o nome do campo (segunda coluna)
                campo = colunas[1].get_text(strip=True).lower()

                # Pega o valor (terceira coluna)
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
                try:
                    produtos.append(ItemEstoque(
                        nome=nome,
                        quantidade=string_to_float(quantidade),
                        quantidadeContagem=string_to_float(quantidade),
                        unidade=unidade if unidade else "UN"
                    ))
                except Exception as e:
                    print(f"⚠️ Erro ao processar item '{nome}': {e}")

        print(f"✅ {len(produtos)} registros de produtos encontrados via web scraping")
        return produtos

    except Exception as e:
        print(f"❌ Erro detalhado ao extrair produtos: {e}")
        return None


def processar_export_csv(arquivo_csv) -> Optional[List[ItemEstoque]]:
    """
    Lê o Cadastro_Itens.csv e retorna a lista de produtos.
    arquivo_csv pode ser: string (caminho) ou file-like object (StreamlitUploadFile)
    """
    try:
        # Se for um arquivo do Streamlit/FastAPI, reseta ponteiro
        if hasattr(arquivo_csv, 'seek'):
            arquivo_csv.seek(0)

        df = None

        # Tenta UTF-8 primeiro
        try:
            if hasattr(arquivo_csv, 'seek'):
                arquivo_csv.seek(0)
            df = pd.read_csv(arquivo_csv, sep=';', skiprows=1, encoding='utf-8')
        except Exception:
            # Se falhar, tenta Latin-1
            if hasattr(arquivo_csv, 'seek'):
                arquivo_csv.seek(0)
            df = pd.read_csv(arquivo_csv, sep=None, skiprows=1, encoding='latin-1')

        if df is None or df.empty:
            print("❌ Erro: DataFrame vazio após leitura do CSV.")
            return None

        # Limpar nomes das colunas
        df.columns = (
            df.columns
            .str.replace('\ufeff', '', regex=False)
            .str.strip()
            .str.upper()
        )

        # Filtro para ATIVO ITEM (trata 1, "1", 1.0)
        df['ATIVO ITEM'] = pd.to_numeric(df['ATIVO ITEM'], errors='coerce').fillna(0).astype(int)

        # Filtramos apenas os ativos (1)
        df_contagem = df[df['ATIVO ITEM'] == 1].copy()

        produtos = []
        for _, row in df_contagem.iterrows():
            nome_item = str(row.get('DESCRIÇÃO ITEM', '')).strip()

            # Pula itens sem nome ou marcados como "Padrão"
            if not nome_item or nome_item.lower() == 'padrão':
                continue

            try:
                produtos.append(ItemEstoque(
                    nome=nome_item,
                    unidade=str(row.get('Unidade de medida', 'UN')).strip(),
                    quantidade=safe_float(row.get('Quantidade')),
                    quantidadeContagem=safe_float(row.get('QuantidadeContagem'))
                ))
            except Exception as e:
                print(f"⚠️ Erro ao processar linha CSV: {e}")

        print(f"✅ Sucesso: {len(produtos)} itens ativos carregados do CSV.")
        return produtos

    except Exception as e:
        print(f"❌ Erro ao processar CSV: {e}")
        return None


def gerar_csv_consolidado(items: List[ItemEstoque]) -> bytes:
    """
    Gera bytes de um CSV a partir de uma lista de ItemEstoque
    Formato: Descrição;Quantidade
    """
    try:
        csv_content = "Descrição;Quantidade\n"
        for item in items:
            qtd = str(item.quantidade).replace('.', ',')
            csv_content += f"{item.nome};{qtd}\n"

        return csv_content.encode('utf-8')
    except Exception as e:
        print(f"❌ Erro ao gerar CSV: {e}")
        return b""


async def obter_contagem_consolidada(
    email: Optional[str] = None,
    senha: Optional[str] = None,
    arquivo_csv=None
) -> Optional[DadosContagem]:
    """
    Consolida dados de contagem de múltiplas fontes.

    Retorna:
        DadosContagem com items consolidados e CSV em bytes
    """
    total_estoque = {}
    dados_email = []
    dados_csv = []

    # 1. Obter dados do E-mail
    if email and senha:
        print("📧 Processando email...")
        link = buscar_link(email, senha)
        if link:
            dados_email = extrair_produtos(link) or []

    # Normalização
    if not isinstance(dados_email, list):
        dados_email = []

    # 2. Obter dados do CSV
    if arquivo_csv:
        print("📂 Processando CSV...")
        dados_csv = processar_export_csv(arquivo_csv) or []

    if not isinstance(dados_csv, list):
        dados_csv = []

    # 3. Consolidação (CSV como base, Email tem prioridade)
    # Passo A: Processar CSV
    for item in dados_csv:
        total_estoque[item.nome] = item

    # Passo B: Processar Email e Sobrepor
    for item in dados_email:
        total_estoque[item.nome] = item

    resultado_final = list(total_estoque.values())

    if not resultado_final:
        print("⚠️ Nenhum dado de contagem encontrado")
        return None

    # 4. Gerar CSV consolidado
    csv_bytes = gerar_csv_consolidado(resultado_final)

    print(f"✅ Contagem consolidada: {len(resultado_final)} itens")

    return DadosContagem(
        items=resultado_final,
        csv_bytes=csv_bytes
    )
