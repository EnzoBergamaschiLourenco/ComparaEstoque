import csv
import json
import streamlit as st


def fix_mojibake(text):
    """
    Corrige textos onde o UTF-8 foi lido incorretamente como Latin-1.
    Ex: 'AÃ‡AÃ' -> 'AÇAÍ'
    """
    if not text:
        return text
    try:
        # Tenta converter os caracteres de volta para bytes latin-1 
        # e re-decodificar como UTF-8.
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Se falhar (ex: o texto já estava correto), retorna o original
        return text

def string_to_float(value):
    """Converte strings com vírgula (ex: '1,50') para float."""
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, AttributeError):
        return 0.0

def convert_report(csv_file_path, json_output_path):
    output_data = []

    try:
        # Mantemos latin-1 para evitar erros de 'byte 0xf3' que você encontrou antes
        with open(csv_file_path, mode='r', encoding='latin-1') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';')
            
            for row in reader:
                nome_bruto = row.get('Descrição')
                
                # Aplicamos a tradução/correção no nome
                nome_corrigido = fix_mojibake(nome_bruto)
                if "*" in str(nome_bruto):
                    st.write(f"DEBUG: Item com asterisco: Original='{nome_bruto}' -> Corrigido='{nome_corrigido}'")
                
                quantidade = string_to_float(row.get('Quantidade'))
                
                if nome_corrigido:
                    entry = {
                        "nome": nome_corrigido.strip(),
                        "quantidade": quantidade,
                        "unidade": "UN"
                    }
                    output_data.append(entry)

        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(output_data, json_file, indent=4, ensure_ascii=False)
            st.write(f"Sucesso! Arquivo salvo em: {json_output_path}")
            
    except FileNotFoundError:
        st.write(f"Erro: Arquivo {csv_file_path} não encontrado.")

if __name__ == "__main__":
    # Certifique-se de que o nome do arquivo coincide com o seu projeto de logística
    convert_report('relatorioABCVenda.csv', 'resultado_vendas.json')