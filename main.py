import streamlit as st
import imaplib
import email
import re
import os
import json
import pandas as pd
from datetime import datetime
from github import Github, GithubException

# Importações dos módulos existentes
from suplycount import obter_contagem_consolidada
from nfextractor import extrair_dados_tabresult
from reportconverter import convert_report
from addpurchase import consolidar_com_dicionario
from salesdeducer import processar_estoque as deduzir_vendas
from importconverter import converter_estoque_para_csv

# --- CONFIGURAÇÃO GITHUB (Pegando dos Secrets) ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = st.secrets.get("REPO_NAME", "EnzoBergamaschiLourenco/ComparaEstoque")
FILE_PATH_IN_REPO = "purchasedictionary.json"

#-- ENVIAR DICIONARIO DE COMPRAS ATUALIZADO--
def commit_to_github(file_path):
    """Faz o push do arquivo JSON atualizado para o GitHub com tratamento de conflito."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Lê o conteúdo local atualizado
        with open(file_path, "r", encoding="utf-8") as f:
            new_content = f.read()

        try:
            # 1. Busca a versão MAIS RECENTE do arquivo no GitHub agora mesmo
            # Isso garante que pegamos o SHA correto para evitar o erro 409
            contents = repo.get_contents(FILE_PATH_IN_REPO)
            
            # 2. Só faz o commit se o conteúdo for realmente diferente
            # Isso evita loops de commit desnecessários no seu repositório
            if contents.decoded_content.decode("utf-8") != new_content:
                repo.update_file(
                    path=FILE_PATH_IN_REPO,
                    message=f"Update: Dicionário atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    content=new_content,
                    sha=contents.sha  # Usa o SHA que acabamos de baixar
                )
                st.toast("✅ GitHub sincronizado com sucesso!")
            else:
                st.toast("ℹ️ Dicionário já estava atualizado no GitHub.")

        except GithubException as e:
            if e.status == 404:
                # Se o arquivo não existir, cria um novo
                repo.create_file(
                    path=FILE_PATH_IN_REPO,
                    message="Initial: Criação do dicionário de compras",
                    content=new_content
                )
                st.toast("✅ Novo dicionário criado no GitHub!")
            else:
                st.error(f"Erro específico do GitHub: {e}")
                
    except Exception as e:
        st.error(f"Erro de conexão: {e}")

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
if 'github_sincronizado' not in st.session_state: st.session_state.github_sincronizado = False

st.set_page_config(page_title="Automação de Estoque", layout="centered")
st.title("📦 Sistema de Automação de Estoque")

# ==========================================
# FUNÇÃO AUXILIAR PARA LER CSV COM SEGURANÇA
# ==========================================
def ler_csv_seguro(uploaded_file):
    try:
        # Tenta UTF-8 primeiro
        return pd.read_csv(uploaded_file, sep=";", engine="python", skiprows=1, encoding="utf-8")
    except:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=";", engine="python", skiprows=1, encoding="latin-1")
        except Exception as e:
            st.error(f"Erro ao ler CSV: {e}")
            return None

# ==========================================
# FASE 0: PREENCHIMENTO DO FORMULÁRIO
# ==========================================
if st.session_state.fase == 'inicio':
    st.header("1. Acesso à Contagem (uMov.me)")
    st.caption("Escolha uma opção: Suba o arquivo exportado OU use as credenciais de e-mail.")
    
    col1, col2, col3 = st.columns([1, 1, 1.5])
    
    with col1: 
        email_user = st.text_input("E-mail IMAP", placeholder="usuario@dominio.com")
    with col2: 
        senha_user = st.text_input("Senha IMAP", type="password")
    with col3: 
        arquivo_csv = st.file_uploader("Upload Cadastro_Itens.csv", type=["csv"])

    st.header("2. Notas Fiscais de Compra (NFC-e)")
    for i, url in enumerate(st.session_state.lista_nfe):
        st.session_state.lista_nfe[i] = st.text_input(
            f"URL da Nota Fiscal {i+1}", 
            value=url, 
            key=f"nfe_{i}"
        )

    if st.button("➕ Adicionar outra Nota"):
        st.session_state.lista_nfe.append("")
        st.rerun()

    st.header("3. Relatório de Vendas")
    arquivo_vendas = st.file_uploader(
        "Faça upload do relatório ABC de Vendas (.csv)", 
        type=["csv"]
    )

    st.divider()

    if st.button("🚀 Iniciar Processamento", use_container_width=True):

        tem_email = bool(email_user and senha_user)
        tem_csv = arquivo_csv is not None

        if not arquivo_vendas:
            st.error("❌ O Relatório de Vendas é obrigatório.")
            st.stop()

        if not (tem_email or tem_csv):
            st.error("⚠️ Forneça e-mail OU CSV de cadastro.")
            st.stop()

        sucesso_contagem = False

        # ==========================================
        # 1. PROCESSAR CONTAGEM
        # ==========================================
        with st.status("Consolidando dados de contagem...") as status:

            df_cadastro = None

            if tem_csv:
                status.write("📂 Lendo CSV de cadastro...")

                df_cadastro = ler_csv_seguro(arquivo_csv)

                if df_cadastro is None or df_cadastro.empty:
                    st.error("❌ CSV inválido ou vazio.")
                    st.stop()

                # DEBUG (opcional)
                st.write("Prévia do CSV:", df_cadastro.head())

                # Salva temporário só se necessário
                caminho_temp_csv = "temp_cadastro.csv"
                df_cadastro.to_csv(caminho_temp_csv, index=False)
            else:
                caminho_temp_csv = None

            status.write("⏳ Consolidando dados...")
            st.write("Colunas detectadas:", df_cadastro.columns.tolist())

            caminho_csv_gerado = obter_contagem_consolidada(
                email_user if tem_email else None,
                senha_user if tem_email else None,
                caminho_temp_csv
            )

            if caminho_csv_gerado:
                st.success("✅ Contagem consolidada com sucesso!")
                sucesso_contagem = True
            else:
                st.error("❌ Falha ao obter contagem.")

        # Limpeza
        if tem_csv and os.path.exists("temp_cadastro.csv"):
            os.remove("temp_cadastro.csv")

        # ==========================================
        # 2. PROCESSAR NF + VENDAS
        # ==========================================
        if sucesso_contagem:
            with st.status("Processando NF-es e Vendas...") as status:

                compras_totais = []

                for url in st.session_state.lista_nfe:
                    if url.strip():
                        status.write(f"📄 Lendo Nota: {url[:40]}...")
                        dados_nota = extrair_dados_tabresult(url)

                        if dados_nota:
                            compras_totais.extend(dados_nota)

                with open("produtos_compra.json", "w", encoding="utf-8") as f:
                    json.dump(compras_totais, f, ensure_ascii=False, indent=4)

                # ==========================
                # VENDAS
                # ==========================
                status.write("📊 Processando vendas...")

                df_vendas = ler_csv_seguro(arquivo_vendas)

                if df_vendas is None or df_vendas.empty:
                    st.error("❌ CSV de vendas inválido.")
                    st.stop()

                df_vendas.to_csv("temp_vendas.csv", index=False)

                convert_report(caminho_csv_gerado, 'resultado_vendas.json')

                # ==========================
                # MAPEAMENTO
                # ==========================
                status.write("🔍 Verificando dicionário...")

                try:
                    with open("purchasedictionary.json", "r", encoding="utf-8") as f:
                        p_dict = json.load(f)
                except:
                    p_dict = {}

                nomes_conhecidos = [
                    s["nome"]
                    for v in p_dict.values()
                    if "sinonimos" in v
                    for s in v["sinonimos"]
                ]

                nao_mapeados = [
                    item for item in compras_totais 
                    if item["nome"] not in nomes_conhecidos
                ]

                if nao_mapeados:
                    st.session_state.itens_pendentes = nao_mapeados
                    st.session_state.fase = 'mapeamento'
                else:
                    st.session_state.fase = 'finalizacao'

                status.update(
                    label="🚀 Finalizado!",
                    state="complete"
                )

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

            item_selecionado = st.selectbox("Pesquise e selecione o item correspondente do sistema: \n Dica: se a busca retorar itens parecidos, opte pelo insumo", opcoes_itens)
            
            unidade_csv = df_cadastrados.loc[df_cadastrados['Nome'] == item_selecionado, 'Unidade'].values[0]

            fator_conv = st.number_input(
                f"Fator de Conversão (Quantos(as) '{unidade_csv}' de '{item_selecionado}' equivalem a 1 '{item_atual['unidade']}' '{item_atual['nome']}'?)", 
                min_value=0.001, 
                value=1.0
            )

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
# FASE 2: FINALIZAÇÃO E SYNC GITHUB
# ==========================================
elif st.session_state.fase == 'finalizacao':
    st.success("✔️ Todos os itens das notas fiscais foram mapeados ou ignorados.")
    
    with st.spinner("Concluindo consolidação e deduzindo vendas..."):
        if not os.path.exists("produtos_contagem.json"):
            with open("produtos_contagem.json", "w") as f: json.dump([], f)
        
        consolidar_com_dicionario("produtos_contagem.json", "produtos_compra.json", "purchasedictionary.json", "estoque_adicionado_compra.json")
        deduzir_vendas("estoque_adicionado_compra.json", "resultado_vendas.json", "salesdictionary.json", "estoque_final.json")
        converter_estoque_para_csv("estoque_final.json")
        
        # --- NOVO: COMMIT AUTOMÁTICO PARA O GITHUB ---
        if not st.session_state.github_sincronizado:
            commit_to_github("purchasedictionary.json")
            st.session_state.github_sincronizado = True
        
        data_hoje = datetime.now().strftime('%Y%m%d')
        arquivo_final = f'ITE_{data_hoje}.csv'
        arquivo_dict = "purchasedictionary.json"
        
        col_down1, col_down2 = st.columns(2)
        
        with col_down1:
            if os.path.exists(arquivo_final):
                with open(arquivo_final, "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar Importação (CSV)", 
                        data=f, 
                        file_name=arquivo_final, 
                        mime="text/csv",
                        use_container_width=True
                    )
        
        with col_down2:
            if os.path.exists(arquivo_dict):
                with open(arquivo_dict, "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar Dicionário Atualizado (JSON)",
                        data=f,
                        file_name="purchasedictionary.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
        if os.path.exists("temp_vendas.csv"): os.remove("temp_vendas.csv")
    
    st.divider()
    if st.button("🔄 Iniciar Novo Processamento"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()