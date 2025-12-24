"""
Gerenciador de Redis para memória de sessão
Fase 3: Memória Contextual (RAO Nível 3)
"""
import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class RedisManager:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db,
                decode_responses=True
            )
            self.client.ping()
            self.connected = True
            print("✅ Redis conectado")
        except:
            self.connected = False
            self.client = None
            print("⚠️ Redis não disponível - usando memória local")
            self.local_memory = {}
    
    def set_session(self, session_id: str, data: Dict, ttl: int = 3600):
        """Salva dados da sessão (TTL padrão: 1 hora)"""
        if self.connected:
            self.client.setex(
                f"session:{session_id}",
                ttl,
                json.dumps(data)
            )
        else:
            self.local_memory[f"session:{session_id}"] = data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Recupera dados da sessão"""
        if self.connected:
            data = self.client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        else:
            return self.local_memory.get(f"session:{session_id}")
    
    def append_to_history(self, session_id: str, entry: Dict):
        """Adiciona entrada ao histórico da sessão"""
        key = f"history:{session_id}"
        
        if self.connected:
            self.client.rpush(key, json.dumps(entry))
            self.client.expire(key, 3600)
        else:
            if key not in self.local_memory:
                self.local_memory[key] = []
            self.local_memory[key].append(entry)
    
    def get_history(self, session_id: str, limit: int = 10) -> list:
        """Recupera histórico da sessão"""
        key = f"history:{session_id}"
        
        if self.connected:
            history = self.client.lrange(key, -limit, -1)
            return [json.loads(h) for h in history]
        else:
            return self.local_memory.get(key, [])[-limit:]
