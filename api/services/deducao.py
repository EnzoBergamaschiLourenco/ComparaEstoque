"""
Serviço de Deduções de Estoque
Deduz vendas do estoque usando dicionário de vendas
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

from ..models import ItemEstoque
from ..config import SALES_DICT_PATH


def carregar_dicionario_vendas() -> Dict:
    """Carrega dicionário de vendas do arquivo JSON"""
    try:
        if not Path(SALES_DICT_PATH).exists():
            return {}
        with open(SALES_DICT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar dicionário de vendas: {e}")
        return {}


async def processar_deducoes(
    estoque: List[ItemEstoque],
    vendas: List[ItemEstoque],
    dicionario: Optional[Dict] = None
) -> List[ItemEstoque]:
    """
    Deduz vendas do estoque usando dicionário de vendas.

    Se o produto vendido está em salesdictionary.json:
        → Deduz componentes conforme receita
    Se não está no dicionário:
        → Deduz quantidade direto do estoque

    Retorna: lista de ItemEstoque com quantidades deduzidas
    """
    if dicionario is None:
        dicionario = carregar_dicionario_vendas()

    # Mapear estoque para acesso rápido
    estoque_map = {}
    for item in estoque:
        nome = item.nome.strip()
        estoque_map[nome] = {
            "quantidade": item.quantidade,
            "unidade": item.unidade,
            "quantidadeContagem": item.quantidadeContagem
        }

    # Processar cada venda
    for venda in vendas:
        nome_venda = venda.nome.strip()

        try:
            qtd_vendida = float(venda.quantidade)
        except (ValueError, TypeError):
            qtd_vendida = 0.0

        # REGRA 1: Se o item está no dicionário de vendas
        if nome_venda in dicionario:
            print(f"📦 Processando {nome_venda} (No Dicionário)")
            componentes = dicionario[nome_venda]

            for nome_componente, info_componente in componentes.items():
                if nome_componente in estoque_map:
                    qtd_antes = estoque_map[nome_componente]["quantidade"]
                    deducao = info_componente.get("quantidade", 1.0) * qtd_vendida
                    estoque_map[nome_componente]["quantidade"] -= deducao

                    print(f"  → Reduzindo {nome_componente}: {qtd_antes:.2f} → {estoque_map[nome_componente]['quantidade']:.2f}")
                else:
                    print(f"  ⚠️ Componente '{nome_componente}' não encontrado no estoque.")

        # REGRA 2: Se NÃO constar no dicionário
        else:
            if nome_venda in estoque_map:
                qtd_antes = estoque_map[nome_venda]["quantidade"]
                estoque_map[nome_venda]["quantidade"] -= qtd_vendida
                print(f"📉 Reduzindo {nome_venda}: {qtd_antes:.2f} → {estoque_map[nome_venda]['quantidade']:.2f}")
            else:
                print(f"⚠️ Item '{nome_venda}' não está no dicionário nem no estoque.")

    # Converter de volta para ItemEstoque
    resultado_final = []
    for nome, dados in estoque_map.items():
        resultado_final.append(ItemEstoque(
            nome=nome,
            quantidade=round(dados["quantidade"], 3),
            unidade=dados["unidade"],
            quantidadeContagem=dados["quantidadeContagem"]
        ))

    print(f"✅ Deduções processadas: {len(resultado_final)} itens")
    return resultado_final
