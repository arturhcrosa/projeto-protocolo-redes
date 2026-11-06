# experimentos/exp_c_concorrencia.py
"""Experimento C: concorrência com 1, 2 e 5 clientes ao mesmo tempo."""
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
NUM_CLIENTES = [1, 2, 5]
DURACAO = 10
TAXA = 20
PASTA_SAIDA = Path(__file__).resolve().parent / "resultados"

async def cliente(id_cliente, n, fim, registros):
    async with websockets.connect(f"ws://{HOST}/ws/sensor") as ws:
        await ws.send(json.dumps({"type": "auth", "device_id": "exp", "token": "teste"}))
        await ws.recv() # auth_ok
        while time.perf_counter() < fim:
            t0 = time.perf_counter()
            await ws.send(json.dumps({"type": "ping", "t": t0}))
            await ws.recv() # pong
            rtt = (time.perf_counter() - t0) * 1000
            registros.append([CENARIO, n, id_cliente, DURACAO, round(rtt, 3)])
            await asyncio.sleep(1 / TAXA)

async def rodada(n):
    registros = []
    fim = time.perf_counter() + DURACAO
    await asyncio.gather(*(cliente(i, n, fim, registros) for i in range(n)))
    return registros

def main():
    todos = []
    print(f"Cenário: {CENARIO} | servidor: {HOST} | {DURACAO}s por rodada, {TAXA} pings/s")
    for n in NUM_CLIENTES:
        registros = asyncio.run(rodada(n))
        todos.extend(registros)
        rtts = [r[4] for r in registros]
        print(f"{n} cliente(s): RTT médio={statistics.mean(rtts):7.3f} ms mediana={statistics.median(rtts):7.3f} ms máx={max(rtts):8.3f} ms taxa atendida={len(rtts)/DURACAO:6.1f} msg/s")
        
    PASTA_SAIDA.mkdir(exist_ok=True)
    arquivo = PASTA_SAIDA / f"exp_c_concorrencia_{CENARIO}.csv"
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["cenario", "num_clientes", "cliente", "duracao_s", "rtt_ms"])
        escritor.writerows(todos)
    print(f"CSV salvo em {arquivo}")

if __name__ == "__main__":
    main()