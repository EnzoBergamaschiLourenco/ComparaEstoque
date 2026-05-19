"""
Serviço de Consolidação de Compras
Consolida dados de contagem com dados de compras (NFC-es) usando dicionário
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from ..models import ItemEstoque, ItemDesconhecido
from ..config import PURCHASE_DICT_PATH


def carregar_dicionario_compras() -> Dict:
    """Carrega dicionário de compras do arquivo JSON"""
    try:
        if not Path(PURCHASE_DICT_PATH).exists():
            return {}
        with open(PURCHASE_DICT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar dicionário de compras: {e}")
        return {}


def salvar_dicionario_compras(dicionario: Dict) -> bool:
    """Salva dicionário de compras em arquivo JSON"""
    try:
        Path(PURCHASE_DICT_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(PURCHASE_DICT_PATH, "w", encoding="utf-8") as f:
            json.dump(dicionario, f, ensure_ascii=False, indent=4)
        print(f"✅ Dicionário de compras salvo em {PURCHASE_DICT_PATH}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar dicionário de compras: {e}")
        return False


def criar_mapa_traducao(dicionario: Dict) -> Dict[str, Tuple]:
    """
    Cria mapa reverso do dicionário para busca rápida.
    Retorna: { "Nome na Nota": ("Nome Correto", fator, "unidade_final") }
    """
    mapa = {}
    for nome_correto, info in dicionario.items():
        unidade_fixa = info.get("unidade")
        for sinonimo in info.get("sinonimos", []):
            nome_nota = sinonimo["nome"]
            fator = sinonimo.get("quantidade", 1.0)
            mapa[nome_nota] = (nome_correto, fator, unidade_fixa)
    return mapa


def encontrar_itens_desconhecidos(
    compras: List[ItemEstoque],
    mapa_traducao: Dict
) -> List[ItemDesconhecido]:
    """
    Encontra itens das compras que não estão no dicionário.

    Retorna: Lista de itens desconhecidos
    """
    desconhecidos = []
    for item in compras:
        if item.nome not in mapa_traducao:
            desconhecidos.append(ItemDesconhecido(
                nome=item.nome,
                quantidade=item.quantidade,
                unidade=item.unidade,
                tipo="compra"
            ))
    return desconhecidos


async def consolidar_com_dicionario(
    contagem: List[ItemEstoque],
    compras: List[ItemEstoque],
    dicionario: Optional[Dict] = None
) -> Tuple[List[ItemEstoque], List[ItemDesconhecido]]:
    """
    Consolida dados de contagem com dados de compras usando dicionário.

    Retorna:
        (Lista de itemizado consolidado, Lista de itens desconhecidos)
    """
    if dicionario is None:
        dicionario = carregar_dicionario_compras()

    # Criar mapa de tradução
    mapa_traducao = criar_mapa_traducao(dicionario)

    # Encontrar itens desconhecidos
    itens_desconhecidos = encontrar_itens_desconhecidos(compras, mapa_traducao)

    # Inicializar estoque com dados de contagem
    estoque_final = {}
    for item in contagem:
        estoque_final[item.nome] = {
            "quantidade": item.quantidade,
            "unidade": item.unidade,
            "quantidadeContagem": item.quantidadeContagem
        }

    # Processar compras e aplicar regras do dicionário
    for item in compras:
        if item.nome in mapa_traducao:
            nome_correto, fator, unidade_fixa = mapa_traducao[item.nome]

            # Aplicar conversão: quantidade_final = qtd_nota * fator
            quantidade_convertida = item.quantidade * fator

            if nome_correto in estoque_final:
                estoque_final[nome_correto]["quantidade"] += quantidade_convertida
            else:
                estoque_final[nome_correto] = {
                    "quantidade": quantidade_convertida,
                    "unidade": unidade_fixa,
                    "quantidadeContagem": 0
                }

            print(f"✅ Traduzido: '{item.nome}' → '{nome_correto}' (+{quantidade_convertida} {unidade_fixa})")
        else:
            print(f"⚠️ AVISO: O item '{item.nome}' não possui sinônimo no dicionário.")

    # Converter para ItemEstoque
    resultado_final = []
    for nome, dados in estoque_final.items():
        resultado_final.append(ItemEstoque(
            nome=nome,
            quantidade=round(dados["quantidade"], 3),
            unidade=dados["unidade"],
            quantidadeContagem=dados["quantidadeContagem"]
        ))

    print(f"✅ Consolidação concluída: {len(resultado_final)} itens")
    print(f"⚠️ {len(itens_desconhecidos)} itens desconhecidos que precisam mapeamento")

    return resultado_final, itens_desconhecidos


def adicionar_mapeamento(
    nome_cadastrado: str,
    unidade: str,
    nome_nota: str,
    fator_conversao: float
) -> bool:
    """
    Adiciona novo mapeamento ao dicionário de compras.

    Retorna: bool indicando sucesso
    """
    try:
        dicionario = carregar_dicionario_compras()

        if nome_cadastrado not in dicionario:
            dicionario[nome_cadastrado] = {
                "unidade": unidade,
                "sinonimos": []
            }

        # Verifica se sinônimo já existe
        sinonimos = dicionario[nome_cadastrado]["sinonimos"]
        if not any(s["nome"] == nome_nota for s in sinonimos):
            sinonimos.append({
                "nome": nome_nota,
                "quantidade": fator_conversao,
                "unidade": "UN"
            })

        return salvar_dicionario_compras(dicionario)

    except Exception as e:
        print(f"❌ Erro ao adicionar mapeamento: {e}")
        return False
