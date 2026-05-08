import imaplib
import email
import re
import json
import pandas as pd
import json
from reportconverter import string_to_float
import requests
from bs4 import BeautifulSoup

def buscar_link(email_usuario, senha_usuario):
    """
    Busca o link de contagem no e-mail utilizando credenciais 
    fornecidas dinamicamente via interface.
    """
    try:
        # Conexão IMAP (Locaweb)
        mail = imaplib.IMAP4_SSL("email-ssl.com.br", 993)
        mail.login(email_usuario, senha_usuario) # Agora usa os parâmetros
        mail.select("inbox")

        # 🔍 Buscar apenas emails do sistema uMov.me
        status, messages = mail.search(None, '(FROM "noreply@umov.me")')
        email_ids = messages[0].split()

        if not email_ids:
            print("Nenhum email encontrado")
            return None # Retorna None em vez de encerrar o programa

        # Pegar o mais recente[cite: 9]
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # 📬 Extrair corpo HTML[cite: 9]
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # 🔗 Extrair link do email usando regex[cite: 9]
        links = re.findall(r'https://[^\s"]+', body)

        if not links:
            print("Nenhum link encontrado no email")
            return None
        
        link = links[0] 
        return link # Retorna o link para ser usado no fluxo principal[cite: 9]

    except Exception as e:
        print(f"Erro ao acessar e-mail: {e}")
        return None

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
    
def obter_contagem_consolidada(email, senha, caminho_csv):
    """
    Novo Fluxo: Obtém dados do e-mail e do CSV e soma as quantidades
    de itens com o mesmo nome.
    """
    total_estoque = {}

    # 1. Obter dados do E-mail (via Link)
    link = buscar_link(email, senha)
    dados_email = extrair_produtos(link) if link else []

    # 2. Obter dados do CSV
    dados_csv = processar_export_csv(caminho_csv)

    # 3. Consolidar e Somar
    # Unificamos as duas listas em um loop
    for item in (dados_email + dados_csv):
        nome = item['nome']
        quantidade = item['quantidade']
        unidade = item['unidade']

        if nome in total_estoque:
            total_estoque[nome]['quantidade'] += quantidade
        else:
            total_estoque[nome] = {
                "nome": nome,
                "unidade": unidade,
                "quantidade": quantidade
            }

    # Retorna como uma lista de dicionários (formato padrão do seu sistema)
    resultado_final = list(total_estoque.values())
    
    # Salva o resultado consolidado para os próximos scripts
    with open("produtos_contagem.json", "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=4, ensure_ascii=False)
        
    return resultado_final