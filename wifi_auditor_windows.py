import os
import time
import subprocess
import json
import ctypes
from datetime import datetime

# =========================================================================
# DSI SUPREME C2 - TERMINAL WINDOWS EDITION
# Adaptação para arquitetura Windows (Sem suporte nativo a injeção NDIS)
# =========================================================================

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich import print as rprint
except ImportError:
    print("[!] O pacote 'rich' não foi encontrado. Instale com: pip install rich")
    exit(1)

console = Console()

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def print_banner():
    banner = """
[bold cyan]██████╗ ███████╗██╗    ██╗    ██╗██╗███╗   ██╗[/bold cyan]
[bold cyan]██╔══██╗██╔════╝██║    ██║    ██║██║████╗  ██║[/bold cyan]
[bold blue]██║  ██║███████╗██║    ██║ █╗ ██║██║██╔██╗ ██║[/bold blue]
[bold blue]██║  ██║╚════██║██║    ██║███╗██║██║██║╚██╗██║[/bold blue]
[bold magenta]██████╔╝███████║██║    ╚███╔███╔╝██║██║ ╚████║[/bold magenta]
[bold magenta]╚═════╝ ╚══════╝╚═╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝[/bold magenta]
[bold white]       W I N D O W S   S U P R E M E          [/bold white]
    """
    console.print(Panel(banner, title="[bold red]DSI C2 ONLINE[/bold red]", border_style="cyan", padding=(1, 2)))

def scan_networks_windows():
    console.print("\n[bold yellow][MAPA DE ESPECTRO] Varrendo redes com API NDIS (Windows)...[/bold yellow]")
    try:
        # Tenta forçar refresh desabilitando/habilitando (pode falhar se nome for diferente)
        subprocess.run(["netsh", "interface", "set", "interface", "name=\"Wi-Fi\"", "admin=disable"], capture_output=True)
        time.sleep(1)
        subprocess.run(["netsh", "interface", "set", "interface", "name=\"Wi-Fi\"", "admin=enable"], capture_output=True)
        time.sleep(4)
        
        result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], capture_output=True, text=True, encoding='cp850', errors='ignore')
        
        networks = []
        current_net = {}
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                if current_net and 'bssid' in current_net: networks.append(current_net)
                current_net = {}
                parts = line.split(":", 1)
                if len(parts) > 1: current_net['essid'] = parts[1].strip()
            elif "Autentica" in line or "Authentication" in line:
                current_net['privacy'] = line.split(":", 1)[1].strip()
            elif "BSSID" in line:
                current_net['bssid'] = line.split(":", 1)[1].strip()
            elif "Sinal" in line or "Signal" in line:
                val = line.split(":", 1)[1].strip()
                current_net['signal'] = val
            elif "Canal" in line or "Channel" in line:
                current_net['channel'] = line.split(":", 1)[1].strip()
        
        if current_net and 'bssid' in current_net: networks.append(current_net)
        
        if not networks:
            console.print("[bold red]Nenhuma rede detectada.[/bold red]")
            return
            
        table = Table(title="[bold green]ALVOS MÚLTIPLOS DETECTADOS[/bold green]", show_lines=True)
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("ESSID", style="bold white")
        table.add_column("BSSID", style="magenta")
        table.add_column("Sinal", justify="center", style="yellow")
        
        for i, net in enumerate(networks):
            table.add_row(str(i+1), net.get('essid', 'N/A'), net.get('bssid', 'N/A'), net.get('signal', 'N/A'))
        
        console.print(table)
        console.print("\n[bold red][!] NOTA DE LIMITAÇÃO (OS WINDOWS):[/bold red]")
        console.print("Ataques ativos como Deauth, MDK4 ou PMKID não podem ser executados neste terminal")
        console.print("pois a Microsoft bloqueia injeção de pacotes brutos nas placas de rede padrão.")
        console.print("Utilize o painel Web (`run_web_windows.bat`) para ataques de Evil Twin, ou rode o C2 em Linux.")

    except Exception as e:
        console.print(f"[bold red]Erro ao invocar API do Windows: {e}[/bold red]")

def crack_offline_windows():
    console.print(Panel("[bold yellow]MÓDULO DE CRACKING (FORÇA BRUTA OFFLINE)[/bold yellow]"))
    console.print("Utilizando CPU/GPU local para quebrar arquivos .cap ou .16800 capturados anteriormente.")
    
    cap = Prompt.ask("\n[bold cyan]Caminho do Arquivo (Ex: C:\\captures\\alvo.cap)[/bold cyan]")
    if not os.path.exists(cap):
        console.print("[bold red]Arquivo não encontrado.[/bold red]")
        return
        
    wordlist = Prompt.ask("[bold cyan]Caminho da Wordlist (Ex: C:\\wordlists\\rockyou.txt)[/bold cyan]")
    if not os.path.exists(wordlist):
        console.print("[bold red]Wordlist não encontrada.[/bold red]")
        return
        
    console.print("\n[bold green]Iniciando Hashcat/Aircrack-ng... (Requer binários no PATH do Windows)[/bold green]")
    try:
        # Se for pmkid
        if cap.endswith(".16800"):
            subprocess.run(f"hashcat -m 16800 -a 0 \"{cap}\" \"{wordlist}\"", shell=True)
        else:
            subprocess.run(f"aircrack-ng -w \"{wordlist}\" \"{cap}\"", shell=True)
    except Exception as e:
        console.print(f"[bold red]Erro de execução: {e}[/bold red]")

def main():
    if not is_admin():
         console.print("[bold yellow][!] AVISO: Executando sem privilégios de Administrador. Alguns recursos falharão.[/bold yellow]\n")

    while True:
        os.system("cls")
        print_banner()
        console.print("\n[bold cyan]1.[/bold cyan] [white]Mapeamento de Redes (Radar Passivo API)[/white]")
        console.print("[bold cyan]2.[/bold cyan] [white]Módulo de Força Bruta Offline (Crack .cap/.16800)[/white]")
        console.print("[bold cyan]3.[/bold cyan] [white]Inicie o C2 Web (`run_web_windows.bat`) para interface completa[/white]")
        console.print("[bold cyan]4.[/bold cyan] [white]Sair[/white]")
        
        opcao = Prompt.ask("\n[bold green]Ação[/bold green]", choices=["1", "2", "3", "4"])
        
        if opcao == '4': return
        elif opcao == '3':
            console.print("\n[bold green]Feche este terminal e execute o arquivo `run_web_windows.bat` na pasta.[/bold green]")
            Prompt.ask("\nPressione ENTER para voltar...")
        elif opcao == '1':
            scan_networks_windows()
            Prompt.ask("\n[bold cyan]Pressione ENTER para voltar ao menu...[/bold cyan]")
        elif opcao == '2':
            crack_offline_windows()
            Prompt.ask("\n[bold cyan]Pressione ENTER para voltar ao menu...[/bold cyan]")

if __name__ == "__main__":
    main()
