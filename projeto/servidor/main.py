import json
import logging
import sqlite3
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

# Configuração
PASTA = Path(__file__).resolve().parent
ARQUIVO_BANCO = PASTA / "dados.db"
ARQUIVO_LOG = PASTA / "servidor.log"
PAGINA_PAINEL = PASTA.parent / "web" / "index.html"
LIMITE_ALERTA = 30.0  # °C: acima disto, o servidor gera um alerta
FAIXA_VALIDA = (-40.0, 125.0)  # °C: fora disto, a leitura é rejeitada (erro 422)

# Um token por dispositivo (autenticação simples).
TOKENS = {
    "s1": "abc123",
    "s2": "def456",
    "s3": "ghi789",
    "exp": "teste",  # usado pelos scripts dos experimentos
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

log = logging.getLogger("servidor")
app = FastAPI(title="Projeto 1 - Monitoramento de sensores")
paineis = set()  # conexões WebSocket dos painéis abertos
em_alerta = {}   # device_id -> True enquanto o valor estiver acima do limite

# Banco de dados (SQLite)
def criar_tabelas():
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            valor REAL NOT NULL,
            ts_sensor REAL NOT NULL,
            ts_servidor REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            valor REAL NOT NULL,
            limite REAL NOT NULL,
            ts REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def salvar_leitura(device_id, seq, valor, ts_sensor):
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.execute(
        "INSERT INTO leituras (device_id, seq, valor, ts_sensor, ts_servidor) VALUES (?, ?, ?, ?, ?)",
        (device_id, seq, valor, ts_sensor, time.time())
    )
    conn.commit()
    conn.close()

def salvar_alerta(device_id, valor, ts):
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.execute(
        "INSERT INTO alertas (device_id, valor, limite, ts) VALUES (?, ?, ?, ?)",
        (device_id, valor, LIMITE_ALERTA, ts)
    )
    conn.commit()
    conn.close()

def buscar_historico(device_id, limite):
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.row_factory = sqlite3.Row
    linhas = conn.execute(
        "SELECT device_id, seq, valor, ts_sensor, ts_servidor FROM leituras WHERE device_id = ? ORDER BY id DESC LIMIT ?",
        (device_id, limite)
    ).fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]

def buscar_alertas(limite):
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.row_factory = sqlite3.Row
    linhas = conn.execute(
        "SELECT device_id, valor, limite, ts FROM alertas ORDER BY id DESC LIMIT ?",
        (limite,)
    ).fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]

criar_tabelas()

# Rotas HTTP
@app.get("/")
def pagina_painel():
    return FileResponse(PAGINA_PAINEL)

@app.get("/api/ping")
def http_ping():
    return {"type": "pong", "ts_servidor": time.time()}

@app.get("/api/historico")
def historico(device_id: str, limite: int = 50):
    if device_id not in TOKENS:
        raise HTTPException(status_code=404, detail="dispositivo desconhecido")
    limite = max(1, min(limite, 1000))
    return buscar_historico(device_id, limite)

@app.get("/api/alertas")
def alertas(limite: int = 20):
    limite = max(1, min(limite, 1000))
    return buscar_alertas(limite)

# WebSocket: funções auxiliares
async def enviar_erro(ws, codigo, texto):
    await ws.send_text(json.dumps({"type": "error", "code": codigo, "msg": texto}))

async def enviar_para_paineis(mensagem):
    texto = json.dumps(mensagem)
    for painel in list(paineis):
        try:
            await painel.send_text(texto)
        except Exception:
            paineis.discard(painel)
            log.warning("Falha ao enviar para um painel; conexão removida")

async def tratar_leitura(ws, device_id, msg):
    valor, seq, ts = msg.get("value"), msg.get("seq"), msg.get("ts")
    
    # Validação das entradas
    if msg.get("device_id") != device_id:
        await enviar_erro(ws, 401, "device_id diferente do autenticado")
        return
    if not isinstance(valor, (int, float)) or not isinstance(seq, int) or not isinstance(ts, (int, float)):
        await enviar_erro(ws, 400, "campos 'value', 'seq' e 'ts' ausentes ou com tipo errado")
        return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)