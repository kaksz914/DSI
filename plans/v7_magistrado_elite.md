# Plano Arquitetônico DSI v7.0 "MAGISTRADO ELITE"

Este documento detalha as melhorias de nível elite para tornar o Command Center 100% infalível e indetectável.

## 1. DSI-Orchestrator (Ataques Paralelos)
Atualmente, os vetores rodam sequencialmente. A v7.0 introduzirá um Gerenciador de Processos Inteligente que:
*   Inicia a captura de PMKID em background (passivo).
*   Executa varredura WPS Pixie-Dust rápida (ativo).
*   Inicia o Evil Twin se a placa secundária estiver disponível.
*   **Decisão em Tempo Real:** Se o PMKID for capturado em 5 segundos, todos os outros ataques param para evitar detecção.

## 2. Stealth Protocol v2
Para evitar detecção por WIDS (Wireless Intrusion Detection Systems):
*   **MAC Swapping:** A cada tentativa de deauth, o MAC do atacante muda dinamicamente dentro de um range de vendedores comuns (ex: Apple, Samsung).
*   **Packet Fragmentation:** Envio de pacotes de desautenticação fragmentados para confundir firewalls de rádio.
*   **Hostname Spoofing:** O sistema assume nomes de rede comuns (ex: "iPhone-de-Joao", "Workstation-Office") no tráfego de rede.

## 3. Distributed Cracking (Ataque de Força Bruta Otimizado)
Integração com o `hashcat` avançado:
*   Uso de máscaras de senha baseadas em padrões locais (ex: datas, números de telefone de Cabo Verde).
*   **API Upload:** Opção para enviar o hash capturado para um servidor remoto (ex: WPA-SEC) via API caso o processamento local demore.

## 4. Visual Topology Mapping
O Radar Tático será atualizado com um mapa visual:
*   Visualização de quem está conectado a qual roteador.
*   Indicador de "Nível de Vulnerabilidade" colorido por AP.
*   Gráfico de "Signal Strength" em tempo real para ajudar no posicionamento físico do adaptador.

## 5. Evil Twin Expert (Bypass de Segurança)
*   **HSTS Stripping:** Tentativa de downgrade de HTTPS para HTTP para capturar credenciais.
*   **DNS Redirection:** Servidor DNS interno que redireciona qualquer domínio comum para o captive portal.

---
**Próximo Passo:** Iniciar a implementação do "Orquestrador de Vetores" no backend.
