import csv
import json

def string_to_float(value):
    """Converte strings com vírgula (ex: '1,50') para float."""
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, AttributeError):
        return 0.0

def convert_report(csv_file_path, json_output_path):
    output_data = []

    try:
        # CORREÇÃO: Alterado de 'utf-8-sig' para 'latin-1' 
        # Isso permite ler o byte 0xf3 (caractere 'ó') sem quebrar o programa.
        with open(csv_file_path, mode='r', encoding='latin-1') as csv_file:
            # Delimitador ponto e vírgula conforme seu CSV[cite: 18]
            reader = csv.DictReader(csv_file, delimiter=';')
            
            for row in reader:
                nome = row.get('Descrição')
                quantidade = string_to_float(row.get('Quantidade'))
                
                if nome:
                    entry = {
                        "nome": nome.strip(),
                        "quantidade": quantidade,
                        "unidade": "UN" # Vendas geralmente são por unidade no relatório[cite: 18]
                    }
                    output_data.append(entry)

        # Salva o resultado em um arquivo JSON sempre em utf-8[cite: 18]
        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(output_data, json_file, indent=4, ensure_ascii=False)
            
    except FileNotFoundError:
        print(f"Erro: Arquivo {csv_file_path} não encontrado.")

if __name__ == "__main__":
    convert_report('relatorioABCVenda.csv', 'resultado_vendas.json')