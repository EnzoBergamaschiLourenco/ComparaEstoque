import os
import pandas as pd
from unittest.mock import patch, MagicMock
from suplycount import processar_export_csv, obter_contagem_consolidada

def criar_ambiente_teste():
    """Garante que o arquivo CSV de teste existe para o script ler"""
    nome_arquivo = "Cadastro_Itens.csv"
    if not os.path.exists(nome_arquivo):
        print(f"⚠️ Aviso: O arquivo {nome_arquivo} não foi encontrado no diretório.")
        print("Certifique-se de que ele está na mesma pasta que este script de teste.")
        return False
    return True

def testar_processamento_csv():
    print("--- Testando: processar_export_csv ---")
    produtos = processar_export_csv("Cadastro_Itens.csv")
    
    if produtos:
        print(f"✅ Sucesso! Extraídos {len(produtos)} itens.")
        print(f"Exemplo do primeiro item: {produtos[0]}")
        
        # Validação de campos
        item = produtos[0]
        campos_esperados = ["nome", "unidade", "quantidade", "quantidadeContagem"]
        if all(k in item for k in campos_esperados):
            print("✅ Estrutura de chaves do dicionário correta.")
    else:
        print("❌ Falha: A função retornou uma lista vazia.")

@patch('suplycount.buscar_link')
@patch('suplycount.extrair_produtos')
def testar_consolidacao(mock_extrair, mock_buscar):
    print("\n--- Testando: obter_contagem_consolidada (Simulando Email) ---")
    
    # Simulando que o email retornou um item que já existe no CSV para testar a sobreposição
    # Vamos supor que o CSV tem 'CASQUINHA - INSUMO'
    mock_buscar.return_value = "http://link-falso.com"
    mock_extrair.return_value = [
        {
            "nome": "CASQUINHA - INSUMO",
            "unidade": "UN",
            "quantidade": 999.0,
            "quantidadeContagem": 999.0
        }
    ]

    arquivo_gerado = obter_contagem_consolidada("teste@email.com", "senha123", "Cadastro_Itens.csv")

    if arquivo_gerado and os.path.exists(arquivo_gerado):
        print(f"✅ Arquivo consolidado gerado: {arquivo_gerado}")
        
        # Verificar se a sobreposição do email funcionou
        df_final = pd.read_csv(arquivo_gerado, sep=';', encoding='latin-1')
        item_sobreposto = df_final[df_final['Descrição'] == 'CASQUINHA - INSUMO']
        
        if not item_sobreposto.empty:
            valor = item_sobreposto.iloc[0]['Quantidade']
            print(f"✅ Valor do item 'CASQUINHA - INSUMO' no CSV final: {valor} (Esperado: 999,0)")
    else:
        print("❌ Erro ao gerar arquivo consolidado.")

if __name__ == "__main__":
    if criar_ambiente_teste():
        testar_processamento_csv()
        testar_consolidacao()