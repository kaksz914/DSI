#!/bin/bash

# Cores para feedback visual
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[*] Inicializando Suite DSI - Auditoria Wi-Fi (Expert Mode)${NC}"
echo -e "${YELLOW}[!] Verificando privilégios de Administrador (Root)...${NC}"

# Verifica se o script está sendo rodado como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[X] Privilégios insuficientes. A placa Wi-Fi requer acesso de baixo nível (root).${NC}"
  echo -e "${GREEN}[+] Solicitando permissão para elevar privilégios automaticamente...${NC}"
  
  # Tenta relançar a si mesmo com sudo e sai da instância sem permissão
  exec sudo "$0" "$@"
fi

# A partir daqui, temos certeza que somos root
echo -e "${GREEN}[+] Privilégios Root confirmados. Acesso total ao Kernel de Rede garantido.${NC}"
echo -e "${YELLOW}[*] Carregando a ferramenta Python...${NC}"
sleep 1 # Pequeno delay cosmético para dar sensação de carregamento

echo -e "${YELLOW}[*] Preparando interface gráfica de próxima geração (Instalando dependências visuais)...${NC}"
# Garante que as bibliotecas modernas de UI de terminal estejam instaladas
python3 -c "import rich" 2>/dev/null || (echo -e "${GREEN}[+] Instalando pacote 'rich' para interface moderna...${NC}" && apt update && apt install -y python3-rich)

# Limpa a tela para a ferramenta principal brilhar
clear

# Executa a ferramenta de auditoria no mesmo processo (substitui o bash pelo python)
exec python3 wifi_auditor.py
