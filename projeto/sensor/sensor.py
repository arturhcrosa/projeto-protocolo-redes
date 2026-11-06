import asyncio
import json
import math
import random
import sys
import time
import websockets
from websockets.exceptions import WebSocketException

URL_PADRAO = "ws://127.0.0.1:8080/ws/sensor"
INTERVALO = 1.0 # segundos entre duas leituras

def gerar_temperatura(seq):
    """Onda lenta entre cerca de 21 e 31 °C, com ruído. Às vezes passa de 30 °C."""
    return round(26.5 + 5 * math.sin(seq / 15.0) + random.uniform(-0.5, 0.5), 2)

async def rodar_sensor(url, device_id, token):
    async with websockets.connect(url) as ws:
        # 1. Autenticação
        await ws.send(json.dumps({"type": "auth", "device_id": device_id, "token": token}))
        resposta = json.loads(await ws.recv())
        if resposta.get("type") != "auth_ok":
            print(f"[{device_id}] autenticação recusada: {resposta}")
            return False
        print(f"[{device_id}] autenticado em {url}")
        
        # 2. Uma leitura a cada INTERVALO segundos
        seq = 0
        while True:
            seq += 1
            leitura = {
                "type": "reading", 
                "device_id": device_id, 
                "seq": seq,
                "value": gerar_temperatura(seq), 
                "ts": time.time()
            }
            await ws.send(json.dumps(leitura))
            print(f"[{device_id}] seq={seq} valor={leitura['value']} °C")
            
            # 3. Espera o próximo envio e, enquanto isso, mostra mensagens do servidor
            try:
                texto = await asyncio.wait_for(ws.recv(), timeout=INTERVALO)
                print(f"[{device_id}] servidor: {json.loads(texto)}")
            except asyncio.TimeoutError:
                pass # caso normal: o servidor não mandou nada neste intervalo

async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    device_id, token = sys.argv[1], sys.argv[2]
    url = sys.argv[3] if len(sys.argv) > 3 else URL_PADRAO
    
    # Se o servidor cair ou ainda não estiver no ar, tenta de novo a cada 3 s
    while True:
        try:
            if await rodar_sensor(url, device_id, token) is False:
                return # token errado: não adianta tentar de novo
        except (OSError, WebSocketException) as erro:
            print(f"[{device_id}] sem conexão ({erro!r}); nova tentativa em 3 s")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Sensor encerrado.")