"""
Serviço de Exportação de Estoque
Converte dados de estoque final em CSV de importação
"""

import csv
import io
from typing import List, Tuple
from datetime import datetime

from ..models import ItemEstoque


def gerar_csv_importacao(itens: List[ItemEstoque]) -> bytes:
    """
    Gera bytes de um CSV pronto para importação no sistema.

    Formato esperado:
    C
    command;alternativeIdentifier;CF_UN;CF_Quantidade;CF_QuantidadeContagem
    I;NOME_PRODUTO;UN;150.5;100.0
    """
    try:
        buffer = io.BytesIO()

        with io.TextIOWrapper(buffer, encoding='utf-8', newline='') as text_buffer:
            writer = csv.writer(text_buffer, delimiter=';')

            # Linha 1: Marcador
            writer.writerow(['C'])

            # Linha 2: Cabeçalhos
            headers = ['command', 'alternativeIdentifier', 'CF_UN', 'CF_Quantidade', 'CF_QuantidadeContagem']
            writer.writerow(headers)

            # Dados do estoque
            for item in itens:
                writer.writerow([
                    'I',  # comando
                    item.nome,
                    item.unidade,
                    round(item.quantidade, 3),
                    round(item.quantidadeContagem, 3)
                ])

        return buffer.getvalue()

    except Exception as e:
        print(f"❌ Erro ao gerar CSV de importação: {e}")
        return b""


def gerar_nome_arquivo_csv() -> str:
    """
    Gera nome do arquivo CSV com data (ex: ITE_20260518.csv)
    """
    data_hoje = datetime.now().strftime('%Y%m%d')
    return f'ITE_{data_hoje}.csv'


async def converter_estoque_para_csv(itens: List[ItemEstoque]) -> Tuple[bytes, str]:
    """
    Converte lista de ItemEstoque para bytes de CSV e retorna nome do arquivo.

    Retorna: (csv_bytes, nome_arquivo)
    """
    try:
        csv_bytes = gerar_csv_importacao(itens)
        nome_arquivo = gerar_nome_arquivo_csv()

        print(f"✅ CSV de exportação gerado: {nome_arquivo} ({len(csv_bytes)} bytes)")
        return csv_bytes, nome_arquivo

    except Exception as e:
        print(f"❌ Erro ao converter estoque para CSV: {e}")
        return b"", ""
