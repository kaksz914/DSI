import subprocess
import os
import time
import json
import re
from datetime import datetime
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def show_manual():
    print("\n" + "="*60)
    print("      MANUAL DE INSTRUÇÕES (EXPERT) - VERSÃO WINDOWS")
    print("="*60)
    print("Aviso Crítico do Expert:")
    print("A auditoria Wi-Fi no Windows sofre severas limitações em comparação ao Linux.")
    print("A API nativa do Windows e os drivers das placas de rede comerciais raramente")
    print("permitem injeção de pacotes (necessária para Deauth Attack).")
    print("\nO que esta versão Windows FAZ:")
    print("- Mapeamento Passivo (Reconhecimento) usando a API nativa ('netsh wlan').")
    print("- Registro de redes e RSSI (Força do Sinal) em JSON permanente.")
    print("- Execução do 'aircrack-ng' offline (caso você tenha arquivos .cap gerados em outro lugar).")
    print("\nO que esta versão Windows NÃO FAZ (Limitações do S.O.):")
    print("- Não captura handshakes ativamente pelo ar sem hardware especial (como as placas Airpcap da Riverbed).")
    print("- Não realiza ataques PMKID nativamente.")
    print("\nPara a experiência completa de captura, use a versão Linux em um ambiente Live USB ou Máquina Virtual com placa Wi-Fi externa USB conectada.")
    print("="*60 + "\n")
    input("Pressione ENTER para voltar ao menu principal...")

def save_networks_log(networks):
    log_file = "redes_identificadas_windows_log.json"
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
                      if not isinstance(todas_sessoes, list):
                          todas_sessoes = [todas_sessoes]
                  except json.JSONDecodeError:
                      pass
                      
        todas_sessoes.append(data)
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(todas_sessoes, f, indent=4, ensure_ascii=False)
            
        print(f"\n[Registro] Informações de {len(networks)} redes salvas em: {log_file}")
    except Exception as e:
        print(f"\n[Erro] Falha ao salvar o log de redes: {e}")

def get_wifi_interfaces():
    print("\nProcurando interfaces Wi-Fi via 'netsh'...")
    try:
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, check=True)
        # Processamento simples para pegar o nome da interface no output do Windows
        interfaces = []
        for line in result.stdout.split('\n'):
            if "Nome" in line or "Name" in line:
                nome = line.split(":")[1].strip()
                interfaces.append(nome)
        
        if interfaces:
             print("\nInterfaces encontradas:")
             for i, iface in enumerate(interfaces):
                 print(f"{i+1}. {iface}")
             return interfaces
        else:
             print("Nenhuma interface Wi-Fi detectada pelo netsh.")
             return None
             
    except Exception as e:
        print(f"Erro ao acessar interfaces: {e}")
        return None

def scan_networks_windows():
    print("\n[Mapeamento] Executando varredura passiva no ambiente...")
    # Força a atualização da lista de redes do Windows (pode exigir direitos de admin para algumas placas)
    subprocess.run(["netsh", "interface", "set", "interface", "name=\"Wi-Fi\"", "admin=disable"], capture_output=True)
    time.sleep(1)
    subprocess.run(["netsh", "interface", "set", "interface", "name=\"Wi-Fi\"", "admin=enable"], capture_output=True)
    print("Aguardando estabilização do sinal... (5s)")
    time.sleep(5)
    
    try:
        # Comando para listar as redes visíveis com BSSID
        result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], capture_output=True, text=True, check=True, encoding='cp850', errors='ignore')
        
        networks = []
        current_network = {}
        
        # Parse rudimentar do output do netsh wlan do Windows
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                if current_network and 'bssid' in current_network:
                    networks.append(current_network)
                current_network = {}
                parts = line.split(":", 1)
                if len(parts) > 1:
                     current_network['essid'] = parts[1].strip()
            elif "Autentica" in line or "Authentication" in line:
                current_network['privacy'] = line.split(":", 1)[1].strip()
            elif "BSSID" in line:
                current_network['bssid'] = line.split(":", 1)[1].strip()
            elif "Sinal" in line or "Signal" in line:
                current_network['signal'] = line.split(":", 1)[1].strip()
            elif "Canal" in line or "Channel" in line:
                current_network['channel'] = line.split(":", 1)[1].strip()
                
        if current_network and 'bssid' in current_network:
             networks.append(current_network)
             
        if not networks:
            print("Nenhuma rede encontrada na varredura.")
            return None
            
        save_networks_log(networks)
        
        print("\nRedes Identificadas:")
        print(f"{'#':<3} {'ESSID':<20} {'BSSID':<20} {'CANAL':<6} {'SINAL':<6}")
        print("-" * 60)
        for i, net in enumerate(networks):
            essid = net.get('essid', 'Oculta')
            bssid = net.get('bssid', 'N/A')
            canal = net.get('channel', 'N/A')
            sinal = net.get('signal', 'N/A')
            print(f"{i + 1:<3} {essid:<20} {bssid:<20} {canal:<6} {sinal:<6}")
            
        return networks

    except Exception as e:
        print(f"Erro durante varredura: {e}")
        return None

def crack_offline_windows():
    print("\n[Expert Offline Cracker] Módulo de quebra de senhas.")
    print("Este módulo usa o aircrack-ng/hashcat (se instalados e no PATH do Windows).")
    print("Ele processa arquivos de captura (.cap/.pcapng/.16800) gerados em outras plataformas.\n")
    
    capture_file = input("Caminho do arquivo de captura (ex: C:\\arquivos\\handshake.cap): ").strip('\"')
    
    if not os.path.exists(capture_file):
        print("Arquivo de captura não encontrado.")
        return
        
    wordlist_file = input("Caminho do arquivo de dicionário (ex: C:\\arquivos\\rockyou.txt): ").strip('\"')
    
    if not os.path.exists(wordlist_file):
        print("Arquivo de dicionário não encontrado.")
        return
        
    print("\nExecutando Aircrack-ng (Certifique-se de ter instalado os binários do Windows).")
    try:
         # Tenta chamar o aircrack-ng no Windows
         crack_cmd = f"aircrack-ng -w \"{wordlist_file}\" \"{capture_file}\""
         subprocess.run(crack_cmd, shell=True)
    except Exception as e:
         print(f"Erro ao tentar rodar aircrack-ng: {e}")
         print("Você tem os binários do aircrack-ng para Windows instalados e nas variáveis de ambiente PATH?")

def main():
    if not is_admin():
         print("[!] AVISO: Executando sem privilégios de Administrador.")
         print("Algumas requisições de rede podem ser negadas. É recomendado executar o Prompt de Comando como Administrador.\n")

    while True:
        print("\n" + "=" * 50)
        print("  Auditoria Wi-Fi Automatizada (Windows Edition)")
        print("  AVISO: Funcionalidade reduzida devido à arquitetura NDIS do Windows.")
        print("=" * 50)
        print("1. Escanear Redes Próximas (Reconhecimento Passivo)")
        print("2. Quebrar Senha Offline (Requer arquivo .cap)")
        print("3. Ler Manual e Limitações do Windows")
        print("4. Sair")
        
        opcao = input("\nEscolha uma opção (1-4): ")
        
        if opcao == '3':
            show_manual()
            continue
        elif opcao == '4':
            print("Saindo da ferramenta. Até logo!")
            return
        elif opcao == '1':
            scan_networks_windows()
            input("\nPressione ENTER para voltar ao menu...")
        elif opcao == '2':
            crack_offline_windows()
            input("\nPressione ENTER para voltar ao menu...")
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
