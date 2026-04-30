import streamlit as st
import imaplib
import email
import re
import os
import json
import pandas as pd # Necessário para ler o CSV de itens cadastrados
from datetime import datetime

# Importações dos módulos existentes
from umovextractor import extrair_produtos
from nfextractor import extrair_dados_tabresult
from report_converter import convert_report
from addpurchase import consolidar_com_dicionario
from salesdeducer import processar_estoque as deduzir_vendas
from importconverter import converter_estoque_para_csv

# --- FUNÇÕES DE AUXÍLIO PARA DICIONÁRIO E COMPRAS ---
def remover_compra(nome_nota):
    """Remove um item ignorado do JSON de compras para que ele não trave a consolidação."""
    with open("produtos_compra.json", "r", encoding="utf-8") as f:
        compras = json.load(f)
    compras = [c for c in compras if c['nome'] != nome_nota]
    with open("produtos_compra.json", "w", encoding="utf-8") as f:
        json.dump(compras, f, ensure_ascii=False, indent=4)

def adicionar_ao_dicionario(nome_cadastrado, unidade, nome_nota, fator):
    """Atualiza e exporta o purchasedictionary.json com a nova relação e unidade do CSV."""
    arquivo_dict = "purchasedictionary.json"
    try:
        with open(arquivo_dict, "r", encoding="utf-8") as f:
            dicionario = json.load(f)
    except FileNotFoundError:
        dicionario = {}

    if nome_cadastrado not in dicionario:
        dicionario[nome_cadastrado] = {"unidade": unidade, "sinonimos": []}

    # Verifica se o sinônimo já existe para evitar duplicatas
    sinonimos = dicionario[nome_cadastrado]["sinonimos"]
    if not any(s["nome"] == nome_nota for s in sinonimos):
        sinonimos.append({
            "nome": nome_nota,
            "quantidade": fator,
            "unidade": "UN" # Padrão para a nota
        })

    with open(arquivo_dict, "w", encoding="utf-8") as f:
        json.dump(dicionario, f, ensure_ascii=False, indent=4)

# 1. Função para buscar link via e-mail sem sensitive.py
def buscar_link_email(email_login, password):
    try:
        mail = imaplib.IMAP4_SSL("email-ssl.com.br", 993)
        mail.login(email_login, password)
        mail.select("inbox")
        status, messages = mail.search(None, '(FROM "noreply@umov.me")')
        email_ids = messages[0].split()

        if not email_ids:
            return None

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        links = re.findall(r'https://[^\s"]+', body)
        return links[0] if links else None
    except Exception as e:
        st.error(f"Erro de conexão IMAP: {e}")
        return None

# --- INICIALIZAÇÃO DA MÁQUINA DE ESTADOS ---
if 'fase' not in st.session_state: st.session_state.fase = 'inicio'
if 'lista_nfe' not in st.session_state: st.session_state.lista_nfe = [""]
if 'itens_pendentes' not in st.session_state: st.session_state.itens_pendentes = []
if 'modo_relacionar' not in st.session_state: st.session_state.modo_relacionar = False

st.set_page_config(page_title="Automação de Estoque", layout="centered")
st.title("📦 Sistema de Automação de Estoque")

# ==========================================
# FASE 0: PREENCHIMENTO DO FORMULÁRIO
# ==========================================
if st.session_state.fase == 'inicio':
    st.header("1. Acesso à Contagem (uMov.me)")
    col1, col2 = st.columns(2)
    with col1: email_usuario = st.text_input("E-mail IMAP", placeholder="usuario@dominio.com")
    with col2: senha_usuario = st.text_input("Senha IMAP", type="password")

    st.header("2. Notas Fiscais de Compra (NFC-e)")
    for i, url in enumerate(st.session_state.lista_nfe):
        st.session_state.lista_nfe[i] = st.text_input(f"URL da Nota Fiscal {i+1}", value=url, key=f"nfe_{i}")

    if st.button("➕ Adicionar outra Nota"):
        st.session_state.lista_nfe.append("")
        st.rerun()

    st.header("3. Relatório de Vendas")
    arquivo_vendas = st.file_uploader("Faça upload do relatório ABC de Vendas (.csv)", type=["csv"])

    st.divider()

    if st.button("🚀 Iniciar Processamento", type="primary"):
        if not email_usuario or not senha_usuario or not arquivo_vendas:
            st.error("Preencha as credenciais e faça o upload do relatório de vendas.")
            st.stop()

        with st.spinner("Extraindo dados iniciais..."):
            # Extração uMov.me
            linkumov = buscar_link_email(email_usuario, senha_usuario)
            if linkumov: extrair_produtos(linkumov)
            
            # Extração NF-e
            compras_totais = []
            for url in st.session_state.lista_nfe:
                if url.strip():
                    dados_nota = extrair_dados_tabresult(url)
                    if dados_nota: compras_totais.extend(dados_nota)
            with open("produtos_compra.json", "w", encoding="utf-8") as f:
                json.dump(compras_totais, f, ensure_ascii=False, indent=4)

            # Conversão Vendas
            with open("temp_vendas.csv", "wb") as f: f.write(arquivo_vendas.getbuffer())
            convert_report("temp_vendas.csv", 'resultado_vendas.json')

            # --- VERIFICAÇÃO DE ITENS NÃO MAPEADOS ---
            try:
                with open("purchasedictionary.json", "r", encoding="utf-8") as f:
                    p_dict = json.load(f)
            except FileNotFoundError:
                p_dict = {}

            nomes_conhecidos = []
            for v in p_dict.values():
                for s in v.get("sinonimos", []):
                    nomes_conhecidos.append(s["nome"])

            nao_mapeados = [item for item in compras_totais if item["nome"] not in nomes_conhecidos]

            if nao_mapeados:
                st.session_state.itens_pendentes = nao_mapeados
                st.session_state.fase = 'mapeamento'
            else:
                st.session_state.fase = 'finalizacao'
            
            st.rerun()

# ==========================================
# FASE 1: RESOLUÇÃO DE ITENS DESCONHECIDOS
# ==========================================
elif st.session_state.fase == 'mapeamento':
    if len(st.session_state.itens_pendentes) > 0:
        item_atual = st.session_state.itens_pendentes[0]
        
        st.warning("⚠️ **Ação Necessária:** O item abaixo veio da nota fiscal, mas não possui relação no dicionário de compras.")
        st.info(f"📦 Item da Nota: **{item_atual['nome']}**")

        col_ignorar, col_relacionar = st.columns(2)
        if col_ignorar.button("❌ Ignorar item", use_container_width=True):
            remover_compra(item_atual['nome'])
            st.session_state.itens_pendentes.pop(0)
            st.session_state.modo_relacionar = False
            st.rerun()

        if col_relacionar.button("🔗 Relacionar item", use_container_width=True):
            st.session_state.modo_relacionar = True

        if st.session_state.modo_relacionar:
            st.divider()
            st.markdown("### Procurar Item no Cadastro")
            
            try:
                df_cadastrados = pd.read_csv("ItensCadastrados.csv", sep=";")
                if 'Nome' not in df_cadastrados.columns or 'Unidade' not in df_cadastrados.columns:
                    st.error("O arquivo 'ItensCadastrados.csv' precisa ter as colunas 'Nome' e 'Unidade'.")
                    st.stop()
                opcoes_itens = df_cadastrados['Nome'].dropna().tolist()
            except FileNotFoundError:
                st.error("Erro: Arquivo 'ItensCadastrados.csv' não encontrado!")
                st.stop()

            item_selecionado = st.selectbox("Pesquise e selecione o item correspondente do sistema:", opcoes_itens)
            
            # Busca a unidade correspondente à seleção atual no CSV[cite: 18]
            unidade_csv = df_cadastrados.loc[df_cadastrados['Nome'] == item_selecionado, 'Unidade'].values[0]

            # Mensagem de input com unidade dinâmica[cite: 18]
            fator_conv = st.number_input(
                f"Fator de Conversão (Quantos(as) '{unidade_csv}' de '{item_selecionado}' equivalem a 1 '{item_atual['nome']}'?)", 
                min_value=0.001, 
                value=1.0
            )

            # Resumo com unidade dinâmica[cite: 18]
            st.markdown(f"> **Resumo da Relação:** Ao comprar 1x `{item_atual['nome']}`, o sistema adicionará **{fator_conv}x {unidade_csv}** de `{item_selecionado}`.")

            if st.button("✅ Sim, tenho certeza. Salvar Relação", type="primary"):
                adicionar_ao_dicionario(item_selecionado, str(unidade_csv), item_atual['nome'], fator_conv)
                st.success("Relação adicionada ao dicionário!")
                
                st.session_state.itens_pendentes.pop(0)
                st.session_state.modo_relacionar = False
                st.rerun()
    else:
        st.session_state.fase = 'finalizacao'
        st.rerun()

# ==========================================
# FASE 2: FINALIZAÇÃO E DOWNLOAD
# ==========================================
elif st.session_state.fase == 'finalizacao':
    st.success("✔️ Todos os itens das notas fiscais foram mapeados ou ignorados.")
    
    with st.spinner("Concluindo consolidação e deduzindo vendas..."):
        if not os.path.exists("produtos_contagem.json"):
            with open("produtos_contagem.json", "w") as f: json.dump([], f)
        
        consolidar_com_dicionario("produtos_contagem.json", "produtos_compra.json", "purchasedictionary.json", "estoque_adicionado_compra.json")
        deduzir_vendas("estoque_adicionado_compra.json", "resultado_vendas.json", "salesdictionary.json", "estoque_final.json")
        converter_estoque_para_csv("estoque_final.json")
        
        data_hoje = datetime.now().strftime('%Y%m%d')
        arquivo_final = f'ITE_{data_hoje}.csv'
        
        if os.path.exists(arquivo_final):
            with open(arquivo_final, "rb") as f:
                st.download_button("⬇️ Baixar Arquivo de Importação (CSV)", f, file_name=arquivo_final, mime="text/csv")
            
        if os.path.exists("temp_vendas.csv"): os.remove("temp_vendas.csv")
    
    st.divider()
    if st.button("🔄 Iniciar Novo Processamento"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()