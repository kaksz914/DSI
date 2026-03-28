import scapy.all as scapy
import threading
import time
from collections import Counter

# ==============================================================
# DSI DEFENDER - ESCUDO MAGISTRADO (WIDS - Intrusion Detection)
# ==============================================================

class DSIDefender:
    def __init__(self, interface, log_callback=None):
        self.interface = interface
        self.log_callback = log_callback
        self.is_running = False
        self.deauth_threshold = 15 # Pacotes por segundo para disparar alerta
        self.packet_counts = Counter()
        self.last_check = time.time()
        
        # Histórico de SSIDs conhecidos para detectar Clones (Evil Twin)
        self.known_ssids = {}

    def log(self, msg, log_type="error"):
        if self.log_callback:
            self.log_callback(f"[ESCUDO] {msg}", log_type)
        else:
            print(f"[SHIELD] {msg}")

    def process_packet(self, packet):
        # 1. Detecção de Deauth Flooding (Ataque de Derrubada)
        if packet.haslayer(scapy.Dot11Deauth):
            addr1 = packet.addr1 # Destino (Vítima)
            addr2 = packet.addr2 # Origem (Atacante ou Roteador legítimo sendo forjado)
            self.packet_counts[f"deauth_{addr2}"] += 1
            
            now = time.time()
            if now - self.last_check > 1:
                for src, count in self.packet_counts.items():
                    if count > self.deauth_threshold:
                        self.log(f"ALERTA: Ataque de Derrubada (Deauth Flood) vindo de {src.split('_')[1]}!", log_type="error")
                self.packet_counts.clear()
                self.last_check = now

        # 2. Detecção de Evil Twin (Gêmeo Maligno)
        # Se virmos o mesmo SSID em um canal diferente ou com sinal muito diferente
        if packet.haslayer(scapy.Dot11Beacon):
            ssid = packet[scapy.Dot11Elt].info.decode(errors='ignore')
            bssid = packet.addr3
            if ssid:
                if ssid in self.known_ssids and self.known_ssids[ssid] != bssid:
                    self.log(f"ALERTA: Possível Rede Gêmea (Evil Twin) detectada para o nome '{ssid}'! BSSID Falso: {bssid}", log_type="error")
                self.known_ssids[ssid] = bssid

        # 3. Detecção de ARP Spoofing (MITM)
        if packet.haslayer(scapy.ARP) and packet.op == 2:
            try:
                real_mac = scapy.getmacbyip(packet.psrc)
                if real_mac and real_mac != packet.hwsrc:
                    self.log(f"ALERTA: Intercepção de Rede (ARP Spoofing) detectada! O IP {packet.psrc} está sendo sequestrado por {packet.hwsrc}", log_type="error")
            except: pass

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.log("Escudo Magistrado Ativado. Monitorando ameaças...", log_type="cmd")
            threading.Thread(target=self._run_defender, daemon=True).start()

    def _run_defender(self):
        try:
            scapy.sniff(iface=self.interface, store=False, prn=self.process_packet, stop_filter=self._stop_check)
        except Exception as e:
            self.log(f"Erro no Escudo: {e}", log_type="error")
            self.is_running = False

    def _stop_check(self, packet):
        return not self.is_running

    def stop(self):
        self.is_running = False
        self.log("Escudo Magistrado desativado.", log_type="info")
