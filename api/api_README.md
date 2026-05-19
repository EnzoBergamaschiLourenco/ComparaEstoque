# ComparaEstoque API - FastAPI Backend

Sistema de Automação de Estoque transformado de Streamlit para FastAPI + React.

## 📋 Estrutura do Projeto

```
api/
├── __init__.py
├── config.py              # Configurações e variáveis de ambiente
├── models.py              # Modelos Pydantic
├── main.py                # Aplicação FastAPI principal
├── services/
│   ├── contagem.py       # Processamento de contagem
│   ├── nfe.py            # Extração de Notas Fiscais
│   ├── vendas.py         # Conversão de vendas
│   ├── consolidacao.py   # Consolidação com dicionário
│   ├── deducao.py        # Deduções de estoque
│   ├── exportacao.py     # Exportação para CSV
│   └── github.py         # Integração GitHub
└── utils/
    └── conversao.py      # Utilitários de conversão
```

## 🚀 Instalação e Execução

### 1. Instalar dependências
```bash
python -m pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Criar arquivo `.env`:
```dotenv
DEBUG=true
HOST=0.0.0.0
PORT=8000
GITHUB_TOKEN=seu_token_github
GITHUB_REPO=EnzoBergamaschiLourenco/ComparaEstoque
DATA_DIR=./data
```

### 3. Executar servidor

```bash
python run.py
```

Servidor estará disponível em: `http://localhost:8000`

Documentação interativa (Swagger UI): `http://localhost:8000/docs`

## 📡 Endpoints da API

### Contagem
- `POST /api/contagem` - Processa dados de contagem (email/CSV)

### Notas Fiscais
- `POST /api/nfe` - Processa URLs de NFC-es

### Vendas
- `POST /api/vendas` - Processa relatório de vendas

### Orquestração
- `POST /api/iniciar-processamento` - Inicia novo processamento
- `POST /api/orquestrar` - Executa pipeline completo

### Dicionários
- `GET /api/dicionarios/compras` - Retorna dicionário de compras
- `POST /api/dicionarios/compras` - Atualiza dicionário de compras
- `GET /api/dicionarios/vendas` - Retorna dicionário de vendas

### Download
- `GET /api/resultado/{processamento_id}/csv` - Baixa CSV do resultado
- `GET /api/resultado/{processamento_id}` - Retorna dados do resultado

### WebSocket
- `WS /ws/processamento/{processamento_id}` - Chat em tempo real

## 🔄 Fluxo de Processamento

1. **Contagem**: Obter dados de contagem (email IMAP + web scraping + CSV)
2. **NFC-es**: Extrair dados de Notas Fiscais eletrônicas
3. **Vendas**: Converter relatório de vendas em dados estruturados
4. **Consolidação**: Mapear compras com dicionário de tradução
5. **Mapeamento**: Se itens desconhecidos, aguardar input do usuário via WebSocket
6. **Deduções**: Deduzir vendas do estoque
7. **Exportação**: Gerar CSV pronto para importação
8. **GitHub Sync**: Sincronizar dicionários com repositório

## 📦 Exemplo de Uso - Fluxo Completo

```bash
# 1. Criar novo processamento
POST /api/iniciar-processamento
→ Retorna: { "processamento_id": "uuid" }

# 2. Processar contagem
POST /api/contagem (com email/CSV)
→ Armazena dados no processamento

# 3. Processar NFC-es
POST /api/nfe (com lista de URLs)
→ Armazena dados no processamento

# 4. Processar Vendas
POST /api/vendas (com arquivo CSV)
→ Armazena dados no processamento

# 5. Iniciar orquestração
POST /api/orquestrar
→ Executa pipeline e retorna resultado

# 6. Baixar resultado
GET /api/resultado/{processamento_id}/csv
→ Retorna arquivo ITE_YYYYMMDD.csv
```

## 🔌 WebSocket - Mapeamento Manual

Se há itens desconhecidos, o servidor envia via WebSocket:
```json
{
  "tipo": "necessario_mapeamento",
  "itens": [
    {
      "nome": "ITEM DA NOTA",
      "quantidade": 100,
      "unidade": "UN",
      "tipo": "compra"
    }
  ]
}
```

Cliente responde com:
```json
{
  "tipo": "resposta_mapeamento",
  "dados": {
    "ITEM DA NOTA": {
      "nome_cadastrado": "ITEM CADASTRO",
      "unidade": "UN",
      "fator": 1.0
    }
  }
}
```

## 🔐 Autenticação GitHub

Requer `GITHUB_TOKEN` configurado como variável de ambiente:
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

## 📝 Notas

- Arquivos JSON são armazenados em `data/`
- `purchasedictionary.json` é sincronizado automaticamente com GitHub
- Máximo de 10 URLs de NFC-es por processamento
- Timeout de 5 minutos para mapeamento manual de itens

## 🛠️ Desenvolvimento

Para dev mode com reload automático:
```bash
DEBUG=true python run.py
```

## 📚 Documentação Adicional

Ver détalhes de cada serviço em `api/services/`
