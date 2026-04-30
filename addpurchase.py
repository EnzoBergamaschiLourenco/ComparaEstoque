import json

def consolidar_com_dicionario(arquivo_contagem, arquivo_compra, arquivo_dict="purchasedictionary.json", arquivo_saida="estoque_adicionado_compra.json"):
    # 1. Carregar o Dicionário de Compras (Tradução)
    try:
        with open(arquivo_dict, "r", encoding="utf-8") as f:
            purchasedict = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Dicionário {arquivo_dict} não encontrado.")
        return

    # Criar um mapa reverso para busca rápida: { "Nome na Nota": ("Nome Correto", fator, "unidade_final") }
    mapa_tradução = {}
    for nome_correto, info in purchasedict.items():
        unidade_fixa = info.get("unidade")
        for sinonimo in info.get("sinonimos", []):
            nome_na_nota = sinonimo["nome"]
            fator = sinonimo["quantidade"]
            mapa_tradução[nome_na_nota] = (nome_correto, fator, unidade_fixa)

    # 2. Carregar o Estoque Atual (Contagem)
    # Formato: { "Nome Correto": {"quantidade": float, "unidade": str} }
    estoque_final = {}
    try:
        with open(arquivo_contagem, "r", encoding="utf-8") as f:
            contagem = json.load(f)
            for item in contagem:
                nome = item["nome"]
                qtd = float(str(item.get("quantidade", "0")).replace(",", "."))
                estoque_final[nome] = {"quantidade": qtd, "unidade": item["unidade"]}
    except FileNotFoundError:
        print(f"Aviso: {arquivo_contagem} não encontrado. Iniciando estoque zerado.")

    # 3. Processar Compras e Aplicar Regras do Dicionário
    try:
        with open(arquivo_compra, "r", encoding="utf-8") as f:
            compras = json.load(f)
            
        for item in compras:
            nome_nota = item["nome"]
            try:
                qtd_nota = float(str(item.get("quantidade", "0")).replace(",", "."))
            except ValueError:
                qtd_nota = 0.0

            if nome_nota in mapa_tradução:
                nome_correto, fator, unidade_fixa = mapa_tradução[nome_nota]
                
                # Aplica a regra: Quantidade Final = Qtd da Nota * Fator do Dicionário
                quantidade_convertida = qtd_nota * fator
                
                if nome_correto in estoque_final:
                    estoque_final[nome_correto]["quantidade"] += quantidade_convertida
                else:
                    # Se o item traduzido não estava na contagem, ele entra como novo
                    estoque_final[nome_correto] = {
                        "quantidade": quantidade_convertida,
                        "unidade": unidade_fixa
                    }
                print(f"✅ Traduzido: '{nome_nota}' -> '{nome_correto}' (+{quantidade_convertida} {unidade_fixa})")
            else:
                # Se não houver sinônimo, gera o aviso e não soma
                print(f"⚠️ AVISO: O item '{nome_nota}' não possui sinônimo no dicionário e será ignorado.")

    except FileNotFoundError:
        print(f"Erro: Arquivo de compras {arquivo_compra} não encontrado.")

    # 4. Salvar Resultado Final (Float)
    resultado = []
    for nome, dados in estoque_final.items():
        resultado.append({
            "nome": nome,
            "quantidade": round(dados["quantidade"], 3),
            "unidade": dados["unidade"]
        })

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    print(f"\nConcluído! Estoque consolidado salvo em '{arquivo_saida}'.")

if __name__ == "__main__":
    consolidar_com_dicionario("produtos_contagem.json", "produtos_compra.json")