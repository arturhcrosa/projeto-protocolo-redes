# projeto-protocolo-redes
Este repositório contém o desenvolvimento de uma aplicação distribuída de Internet projetada para coletar, transmitir, armazenar e visualizar eventos em tempo real, como parte da disciplina de Redes de Computadores da UnB.

## 📌 Acordos da Equipe
- **Clean Code:** Manter o código legível, modular e com variáveis e funções claras.
- **Documentação Contínua:** Toda funcionalidade implementada deve ser documentada logo em seguida. As decisões de arquitetura e o formato das mensagens do protocolo próprio devem ser registrados imediatamente.

## 🗺️ Fases do Desenvolvimento
O projeto será construído em conjunto por todos os membros, que atuarão em todas as frentes seguindo estas fases:

### 🏗️ Fase 1: Infraestrutura e Redes
- Configuração inicial do repositório.
- Implementação dos *sockets* nativos no servidor em Python.
- Testes iniciais de conexão (TCP/UDP).
- **Meta de Documentação:** Rascunho do diagrama de arquitetura indicando clientes, servidor e fluxos de comunicação.

### ⚙️ Fase 2: Aplicação e Protocolo
- Gerenciamento de requisições HTTP e implementação do canal de comunicação em tempo real.
- Construção da interface gráfica dos clientes.
- Implementação da persistência de dados e dos alertas.
- **Meta de Documentação:** Detalhamento do protocolo de aplicação próprio (formato da mensagem, campos, sequência de operações e tratamento de erros).

### 📊 Fase 3: Experimentos e Relatório
- Medição de RTT, throughput e testes de concorrência com 1, 2 e 5 clientes.
- Captura de tráfego real com o Wireshark e análise de conexões, encapsulamento e portas.
- **Meta de Documentação:** Geração de tabelas, gráficos, e consolidação do relatório técnico em formato PDF.

## 🛠️ Tecnologias e Bibliotecas

A linguagem escolhida para o desenvolvimento de toda a aplicação foi o **Python**. Essa escolha se justifica por dois motivos principais:
1. **Foco em Redes:** A familiaridade da equipe com a linguagem permite focar o esforço na criação do protocolo de aplicação próprio e nos experimentos de rede exigidos, em vez de lidar com a curva de aprendizado de uma nova sintaxe.
2. **Biblioteca Padrão Completa:** O ecossistema nativo do Python atende a todos os requisitos arquiteturais do projeto sem a necessidade de frameworks externos complexos, utilizando as seguintes bibliotecas embutidas:

| Biblioteca 📦 | Propósito no Projeto 🎯 | Requisito Atendido 📄 |
| :--- | :--- | :--- |
| `socket` | Criação das conexões de rede de baixo nível (TCP e UDP). | Canal em tempo real e testes do Experimento de Transporte. |
| `threading` | Gerenciamento de múltiplas conexões simultâneas no servidor. | Suporte a 2 ou mais clientes simultâneos e concorrência. |
| `time` | Captura de *timestamps* precisos de envio e recebimento. | Registro de *logs*, medição de RTT e *throughput*. |
| `json` | Estruturação e serialização das mensagens trafegadas. | Implementação do protocolo de aplicação próprio e documentado. |
| `sqlite3` | Banco de dados relacional leve e integrado em arquivo local. | Persistência de dados e histórico consultável de eventos. |