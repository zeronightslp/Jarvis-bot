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

load_dotenv()

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

def open_url_safely(url, description=""):
    global opened_urls
    opened_urls.add(url)
    browsers = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "firefox", "xdg-open"]
    opened = False
    for b in browsers:
        try:
            subprocess.Popen([b, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

# --- SKILL: SMART MEDIA PLAYER ---
def smart_media_player(query, platform="YouTube", media_type="música", mode="play"):
    """
    Skill: Smart Media Player
    Responsabilidades:
    - Abrir plataformas de mídia (YouTube, Spotify, etc.)
    - Pesquisar mídias ignorando anúncios e anúncios patrocinados (ytd-promoted, badge-style-ad)
    - Selecionar e reproduzir o primeiro resultado orgânico
    """
    print(f"🎬 [Skill: Smart Media Player] Plataforma: {platform} | Consulta: '{query}' | Tipo: {media_type} | Modo: {mode}")

    if platform.lower() == "youtube":
        if not query or len(query.strip()) == 0:
            speak("Abrindo YouTube.")
            return open_url_safely("https://www.youtube.com", "YouTube Home")

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
def classify_intent(raw_text: str) -> dict:
    """
    Skill: Intent Classifier
    Responsabilidade: Transformar fala natural do usuário em um payload estruturado.
    Não executa nada no sistema ou navegador.
    """
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
                acdc_url = "https://www.youtube.com/watch?v=pAgnJDJN4VA"
                speak("Tocando AC/DC.")
                open_url_safely(acdc_url, "AC/DC YouTube")
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

        elif intent == "system_action":
            if query == "close_all":
                speak(close_all_pages())
            elif query == "get_urls":
                speak(get_opened_urls())

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
