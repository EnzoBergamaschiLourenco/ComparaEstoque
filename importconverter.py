import json
import csv
from datetime import datetime

def converter_estoque_para_csv(arquivo_json):
    # Gera o nome baseado na data de hoje (Ex: ITE_20260430.csv)
    data_hoje = datetime.now().strftime('%Y%m%d')
    arquivo_saida = f'ITE_{data_hoje}.csv'

    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Linha 1: Marcador
            writer.writerow(['C'])
            
            # Linha 2: Cabeçalhos
            headers = ['command', 'alternativeIdentifier', 'CF_UN', 'CF_Quantidade']
            writer.writerow(headers)
            
            # Dados do estoque
            for item in dados:
                writer.writerow([
                    'I',                           
                    item.get('nome', ''),          
                    item.get('unidade', ''),       
                    item.get('quantidade', 0)      
                ])
                
        print(f"Sucesso! Arquivo '{arquivo_saida}' gerado com sucesso.")
        
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo_json}' não foi encontrado.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    converter_estoque_para_csv('estoque_final.json')