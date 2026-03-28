import json
import os
from datetime import datetime

class DSIAI:
    def __init__(self):
        self.brain_file = "dsi_brain.json"
        self.memory = self.load_memory()
        
        # Vetores de ataque base e seus tempos recomendados
        self.attack_vectors = ['pmkid', 'handshake', 'vetorx', 'wps', 'ghost']
        self.default_params = {
            'pmkid': {'timeout': 60, 'intensity': 15}, # enable_status
            'handshake': {'deauth_count': 10, 'timeout': 30, 'tool': 'aireplay'},
            'vetorx': {'timeout': 120, 'intensity': 31}, # active_beacon, proberequest
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
        with open(self.brain_file, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def learn(self, bssid, essid, attack_type, success, params=None, details=""):
        """ Registra o resultado detalhado (com parâmetros) para treinar o sistema """
        if bssid not in self.memory:
            self.memory[bssid] = {
                "essid": essid,
                "history": [],
                "best_vector": None,
                "best_params": None,
                "resistance_score": 0,
                "failed_vectors": []
            }
        
        mem = self.memory[bssid]
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attack": attack_type,
            "success": success,
            "params": params,
            "details": details
        }
        mem["history"].append(entry)
        
        if success:
            mem["best_vector"] = attack_type
            mem["best_params"] = params
            mem["resistance_score"] = max(0, mem["resistance_score"] - 1)
            # Remove do histórico de falhas se teve sucesso agora
            if attack_type in mem["failed_vectors"]:
                mem["failed_vectors"].remove(attack_type)
        else:
            mem["resistance_score"] += 1
            if attack_type not in mem["failed_vectors"]:
                mem["failed_vectors"].append(attack_type)
            
        self.save_memory()

    def get_strategy(self, bssid):
        """ Retorna uma string descritiva da estratégia atual da IA """
        if bssid in self.memory:
            mem = self.memory[bssid]
            if mem["best_vector"]:
                return f"ESTRATÉGIA APRENDIDA: Usar {mem['best_vector'].upper()} com parâmetros ótimos."
            if mem["resistance_score"] > 3:
                return "ESTRATÉGIA IA: Alvo Altamente Resistente. Iniciando ciclo de força bruta adaptativa (Autopilot Nível Máximo)."
            if len(mem["failed_vectors"]) > 0:
                return f"ESTRATÉGIA IA: Evitando vetores falhos ({', '.join(mem['failed_vectors'])}). Ajustando abordagem."
        return "IA: Alvo novo. Iniciando rotina de descoberta de vulnerabilidades (Recomendado: Autopilot)."

    def suggest_next_attack(self, bssid, hw_injection_ok=True):
        """
        O CÉREBRO: Decide qual o próximo ataque a ser executado no modo Autopilot, 
        baseado no histórico do alvo e na capacidade do hardware.
        Retorna: (attack_type, params_dict)
        """
        # Se for um alvo novo, cria entrada vazia
        if bssid not in self.memory:
            self.memory[bssid] = {
                "essid": "Unknown", "history": [], "best_vector": None, 
                "best_params": None, "resistance_score": 0, "failed_vectors": []
            }
            
        mem = self.memory[bssid]
        
        # 1. Se já sabemos o que funciona, repete exatamente como foi
        if mem["best_vector"]:
            # Se a melhor opção exige injeção e não temos mais, ignoramos a melhor
            if mem["best_vector"] in ['handshake', 'vetorx', 'ghost'] and not hw_injection_ok:
                pass # Cai no fallback
            else:
                return mem["best_vector"], mem.get("best_params", self.default_params[mem["best_vector"]])

        # 2. Definição da ordem lógica de ataque baseada no hardware e histórico
        available_vectors = []
        if hw_injection_ok:
            available_vectors = ['pmkid', 'handshake', 'vetorx', 'wps', 'ghost']
        else:
            available_vectors = ['pmkid', 'wps'] # Apenas ataques passivos/diretos

        # Remove vetores que já falharam repetidas vezes (para não ficar preso em loop)
        # Se todos falharam, reseta a lista para tentar com parâmetros mais agressivos
        untried = [v for v in available_vectors if v not in mem["failed_vectors"]]
        
        if not untried:
            # Todos falharam. Hora de ficar AGRESSIVO.
            # Escolhe o primeiro vetor válido, mas vamos sugerir parâmetros multiplicados
            attack_to_try = available_vectors[0]
            params = self.default_params[attack_to_try].copy()
            
            # Aumenta agressividade baseado no score de resistência
            multiplier = min(3, 1 + (mem["resistance_score"] * 0.5)) 
            
            if 'timeout' in params: params['timeout'] = int(params['timeout'] * multiplier)
            if 'intensity' in params: params['intensity'] = min(255, int(params['intensity'] * multiplier))
            if 'deauth_count' in params: params['deauth_count'] = int(params['deauth_count'] * multiplier)
            
            # Muda de ferramenta se a primária falhou muito (Ex: aireplay -> mdk4)
            if attack_to_try == 'handshake' and mem["resistance_score"] > 2:
                params['tool'] = 'mdk4_deauth'
                if mem["resistance_score"] > 4: params['tool'] = 'mdk4_auth_dos'
                if mem["resistance_score"] > 6: params['tool'] = 'mdk4_michael'
                
            return attack_to_try, params
            
        else:
            # Tenta um vetor inédito para este alvo com parâmetros padrão
            attack_to_try = untried[0]
            return attack_to_try, self.default_params[attack_to_try]
