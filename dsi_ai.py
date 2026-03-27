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
        """ Registra o resultado para treinar o sistema """
        if bssid not in self.memory:
            self.memory[bssid] = {
                "essid": essid,
                "history": [],
                "best_vector": None,
                "resistance_score": 0
            }
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attack": attack_type,
            "success": success,
            "details": details
        }
        
        self.memory[bssid]["history"].append(entry)
        
        # Lógica de "Treinamento": Define o melhor vetor baseado no sucesso
        if success:
            self.memory[bssid]["best_vector"] = attack_type
            self.memory[bssid]["resistance_score"] = max(0, self.memory[bssid]["resistance_score"] - 1)
        else:
            self.memory[bssid]["resistance_score"] += 1
            
        self.save_memory()

    def get_strategy(self, bssid):
        """ Retorna a melhor estratégia baseada no aprendizado anterior """
        if bssid in self.memory:
            mem = self.memory[bssid]
            if mem["best_vector"]:
                return f"ESTRATÉGIA APRENDIDA: Use {mem['best_vector']} (Eficiência Comprovada)."
            if mem["resistance_score"] > 3:
                return "ESTRATÉGIA IA: Alvo altamente resistente a ataques de rádio. Use EVIL TWIN."
        return "IA: Alvo novo. Recomendado iniciar pelo VETOR X."
