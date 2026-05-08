import pandas as pd
import json
import os

def processar_export_csv(caminho_csv, caminho_json="produtos_contagem.json"):
    """
    Lê o Cadastro_Itens.csv e converte para produtos_contagem.json
    """
    try:
        # Lendo o CSV: sep=';', pula a primeira linha (metadados)
        df = pd.read_csv(caminho_csv, sep=';', skiprows=1, encoding='utf-8')

        # Filtrar apenas itens que são de 'Contagem' (opcional, dependendo da sua regra)
        # Se quiser todos os itens, basta comentar a linha abaixo
        df = df[df['ID CATEGORIA DE ITENS'] == 'Contagem']

        # Mapeando colunas para o formato do dicionário
        # nome -> DESCRIÇÃO ITEM, unidade -> Unidade de medida, quantidade -> QuantidadeContagem
        lista_produtos = []
        for _, row in df.iterrows():
            produto = {
                "nome": str(row['DESCRIÇÃO ITEM']),
                "unidade": str(row['Unidade de medida']),
                "quantidade": float(row['QuantidadeContagem']) if pd.notnull(row['QuantidadeContagem']) else 0.0
            }
            lista_produtos.append(produto)

        # Salvar em JSON
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(lista_produtos, f, indent=4, ensure_ascii=False)

        return True, f"Sucesso! {len(lista_produtos)} itens processados."

    except Exception as e:
        return False, f"Erro ao processar CSV: {str(e)}"