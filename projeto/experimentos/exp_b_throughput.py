# experimentos/exp_b_throughput.py
"""Experimento B: vazão útil (throughput) por WebSocket."""
import asyncio
import csv
import json
import statistics
import sys
import time
from pathlib import Path
import websockets

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8080"
CENARIO = sys.argv[2] if len(sys.argv) > 2 else "normal"
TAMANHOS = [1_000, 10_000, 100_000, 1_000_000] # bytes úteis por mensagem
REPETICOES = 10
PASTA_SAIDA = Path(__file__).resolve().parent / "resultados"

async def medir():
    linhas = []
    async with websockets.connect(f"ws://{HOST}/ws/sensor") as ws:
        await ws.send(json.dumps({"type": "auth", "device_id": "exp", "token": "teste"}))
        await ws.recv() # auth_ok
        for tamanho in TAMANHOS:
            mensagem = json.dumps({"type": "throughput", "data": "x" * tamanho})
            for rep in range(REPETICOES):
                t0 = time.perf_counter()
                await ws.send(mensagem)
                confirmacao = json.loads(await ws.recv())
                segundos = time.perf_counter() - t0
                if confirmacao.get("size") != tamanho:
                    raise RuntimeError(f"confirmação inesperada: {confirmacao}")
                vazao_mbps = (tamanho * 8) / segundos / 1e6
                linhas.append([CENARIO, tamanho, rep, round(segundos * 1000, 3), round(vazao_mbps, 3)])
    return linhas

def main():
    linhas = asyncio.run(medir())
    PASTA_SAIDA.mkdir(exist_ok=True)
    arquivo = PASTA_SAIDA / f"exp_b_throughput_{CENARIO}.csv"
    
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["cenario", "tamanho_bytes", "repeticao", "tempo_ms", "vazao_mbps"])
        escritor.writerows(linhas)
        
    print(f"Cenário: {CENARIO} | servidor: {HOST} | {REPETICOES} repetições por tamanho")
    for tamanho in TAMANHOS:
        vazoes = [l[4] for l in linhas if l[1] == tamanho]
        print(f"{tamanho:>9} bytes: vazão média={statistics.mean(vazoes):9.3f} Mbit/s desvio={statistics.stdev(vazoes):8.3f} Mbit/s")
    print(f"CSV salvo em {arquivo}")

if __name__ == "__main__":
    main()