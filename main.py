import streamlit as st
import imaplib
import email
import re
import os
import json

# Importações dos seus módulos existentes
from umovextractor import extrair_produtos
from nfextractor import extrair_dados_tabresult
from report_converter import convert_report
from addpurchase import consolidar_com_dicionario
from salesdeducer import processar_estoque as deduzir_vendas

# 1. Função adaptada para receber credenciais do Streamlit em vez do sensitive.py
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

        if not links:
            st.warning("Nenhum link encontrado no corpo do email.")
            return None
        
        return links[0]

    except Exception as e:
        st.error(f"Erro de conexão IMAP: {e}")
        return None

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Automação de Estoque", layout="centered")

st.title("📦 Sistema de Automação de Estoque")
st.markdown("Insira os dados abaixo para processar o estoque do mês.")

# --- SEÇÃO 1: Credenciais IMAP ---
st.header("1. Acesso à Contagem (uMov.me)")
col1, col2 = st.columns(2)
with col1:
    email_usuario = st.text_input("E-mail IMAP", placeholder="usuario@dominio.com")
with col2:
    senha_usuario = st.text_input("Senha IMAP", type="password")

# --- SEÇÃO 2: Nota Fiscal ---
st.header("2. Nota Fiscal de Compra (NFC-e)")
link_nfce = st.text_input("URL do QRCode da NFC-e", placeholder="Cole o link da consulta pública aqui...")

# --- SEÇÃO 3: Upload do CSV de Vendas ---
st.header("3. Relatório de Vendas")
arquivo_vendas = st.file_uploader("Faça upload do relatório ABC de Vendas (.csv)", type=["csv"])

st.divider()

# --- BOTÃO DE EXECUÇÃO ---
if st.button("🚀 Iniciar Processamento", type="primary"):
    
    # Validações Iniciais
    if not email_usuario or not senha_usuario:
        st.error("Por favor, preencha o E-mail e Senha para buscar o link da contagem.")
        st.stop()
        
    if not arquivo_vendas:
        st.error("Por favor, faça o upload do relatório de vendas CSV.")
        st.stop()

    # Fluxo principal
    with st.spinner("Processando automação... Isso pode levar alguns instantes."):
        try:
            # Passo 1: Obter link do uMov.me
            st.info("Buscando link da contagem no e-mail...")
            linkumov = buscar_link_email(email_usuario, senha_usuario)
            
            # Passo 2: Extração
            if linkumov:
                st.success(f"Link da contagem capturado!")
                extrair_produtos(linkumov) 
            
            if link_nfce:
                st.info("Extraindo dados da NFC-e informada...")
                extrair_dados_tabresult(link_nfce)
            else:
                st.warning("Nenhum link de NFC-e preenchido. As compras não serão somadas.")
                # Cria um JSON vazio caso não haja NFC-e para não quebrar a consolidação
                with open("produtos_compra.json", "w") as f: json.dump([], f)

            # Passo 3: Salvar o CSV temporário e Converter
            st.info("Processando o relatório de vendas...")
            temp_vendas_path = "temp_relatorioABCVenda.csv"
            with open(temp_vendas_path, "wb") as f:
                f.write(arquivo_vendas.getbuffer())
                
            convert_report(temp_vendas_path, 'resultado_vendas.json')

            # Garantir que produtos_contagem.json exista (caso a busca de e-mail falhe)
            if not os.path.exists("produtos_contagem.json"):
                with open("produtos_contagem.json", "w") as f: json.dump([], f)

            # Passo 4: Consolidar com Dicionário
            st.info("Aplicando compras ao estoque base...")
            consolidar_com_dicionario(
                "produtos_contagem.json", 
                "produtos_compra.json", 
                "purchasedictionary.json", 
                "estoque_adicionado_compra.json"
            )

            # Passo 5: Deduzir Vendas
            st.info("Deduzindo vendas do estoque consolidado...")
            deduzir_vendas(
                "estoque_adicionado_compra.json", 
                "resultado_vendas.json", 
                "salesdictionary.json",
                "estoque_final.json"
            )
            
            st.success("🎉 Fluxo concluído com sucesso!")
            
            # Botão de Download do Arquivo Final
            if os.path.exists("estoque_final.json"):
                with open("estoque_final.json", "rb") as f:
                    json_bytes = f.read()
                    
                st.download_button(
                    label="⬇️ Baixar Estoque Final (JSON)",
                    data=json_bytes,
                    file_name="estoque_final.json",
                    mime="application/json"
                )

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
            
        finally:
            # Limpar o arquivo temporário por segurança
            if os.path.exists(temp_vendas_path):
                os.remove(temp_vendas_path)