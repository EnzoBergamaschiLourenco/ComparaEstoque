"""
Serviço de Extração de Notas Fiscais (NFC-e)
Extrai dados de URLs de notas fiscais eletrônicas
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Optional

from ..models import ItemEstoque
from ..utils.conversao import string_to_float


async def extrair_dados_nfe(url: str) -> Optional[List[ItemEstoque]]:
    """
    Extrai dados de uma URL de NFC-e.
    Busca a tabela com id='tabResult' e extrai nome, quantidade e unidade.

    Retorna: Lista de ItemEstoque ou None
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"❌ Erro ao acessar NFC-e: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        tabela = soup.find("table", id="tabResult")

        if not tabela:
            print("⚠️ Tabela 'tabResult' não encontrada na NFC-e")
            return None

        produtos = []
        linhas = tabela.find_all("tr")

        for linha in linhas:
            # Captura o texto e remove quebras, tabs
            texto_bruto = linha.get_text(separator=" ", strip=True)
            texto_completo = " ".join(texto_bruto.split())

            if "Qtde.:" not in texto_completo:
                continue

            try:
                # 1. Nome: Tudo antes de 'Qtde.:'
                nome_bruto = texto_completo.split("Qtde.:")[0].strip()
                nome = " ".join(nome_bruto.split())

                # 2. Quantidade: Busca números/vírgulas entre 'Qtde.:' e 'UN:'
                match_qtde = re.search(r"Qtde.:\s*([\d,.]+)", texto_completo)
                quantidade_str = match_qtde.group(1) if match_qtde else "0"

                # 3. Unidade: Busca a palavra entre 'UN:' e 'Vl.'
                match_unidade = re.search(r"UN:\s*(\w+)", texto_completo)
                unidade = match_unidade.group(1).upper() if match_unidade else "UN"

                if nome and quantidade_str:
                    produtos.append(ItemEstoque(
                        nome=nome,
                        quantidade=string_to_float(quantidade_str),
                        unidade=unidade,
                        quantidadeContagem=0.0
                    ))

            except Exception as e:
                print(f"⚠️ Erro ao processar linha da NFC-e: {e}")
                continue

        print(f"✅ NFC-e processada: {len(produtos)} itens extraídos")
        return produtos

    except Exception as e:
        print(f"❌ Erro ao extrair dados da NFC-e: {e}")
        return None


async def extrair_multiplas_nfes(urls: List[str]) -> List[ItemEstoque]:
    """
    Processa múltiplas URLs de NFC-e e consolida o resultado.

    Retorna: Lista consolidada de ItemEstoque
    """
    todos_produtos = []

    for i, url in enumerate(urls, 1):
        if not url.strip():
            continue

        print(f"📄 Processando NFC-e {i}/{len(urls)}...")
        produtos = await extrair_dados_nfe(url)

        if produtos:
            todos_produtos.extend(produtos)

    print(f"✅ Total de itens de todas as NFC-es: {len(todos_produtos)}")
    return todos_produtos
