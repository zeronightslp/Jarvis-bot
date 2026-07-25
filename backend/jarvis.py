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
from lmnt import AsyncLmnt
from dotenv import load_dotenv

load_dotenv()

async def lmnt_speak(text):
    try:
        client = AsyncLmnt() # Pega LMNT_API_KEY do .env
        async with client.speech.with_streaming_response.generate(
            text=text,
            voice='leah',
        ) as response:
            await response.stream_to_file('voice_temp.mp3')
        # Tenta tocar usando ffplay (comum no linux)
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "voice_temp.mp3"], check=False)
    except Exception as e:
        print(f"Erro no LMNT TTS: {e}")

def speak(text):
    print(f"🤖 Jarvis: {text}")
    asyncio.run(lmnt_speak(text))


# --- CALIBRAÇÃO DAS PALMAS ---
THRESHOLD = 0.15       # Aumentado significativamente para evitar que fala normal ative as palmas
MAX_TIME_BETWEEN_CLAPS = 1.0
MIN_TIME_BETWEEN_CLAPS = 0.2

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

def on_two_claps():
    print("\n[+] 2 Palmas confirmadas! Abrindo ACDC e Obsidian...")
    speak("Duas palmas detectadas. Abrindo área de trabalho, senhor.")
    # Abre o Youtube com AC/DC
    webbrowser.open("https://www.youtube.com/watch?v=pAgnJDJN4VA&list=RDpAgnJDJN4VA&start_radio=1")
    # Tenta abrir o Obsidian usando a URL scheme padrão do sistema
    webbrowser.open("obsidian://open")

def get_rms(block):
    count = len(block) // 2
    shorts = struct.unpack(f"{count}h", block)
    sum_squares = sum((sample * (1.0 / 32768)) ** 2 for sample in shorts)
    return math.sqrt(sum_squares / count) if count > 0 else 0

def listen_for_claps():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("🤖 Jarvis [Módulo Palmas] online. Aguardando 2 palmas (Validação Estrita)...")
    
    claps = 0
    last_clap_time = 0
    
    while True:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            rms = get_rms(data)
            
            if rms > THRESHOLD:
                current_time = time.time()
                time_since_last = current_time - last_clap_time
                
                if time_since_last > MIN_TIME_BETWEEN_CLAPS:
                    if time_since_last <= MAX_TIME_BETWEEN_CLAPS:
                        claps += 1
                    else:
                        claps = 1  
                        
                    last_clap_time = current_time
                    print(f"👏 Palma detectada! ({claps}/2) - Volume real: {rms:.3f}")
                    
                    if claps == 2:
                        on_two_claps()
                        claps = 0
                        time.sleep(4) # Cooldown para não duplicar
        except Exception:
            time.sleep(0.1)




def exec_media_command(command):
    try:
        subprocess.run(["playerctl", command], check=False)
    except FileNotFoundError:
        pass


def process_voice_command(command):
    import urllib.parse
    import urllib.request
    import re
    
    if "troca" in command or "próxima" in command or "pula" in command:
        print("Executando: Avançar Música")
        exec_media_command("next")
    elif "pausa" in command or "para" in command:
        print("Executando: Pausar Música")
        exec_media_command("pause")
    elif "play" in command or "tocar" in command or "toca" in command or "ativar" in command or "coloque" in command or "coloca" in command:
        query = command
        for word in ["coloque", "coloca", "tocar", "toca", "música", " de ", " o ", " a ", "um ", "uma "]:
            query = query.replace(word, " ")
        query = query.strip()
        
        if len(query) > 2:
            print(f"Executando: Buscar música '{query}' no YouTube...")
            try:
                # Faz a busca no YouTube de forma oculta
                url_search = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                req = urllib.request.Request(url_search, headers={"User-Agent": "Mozilla/5.0"})
                html = urllib.request.urlopen(req).read().decode()
                
                # Extrai o ID do primeiro vídeo encontrado
                video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
                if video_ids:
                    first_video = f"https://www.youtube.com/watch?v={video_ids[0]}"
                    print(f"Tocando automaticamente: {first_video}")
                    webbrowser.open(first_video)
                else:
                    print("Nenhum vídeo encontrado. Abrindo página de busca...")
                    webbrowser.open(url_search)
            except Exception as e:
                print(f"Erro na busca oculta. Abrindo tela padrão. Erro: {e}")
                webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        else:
            print("Executando: Tocar Música (Play/Pause ou AC/DC padrão)")
            result = subprocess.run(["playerctl", "status"], capture_output=True, text=True)
            status = result.stdout.strip().lower()
            if status in ["playing", "paused"]:
                subprocess.run(["playerctl", "play-pause"], capture_output=True)
            else:
                print("[+] Nenhum player tocando. Abrindo o clipe do AC/DC no navegador...")
                webbrowser.open("https://www.youtube.com/watch?v=pAgnJDJN4VA&list=RDpAgnJDJN4VA&start_radio=1")

def listen_for_voice():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.0 
    is_awake = False
    
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=8)
            
            text = recognizer.recognize_google(audio, language="pt-BR").lower()
            print(f"🎙️ Você disse: '{text}'")
            
            wake_words = ["jarvis", "chaves", "charles", "davis"]
            
            # 1. Se já estiver acordado (esperando comando)
            if is_awake:
                process_voice_command(text)
                speak("Comando executado. Entrando em modo de espera.")
                is_awake = False
                continue

            # 2. Se estiver dormindo, procura a Wake Word
            if any(w in text for w in wake_words):
                command = text
                for w in wake_words:
                    command = command.replace(w, " ")
                command = command.strip()
                
                if len(command) > 3:
                    # Falou tudo de uma vez (Ex: "Jarvis toca one piece")
                    process_voice_command(command)
                else:
                    # Falou APENAS "Jarvis"
                    is_awake = True
                    speak("Estou ouvindo, mestre.")
                    
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            time.sleep(5)
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=listen_for_claps, daemon=True).start()
    time.sleep(1)
    threading.Thread(target=listen_for_voice, daemon=True).start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDesligando Jarvis...")
