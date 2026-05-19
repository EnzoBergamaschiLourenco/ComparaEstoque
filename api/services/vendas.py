"""
Serviço de Conversão de Vendas
Converte relatório de vendas (CSV) em dados estruturados
"""

import csv
import pandas as pd
from typing import List, Optional

from ..models import ItemEstoque
from ..utils.conversao import string_to_float


async def converter_relatorio_vendas(arquivo_csv) -> Optional[List[ItemEstoque]]:
    """
    Lê um arquivo CSV de relatório de vendas e retorna lista de ItemEstoque.
    Esperado: CSV com coluna 'Descrição' e 'Quantidade', delimitador ';'

    Retorna: Lista de ItemEstoque ou None
    """
    try:
        # Se for arquivo do FastAPI, reseta ponteiro
        if hasattr(arquivo_csv, 'seek'):
            arquivo_csv.seek(0)

        output_data = []

        # Tenta Latin-1 (comum em relatórios brasileiros)
        try:
            if hasattr(arquivo_csv, 'seek'):
                arquivo_csv.seek(0)

            with open(arquivo_csv, mode='r', encoding='latin-1') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    nome = row.get('Descrição')
                    quantidade = string_to_float(row.get('Quantidade', 0))

                    if nome:
                        output_data.append(ItemEstoque(
                            nome=nome.strip(),
                            quantidade=quantidade,
                            unidade="UN",  # Vendas geralmente são por unidade
                            quantidadeContagem=0.0
                        ))
        except (FileNotFoundError, TypeError):
            # Se for file-like object do FastAPI
            if hasattr(arquivo_csv, 'seek'):
                arquivo_csv.seek(0)

            df = pd.read_csv(arquivo_csv, sep=';', encoding='latin-1')

            for _, row in df.iterrows():
                nome = row.get('Descrição')
                quantidade = string_to_float(row.get('Quantidade', 0))

                if nome:
                    output_data.append(ItemEstoque(
                        nome=str(nome).strip(),
                        quantidade=quantidade,
                        unidade="UN",
                        quantidadeContagem=0.0
                    ))

        print(f"✅ Relatório de vendas processado: {len(output_data)} itens")
        return output_data

    except Exception as e:
        print(f"❌ Erro ao processar relatório de vendas: {e}")
        return None
