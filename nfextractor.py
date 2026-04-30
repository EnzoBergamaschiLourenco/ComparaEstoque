import requests
from bs4 import BeautifulSoup
import json
import re
from report_converter import string_to_float

def extrair_dados_tabresult(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Erro ao acessar: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        tabela = soup.find("table", id="tabResult")
        
        if not tabela:
            print("Tabela 'tabResult' não encontrada.")
            return

        produtos = []
        linhas = tabela.find_all("tr")

        for linha in linhas:
            # Captura o texto e já remove \r, \n, \t substituindo por espaço
            texto_bruto = linha.get_text(separator=" ", strip=True)
            
            # Limpeza radical: remove quebras de linha e tabs extras dentro da string
            texto_completo = " ".join(texto_bruto.split())
            
            if "Qtde.:" not in texto_completo:
                continue

            try:
                # 1. Nome: Tudo antes de 'Qtde.:'
                nome_bruto = texto_completo.split("Qtde.:")[0].strip()
                # Remove espaços duplos que sobraram da remoção dos \t\n
                nome = " ".join(nome_bruto.split())

                # 2. Quantidade: Busca números/vírgulas entre 'Qtde.:' e 'UN:'
                match_qtde = re.search(r"Qtde.:\s*([\d,.]+)", texto_completo)
                quantidade = match_qtde.group(1) if match_qtde else "N/A"

                # 3. Unidade: Busca a palavra entre 'UN:' e 'Vl.'
                match_unidade = re.search(r"UN:\s*(\w+)", texto_completo)
                unidade = match_unidade.group(1) if match_unidade else "UN"

                produtos.append({
                    "nome": nome,
                    "quantidade": string_to_float(quantidade),
                    "unidade": unidade.upper()
                })

            except Exception as e:
                print(f"Erro ao processar linha: {e}")

        # Salvar JSON
        with open("produtos_compra.json", "w", encoding="utf-8") as f:
            json.dump(produtos, f, ensure_ascii=False, indent=4)

        print(f"Sucesso! {len(produtos)} itens processados sem caracteres especiais.")
        return produtos

    except Exception as e:
        print(f"Erro detalhado: {e}")

# Uso:
#extrair_dados_tabresult("https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35260401157555005173651090000563311424429371%7C2%7C1%7C1%7CD9518715BD2F7807C13B726F53F5BA69CC89BD46")