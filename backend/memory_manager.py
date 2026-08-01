import json
import os

class JarvisMemory:
    def __init__(self, filepath="memory.json", max_history=10):
        self.filepath = filepath
        self.max_history = max_history
        self.memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao ler memória ({e}), iniciando vazio.")
        return []

    def _save_memory(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar memória: {e}")

    def add_message(self, role: str, content: str):
        if not content:
            return
            
        self.memory.append({"role": role, "content": content})
        
        # Mantém apenas o limite máximo estipulado (evita alto custo de tokens)
        if len(self.memory) > self.max_history:
            self.memory = self.memory[-self.max_history:]
            
        self._save_memory()

    def get_context(self):
        return self.memory

    def clear_memory(self):
        self.memory = []
        self._save_memory()
        print("🧠 [Memory Manager] Memória resetada com sucesso.")

# Singleton para ser importado globalmente
memory = JarvisMemory()
