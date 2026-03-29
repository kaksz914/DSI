#!/bin/bash
# ==============================================================
# DSI AETHER v5.0 - LANÇADOR AUTOMATIZADO (MASTER)
# Codinome: Magistrado Negro
# ==============================================================

# Cores para o Terminal Moderno
VERMELHO='\033[0;31m'
VERDE='\033[0;32m'
CIANO='\033[0;36m'
MAGENTA='\033[0;35m'
AMARELO='\033[1;33m'
RESET='\033[0m'

clear
echo -e "${MAGENTA}"
echo "    ██████╗ ███████╗██╗     █████╗ ███████╗████████╗██╗  ██╗███████╗██████╗ "
echo "    ██╔══██╗██╔════╝██║    ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗"
echo "    ██║  ██║███████╗██║    ███████║█████╗     ██║   ███████║█████╗  ██████╔╝"
echo "    ██║  ██║╚════██║██║    ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗"
echo "    ██████╔╝███████║██║    ██║  ██║███████╗    ██║   ██║  ██║███████╗██║  ██║"
echo "    ╚═════╝ ╚══════╝╚═╝    ╚═╝  ╚═╝╚══════╝    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝"
echo -e "                   [ MAGISTRADO NEGRO - VERSÃO 5.0 AETHER ]${RESET}"
echo "--------------------------------------------------------------------------------"

# 1. Verificação de Privilégios
if [ "$EUID" -ne 0 ]; then
  echo -e "${VERMELHO}[!] ERRO CRÍTICO: Este sistema exige acesso ROOT (sudo).${RESET}"
  exit 1
fi

# 2. Higienização do Ambiente
echo -e "${CIANO}[*] Higienizando processos conflitantes...${RESET}"
airmon-ng check kill > /dev/null 2>&1
killall -9 airodump-ng aircrack-ng mdk4 reaver python3 > /dev/null 2>&1

# 3. Verificação de Dependências (Inteligente)
echo -e "${CIANO}[*] Validando arsenal de dependências...${RESET}"
DEPS=("python3" "pip3" "aircrack-ng" "hcxdumptool" "macchanger" "nmcli")
for dep in "${DEPS[@]}"; do
    if ! command -v $dep &> /dev/null; then
        echo -e "${AMARELO}[!] Instalando: $dep...${RESET}"
        apt update && apt install -y $dep
    fi
done

# Instalação das bibliotecas Python necessárias
pip3 install flask rich numpy --quiet

# 4. Configuração de Caminhos
export PYTHONPATH=$PYTHONPATH:$(pwd)/dsi_v5_aether/core
mkdir -p dsi_v5_aether/data dsi_v5_aether/logs dsi_v5_aether/captures

# 5. Calibração de Hardware
echo -e "${VERDE}[+] Detectando adaptadores Wi-Fi 6 / AX...${RESET}"
IFACE=$(iw dev | grep Interface | awk '{print $2}' | head -n 1)

if [ -z "$IFACE" ]; then
    echo -e "${VERMELHO}[!] Nenhuma interface Wi-Fi detectada! Verifique o hardware.${RESET}"
else
    echo -e "${VERDE}[+] Interface alvo inicial: $IFACE${RESET}"
fi

# 6. Ignição do Centro de Comando
echo "--------------------------------------------------------------------------------"
echo -e "${AMARELO}[⚡] SISTEMA PRONTO PARA OPERAÇÃO.${RESET}"
echo -e "${CIANO}[🌐] DASHBOARD WEB: http://localhost:8888${RESET}"
echo -e "${CIANO}[📟] CONSOLE LOG: dsi_v5_aether/logs/aether_core.log${RESET}"
echo "--------------------------------------------------------------------------------"
echo -e "${MAGENTA}>>> Iniciando Motor Aether...${RESET}"

# Opção de Modo Automático
if [ "$1" == "--autopwn" ]; then
    echo -e "${VERMELHO}[!] MODO AUTOPWN ATIVADO. INICIANDO SEQUÊNCIA DE COMBATE IA...${RESET}"
    python3 dsi_v5_aether/core/aether_autopwn.py $IFACE
else
    # Roda o servidor web e o núcleo simultaneamente
    python3 dsi_v5_aether/core/aether_web.py
fi
