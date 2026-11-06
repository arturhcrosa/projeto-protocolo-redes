# experimentos/eco_servidor.py
"""Servidor de eco do Experimento D: UDP na porta 5000 e TCP na porta 5001."""
import socket
import threading

PORTA_UDP = 5000
PORTA_TCP = 5001

def eco_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORTA_UDP))
    print(f"UDP: eco na porta {PORTA_UDP}")
    while True:
        dados, endereco = sock.recvfrom(65535)
        sock.sendto(dados, endereco)

def atender_tcp(conn, endereco):
    print("TCP: conexão de", endereco)
    with conn, conn.makefile("rb") as leitor:
        for linha in leitor:
            conn.sendall(linha)
    print("TCP: fim da conexão de", endereco)

def eco_tcp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORTA_TCP))
    sock.listen()
    sock.settimeout(1.0)
    print(f"TCP: eco na porta {PORTA_TCP}")
    while True:
        try:
            conn, endereco = sock.accept()
        except socket.timeout:
            continue
        conn.settimeout(None)
        threading.Thread(target=atender_tcp, args=(conn, endereco), daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=eco_udp, daemon=True).start()
    try:
        eco_tcp()
    except KeyboardInterrupt:
        print("Servidor de eco encerrado.")