import requests
from bs4 import BeautifulSoup
import json
from report_converter import string_to_float

def extrair_produtos(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("Erro ao acessar:", response.status_code)
            return

        soup = BeautifulSoup(response.text, "html.parser")
        produtos = []

        # 🔎 Busca todas as seções que contêm produtos
        secoes = soup.find_all("div", class_="report_table c-table-report")

        for secao in secoes:
            # Pega o título (H3)
            titulo_tag = secao.find("h3")
            if not titulo_tag:
                continue

            nome = titulo_tag.get_text(strip=True)
            
            quantidade = None
            unidade = None

            # Percorre as linhas da tabela dentro da seção
            linhas = secao.find_all("tr")
            for linha in linhas:
                colunas = linha.find_all("td")

                # No seu HTML, a primeira coluna <td> é oculta (ID), 
                # a segunda é o Nome do Campo e a terceira é o Valor.
                if len(colunas) < 3:
                    continue

                # Normaliza o nome do campo (segunda coluna)
                campo = colunas[1].get_text(strip=True).lower()
                
                # Pega o valor (terceira coluna) buscando o span interno se existir
                valor_tag = colunas[2].find("span", class_="valueForExibition")
                if valor_tag:
                    valor = valor_tag.get_text(strip=True)
                else:
                    valor = colunas[2].get_text(strip=True)

                if "quantidade" in campo:
                    quantidade = valor
                elif "unidade" in campo:
                    unidade = valor.upper()

            # Só adiciona se capturou os dados essenciais
            if nome and quantidade:
                produtos.append({
                    "nome": nome,
                    "quantidade": string_to_float(quantidade),
                    "unidade": unidade if unidade else "N/A"
                })

        # Opcional: Remover duplicatas se o relatório repetir o mesmo item
        # produtos = [dict(t) for t in {tuple(d.items()) for d in produtos}]

        print(f"{len(produtos)} registros de produtos encontrados")

        # 📦 Salvar JSON
        with open("produtos_contagem.json", "w", encoding="utf-8") as f:
            json.dump(produtos, f, ensure_ascii=False, indent=4)

        print("JSON salvo com sucesso")
        return produtos

    except Exception as e:
        print("Erro detalhado:", e)
