#!/bin/bash

# Cores para feedback visual
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[*] Inicializando Suite DSI - WEB AUDITOR (C2 Dashboard)${NC}"

# Verifica privilégios Root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[X] Privilégios insuficientes. A placa Wi-Fi requer acesso de baixo nível (root).${NC}"
  echo -e "${GREEN}[+] Solicitando permissão para elevar privilégios automaticamente...${NC}"
  exec sudo "$0" "$@"
fi

# Instala as dependências de sistema para o Nível Grão-Mestre Supremo
echo -e "${YELLOW}[*] Verificando Arsenal Supremo (MDK4, Reaver, Scapy, Requests, Netifaces, Hostapd, Dnsmasq)...${NC}"
dpkg -s mdk4 macchanger reaver hostapd dnsmasq python3-flask python3-rich python3-scapy python3-requests python3-netifaces >/dev/null 2>&1 || (echo -e "${GREEN}[+] Baixando componentes táticos ausentes...${NC}" && apt update && apt install -y mdk4 macchanger reaver hostapd dnsmasq python3-flask python3-rich python3-scapy python3-requests python3-netifaces)

# Garante que o IP Forwarding esteja ativado para intercepção (MITM)
echo 1 > /proc/sys/net/ipv4/ip_forward

# Mata qualquer processo airodump antigo que tenha ficado zumbi
killall airodump-ng 2>/dev/null

clear
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}       [ DSI CYBERPUNK WEB AUDITOR ]             ${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "${YELLOW}1. O Servidor Local (C2) será iniciado agora.${NC}"
echo -e "${YELLOW}2. Mantenha esta janela preta ABERTA.${NC}"
echo -e "${YELLOW}3. Vá até o seu Navegador (Firefox/Chrome) e acesse:${NC}"
echo -e "${GREEN}       http://localhost:8080                     ${NC}"
echo -e "${GREEN}=================================================${NC}"

# Tenta abrir o navegador como o usuário real (não root) para evitar erros de segurança do Chrome/Firefox
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)

# Tenta capturar DISPLAY e XAUTHORITY se não estiverem definidos (comum em sudo)
export DISPLAY=${DISPLAY:-:0}
export XAUTHORITY=${XAUTHORITY:-$USER_HOME/.Xauthority}

if [ "$REAL_USER" != "root" ]; then
    echo -e "${YELLOW}[*] Tentando lançar Dashboard no navegador como usuário $REAL_USER...${NC}"
    # Usa sudo -u para rodar o navegador como usuário, passando DISPLAY e XAUTHORITY
    (sleep 4 && sudo -u "$REAL_USER" DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" xdg-open "http://localhost:8080" 2>/dev/null || \
     sudo -u "$REAL_USER" DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" sensible-browser "http://localhost:8080" 2>/dev/null) &
else
    (sleep 4 && xdg-open "http://localhost:8080" 2>/dev/null || sensible-browser "http://localhost:8080" 2>/dev/null) &
fi

# Lança a aplicação web controladora
exec python3 web_auditor.py
