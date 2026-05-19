import os
from typing import Optional

# Diretório base para dados
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# Paths dos arquivos JSON
PURCHASE_DICT_PATH = os.path.join(DATA_DIR, "purchasedictionary.json")
SALES_DICT_PATH = os.path.join(DATA_DIR, "salesdictionary.json")
PROCESSAMENTOS_LOG_PATH = os.path.join(DATA_DIR, "processamentos_log.json")

# GitHub Config
GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
GITHUB_REPO: str = os.getenv("GITHUB_REPO", "EnzoBergamaschiLourenco/ComparaEstoque")
GITHUB_FILE_PATH: str = "purchasedictionary.json"

# Email IMAP Config (para suplycount)
IMAP_HOST = "email-ssl.com.br"
IMAP_PORT = 993

# API Config
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Timeouts
REQUEST_TIMEOUT = 30
IMAP_TIMEOUT = 30

# Limites
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_NF_URLS = 10

print(f"Config loaded: DATA_DIR={DATA_DIR}")
