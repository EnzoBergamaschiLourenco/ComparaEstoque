const API_BASE = 'http://localhost:8000';

export async function criarProcessamento() {
  const res = await fetch(`${API_BASE}/api/processamentos/novo`, { method: 'POST' });
  return res.json();
}

export async function getStatus(processamentoId) {
  const res = await fetch(`${API_BASE}/api/processamentos/${processamentoId}/status`);
  return res.json();
}

export async function processarContagem(email, senha, file, processamentoId) {
  const formData = new FormData();
  if (email) formData.append('email', email);
  if (senha) formData.append('senha', senha);
  if (file) formData.append('file', file);
  if (processamentoId) formData.append('processamento_id', processamentoId);

  const res = await fetch(`${API_BASE}/api/contagem`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}

export async function processarNFe(urls, processamentoId) {
  const formData = new FormData();
  urls.forEach(url => formData.append('urls', url));
  if (processamentoId) formData.append('processamento_id', processamentoId);

  const res = await fetch(`${API_BASE}/api/nfe`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}

export async function processarVendas(file, processamentoId) {
  const formData = new FormData();
  if (file) formData.append('file', file);
  if (processamentoId) formData.append('processamento_id', processamentoId);

  const res = await fetch(`${API_BASE}/api/vendas`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}

export async function orquestrar(processamentoId) {
  const res = await fetch(`${API_BASE}/api/orquestrar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ processamento_id: processamentoId }),
  });
  return res.json();
}

export async function getResultado(processamentoId) {
  const res = await fetch(`${API_BASE}/api/resultado/${processamentoId}`);
  return res.json();
}

export async function baixarCsv(processamentoId) {
  const res = await fetch(`${API_BASE}/api/resultado/${processamentoId}/csv`);
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ITE_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export async function getDicionarioCompras() {
  const res = await fetch(`${API_BASE}/api/dicionarios/compras`);
  return res.json();
}

export async function salvarDicionarioCompras(data) {
  const res = await fetch(`${API_BASE}/api/dicionarios/compras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export function conectarWebSocket(processamentoId, onMessage) {
  const ws = new WebSocket(`ws://localhost:8000/ws/processamento/${processamentoId}`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  ws.onerror = (error) => console.error('WebSocket error:', error);
  return ws;
}