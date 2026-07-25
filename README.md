# 🤖 J.A.R.V.I.S. AI Autonomous Assistant & Web HUD

Sistema de automação residencial e controle pessoal ativado por voz (microfone) e por gestos acústicos (duas palmas). O projeto conta com um **Backend Python de Alta Performance** e um **Dashboard Web HUD Futurista em Next.js para Vercel**.

---

## 🌟 Funcionalidades Principais

### 1. Backend Python (`/backend/jarvis.py`)
- 👏 **Sensor de Duas Palmas (*Double-Clap*):** Análise de pulso de áudio RMS estrita (< 60ms) para evitar disparos falsos. Ativa o Obsidian automaticamente.
- 🎙️ **Reconhecimento de Voz Contínuo:** Palavra de ativação (`Jarvis`, `Chaves`, `Charles`) sem interrupções incômodas.
- 🗣️ **Sintetizador de Voz (LMNT API / Local):** Confirmações de áudio curtas e diretas, falando apenas uma vez por comando.
- 🖥️ **Automação Nativa Linux:** Abertura nativa do Obsidian via Flatpak (`flatpak run md.obsidian.Obsidian`).
- 🛡️ **Navegação Inteligente Anti-Duplicação:** Bloqueia abertura de abas repetidas no navegador.

### 2. Frontend Next.js Web HUD (`/dashboard`)
- 🌐 **Deploy no Vercel:** Interface HUD em tempo real.
- 🎙️ **Microfone no Navegador:** Web Speech API integrada para capturar áudio em qualquer dispositivo (PC ou Celular).
- ⚡ **Reator Arc Animado:** Visualização reativa com iluminação dinâmica.
- ⌨️ **Terminal & Entrada de Texto:** Campo para digitar comandos manuais ou falar por áudio.

---

## 🚀 Como Executar

### 1. Backend Python
```bash
cd backend
python3 -m pip install -r requirements.txt
python3 jarvis.py
```

### 2. Frontend Dashboard (Web)
```bash
cd dashboard
npm install
npm run dev
```

---

## 💬 Comandos por Voz / Texto Suportados
- *"Jarvis, abra o Obsidian"*
- *"Jarvis, abra o WhatsApp"*
- *"Jarvis, toca AC/DC"*
- *"Jarvis, abra o ChatGPT"*
- *"Jarvis, abra o GitHub"*
- *"Jarvis, abra o Google"*

---

## 🛠️ Tecnologias Utilizadas
- **Python 3 / PyAudio / SpeechRecognition / LMNT API / Flatpak**
- **Next.js 16 / React 19 / Tailwind CSS / Web Speech API**
