import json
import streamlit as st

def processar_estoque(arquivo_estoque, arquivo_vendas, arquivo_dicionario, arquivo_saida="estoque_final.json"):
    # 1. Carregar o dicionário de vendas (substituindo o import salesdictionary)
    try:
        with open(arquivo_dicionario, "r", encoding="utf-8") as f:
            sales_dict = json.load(f)
    except FileNotFoundError:
        st.write(f"Erro: {arquivo_dicionario} não encontrado.")
        return

    # 2. Carregar o estoque inicial
    try:
        with open(arquivo_estoque, "r", encoding="utf-8") as f:
            estoque_lista = json.load(f)
    except FileNotFoundError:
        st.write(f"Erro: {arquivo_estoque} não encontrado.")
        return

    # Mapeia o estoque para facilitar a busca
    st.write(f"DEBUG: Primeiros 2 itens do estoque carregado: {estoque_lista[:2]}")
    estoque_map = {}
    for item in estoque_lista:
        nome = item.get("nome", "").strip()
        if not nome:
            st.write(f"DEBUG: Item sem nome encontrado no estoque! Chaves disponíveis: {item.keys()}")
        try:
            qtd = float(str(item.get("quantidade", "0")).replace(",", "."))
        except ValueError:
            qtd = 0.0
        try:
            qtdC = float(str(item.get("quantidadeContagem", "0")).replace(",", "."))
        except ValueError:
            qtdC = 0.0
        estoque_map[nome] = {
            "quantidade": qtd,
            "unidade": item.get("unidade", "").upper().strip(),
            "quantidadeContagem": qtdC
        }

    # 3. Carregar as vendas
    try:
        with open(arquivo_vendas, "r", encoding="utf-8") as f:
            vendas_lista = json.load(f)
    except FileNotFoundError:
        st.write(f"Erro: {arquivo_vendas} no encontrado.")
        return

    # 4. Processar cada venda
    for venda in vendas_lista:
        nome_venda = venda.get("nome", "").strip()
        try:
            qtd_vendida = float(str(venda.get("quantidade", "0")).replace(",", "."))
        except ValueError:
            qtd_vendida = 0.0

        # REGRA 1: Se o item está no dicionário carregado do JSON
        if nome_venda in sales_dict:
            st.write(f"DEBUG: Processando {nome_venda} (No Dicionário)")
            componentes = sales_dict[nome_venda]
            for nome_componente, info_componente in componentes.items():
                if nome_componente in estoque_map:
                    deducao = info_componente["quantidade"] * qtd_vendida
                    estoque_map[nome_componente]["quantidade"] -= deducao
                    st.write(f"  -> Reduzindo {nome_componente}: {qtd_antes} -> {estoque_map[nome_componente]['quantidade']}")
                else:
                    st.write(f"Aviso: Componente '{nome_componente}' não encontrado no estoque.")
        
        # REGRA 2: Se NÃO constar no dicionário
        else:
            if nome_venda in estoque_map:
                estoque_map[nome_venda]["quantidade"] -= qtd_vendida
            else:
                st.write(f"Aviso: Item '{nome_venda}' não está no dicionário nem no estoque.")

    # 5. Formatar e salvar a saída
    resultado_final = []
    for nome, dados in estoque_map.items():
        resultado_final.append({
            "nome": nome,
            "quantidade": round(dados["quantidade"], 3),
            "unidade": dados["unidade"],
            "quantidadeContagem": dados["quantidadeContagem"]
        })

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=4)

    st.write(f"Concluído! Estoque atualizado salvo em '{arquivo_saida}'.")

if __name__ == "__main__":
    # Agora passamos os 3 arquivos necessários
    processar_estoque(
        "estoque_adicionado_compra.json", 
        "resultado_vendas.json", 
        "salesdictionary.json"  # Nome do seu arquivo de dicionário
    )