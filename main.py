import streamlit as st
import imaplib
import email
import re
import os
import json
from datetime import datetime

# Importações dos seus módulos existentes
from umovextractor import extrair_produtos
from nfextractor import extrair_dados_tabresult
from report_converter import convert_report
from addpurchase import consolidar_com_dicionario
from salesdeducer import processar_estoque as deduzir_vendas
from importconverter import converter_estoque_para_csv

# 1. Função para buscar link via e-mail sem sensitive.py
def buscar_link_email(email_login, password):
    try:
        mail = imaplib.IMAP4_SSL("email-ssl.com.br", 993)
        mail.login(email_login, password)
        mail.select("inbox")
        status, messages = mail.search(None, '(FROM "noreply@umov.me")')
        email_ids = messages[0].split()

        if not email_ids:
            st.warning("Nenhum email de 'noreply@umov.me' encontrado.")
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

# --- INICIALIZAÇÃO DO ESTADO (Para múltiplas URLs de NF) ---
if 'lista_nfe' not in st.session_state:
    st.session_state.lista_nfe = [""] # Inicia com um campo vazio

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Automação de Estoque", layout="centered")
st.title("📦 Sistema de Automação de Estoque")

# 1. Credenciais IMAP
st.header("1. Acesso à Contagem (uMov.me)")
col1, col2 = st.columns(2)
with col1:
    email_usuario = st.text_input("E-mail IMAP", placeholder="usuario@dominio.com")
with col2:
    senha_usuario = st.text_input("Senha IMAP", type="password")

# 2. Notas Fiscais de Compra (Dinâmico)
st.header("2. Notas Fiscais de Compra (NFC-e)")
for i, url in enumerate(st.session_state.lista_nfe):
    st.session_state.lista_nfe[i] = st.text_input(
        f"URL da Nota Fiscal {i+1}", 
        value=url, 
        key=f"nfe_{i}",
        placeholder="Cole o link da consulta pública aqui..."
    )

if st.button("➕ Adicionar outra Nota"):
    st.session_state.lista_nfe.append("")
    st.rerun()

# 3. Relatório de Vendas
st.header("3. Relatório de Vendas")
arquivo_vendas = st.file_uploader("Faça upload do relatório ABC de Vendas (.csv)", type=["csv"])

st.divider()

# --- EXECUÇÃO ---
if st.button("🚀 Iniciar Processamento", type="primary"):
    if not email_usuario or not senha_usuario or not arquivo_vendas:
        st.error("Preencha as credenciais e faça o upload do relatório de vendas.")
        st.stop()

    with st.spinner("Processando..."):
        try:
            # Passo 1: Link uMov.me
            st.info("Buscando link da contagem...")
            linkumov = buscar_link_email(email_usuario, senha_usuario)
            if linkumov:
                st.success("Link capturado!")
                extrair_produtos(linkumov) # Gera produtos_contagem.json
            
            # Passo 2: Múltiplas Notas Fiscais
            compras_totais = []
            for url in st.session_state.lista_nfe:
                if url.strip():
                    st.info(f"Extraindo dados da nota...")
                    dados_nota = extrair_dados_tabresult(url)
                    if dados_nota:
                        compras_totais.extend(dados_nota)
            
            with open("produtos_compra.json", "w", encoding="utf-8") as f:
                json.dump(compras_totais, f, ensure_ascii=False, indent=4)

            # Passo 3: Relatório de Vendas
            temp_path = "temp_vendas.csv"
            with open(temp_path, "wb") as f:
                f.write(arquivo_vendas.getbuffer())
            convert_report(temp_path, 'resultado_vendas.json')

            # Passo 4 e 5: Consolidação e Dedução
            st.info("Consolidando dados e deduzindo vendas...")
            if not os.path.exists("produtos_contagem.json"):
                with open("produtos_contagem.json", "w") as f: json.dump([], f)
            
            consolidar_com_dicionario("produtos_contagem.json", "produtos_compra.json", "purchasedictionary.json", "estoque_adicionado_compra.json")
            deduzir_vendas("estoque_adicionado_compra.json", "resultado_vendas.json", "salesdictionary.json", "estoque_final.json")

            # Passo 6: Conversão para CSV Final e Download
            st.info("Gerando arquivo de importação...")
            converter_estoque_para_csv("estoque_final.json")
            
            data_hoje = datetime.now().strftime('%Y%m%d')
            arquivo_final = f'ITE_{data_hoje}.csv'
            
            if os.path.exists(arquivo_final):
                with open(arquivo_final, "rb") as f:
                    st.download_button("⬇️ Baixar Arquivo de Importação (CSV)", f, file_name=arquivo_final, mime="text/csv")
                st.success("🎉 Processo finalizado!")
            else:
                st.error("Erro ao gerar o arquivo CSV final.")

        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            if os.path.exists("temp_vendas.csv"): os.remove("temp_vendas.csv")