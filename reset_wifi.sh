#!/bin/bash
# Script de Reset Wi-Fi DSI
# Devolve a placa ao modo normal de navegação.

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[*] Restaurando sistema Wi-Fi para modo navegação...${NC}"

# 1. Pega as interfaces que estão em modo monitor
MON_INTERFACES=$(iw dev | grep Interface | awk '{print $2}')

for iface in $MON_INTERFACES; do
    echo -e "${YELLOW}[*] Resetando $iface...${NC}"
    sudo airmon-ng stop $iface 2>/dev/null
    sudo ip link set $iface down 2>/dev/null
    sudo iw dev $iface set type managed 2>/dev/null
    sudo macchanger -p $iface 2>/dev/null
    sudo ip link set $iface up 2>/dev/null
done

# 2. Reinicia serviços essenciais
echo -e "${YELLOW}[*] Reiniciando NetworkManager e WPA Supplicant...${NC}"
sudo systemctl start wpa_supplicant NetworkManager
sudo nmcli networking on

echo -e "${GREEN}[+] SUCESSO! Internet restaurada. Placa pronta para uso normal.${NC}"
