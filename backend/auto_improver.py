import os
import json
import time
import threading
import importlib.util
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "command_history.json")
OBSIDIAN_PROPOSALS_FILE = "/home/zeronight/Documentos/Minha mente/04-Tasks/Jarvis Auto Improvements.md"
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

os.makedirs(SKILLS_DIR, exist_ok=True)

class AutoImproverEngine:
    """
    Motor de Auto-Aprendizado e Auto-Melhoria Contínua do Jarvis AI.
    Analisa histórico de comandos, detecta falhas ou intenções não reconhecidas,
    e gera propostas de melhoria contínua diretamente no Obsidian do usuário.
    """

    def __init__(self):
        self.history = self._load_history()
        self.dynamic_skills = {}
        self.reload_skills()

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def log_command_execution(self, raw_command: str, intent_data: dict, success: bool, response_msg: str = ""):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "raw_command": raw_command,
            "intent": intent_data.get("intent", "unknown"),
            "confidence": intent_data.get("confidence", 0.0),
            "platform": intent_data.get("platform", ""),
            "query": intent_data.get("query", ""),
            "success": success,
            "response": response_msg
        }
        self.history.append(entry)
        self._save_history()
        self.analyze_and_generate_proposals()

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[-100:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar histórico de comandos: {e}")

    def reload_skills(self):
        """
        Carrega dinamicamente novos módulos de skills a partir do diretório backend/skills/
        """
        self.dynamic_skills.clear()
        if not os.path.exists(SKILLS_DIR):
            return

        for fname in os.listdir(SKILLS_DIR):
            if fname.endswith(".py") and not fname.startswith("_"):
                skill_name = fname[:-3]
                path = os.path.join(SKILLS_DIR, fname)
                try:
                    spec = importlib.util.spec_from_file_location(skill_name, path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "execute_skill"):
                        self.dynamic_skills[skill_name] = mod.execute_skill
                        print(f"🧩 [Auto-Improver] Skill dinâmica carregada: {skill_name}")
                except Exception as e:
                    print(f"⚠️ Erro ao carregar skill dinâmica {fname}: {e}")

    def analyze_and_generate_proposals(self):
        """
        Analisa os últimos comandos e publica propostas de melhoria no Obsidian.
        """
        if not self.history:
            return

        unhandled = [h for h in self.history if h.get("intent") == "web_search" or h.get("confidence", 1.0) < 0.85]
        failed = [h for h in self.history if not h.get("success", True)]

        content = []
        content.append("# 🧠 Jarvis AI - Propostas de Auto-Melhoria & Aprendizado\n")
        content.append(f"> **Última Atualização:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        content.append("## 📊 Diagnóstico do Sistema em Tempo Real\n")
        content.append(f"- **Total de Comandos Analisados:** {len(self.history)}")
        content.append(f"- **Comandos com Baixa Confiança/Sem Skill Dedicada:** {len(unhandled)}")
        content.append(f"- **Comandos com Falha de Execução:** {len(failed)}\n")

        content.append("## 💡 Oportunidades de Auto-Melhoria Identificadas\n")

        if unhandled:
            content.append("### 🔍 Comandos Frequentes que Precisam de Skill Dedicada:")
            for item in unhandled[-5:]:
                content.append(f"- `\"{item['raw_command']}\"` → Sugestão: Criar módulo em `backend/skills/{item['raw_command'].split()[0]}.py`")
            content.append("")
        else:
            content.append("✅ Todas as intenções recentes foram classificadas com alta precisão.\n")

        if failed:
            content.append("### ⚠️ Falhas de Execução Recentes (Auto-Correção Pendente):")
            for item in failed[-5:]:
                content.append(f"- `\"{item['raw_command']}\"` → Resposta: {item.get('response', 'Erro desconhecido')}")
            content.append("")

        content.append("## 🛠️ Como Adicionar Novas Skills Rapidamente")
        content.append("Crie um arquivo Python na pasta `backend/skills/nome_da_skill.py` exportando a função `execute_skill(intent_payload)`.")
        content.append("O Jarvis carregará a nova capacidade **automaticamente em tempo real** sem reiniciar a plataforma.\n")

        try:
            os.makedirs(os.path.dirname(OBSIDIAN_PROPOSALS_FILE), exist_ok=True)
            with open(OBSIDIAN_PROPOSALS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
        except Exception as e:
            print(f"⚠️ Erro ao atualizar nota de auto-melhoria no Obsidian: {e}")

# Singleton Instance
improver_engine = AutoImproverEngine()
