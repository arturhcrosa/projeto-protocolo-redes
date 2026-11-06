# experimentos/exp_d_tcp_udp.py
"""Experimento D: TCP x UDP com a mesma carga."""
import csv
import socket
import statistics
import sys
import time
from pathlib import Path

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
CENARIO = sys.argv[2] if len(sys.argv) > 2 else "normal"
N = 500
TAMANHO = 100
TIMEOUT_UDP = 1.0
PORTA_UDP, PORTA_TCP = 5000, 5001
PASTA_SAIDA = Path(__file__).resolve().parent / "resultados"

def montar_mensagem(seq):
    cabecalho = f"{seq:06d}|".encode()
    return cabecalho + b"x" * (TAMANHO - len(cabecalho) - 1) + b"\n"

def teste_tcp():
    resultados = []
    with socket.create_connection((HOST, PORTA_TCP), timeout=3.0) as sock, sock.makefile("rb") as leitor:
        for seq in range(N):
            mensagem = montar_mensagem(seq)
            t0 = time.perf_counter()
            sock.sendall(mensagem)
            eco = leitor.readline()
            rtt = (time.perf_counter() - t0) * 1000
            resultados.append((seq, round(rtt, 3), "ok" if eco == mensagem else "corrompida"))
    return resultados

def teste_udp():
    resultados = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(TIMEOUT_UDP)
        for seq in range(N):
            mensagem = montar_mensagem(seq)
            t0 = time.perf_counter()
            sock.sendto(mensagem, (HOST, PORTA_UDP))
            while True:
                try:
                    eco, _ = sock.recvfrom(65535)
                except socket.timeout:
                    resultados.append((seq, "", "perdida"))
                    break
                seq_eco = int(eco[:6])
                if seq_eco == seq:
                    rtt = (time.perf_counter() - t0) * 1000
                    resultados.append((seq, round(rtt, 3), "ok"))
                    break
                resultados.append((seq_eco, "", "atrasada"))
    return resultados

def resumir(protocolo, resultados):
    rtts = [r[1] for r in resultados if r[2] == "ok"]
    perdidas = sum(1 for r in resultados if r[2] == "perdida")
    atrasadas = sum(1 for r in resultados if r[2] == "atrasada")
    print(f"{protocolo}: ok={len(rtts)}/{N} perdidas={perdidas} atrasadas={atrasadas}")
    print(f"RTT médio={statistics.mean(rtts):7.3f} ms mediana={statistics.median(rtts):7.3f} ms máx={max(rtts):8.3f} ms")

def main():
    print(f"Cenário: {CENARIO} | servidor: {HOST} | {N} mensagens de {TAMANHO} bytes por protocolo")
    tcp = teste_tcp()
    udp = teste_udp()
    resumir("TCP", tcp)
    resumir("UDP", udp)
    
    PASTA_SAIDA.mkdir(exist_ok=True)
    arquivo = PASTA_SAIDA / f"exp_d_tcp_udp_{CENARIO}.csv"
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["cenario", "protocolo", "seq", "rtt_ms", "situacao"])
        for protocolo, resultados in (("TCP", tcp), ("UDP", udp)):
            for seq, rtt, situacao in resultados:
                escritor.writerow([CENARIO, protocolo, seq, rtt, situacao])
    print(f"CSV salvo em {arquivo}")

if __name__ == "__main__":
    main()