#!/bin/bash

# --- Cores para feedback ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando Otimização e Limpeza do Sistema ===${NC}"

# 1. Limpeza de Cache de Usuário (Browsers e outros)
echo -e "${GREEN}[1/4] Limpando caches de browsers...${NC}"
rm -rf ~/.cache/google-chrome/*
rm -rf ~/.cache/mozilla/firefox/*.default-release/cache2/* 2>/dev/null
rm -rf ~/.cache/mozilla/firefox/*.default/cache2/* 2>/dev/null
rm -rf ~/.cache/thumbnails/*

# 2. Limpeza de pacotes APT (Requer Sudo)
echo -e "${GREEN}[2/4] Limpando pacotes e repositórios...${NC}"
sudo apt-get clean
sudo apt-get autoremove -y

# 3. Limpeza de Logs do Sistema (Requer Sudo)
echo -e "${GREEN}[3/4] Limpando logs antigos do systemd...${NC}"
sudo journalctl --vacuum-time=3d

# 4. Otimização de Memória (Swap)
echo -e "${GREEN}[4/4] Aplicando otimização de Swap...${NC}"
sudo sysctl -w vm.swappiness=10

echo -e "${BLUE}=== Otimização Concluída! ===${NC}"
