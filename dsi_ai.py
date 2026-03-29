import json
import os
from datetime import datetime

class DSIAI:
    def __init__(self):
        self.brain_file = "dsi_brain.json"
        self.memory = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.brain_file):
            with open(self.brain_file, 'r') as f:
                try: return json.load(f)
                except: return {}
        return {}

    def save_memory(self):
        with open(self.brain_file, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def learn(self, bssid, essid, attack_type, success, details=""):
        if bssid not in self.memory:
            self.memory[bssid] = {"essid": essid, "history": [], "best_vector": None, "resistance": 0, "failed_vectors": []}
        
        mem = self.memory[bssid]
        entry = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "attack": attack_type, "success": success}
        mem["history"].append(entry)
        
        if success:
            mem["best_vector"] = attack_type
            mem["resistance"] = 0
            if attack_type in mem["failed_vectors"]: mem["failed_vectors"].remove(attack_type)
        else:
            mem["resistance"] += 1
            if attack_type not in mem["failed_vectors"]:
                mem["failed_vectors"].append(attack_type)
        
        self.save_memory()

    def get_strategy(self, bssid, hw_ok):
        if bssid in self.memory:
            mem = self.memory[bssid]
            if mem["best_vector"]: return f"IA: Vetor {mem['best_vector'].upper()} é a chave."
            if mem["resistance"] > 5 and not hw_ok:
                return "IA: Resistência Crítica + Hardware Limitado. A única chance é o EVIL TWIN."
        return "IA: Calculando vetores..."

    def suggest_next_attack(self, bssid, hw_injection_ok=True, target=None):
        if bssid not in self.memory:
            self.memory[bssid] = {"essid": "Unknown", "history": [], "best_vector": None, "resistance": 0, "failed_vectors": []}
        mem = self.memory[bssid]
        
        if mem["best_vector"] and (hw_injection_ok or mem["best_vector"] in ['pmkid', 'wps', 'pmkid_v6']):
            return mem["best_vector"], {}

        available = ['pmkid', 'wps']
        if hw_injection_ok: available += ['vetorx', 'handshake', 'ghost']
        
        # Prioriza PMKID para Wi-Fi 6
        if target and target.get('wifi6', False):
            available = ['pmkid_v6'] + available
            
        # Filtra vetores que já falharam
        untried = [v for v in available if v not in mem["failed_vectors"]]
        
        if not untried:
            # Se tudo falhou, a IA entra em modo desespero
            if hw_injection_ok:
                return "handshake", {'tool': 'mdk4_michael'} # Ataque mais forte
            else:
                return "eviltwin", {} # Única opção se passivos falharam

        attack_to_try = untried[0]
        params = {}
        if attack_to_try == 'pmkid':
            params['timeout'] = 60 + (mem['resistance'] * 10) # Aumenta tempo de escuta
            
        return attack_to_try, params
