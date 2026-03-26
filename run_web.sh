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

# Instala a dependência do Flask Web Server (se não existir)
echo -e "${YELLOW}[*] Verificando motor Web (Flask)...${NC}"
python3 -c "import flask" 2>/dev/null || (echo -e "${GREEN}[+] Baixando servidor Web Flask...${NC}" && apt update && apt install -y python3-flask)

# Mata qualquer processo airodump antigo que tenha ficado zumbi
killall airodump-ng 2>/dev/null

clear
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}       [ DSI CYBERPUNK WEB AUDITOR ]             ${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "${YELLOW}1. O Servidor Local (C2) será iniciado agora.${NC}"
echo -e "${YELLOW}2. Mantenha esta janela preta ABERTA.${NC}"
echo -e "${YELLOW}3. Vá até o seu Navegador (Firefox/Chrome) e acesse:${NC}"
echo -e "${GREEN}       http://localhost:5000                     ${NC}"
echo -e "${GREEN}=================================================${NC}"

# Abre o navegador automaticamente (Funciona na maioria das distros Desktop)
(sleep 2 && xdg-open "http://localhost:5000" 2>/dev/null || sensible-browser "http://localhost:5000" 2>/dev/null) &

# Lança a aplicação web controladora
exec python3 web_auditor.py
