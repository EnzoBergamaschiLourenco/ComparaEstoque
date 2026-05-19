"""
Serviço de Integração com GitHub
Sincroniza dicionários com repositório GitHub
"""

from github import Github, GithubException
from datetime import datetime
import json
from pathlib import Path
from typing import Optional

from ..config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_FILE_PATH, PURCHASE_DICT_PATH


async def sincronizar_github(arquivo_local: str = PURCHASE_DICT_PATH) -> bool:
    """
    Sincroniza arquivo local com GitHub.
    Atualiza purchasedictionary.json no repositório.

    Retorna: bool indicando sucesso
    """
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN não configurado. Sincronização GitHub desabilitada.")
        return False

    try:
        # Autenticar com GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        # Ler arquivo local
        if not Path(arquivo_local).exists():
            print(f"⚠️ Arquivo local não encontrado: {arquivo_local}")
            return False

        with open(arquivo_local, "r", encoding="utf-8") as f:
            conteudo_novo = f.read()

        try:
            # Buscar versão mais recente do arquivo no GitHub
            conteudo_arquivo = repo.get_contents(GITHUB_FILE_PATH)

            # Só fazer commit se conteúdo for diferente
            if conteudo_arquivo.decoded_content.decode("utf-8") != conteudo_novo:
                repo.update_file(
                    path=GITHUB_FILE_PATH,
                    message=f"Update: Dicionário atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    content=conteudo_novo,
                    sha=conteudo_arquivo.sha
                )
                print(f"✅ GitHub sincronizado com sucesso! Arquivo: {GITHUB_FILE_PATH}")
                return True
            else:
                print(f"ℹ️ Dicionário já estava atualizado no GitHub.")
                return True

        except GithubException as e:
            if e.status == 404:
                # Arquivo não existe no repo, criar novo
                repo.create_file(
                    path=GITHUB_FILE_PATH,
                    message="Initial: Criação do dicionário de compras",
                    content=conteudo_novo
                )
                print(f"✅ Novo arquivo criado no GitHub: {GITHUB_FILE_PATH}")
                return True
            else:
                print(f"❌ Erro do GitHub: {e}")
                return False

    except Exception as e:
        print(f"❌ Erro ao sincronizar GitHub: {e}")
        return False


async def baixar_dicionario_github(arquivo_local: str = PURCHASE_DICT_PATH) -> bool:
    """
    Baixa dicionário mais recente do GitHub e sobrescreve arquivo local.

    Retorna: bool indicando sucesso
    """
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN não configurado.")
        return False

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        try:
            conteudo = repo.get_contents(GITHUB_FILE_PATH)
            dados = json.loads(conteudo.decoded_content.decode("utf-8"))

            # Salvar localmente
            Path(arquivo_local).parent.mkdir(parents=True, exist_ok=True)
            with open(arquivo_local, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)

            print(f"✅ Dicionário baixado do GitHub e salvo localmente")
            return True

        except GithubException as e:
            if e.status == 404:
                print(f"⚠️ Arquivo não encontrado no GitHub: {GITHUB_FILE_PATH}")
                return False
            else:
                print(f"❌ Erro do GitHub: {e}")
                return False

    except Exception as e:
        print(f"❌ Erro ao baixar dicionário GitHub: {e}")
        return False
