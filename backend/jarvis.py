import pyaudio
import time
import subprocess
import webbrowser
import math
import struct
import speech_recognition as sr
import threading
import asyncio
import os
import urllib.parse
import urllib.request
import re
import psutil
import json
from lmnt import AsyncLmnt
from dotenv import load_dotenv

from browser_manager import manager

load_dotenv()

# --- SKILL: BROWSER BRIDGE ---
def browser_action(action, target="", value=""):
    try:
        asyncio.run(manager.broadcast_command(action, target, value))
    except Exception as e:
        print(f"⚠️ Erro ao enviar ação para o navegador: {e}")

# --- HELPER PARA CHECAR PROCESSOS ---
def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if process_name.lower() in proc.info['name'].lower():
            return True
    return False

# --- ESTADO GLOBAL DO SISTEMA ---
opened_urls = set()
is_voice_processing = False

# --- AUDIO / TTS LOGIC ---
async def lmnt_speak(text):
    try:
        api_key = os.getenv("LMNT_API_KEY")
        if not api_key:
            print(f"🤖 Jarvis (TTS Local): {text}")
            return

        client = AsyncLmnt(api_key=api_key)
        async with client.speech.with_streaming_response.generate(
            text=text,
            voice='leah',
        ) as response:
            await response.stream_to_file('voice_temp.mp3')
        
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "voice_temp.mp3"], check=False)
    except Exception as e:
        print(f"🤖 Jarvis: {text} (Erro TTS: {e})")

def speak(text):
    print(f"🤖 Jarvis: {text}")
    try:
        asyncio.run(lmnt_speak(text))
    except Exception as e:
        print(f"Erro ao executar fala: {e}")

current_media_process = None

def stop_previous_media():
    """
    Interrompe e fecha a mídia/música anterior para evitar reprodução simultânea de áudio,
    garantindo que a aba do Vercel/navegador principal não seja fechada.
    """
    global current_media_process
    if current_media_process is not None:
        try:
            current_media_process.terminate()
            current_media_process = None
        except Exception:
            pass

    # Fecha especificamente as janelas/abas que possuem "YouTube" no título, preservando o Vercel
    try:
        subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--name", "YouTube", "windowclose"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
        )
    except Exception:
        pass

def open_url_safely(url, description="", is_media=False):
    global opened_urls, current_media_process
    opened_urls.add(url)

    # Se for mídia do YouTube ou pedido explícito de áudio, interrompe a mídia anterior primeiro
    if is_media or "youtube.com" in url or "youtu.be" in url:
        stop_previous_media()

    browsers = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "firefox", "xdg-open"]
    opened = False
    for b in browsers:
        try:
            if ("chrome" in b or "chromium" in b) and ("youtube.com" in url or "youtu.be" in url):
                current_media_process = subprocess.Popen([b, f"--app={url}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                current_media_process = subprocess.Popen([b, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            opened = True
            break
        except Exception:
            continue
    if not opened:
        try:
            webbrowser.open(url)
            opened = True
        except Exception as e:
            print(f"❌ Erro ao abrir URL {url}: {e}")
            return False
    print(f"✅ Página/Mídia aberta com sucesso ({description or url}): {url}")
    return True

# --- SKILL: OBSIDIAN FAVORITES LOADER ---
OBSIDIAN_FAVORITES_FILE = "/home/zeronight/Documentos/Minha mente/Músicas Favoritas.md"

def load_obsidian_favorites():
    """
    Skill: Obsidian Favorites Loader
    Lê o arquivo 'Músicas Favoritas.md' no cofre do Obsidian e mapeia palavras-chave para URLs.
    """
    favorites = {}
    if not os.path.exists(OBSIDIAN_FAVORITES_FILE):
        return favorites
    try:
        with open(OBSIDIAN_FAVORITES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Matches format: - **Nome**: URL or - Nome: URL
                match = re.search(r'[-*]\s+(.*?)\s*:\s*(https?://\S+)', line)
                if match:
                    raw_key = match.group(1).strip()
                    url = match.group(2).strip()
                    # Strip markdown bold asterisks
                    key = re.sub(r'\*+', '', raw_key).lower().strip()
                    favorites[key] = url
                    clean_key = re.sub(r'\(.*?\)', '', key).strip()
                    if clean_key:
                        favorites[clean_key] = url
    except Exception as e:
        print(f"⚠️ Erro ao ler favoritos do Obsidian: {e}")
    return favorites

# --- SKILL: SMART MEDIA PLAYER ---
def smart_media_player(query, platform="YouTube", media_type="música", mode="play"):
    """
    Skill: Smart Media Player
    Responsabilidades:
    - Consultar primeiramente as Músicas Favoritas do Obsidian
    - Caso não encontre, pesquisar no YouTube filtrando anúncios e elementos irrelevantes
    """
    print(f"🎬 [Skill: Smart Media Player] Plataforma: {platform} | Consulta: '{query}' | Tipo: {media_type} | Modo: {mode}")

    if platform.lower() == "youtube":
        if not query or len(query.strip()) == 0:
            speak("Abrindo YouTube.")
            return open_url_safely("https://www.youtube.com", "YouTube Home")

        # 1. Verifica favoritos do Obsidian primeiro!
        obsidian_favs = load_obsidian_favorites()
        query_clean = query.lower().strip()
        for fav_name, fav_url in obsidian_favs.items():
            if query_clean in fav_name or fav_name in query_clean:
                speak(f"Reproduzindo {fav_name} dos favoritos do Obsidian.")
                return open_url_safely(fav_url, f"Obsidian Favorito: {fav_name}")

        speak(f"Buscando {query} no YouTube e selecionando vídeo orgânico.")
        try:
            url_search = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            req = urllib.request.Request(
                url_search,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
            html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

            organic_video_ids = []

            # Method 1: Extract from ytInitialData JSON payload
            yt_data_match = re.search(r'var\s+ytInitialData\s*=\s*({.*?});</script>', html)
            if yt_data_match:
                try:
                    data = json.loads(yt_data_match.group(1))
                    sections = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                    for section in sections:
                        items = section.get("itemSectionRenderer", {}).get("contents", [])
                        for item in items:
                            # Only target videoRenderer (ignores channelRenderer, playlistRenderer, radioRenderer/mixes, shorts, ads)
                            if "videoRenderer" in item:
                                vr = item["videoRenderer"]
                                badges = vr.get("badges", [])
                                is_ad = any("AD" in str(b).upper() or "SPONSORED" in str(b).upper() for b in badges)
                                if not is_ad and "videoId" in vr:
                                    organic_video_ids.append(vr["videoId"])
                except Exception as parse_err:
                    print(f"⚠️ Aviso no parse de ytInitialData: {parse_err}")

            # Method 2: Fallback regex if ytInitialData parsing produced no video IDs
            if not organic_video_ids:
                clean_html = re.sub(r'<ytd-promoted-[^>]+>.*?</ytd-promoted-[^>]+>', '', html, flags=re.DOTALL)
                clean_html = re.sub(r'("badgeStyleType"\s*:\s*"BADGE_STYLE_TYPE_AD")[^}]+', '', clean_html)
                raw_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", clean_html)
                seen = set()
                organic_video_ids = [v for v in raw_ids if not (v in seen or seen.add(v))]

            if organic_video_ids:
                first_organic = f"https://www.youtube.com/watch?v={organic_video_ids[0]}"
                speak(f"Reproduzindo primeiro vídeo orgânico para {query}.")
                return open_url_safely(first_organic, f"Vídeo Orgânico: {query}")
            else:
                return open_url_safely(url_search, f"Busca Orgânica YouTube: {query}")

        except Exception as e:
            print(f"⚠️ Erro no Smart Media Player: {e}")
            return open_url_safely(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}", f"Busca YouTube: {query}")

    elif platform.lower() == "spotify":
        speak(f"Buscando {query} no Spotify.")
        return open_url_safely(f"https://open.spotify.com/search/{urllib.parse.quote(query)}", f"Spotify Search: {query}")

# --- HELPER PARA FECHAR PAGINAS ABERTAS ---
def close_all_pages():
    global opened_urls
    if not opened_urls:
        return "Nenhuma página para fechar."
    opened_urls.clear()
    subprocess.run(["pkill", "chrome"], check=False)
    return "Todas as páginas foram fechadas."

# --- HELPER PARA LISTAR PÁGINAS ABERTAS ---
def get_opened_urls():
    if not opened_urls:
        return "Nenhuma página foi registrada como aberta nesta sessão."
    return "As páginas abertas são: " + ", ".join([url.split('//')[-1].split('/')[0] for url in opened_urls])

# --- HELPER PARA ABRIR OBSIDIAN NO LINUX ---
def open_obsidian():
    print("Executando: Abrir Obsidian")
    speak("Abrindo Obsidian.")
    try:
        subprocess.Popen(["flatpak", "run", "md.obsidian.Obsidian"])
    except Exception:
        try:
            subprocess.Popen(["obsidian"])
        except Exception:
            webbrowser.open("obsidian://open")

# --- TRIGGER DE DUAS PALMAS ---
STRICT_CLAP_THRESHOLD = 0.40
MAX_CLAP_PULSE_DURATION = 0.06
MIN_TIME_BETWEEN_CLAPS = 0.25
MAX_TIME_BETWEEN_CLAPS = 0.70

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

def on_two_claps():
    print("\n[+] 2 Palmas confirmadas! Abrindo Obsidian...")
    speak("Abrindo Obsidian.")
    open_obsidian()

def get_rms(block):
    count = len(block) // 2
    if count == 0:
        return 0
    shorts = struct.unpack(f"{count}h", block)
    sum_squares = sum((sample * (1.0 / 32768)) ** 2 for sample in shorts)
    return math.sqrt(sum_squares / count)

def listen_for_claps():
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    except Exception as e:
        print(f"❌ Módulo de palmas desativado: {e}")
        return

    time.sleep(2.5)
    print("🤖 Jarvis [Módulo Palmas] ONLINE.")

    claps = 0
    last_clap_time = 0
    pulse_start_time = 0
    in_pulse = False

    while True:
        try:
            if is_voice_processing:
                time.sleep(0.1)
                continue

            data = stream.read(CHUNK, exception_on_overflow=False)
            rms = get_rms(data)
            now = time.time()

            if rms > STRICT_CLAP_THRESHOLD:
                if not in_pulse:
                    in_pulse = True
                    pulse_start_time = now
            else:
                if in_pulse:
                    pulse_duration = now - pulse_start_time
                    in_pulse = False

                    if pulse_duration <= MAX_CLAP_PULSE_DURATION:
                        time_since_last = now - last_clap_time

                        if time_since_last > MIN_TIME_BETWEEN_CLAPS:
                            if time_since_last <= MAX_TIME_BETWEEN_CLAPS:
                                claps += 1
                            else:
                                claps = 1
                            
                            last_clap_time = now

                            if claps == 2:
                                on_two_claps()
                                claps = 0
                                time.sleep(3.0)
        except Exception:
            time.sleep(0.05)

# --- SKILL 1: INTENT CLASSIFIER ---
def llm_intent_classifier(raw_text: str):
    """
    Skill: Zero AI Hub LLM Intent Classifier
    Usa o LiteLLM local (Zero AI Hub) para classificar o comando inteligentemente.
    """
    url = "http://localhost:4000/v1/chat/completions"
    cmd = re.sub(r'^(chaves|jarvis|charles|davis|ei jarvis|ouvi jarvis)\s*', '', raw_text, flags=re.IGNORECASE).strip()
    
    system_prompt = """Você é o motor de classificação de intenções do Jarvis AI.
Sua única função é receber o comando do usuário (com base no histórico da conversa se houver) e retornar EXATAMENTE um objeto JSON válido. Não adicione texto extra.

Formato esperado:
{
    "intent": "play_media" | "open_app" | "web_search" | "stop_media" | "conversational" | "browser_action" | "system_action",
    "platform": "youtube" | "google" | "whatsapp" | "obsidian" | "calendar" | "chatgpt" | "browser" | "",
    "query": "texto da busca, ação do browser, ou comando de sistema (ex: clear_memory)",
    "media_type": "music" | "video" | "app" | "search" | "chat" | "target/value",
    "confidence": 0.95,
    "llm_response": "Opcional. Se for 'conversational', coloque aqui a sua resposta direta e curta para falar em áudio ao usuário."
}

Exemplos para browser_action:
- "role a página para baixo" -> {"intent": "browser_action", "platform": "browser", "query": "scroll", "media_type": "down"}
- "clique no botão de login" -> {"intent": "browser_action", "platform": "browser", "query": "click", "media_type": "button.login"}

Comandos especiais (system_action):
Se o usuário disser "esquece tudo", "apague a memória", "nova conversa", retorne:
{"intent": "system_action", "platform": "", "query": "clear_memory", "media_type": "action"}
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Injetar contexto da memória
    from memory_manager import memory
    context_msgs = memory.get_context()
    for msg in context_msgs:
        messages.append(msg)
        
    messages.append({"role": "user", "content": cmd})

    payload = {
        "model": "fast-chat",
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 150
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json", "Authorization": "Bearer sk-zero-hub-2026"})
        response = urllib.request.urlopen(req, timeout=4.0)
        result_data = json.loads(response.read().decode('utf-8'))
        
        content = result_data["choices"][0]["message"]["content"].strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"⚠️ Aviso: Zero AI Hub LLM indisponível ou falhou. Fallback para Regex. ({e})")
        return None

def classify_intent(raw_text: str) -> dict:
    """
    Skill: Intent Classifier
    Responsabilidade: Transformar fala natural do usuário em um payload estruturado.
    Usa LLM (Zero AI Hub) primariamente e Regex como Fallback.
    """
    llm_parsed = llm_intent_classifier(raw_text)
    if llm_parsed and "intent" in llm_parsed:
        return llm_parsed
    cmd = raw_text.lower().strip()
    cmd = re.sub(r'^(chaves|jarvis|charles|davis|ei jarvis|ouvi jarvis)\s*', '', cmd, flags=re.IGNORECASE).strip()

    if bool(re.search(r'\b(acdc|ac\/dc|a cdc|ac dc|a c d c|toca cd|coloca cd)\b', cmd, flags=re.IGNORECASE)):
        return {
            "intent": "play_media",
            "platform": "youtube",
            "query": "AC/DC",
            "media_type": "music",
            "confidence": 0.99
        }

    if bool(re.search(r'\b(leave johnny|leave joni|liv johnny|música 2|musica 2)\b', cmd, flags=re.IGNORECASE)):
        return {
            "intent": "play_media",
            "platform": "youtube",
            "query": "LEAVE_JOHNNY",
            "media_type": "music",
            "confidence": 0.99
        }

    if bool(re.search(r'^(abra|abrir|open|abrindo)?\s*o?\s*youtube$', cmd, flags=re.IGNORECASE)) or cmd == "no youtube":
        return {
            "intent": "open_app",
            "platform": "youtube",
            "query": "",
            "media_type": "homepage",
            "confidence": 0.95
        }

    play_verbs = r'^(coloca|toca|reproduz|reprodut|inicia|quero\s+ouvir|quero\s+assistir|pesquisa|procura|abrir|abra|abrindo)\s+'
    has_play_keyword = any(w in cmd for w in ["coloca", "toca", "reproduz", "ouvir", "assistir", "abertura", "música", "musica", "vídeo", "video"])

    if bool(re.search(play_verbs, cmd, flags=re.IGNORECASE)) or has_play_keyword or "youtube" in cmd:
        query = re.sub(play_verbs, '', cmd, flags=re.IGNORECASE)
        query = re.sub(r'^(a\s+|o\s+)?(música\s+de|música|vídeo\s+de|vídeo|abertura\s+de|abertura)?\s*', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\b(para mim|pra mim|por favor|no youtube|pelo youtube|youtube)\b', '', query, flags=re.IGNORECASE).strip()

        return {
            "intent": "play_media",
            "platform": "youtube",
            "query": query,
            "media_type": "video",
            "confidence": 0.95
        }

    if "whatsapp" in cmd or "zap" in cmd:
        return {"intent": "open_app", "platform": "whatsapp", "query": "", "media_type": "app", "confidence": 0.95}

    if "obsidian" in cmd:
        return {"intent": "open_app", "platform": "obsidian", "query": "", "media_type": "app", "confidence": 0.95}

    if "calendário" in cmd or "agenda" in cmd:
        return {"intent": "open_app", "platform": "calendar", "query": "", "media_type": "app", "confidence": 0.95}

    if "fechar tudo" in cmd:
        return {"intent": "system_action", "platform": "system", "query": "close_all", "media_type": "action", "confidence": 0.99}

    if "qual página" in cmd or "página atual" in cmd:
        return {"intent": "system_action", "platform": "system", "query": "get_urls", "media_type": "action", "confidence": 0.99}

    if "chatgpt" in cmd or "chat gpt" in cmd:
        return {"intent": "open_app", "platform": "chatgpt", "query": "", "media_type": "app", "confidence": 0.95}

    if "github" in cmd:
        return {"intent": "open_app", "platform": "github", "query": "", "media_type": "app", "confidence": 0.95}

    if "google" in cmd:
        return {"intent": "open_app", "platform": "google", "query": "", "media_type": "app", "confidence": 0.95}

    return {
        "intent": "web_search",
        "platform": "google",
        "query": cmd,
        "media_type": "search",
        "confidence": 0.80
    }

# --- PROCESSADOR DE COMANDOS BASEADO EM INTENT CLASSIFIER ---
def process_voice_command(command):
    global is_voice_processing
    is_voice_processing = True

    try:
        print(f"⚙️ Transcrição recebida: '{command}'")
        parsed = classify_intent(command)
        print(f"🧠 [Intent Classifier Output] {parsed}")

        intent = parsed.get("intent")
        platform = parsed.get("platform")
        query = parsed.get("query", "")

        if intent == "play_media":
            if query == "AC/DC":
                acdc_url = "https://www.youtube.com/watch?v=pAgnJDJN4VA&list=RDpAgnJDJN4VA&start_radio=1"
                speak("Tocando AC/DC.")
                open_url_safely(acdc_url, "AC/DC YouTube Mix")
            elif query == "LEAVE_JOHNNY":
                johnny_url = "https://www.youtube.com/watch?v=1JfJshL8etQ&list=RD1JfJshL8etQ&start_radio=1"
                speak("Tocando Leave Johnny Leave.")
                open_url_safely(johnny_url, "Leave Johnny Leave YouTube Mix")
            else:
                smart_media_player(query=query, platform=platform, media_type=parsed.get("media_type", "video"), mode="play")

        elif intent == "open_app":
            if platform == "youtube":
                speak("Abrindo YouTube.")
                open_url_safely("https://www.youtube.com", "YouTube")
            elif platform == "whatsapp":
                speak("Abrindo WhatsApp.")
                open_url_safely("https://web.whatsapp.com", "WhatsApp Web")
            elif platform == "obsidian":
                open_obsidian()
            elif platform == "calendar":
                speak("Abrindo agenda.")
                open_url_safely("https://calendar.google.com", "Google Calendar")
            elif platform == "chatgpt":
                speak("Abrindo ChatGPT.")
                open_url_safely("https://chatgpt.com", "ChatGPT")
            elif platform == "github":
                speak("Abrindo GitHub.")
                open_url_safely("https://github.com", "GitHub")
            elif platform == "google":
                speak("Abrindo Google.")
                open_url_safely("https://www.google.com", "Google")

        elif intent == "browser_action":
            action = query
            target = parsed.get("media_type", "")
            speak(f"Executando ação no navegador: {action}")
            browser_action(action, target)
        
        elif intent == "conversational":
            llm_response = parsed.get("llm_response")
            if llm_response:
                # Salvar histórico de conversa
                from memory_manager import memory
                memory.add_message("user", command)
                memory.add_message("assistant", llm_response)
                
                speak(llm_response)
            else:
                speak("Desculpe, não consegui processar a resposta.")
        
        elif intent == "stop_media":
            # Caso a função stop_previous_media exista (como desenhado em iterações futuras)
            speak("Parando mídia.")
            # stop_previous_media()

        elif intent == "system_action":
            if query == "close_all":
                speak(close_all_pages())
            elif query == "get_urls":
                speak(get_opened_urls())
            elif query == "clear_memory":
                from memory_manager import memory
                memory.clear_memory()
                speak("Memória limpa com sucesso. Sobre o que quer falar agora?")

        elif intent == "web_search":
            if len(query) > 1:
                speak(f"Buscando {query} no Google.")
                open_url_safely(f"https://www.google.com/search?q={urllib.parse.quote(query)}", f"Busca Google {query}")

        return parsed

    finally:
        time.sleep(0.5)
        is_voice_processing = False

def listen_for_voice():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    is_awake = False
    wake_words = ["jarvis", "chaves", "charles", "davis"]

    print("🤖 Jarvis [Módulo Voz] ONLINE - Modo Contínuo.")

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)

            text = recognizer.recognize_google(audio, language="pt-BR").lower()
            print(f"🎙️ Ouvido: '{text}'")

            if is_awake:
                process_voice_command(text)
                is_awake = False
                continue

            if any(w in text for w in wake_words):
                cmd = text
                for w in wake_words:
                    cmd = cmd.replace(w, " ")
                cmd = cmd.strip()

                if len(cmd) > 2:
                    process_voice_command(cmd)
                else:
                    is_awake = True

        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            time.sleep(2)
        except Exception:
            time.sleep(0.5)

if __name__ == "__main__":
    print("==========================================")
    print("      J.A.R.V.I.S. CONTINUOUS AGENT       ")
    print("==========================================")
    
    threading.Thread(target=listen_for_voice, daemon=True).start()
    threading.Thread(target=listen_for_claps, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Desligando Jarvis...")
