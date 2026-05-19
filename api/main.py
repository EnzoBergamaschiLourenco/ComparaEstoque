"""
FastAPI Application - ComparaEstoque API
Sistema de Automação de Estoque
"""

from fastapi import FastAPI, WebSocket, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from typing import List
import uuid
import asyncio
import json
from datetime import datetime
from pathlib import Path
import io

from .config import HOST, PORT, DEBUG
from . import models
from .services import contagem, nfe, vendas, consolidacao, deducao, exportacao, github

# ========================
# FastAPI App Initialization
# ========================

app = FastAPI(
    title="ComparaEstoque API",
    description="Sistema de Automação de Estoque - Backend API",
    version="1.0.0"
)

# ========================
# CORS Middleware
# ========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# Global State
# ========================

# Armazena conexões WebSocket ativas
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, processamento_id: str):
        await websocket.accept()
        self.active_connections[processamento_id] = websocket

    async def disconnect(self, processamento_id: str):
        if processamento_id in self.active_connections:
            del self.active_connections[processamento_id]

    async def send_message(self, processamento_id: str, message: dict):
        if processamento_id in self.active_connections:
            try:
                await self.active_connections[processamento_id].send_json(message)
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")


manager = ConnectionManager()

# Armazena estado dos processamentos
processamentos_ativos = {}


# ========================
# Health Check
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ========================
# WebSocket Endpoints
# ========================

@app.websocket("/ws/processamento/{processamento_id}")
async def websocket_endpoint(websocket: WebSocket, processamento_id: str):
    """WebSocket para comunicação bidirecional durante processamento"""
    await manager.connect(websocket, processamento_id)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"📨 Mensagem recebida em {processamento_id}: {data}")

            # Armazena resposta do usuário
            if data.get("tipo") == "resposta_mapeamento":
                processamentos_ativos[processamento_id]["mapeamento_resposta"] = data.get("dados", {})
                processamentos_ativos[processamento_id]["aguardando_mapeamento"] = False

            # Echo para testes
            await manager.send_message(
                processamento_id,
                {"tipo": "echo", "mensagem": data}
            )
    except Exception as e:
        print(f"Erro WebSocket: {e}")
    finally:
        await manager.disconnect(processamento_id)


# ========================
# Rotas da API
# ========================

@app.get("/api/dicionarios/compras")
async def get_purchase_dictionary():
    """Retorna dicionário de compras (purchasedictionary.json)"""
    from .config import PURCHASE_DICT_PATH
    try:
        if Path(PURCHASE_DICT_PATH).exists():
            with open(PURCHASE_DICT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        return {"erro": str(e)}


@app.get("/api/dicionarios/vendas")
async def get_sales_dictionary():
    """Retorna dicionário de vendas (salesdictionary.json)"""
    from .config import SALES_DICT_PATH
    try:
        if Path(SALES_DICT_PATH).exists():
            with open(SALES_DICT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        return {"erro": str(e)}


@app.post("/api/dicionarios/compras")
async def update_purchase_dictionary(data: dict):
    """Atualiza dicionário de compras"""
    from .config import PURCHASE_DICT_PATH
    try:
        with open(PURCHASE_DICT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return {"success": True, "mensagem": "Dicionário atualizado"}
    except Exception as e:
        return {"success": False, "erro": str(e)}


@app.post("/api/processamentos/novo")
async def criar_novo_processamento():
    """Cria um novo ID de processamento e retorna"""
    processamento_id = str(uuid.uuid4())
    processamentos_ativos[processamento_id] = {
        "id": processamento_id,
        "status": "iniciado",
        "timestamp": datetime.now(),
        "dados": {},
        "aguardando_mapeamento": False,
        "mapeamento_resposta": None
    }
    return {"processamento_id": processamento_id}


@app.get("/api/processamentos/{processamento_id}/status")
async def get_processamento_status(processamento_id: str):
    """Retorna status do processamento"""
    if processamento_id in processamentos_ativos:
        proc = processamentos_ativos[processamento_id]
        return {
            "id": proc["id"],
            "status": proc["status"],
            "timestamp": proc["timestamp"].isoformat(),
            "aguardando_mapeamento": proc["aguardando_mapeamento"]
        }
    return {"erro": "Processamento não encontrado"}


# ========================
# Placeholder Endpoints (implementar posteriormente)
# ========================

@app.post("/api/contagem")
async def processar_contagem(
    email: str = Form(None),
    senha: str = Form(None),
    file: UploadFile = File(None),
    processamento_id: str = Form(None)
):
    """Processa dados de contagem (email IMAP ou CSV)"""
    try:
        # Se forneceu arquivo, salvar temporariamente
        arquivo_temp = None
        if file:
            conteudo = await file.read()
            arquivo_temp = io.BytesIO(conteudo)

        # Processar contagem
        dados_contagem = await contagem.obter_contagem_consolidada(
            email=email,
            senha=senha,
            arquivo_csv=arquivo_temp
        )

        if not dados_contagem:
            raise HTTPException(status_code=400, detail="Falha ao processar contagem")

        # Armazenar em processamento ativo
        if processamento_id and processamento_id in processamentos_ativos:
            processamentos_ativos[processamento_id]["dados"]["contagem"] = [
                item.dict() for item in dados_contagem.items
            ]

        return {
            "status": "sucesso",
            "itens": dados_contagem.items,
            "total": len(dados_contagem.items)
        }

    except Exception as e:
        print(f"❌ Erro ao processar contagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/nfe")
async def processar_nfe_endpoint(urls: List[str] = Form([]), processamento_id: str = Form(None)):
    """Processa URLs de Notas Fiscais"""
    try:
        if not urls:
            raise HTTPException(status_code=400, detail="Nenhuma URL fornecida")

        produtos = await nfe.extrair_multiplas_nfes(urls)

        if not produtos:
            raise HTTPException(status_code=400, detail="Falha ao processar NFC-es")

        # Armazenar em processamento ativo
        if processamento_id and processamento_id in processamentos_ativos:
            processamentos_ativos[processamento_id]["dados"]["nfe"] = [
                item.dict() for item in produtos
            ]

        return {
            "status": "sucesso",
            "itens": produtos,
            "total": len(produtos)
        }

    except Exception as e:
        print(f"❌ Erro ao processar NFC-es: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vendas")
async def processar_vendas_endpoint(file: UploadFile = File(None), processamento_id: str = Form(None)):
    """Processa relatório de vendas (CSV)"""
    try:
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo fornecido")

        conteudo = await file.read()
        arquivo_temp = io.BytesIO(conteudo)

        produtos = await vendas.converter_relatorio_vendas(arquivo_temp)

        if not produtos:
            raise HTTPException(status_code=400, detail="Falha ao processar vendas")

        # Armazenar em processamento ativo
        if processamento_id and processamento_id in processamentos_ativos:
            processamentos_ativos[processamento_id]["dados"]["vendas"] = [
                item.dict() for item in produtos
            ]

        return {
            "status": "sucesso",
            "itens": produtos,
            "total": len(produtos)
        }

    except Exception as e:
        print(f"❌ Erro ao processar vendas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Endpoints de Orquestração
# ========================

@app.post("/api/orquestrar")
async def orquestrar_processamento(processamento_id: str):
    """
    Orquestra o processamento completo:
    Contagem → NF → Consolidação → Vendas → Deduções → Exportação
    """
    if processamento_id not in processamentos_ativos:
        raise HTTPException(status_code=404, detail="Processamento não encontrado")

    proc = processamentos_ativos[processamento_id]

    try:
        proc["status"] = "em_progresso"

        # Extrair dados já processados
        contagem_items = [models.ItemEstoque(**item) for item in proc["dados"].get("contagem", [])]
        nfe_items = [models.ItemEstoque(**item) for item in proc["dados"].get("nfe", [])]
        vendas_items = [models.ItemEstoque(**item) for item in proc["dados"].get("vendas", [])]

        if not contagem_items:
            raise HTTPException(status_code=400, detail="Dados de contagem não encontrados")

        # PASSO 1: Consolidação com dicionário
        print(f"🔄 Consolidando compras...")
        estoque_consolidado, itens_desconhecidos = await consolidacao.consolidar_com_dicionario(
            contagem=contagem_items,
            compras=nfe_items
        )

        # Se há itens desconhecidos, avisar via WebSocket
        if itens_desconhecidos:
            proc["aguardando_mapeamento"] = True
            proc["itens_desconhecidos"] = [item.dict() for item in itens_desconhecidos]

            await manager.send_message(
                processamento_id,
                {
                    "tipo": "necessario_mapeamento",
                    "itens": [item.dict() for item in itens_desconhecidos]
                }
            )

            # Aguardar resposta do cliente
            timeout = 300  # 5 minutos
            tempo_inicio = datetime.now()
            while proc["aguardando_mapeamento"]:
                if (datetime.now() - tempo_inicio).total_seconds() > timeout:
                    raise HTTPException(status_code=408, detail="Timeout aguardando mapeamento")
                await asyncio.sleep(1)

            # Processar respostas de mapeamento
            mapeamentos = proc.get("mapeamento_resposta", {})
            for nome_nota, nome_cadastrado in mapeamentos.items():
                # ... aplicar mapeamento ...
                pass

        # PASSO 2: Deduzir vendas
        print(f"🔄 Deduzindo vendas...")
        estoque_final = await deducao.processar_deducoes(
            estoque=estoque_consolidado,
            vendas=vendas_items
        )

        # PASSO 3: Exportar para CSV
        print(f"🔄 Gerando CSV de exportação...")
        csv_bytes, nome_arquivo = await exportacao.converter_estoque_para_csv(estoque_final)

        # PASSO 4: Sincronizar GitHub
        print(f"🔄 Sincronizando GitHub...")
        await github.sincronizar_github()

        # Salvar resultado no processamento
        proc["status"] = "concluido"
        proc["estoque_final"] = [item.dict() for item in estoque_final]
        proc["csv_bytes"] = csv_bytes
        proc["nome_arquivo_csv"] = nome_arquivo

        # Notificar conclusão
        await manager.send_message(
            processamento_id,
            {
                "tipo": "concluido",
                "status": "sucesso",
                "itens_total": len(estoque_final),
                "nome_arquivo": nome_arquivo
            }
        )

        return {
            "status": "concluido",
            "processamento_id": processamento_id,
            "itens_final": len(estoque_final)
        }

    except Exception as e:
        proc["status"] = "erro"
        proc["erro"] = str(e)
        print(f"❌ Erro na orquestração: {e}")

        await manager.send_message(
            processamento_id,
            {
                "tipo": "erro",
                "mensagem": str(e)
            }
        )

        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Endpoints de Download
# ========================

@app.get("/api/resultado/{processamento_id}/csv")
async def baixar_csv(processamento_id: str):
    """Baixa o CSV de exportação do processamento"""
    if processamento_id not in processamentos_ativos:
        raise HTTPException(status_code=404, detail="Processamento não encontrado")

    proc = processamentos_ativos[processamento_id]

    if proc["status"] != "concluido":
        raise HTTPException(status_code=400, detail="Processamento não concluído")

    csv_bytes = proc.get("csv_bytes")
    nome_arquivo = proc.get("nome_arquivo_csv", "ITE.csv")

    if not csv_bytes:
        raise HTTPException(status_code=404, detail="Arquivo CSV não encontrado")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"}
    )


@app.get("/api/resultado/{processamento_id}")
async def obter_resultado(processamento_id: str):
    """Retorna dados do resultado do processamento"""
    if processamento_id not in processamentos_ativos:
        raise HTTPException(status_code=404, detail="Processamento não encontrado")

    proc = processamentos_ativos[processamento_id]

    return {
        "id": proc["id"],
        "status": proc["status"],
        "timestamp": proc["timestamp"].isoformat(),
        "estoque_final": proc.get("estoque_final"),
        "erro": proc.get("erro")
    }


# ========================
# Main Entry Point
# ========================

if __name__ == "__main__":
    print(f"""
    🚀 Iniciando ComparaEstoque API
    📍 Host: {HOST}:{PORT}
    🔧 Debug: {DEBUG}
    📚 Docs: http://{HOST}:{PORT}/docs
    """)

    uvicorn.run(
        "api.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )
