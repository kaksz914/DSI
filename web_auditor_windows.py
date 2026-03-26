import os
import time
import subprocess
import threading
from flask import Flask, render_template, request, jsonify
from datetime import datetime

# =========================================================================
# BACKEND WEB - VERSÃO WINDOWS (Limitações de API Nativa do NDIS)
# =========================================================================

app = Flask(__name__)

CURRENT_MONITOR_IFACE = None
SCAN_THREAD = None
SCAN_ACTIVE = False
NETWORKS_CACHE = []

def scan_networks_windows_loop():
    global SCAN_ACTIVE, NETWORKS_CACHE
    while SCAN_ACTIVE:
        try:
            # Comando passivo no Windows
            result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], capture_output=True, text=True, check=True, encoding='cp850', errors='ignore')
            
            networks = []
            current_network = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith("SSID"):
                    if current_network and 'bssid' in current_network:
                        networks.append(current_network)
                    current_network = {}
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                         current_network['essid'] = parts[1].strip()
                elif "Autentica" in line or "Authentication" in line:
                    current_network['privacy'] = line.split(":", 1)[1].strip()
                elif "BSSID" in line:
                    current_network['bssid'] = line.split(":", 1)[1].strip()
                elif "Sinal" in line or "Signal" in line:
                    val = line.split(":", 1)[1].strip()
                    # Converte % de sinal para dBm aproximado para a UI do radar
                    try:
                        perc = int(val.replace("%", ""))
                        current_network['signal'] = str((perc / 2) - 100)
                    except:
                        current_network['signal'] = "-90"
                elif "Canal" in line or "Channel" in line:
                    current_network['channel'] = line.split(":", 1)[1].strip()
                    
            if current_network and 'bssid' in current_network:
                 networks.append(current_network)
                 
            NETWORKS_CACHE = networks
        except Exception as e:
            print(f"Erro na thread de scan: {e}")
        
        time.sleep(4) # Refresh a cada 4 segundos no Windows para não travar a UI nativa

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    try:
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, check=True)
        interfaces = []
        for line in result.stdout.split('\n'):
            if "Nome" in line or "Name" in line:
                nome = line.split(":")[1].strip()
                interfaces.append(nome)
        return jsonify({"status": "success", "interfaces": interfaces, "os_type": "windows"})
    except:
        return jsonify({"status": "error", "message": "Falha ao listar interfaces Wi-Fi no Windows.", "os_type": "windows"})

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    data = request.get_json()
    iface = data.get('interface')
    global CURRENT_MONITOR_IFACE
    CURRENT_MONITOR_IFACE = iface
    # No Windows, modo monitor de injeção é negado pela Microsoft em drivers normais
    return jsonify({"status": "success", "monitor_interface": iface + " (Modo Passivo WinAPI)"})

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_ACTIVE, SCAN_THREAD
    if not SCAN_ACTIVE:
        SCAN_ACTIVE = True
        SCAN_THREAD = threading.Thread(target=scan_networks_windows_loop, daemon=True)
        SCAN_THREAD.start()
    return jsonify({"status": "success", "message": "Radar Passivo do Windows ligado."})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_ACTIVE
    SCAN_ACTIVE = False
    return jsonify({"status": "success", "message": "Radar desligado."})

@app.route('/api/get_networks', methods=['GET'])
def get_networks():
    global NETWORKS_CACHE
    # Ordena pelo sinal (convertido pra numérico negativo)
    sorted_nets = sorted(NETWORKS_CACHE, key=lambda x: float(x.get('signal', -100)), reverse=True)
    return jsonify({"status": "success", "networks": sorted_nets})

@app.route('/api/attack', methods=['POST'])
def launch_attack():
    # O Windows não permite injeção de pacotes Deauth sem placas caras como a Riverbed Airpcap.
    return jsonify({
        "status": "error", 
        "message": "ATAQUE BLOQUEADO PELA ARQUITETURA WINDOWS: A injeção de pacotes (Deauth/PMKID) é restrita pelo Kernel do Windows (NDIS). Para ejetar clientes ou capturar handshakes ativamente, inicialize a versão Linux (C2 Server) deste painel em uma máquina virtual ou Live USB."
    })

@app.route('/api/restore', methods=['POST'])
def restore():
    global SCAN_ACTIVE
    SCAN_ACTIVE = False
    return jsonify({"status": "success", "message": "Rede local pronta. Limpeza concluída (Windows Mode)."})

if __name__ == '__main__':
    print("\n" + "="*50)
    print(" >>> C2 SERVER (WINDOWS BACKEND) ONLINE <<< ")
    print(" 1. Abra o navegador web.")
    print(" 2. Acesse: http://localhost:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
