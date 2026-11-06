# experimentos/graficos.py
"""Gera os gráficos e as tabelas de resumo dos experimentos."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PASTA = Path(__file__).resolve().parent / "resultados"
ESTILOS = {
    "normal": {"color": "#2a78d6", "marker": "o", "linestyle": "-"},
    "degradado": {"color": "#eb6834", "marker": "s", "linestyle": "--"},
}
ESTILO_OUTRO = {"color": "#1baf7a", "marker": "^", "linestyle": ":"}

plt.rcParams.update({
    "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.3,
    "axes.spines.top": False, "axes.spines.right": False,
})
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

def estilo(cenario):
    return ESTILOS.get(cenario, ESTILO_OUTRO)

def ordem_cenarios(df):
    return sorted(df["cenario"].unique(), key=lambda c: (c != "normal", c))

def ler(padrao):
    arquivos = sorted(PASTA.glob(padrao))
    if not arquivos:
        print(f"Sem arquivos {padrao}: gráfico ignorado.")
        return None
    return pd.concat([pd.read_csv(a) for a in arquivos], ignore_index=True)

def salvar(fig, nome):
    fig.tight_layout()
    fig.savefig(PASTA / nome, dpi=300)
    plt.close(fig)
    print("Gráfico salvo:", PASTA / nome, "\n")

def grafico_a():
    df = ler("exp_a_rtt_*.csv")
    if df is None: return
    resumo = (df.groupby(["cenario", "tecnica"])["rtt_ms"]
             .agg(["count", "mean", "median", "std", "min", "max"]).round(3))
    resumo.to_csv(PASTA / "resumo_a_rtt.csv")
    print(resumo)
    
    tecnicas = ["websocket", "http_mesma_conexao", "http_conexao_nova"]
    rotulos = ["WebSocket", "HTTP\nkeep-alive", "HTTP\nnova conexão"]
    cenarios = ordem_cenarios(df)
    
    fig, eixos = plt.subplots(1, len(cenarios), figsize=(3.5 * len(cenarios), 3), squeeze=False)
    for eixo, cenario in zip(eixos[0], cenarios):
        dados = [df[(df["cenario"] == cenario) & (df["tecnica"] == t)]["rtt_ms"] for t in tecnicas]
        eixo.boxplot(dados, widths=0.5, medianprops={"color": estilo(cenario)["color"], "linewidth": 2})
        eixo.set_xticks([1, 2, 3], rotulos)
        eixo.set_title(f"Cenário: {cenario}")
        eixo.set_ylabel("RTT (ms)")
    salvar(fig, "exp_a_rtt.png")

def grafico_b():
    df = ler("exp_b_throughput_*.csv")
    if df is None: return
    resumo = (df.groupby(["cenario", "tamanho_bytes"])["vazao_mbps"]
             .agg(["count", "mean", "std"]).round(3).reset_index())
    resumo.to_csv(PASTA / "resumo_b_throughput.csv", index=False)
    print(resumo)
    
    fig, eixo = plt.subplots(figsize=(3.5, 2.8))
    for cenario in ordem_cenarios(resumo):
        grupo = resumo[resumo["cenario"] == cenario]
        eixo.errorbar(grupo["tamanho_bytes"], grupo["mean"], yerr=grupo["std"], capsize=3, label=cenario, **estilo(cenario))
    eixo.set_xscale("log")
    eixo.set_yscale("log")
    eixo.set_xlabel("Tamanho da mensagem (bytes úteis, escala log)")
    eixo.set_ylabel("Vazão útil (Mbit/s, escala log)")
    eixo.legend(title="Cenário")
    salvar(fig, "exp_b_throughput.png")

def grafico_c():
    df = ler("exp_c_concorrencia_*.csv")
    if df is None: return
    resumo = (df.groupby(["cenario", "num_clientes"])
             .agg(rtt_medio_ms=("rtt_ms", "mean"), rtt_desvio_ms=("rtt_ms", "std"),
                  mensagens=("rtt_ms", "count"), duracao_s=("duracao_s", "first"))
             .reset_index())
    resumo["taxa_msg_s"] = resumo["mensagens"] / resumo["duracao_s"]
    resumo = resumo.round(3)
    resumo.to_csv(PASTA / "resumo_c_concorrencia.csv", index=False)
    print(resumo)
    
    fig, (eixo_rtt, eixo_taxa) = plt.subplots(1, 2, figsize=(7, 2.8))
    for cenario in ordem_cenarios(resumo):
        grupo = resumo[resumo["cenario"] == cenario]
        eixo_rtt.errorbar(grupo["num_clientes"], grupo["rtt_medio_ms"], yerr=grupo["rtt_desvio_ms"], capsize=3, label=cenario, **estilo(cenario))
        eixo_taxa.plot(grupo["num_clientes"], grupo["taxa_msg_s"], label=cenario, **estilo(cenario))
    eixo_rtt.set_yscale("log")
    eixo_rtt.set_ylabel("RTT médio (ms, escala log)")
    eixo_taxa.set_ylabel("Taxa atendida (msg/s)")
    for eixo in (eixo_rtt, eixo_taxa):
        eixo.set_xlabel("Clientes simultâneos")
        eixo.set_xticks(sorted(resumo["num_clientes"].unique()))
        eixo.legend(title="Cenário")
    salvar(fig, "exp_c_concorrencia.png")

def grafico_d():
    df = ler("exp_d_tcp_udp_*.csv")
    if df is None: return
    df["rtt_ms"] = pd.to_numeric(df["rtt_ms"], errors="coerce")
    enviadas = df[df["situacao"] != "atrasada"]
    resumo = (enviadas.groupby(["cenario", "protocolo"])
             .agg(enviadas=("seq", "count"),
                  ok=("situacao", lambda s: (s == "ok").sum()),
                  rtt_mediana_ms=("rtt_ms", "median"),
                  rtt_p5_ms=("rtt_ms", lambda s: s.quantile(0.05)),
                  rtt_p95_ms=("rtt_ms", lambda s: s.quantile(0.95)),
                  rtt_max_ms=("rtt_ms", "max"))
             .reset_index())
    atrasadas = df[df["situacao"] == "atrasada"].groupby(["cenario", "protocolo"]).size()
    resumo["atrasadas"] = [atrasadas.get((c, p), 0) for c, p in zip(resumo["cenario"], resumo["protocolo"])]
    resumo["sem_eco_pct"] = 100 * (1 - resumo["ok"] / resumo["enviadas"])
    resumo = resumo.round(3)
    resumo.to_csv(PASTA / "resumo_d_tcp_udp.csv", index=False)
    print(resumo)
    
    protocolos = ["TCP", "UDP"]
    cenarios = ordem_cenarios(resumo)
    largura = 0.8 / len(cenarios)
    
    fig, (eixo_perda, eixo_rtt) = plt.subplots(1, 2, figsize=(7, 2.8))
    for k, cenario in enumerate(cenarios):
        linhas = resumo[resumo["cenario"] == cenario].set_index("protocolo").reindex(protocolos)
        x = [i + (k - (len(cenarios) - 1) / 2) * largura for i in range(len(protocolos))]
        barras = eixo_perda.bar(x, linhas["sem_eco_pct"], width=largura * 0.9, color=estilo(cenario)["color"], label=cenario)
        eixo_perda.bar_label(barras, fmt="%.1f%%", fontsize=8)
        
        mediana = linhas["rtt_mediana_ms"]
        eixo_rtt.errorbar(x, mediana, yerr=[mediana - linhas["rtt_p5_ms"], linhas["rtt_p95_ms"] - mediana], capsize=3, linestyle="none", color=estilo(cenario)["color"], marker=estilo(cenario)["marker"], label=cenario)
        
    for eixo in (eixo_perda, eixo_rtt):
        eixo.set_xticks(range(len(protocolos)), protocolos)
        eixo.legend(title="Cenário")
    eixo_perda.set_ylabel("Mensagens sem eco em 1 s (%)")
    eixo_rtt.set_yscale("log")
    eixo_rtt.set_ylabel("RTT (ms, escala log)\nponto: mediana; barra: p5 a p95")
    salvar(fig, "exp_d_tcp_udp.png")

if __name__ == "__main__":
    PASTA.mkdir(exist_ok=True)
    grafico_a()
    grafico_b()
    grafico_c()
    grafico_d()