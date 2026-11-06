# experimentos/exp_a_rtt.py
"""Experimento A: RTT da aplicação."""
import asyncio
import csv
import json
import statistics
import sys
import time
from pathlib import Path
import requests
import websockets

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8080"
CENARIO = sys.argv[2] if len(sys.argv) > 2 else "normal"
N = 50
PAUSA = 0.05
PASTA_SAIDA = Path(__file__).resolve().parent / "resultados"

async def medir_websocket():
    rtts = []
    async with websockets.connect(f"ws://{HOST}/ws/sensor") as ws:
        await ws.send(json.dumps({"type": "auth", "device_id": "exp", "token": "teste"}))
        await ws.recv() # auth_ok
        for i in range(N):
            t0 = time.perf_counter()
            await ws.send(json.dumps({"type": "ping", "t": t0}))
            await ws.recv() # pong
            rtts.append((time.perf_counter() - t0) * 1000)
            await asyncio.sleep(PAUSA)
    return rtts

def medir_http(mesma_conexao):
    url = f"http://{HOST}/api/ping"
    sessao = requests.Session() if mesma_conexao else None
    rtts = []
    for i in range(N):
        t0 = time.perf_counter()
        if sessao:
            resposta = sessao.get(url, timeout=10)
        else:
            resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        rtts.append((time.perf_counter() - t0) * 1000)
        time.sleep(PAUSA)
    return rtts

def main():
    resultados = {
        "websocket": asyncio.run(medir_websocket()),
        "http_mesma_conexao": medir_http(mesma_conexao=True),
        "http_conexao_nova": medir_http(mesma_conexao=False),
    }
    PASTA_SAIDA.mkdir(exist_ok=True)
    arquivo = PASTA_SAIDA / f"exp_a_rtt_{CENARIO}.csv"
    
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["cenario", "tecnica", "i", "rtt_ms"])
        for tecnica, rtts in resultados.items():
            for i, rtt in enumerate(rtts):
                escritor.writerow([CENARIO, tecnica, i, round(rtt, 3)])
                
    print(f"Cenário: {CENARIO} | servidor: {HOST} | N = {N} por técnica")
    for tecnica, rtts in resultados.items():
        print(f"{tecnica:20s} média={statistics.mean(rtts):8.3f} ms mediana={statistics.median(rtts):8.3f} ms desvio={statistics.stdev(rtts):7.3f} ms máx={max(rtts):8.3f} ms")
    print(f"CSV salvo em {arquivo}")

if __name__ == "__main__":
    main()