#!/bin/bash
# DSI Comando: Desativar Bluetooth Definitivamente

echo "[*] Desativando Bluetooth em nivel de Kernel (RFKILL)..."
rfkill block bluetooth

echo "[*] Parando serviço Bluetooth..."
systemctl stop bluetooth

echo "[*] Desabilitando auto-start do serviço..."
systemctl disable bluetooth

echo "[*] Mascarando o serviço (Impede que outros processos liguem o Bluetooth acidentalmente)..."
systemctl mask bluetooth

echo "[+] SUCESSO! O Bluetooth desta maquina foi DESATIVADO permanentemente."
echo "[!] Para ligar um dia, execute o arquivo: ./ativar_bluetooth.sh"
