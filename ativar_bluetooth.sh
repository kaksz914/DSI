#!/bin/bash
# DSI Comando: Ativar Bluetooth

echo "[*] Removendo máscara do serviço Bluetooth..."
systemctl unmask bluetooth

echo "[*] Habilitando auto-start do serviço..."
systemctl enable bluetooth

echo "[*] Iniciando serviço Bluetooth..."
systemctl start bluetooth

echo "[*] Desbloqueando a nivel de Kernel (RFKILL)..."
rfkill unblock bluetooth

echo "[+] SUCESSO! O Bluetooth da maquina foi ATIVADO novamente."
