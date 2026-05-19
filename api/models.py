from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class ItemEstoque(BaseModel):
    """Representa um item do estoque"""
    nome: str
    quantidade: float
    unidade: str
    quantidadeContagem: float = 0.0


class DadosContagem(BaseModel):
    """Dados retornados ao processar contagem"""
    items: List[ItemEstoque]
    csv_bytes: Optional[bytes] = None


class DadosNFe(BaseModel):
    """Dados retornados ao processar Nota Fiscal"""
    items: List[ItemEstoque]


class DadosVendas(BaseModel):
    """Dados retornados ao processar vendas"""
    items: List[ItemEstoque]


class MapeamentoItem(BaseModel):
    """Mapeamento de um item desconhecido"""
    nome_nota: str  # Nome como aparece na nota fiscal
    nome_cadastrado: str  # Nome no sistema
    unidade: str
    fator_conversao: float


class RelacionarItensRequest(BaseModel):
    """Request para relacionar itens desconhecidos"""
    mapeamentos: List[MapeamentoItem]


class ProcessamentoResponse(BaseModel):
    """Resposta do processamento"""
    id: str
    status: str  # "iniciado", "em_progresso", "concluido", "erro"
    timestamp: datetime
    items_desconhecidos: List[Dict] = []
    estoque_final: Optional[List[ItemEstoque]] = None
    csv_bytes: Optional[bytes] = None
    dict_atualizado: Optional[Dict] = None
    erro: Optional[str] = None


class DictionaryItem(BaseModel):
    """Item do dicionário de compras"""
    unidade: str
    sinonimos: List[Dict] = []
    quantidadeContagem: Optional[float] = None


class DictionaryRequest(BaseModel):
    """Request para atualizar dicionário"""
    data: Dict[str, DictionaryItem]


class ItemDesconhecido(BaseModel):
    """Item desconhecido que precisa de mapeamento"""
    nome: str
    quantidade: float
    unidade: str
    tipo: str  # "compra" ou "venda"
