#!/bin/bash
# Script de Restauração Expert do Adaptador Wi-Fi 6
# Use este script se o adaptador parar de funcionar após atualizar o Kali.

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}[*] Iniciando restauração do adaptador Wi-Fi 6...${NC}"

# Caminho da fonte patcheada
SRC_DIR="/home/kalibox/Documents/aic8800-driver-source/aic8800_linux_drvier/drivers/aic8800"

if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}[X] Erro: Fontes do driver não encontradas em $SRC_DIR${NC}"
    exit 1
fi

# Instala headers do kernel atual
echo -e "${YELLOW}[*] Sincronizando headers do kernel...${NC}"
sudo apt update && sudo apt install -y linux-headers-$(uname -r) build-essential dkms bc

# Compila e instala loader de firmware
echo -e "${YELLOW}[*] Compilando Loader de Firmware...${NC}"
cd $SRC_DIR/aic_load_fw
make clean
make -j$(nproc)
sudo make install

# Compila e instala driver principal
echo -e "${YELLOW}[*] Compilando Driver Principal (FDRV)...${NC}"
cd $SRC_DIR/aic8800_fdrv
make clean
make -j$(nproc) KBUILD_EXTRA_SYMBOLS=$SRC_DIR/aic_load_fw/Module.symvers
sudo make install

# Recarrega módulos
echo -e "${YELLOW}[*] Reiniciando drivers...${NC}"
sudo modprobe -r aic8800_fdrv 2>/dev/null
sudo modprobe -r aic_load_fw 2>/dev/null
sudo modprobe aic_load_fw
sudo modprobe aic8800_fdrv

echo -e "${GREEN}[+] SUCESSO! O adaptador Wi-Fi 6 deve estar funcional novamente.${NC}"
echo -e "${GREEN}[+] Verifique com o comando: iw dev${NC}"
