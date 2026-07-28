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

# --- HELPER DE ABERTURA SEGURA DE URLS ---
def open_url_safely(url, description=""):
    if url in opened_urls:
        print(f"⚠️ {description or 'Página'} já está aberta.")
        return False
    opened_urls.add(url)
    try:
        if is_process_running("chrome"):
            subprocess.Popen(["google-chrome", "--new-window", url])
        else:
            subprocess.Popen(["google-chrome", url])
    except:
        webbrowser.open(url)
    return True

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

# --- PROCESSAMENTO DE COMANDOS DE VOZ ---
def process_voice_command(command):
    global is_voice_processing
    is_voice_processing = True

    try:
        command = command.lower().strip()
        print(f"⚙️ Comando detectado: '{command}'")

        # Clean wake words at the beginning
        raw = re.sub(r'^(chaves|jarvis|charles|davis|ei jarvis|ouvi jarvis)\s*', '', command, flags=re.IGNORECASE).strip()

        # Phonetic normalization for AC/DC variants ("a cdc", "ac dc", "coloca cd", etc.)
        is_acdc = bool(re.search(r'\b(acdc|ac\/dc|a cdc|ac dc|a c d c|toca cd|coloca cd)\b', raw, flags=re.IGNORECASE))

        # Check for media/play intent
        has_play_action = any(w in raw for w in ["toca", "tocar", "play", "coloca", "coloque", "ouvir", "pesquisa", "procura", "abertura", "música", "musica", "vídeo", "video"])
        is_yt_intent = has_play_action or ("youtube" in raw and len(re.sub(r'^(abra|abrir|open)?\s*o?\s*youtube\s*', '', raw, flags=re.IGNORECASE).strip()) > 0)

        if is_acdc:
            acdc_url = "https://www.youtube.com/watch?v=pAgnJDJN4VA"
            if acdc_url in opened_urls:
                print("AC/DC já aberto.")
            else:
                speak("Tocando AC/DC.")
                open_url_safely(acdc_url, "AC/DC YouTube")

        elif is_yt_intent:
            query = re.sub(
                r'^(toca|tocar|play|coloca|coloque|ouvir|pesquisa|procura|abrir|abra)\s+(a\s+|o\s+)?(música\s+de|música|vídeo\s+de|vídeo|abertura\s+de|abertura)?\s*',
                '',
                raw,
                flags=re.IGNORECASE
            )
            query = re.sub(r'\b(no youtube|pelo youtube|youtube|para mim|por favor)\b', '', query, flags=re.IGNORECASE).strip()

            if len(query) > 0:
                speak(f"Buscando {query} no YouTube.")
                try:
                    url_search = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                    req = urllib.request.Request(url_search, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
                    html = urllib.request.urlopen(req).read().decode()
                    video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
                    if video_ids:
                        first_video = f"https://www.youtube.com/watch?v={video_ids[0]}"
                        open_url_safely(first_video, f"Vídeo {query}")
                    else:
                        open_url_safely(url_search, f"Busca {query}")
                except Exception:
                    open_url_safely(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}", "Busca YouTube")
            else:
                speak("Abrindo YouTube.")
                open_url_safely("https://www.youtube.com", "YouTube")

        # 1. OBSIDIAN
        elif "obsidian" in raw:
            open_obsidian()

        # 2. WHATSAPP
        elif "whatsapp" in raw or "zap" in raw:
            speak("Abrindo WhatsApp.")
            open_url_safely("https://web.whatsapp.com", "WhatsApp Web")

        # 2.5 CALENDAR
        elif "calendário" in raw or "agenda" in raw:
            speak("Abrindo agenda.")
            open_url_safely("https://calendar.google.com", "Google Calendar")

        # 2.6 STATUS DAS PAGINAS
        elif "fechar tudo" in raw:
            speak(close_all_pages())

        elif "qual página" in raw or "página atual" in raw:
            speak(get_opened_urls())

        # 4. OUTROS SITES
        elif "youtube" in raw:
            speak("Abrindo YouTube.")
            open_url_safely("https://www.youtube.com", "YouTube")

        elif "chatgpt" in raw or "chat gpt" in raw:
            speak("Abrindo ChatGPT.")
            open_url_safely("https://chatgpt.com", "ChatGPT")

        elif "github" in raw:
            speak("Abrindo GitHub.")
            open_url_safely("https://github.com", "GitHub")

        elif "google" in raw:
            speak("Abrindo Google.")
            open_url_safely("https://www.google.com", "Google")

        # 5. CONTROLE DE MÍDIA EXPLÍCITO
        elif any(w in command for w in ["pausar música", "para a música", "pausar o vídeo", "parar música"]):
            subprocess.run(["playerctl", "pause"], check=False)

        elif any(w in command for w in ["próxima música", "pular música", "avança a música"]):
            subprocess.run(["playerctl", "next"], check=False)

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
