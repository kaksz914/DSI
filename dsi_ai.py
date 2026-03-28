import json
import os
from datetime import datetime

class DSIAI:
    def __init__(self):
        self.brain_file = "dsi_brain.json"
        self.memory = self.load_memory()
        self.attack_vectors = ['pmkid', 'handshake', 'vetorx', 'wps', 'ghost']
        self.default_params = {
            'pmkid': {'timeout': 60, 'intensity': 15},
            'handshake': {'deauth_count': 10, 'timeout': 30, 'tool': 'aireplay'},
            'vetorx': {'timeout': 120, 'intensity': 31},
            'wps': {'timeout': 300},
            'ghost': {'timeout': 60}
        }

    def load_memory(self):
        if os.path.exists(self.brain_file):
            with open(self.brain_file, 'r') as f:
                try: return json.load(f)
                except: return {}
        return {}

    def save_memory(self):
        with open(self.brain_file, 'w') as f: json.dump(self.memory, f, indent=4)

    def learn(self, bssid, essid, attack_type, success, params=None, details=""):
        if bssid not in self.memory:
            self.memory[bssid] = {"essid": essid, "history": [], "best_vector": None, "resistance_score": 0, "failed_vectors": []}
        mem = self.memory[bssid]
        entry = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "attack": attack_type, "success": success, "params": params, "details": details}
        mem["history"].append(entry)
        if success:
            mem["best_vector"] = attack_type
            mem["resistance_score"] = 0
            if attack_type in mem["failed_vectors"]: mem["failed_vectors"].remove(attack_type)
        else:
            mem["resistance_score"] += 1
            # Se falhou 3 vezes seguidas no mesmo ataque, marca como falho
            recent_fails = [h for h in mem["history"][-3:] if h['attack'] == attack_type and not h['success']]
            if len(recent_fails) >= 3 and attack_type not in mem["failed_vectors"]:
                mem["failed_vectors"].append(attack_type)
        self.save_memory()

    def get_strategy(self, bssid):
        if bssid in self.memory:
            mem = self.memory[bssid]
            if mem["best_vector"]: return f"IA: Vetor {mem['best_vector'].upper()} é a chave do sucesso."
            if mem["resistance_score"] > 10: return "IA: Resistência Crítica. Recomendado: EVIL TWIN imediato."
        return "IA: Calculando vetores de penetração..."

    def suggest_next_attack(self, bssid, hw_injection_ok=True):
        if bssid not in self.memory: self.memory[bssid] = {"essid": "Unknown", "history": [], "best_vector": None, "resistance_score": 0, "failed_vectors": []}
        mem = self.memory[bssid]
        
        if mem["best_vector"] and (hw_injection_ok or mem["best_vector"] in ['pmkid', 'wps']):
            return mem["best_vector"], self.default_params[mem["best_vector"]]

        available = ['pmkid', 'wps']
        if hw_injection_ok: available += ['handshake', 'vetorx', 'ghost']
        
        # Filtra ataques que não falharam 3 vezes seguidas
        untried = [v for v in available if v not in mem["failed_vectors"]]
        
        if not untried:
            # Todos os ataques de rádio falharam. Força EVIL TWIN ou reseta com agressividade máx.
            if mem["resistance_score"] > 20: return "eviltwin", {}
            untried = available # Reseta para tentar de novo com timeouts maiores
            
        attack = untried[0]
        params = self.default_params[attack].copy()
        # Escalonamento: +20s de timeout a cada 2 falhas totais no alvo
        bonus = (mem["resistance_score"] // 2) * 20
        if 'timeout' in params: params['timeout'] += bonus
        
        return attack, params
