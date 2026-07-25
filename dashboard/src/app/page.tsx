"use client";

import React, { useState, useEffect, useRef } from "react";

export default function JarvisDashboard() {
  const [currentTime, setCurrentTime] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [lastHeard, setLastHeard] = useState("");
  const [statusMessage, setStatusMessage] = useState("Microfone em espera (Modo Contínuo)");
  const [logs, setLogs] = useState<Array<{ time: string; type: string; message: string }>>([
    { time: new Date().toLocaleTimeString(), type: "SYSTEM", message: "JARVIS Web Core v3.7 - Escuta Direta Contínua." },
  ]);

  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString("pt-BR", { hour12: false }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const addLog = (type: string, message: string) => {
    const time = new Date().toLocaleTimeString("pt-BR", { hour12: false });
    setLogs((prev) => [{ time, type, message }, ...prev.slice(0, 15)]);
  };

  // Fala apenas 1 vez, sem interromper ou desativar o microfone
  const speakWebOnce = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "pt-BR";
      utterance.rate = 1.05;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleBrowserCommand = (text: string) => {
    const command = text.toLowerCase().strip ? text.toLowerCase().strip() : text.toLowerCase().trim();
    setLastHeard(command);
    addLog("VOICE_IN", `Ouvido: "${command}"`);

    // 1. WHATSAPP
    if (command.includes("whatsapp") || command.includes("zap")) {
      addLog("ACTION", "Abrindo WhatsApp Web...");
      speakWebOnce("Abrindo WhatsApp.");
      window.open("https://web.whatsapp.com", "_blank");
    }
    // 2. OBSIDIAN
    else if (command.includes("obsidian")) {
      addLog("ACTION", "Abrindo Obsidian...");
      speakWebOnce("Abrindo Obsidian.");
      window.open("obsidian://open", "_blank");
    }
    // 3. AC/DC / YOUTUBE MÚSICA
    else if (command.includes("acdc") || command.includes("ac/dc") || command.includes("toca acdc")) {
      addLog("ACTION", "Tocando AC/DC no YouTube...");
      speakWebOnce("Tocando AC/DC.");
      window.open("https://www.youtube.com/watch?v=pAgnJDJN4VA", "_blank");
    }
    // 4. YOUTUBE
    else if (command.includes("youtube")) {
      addLog("ACTION", "Abrindo YouTube...");
      speakWebOnce("Abrindo YouTube.");
      window.open("https://www.youtube.com", "_blank");
    }
    // 5. CHATGPT
    else if (command.includes("chatgpt") || command.includes("chat gpt")) {
      addLog("ACTION", "Abrindo ChatGPT...");
      speakWebOnce("Abrindo ChatGPT.");
      window.open("https://chatgpt.com", "_blank");
    }
    // 6. GITHUB
    else if (command.includes("github")) {
      addLog("ACTION", "Abrindo GitHub...");
      speakWebOnce("Abrindo GitHub.");
      window.open("https://github.com", "_blank");
    }
    // 7. GOOGLE
    else if (command.includes("google")) {
      addLog("ACTION", "Abrindo Google...");
      speakWebOnce("Abrindo Google.");
      window.open("https://www.google.com", "_blank");
    }
    // 8. PALAVRA DE ATIVAÇÃO SIMPLES
    else if (command.includes("jarvis") || command.includes("chaves")) {
      addLog("JARVIS", "Jarvis ouvindo...");
      // Não fala redundância extra
    }
  };

  const toggleMicrophone = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      setStatusMessage("Microfone desativado.");
      addLog("MIC", "Microfone desligado.");
      return;
    }

    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Seu navegador não suporta Web Speech API. Use Chrome ou Edge.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = "pt-BR";

      recognition.onstart = () => {
        setIsListening(true);
        setStatusMessage("Microfone ONLINE e escutando continuamente.");
        addLog("MIC", "Microfone ligado em modo contínuo.");
      };

      recognition.onresult = (event: any) => {
        const lastIndex = event.results.length - 1;
        const transcript = event.results[lastIndex][0].transcript;
        handleBrowserCommand(transcript);
      };

      recognition.onerror = (event: any) => {
        if (event.error !== "no-speech") {
          addLog("ERROR", `Status: ${event.error}`);
        }
      };

      recognition.onend = () => {
        if (recognitionRef.current && isListening) {
          try {
            recognition.start();
          } catch (e) {}
        } else {
          setIsListening(false);
          setStatusMessage("Microfone desativado.");
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.error(err);
      addLog("ERROR", "Erro ao iniciar microfone.");
    }
  };

  return (
    <div className="min-h-screen bg-[#03060d] text-cyan-400 font-mono flex flex-col justify-between selection:bg-cyan-500 selection:text-black relative overflow-hidden">
      <div className="fixed inset-0 bg-[radial-gradient(#00f2ff_1px,transparent_1px)] [background-size:32px_32px] opacity-10 pointer-events-none" />
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed -bottom-40 -right-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="border-b border-cyan-900/50 bg-[#060b18]/80 backdrop-blur-md px-6 py-4 flex flex-wrap justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <div className={`w-4 h-4 rounded-full ${isListening ? "bg-emerald-400 animate-ping" : "bg-cyan-600"}`} />
          <h1 className="text-xl font-bold tracking-widest text-cyan-200 uppercase flex items-center gap-2">
            J.A.R.V.I.S. <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">WEB HUD v3.7</span>
          </h1>
        </div>

        <div className="flex items-center gap-6 text-sm text-cyan-300">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${isListening ? "bg-emerald-400" : "bg-amber-500"}`} />
            <span>MIC: {isListening ? "MODO CONTÍNUO (ATIVO)" : "AGUARDANDO ATIVAÇÃO"}</span>
          </div>
          <div className="border-l border-cyan-900 h-4" />
          <div>HORA: <span className="text-cyan-100 font-bold">{currentTime || "00:00:00"}</span></div>
        </div>
      </header>

      {/* Main Area */}
      <main className="flex-1 p-6 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl w-full mx-auto z-10">
        
        {/* Arc Reactor Core & Mic Controller */}
        <section className="bg-[#060c1d]/70 border border-cyan-900/50 rounded-xl p-6 flex flex-col items-center justify-between shadow-[0_0_40px_rgba(0,242,255,0.05)] backdrop-blur-md">
          <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase w-full border-b border-cyan-900/50 pb-2 text-center">
            Reator Arc & Captura Sem Interrupção
          </h2>

          <div className="relative my-8 flex items-center justify-center cursor-pointer" onClick={toggleMicrophone}>
            <div className={`w-52 h-52 rounded-full border-2 ${isListening ? "border-cyan-400 animate-[spin_6s_linear_infinite]" : "border-cyan-900/50"} flex items-center justify-center border-dashed`} />
            
            <div className={`absolute w-38 h-38 rounded-full border ${isListening ? "border-cyan-300 shadow-[0_0_60px_#00f2ff] bg-cyan-950/60" : "border-cyan-900 shadow-none bg-slate-950/40"} flex flex-col items-center justify-center transition-all duration-500`}>
              <span className="text-3xl font-black text-cyan-100 tracking-tighter">JARVIS</span>
              <span className="text-[10px] text-cyan-400 tracking-widest uppercase mt-1">
                {isListening ? "MODO CONTÍNUO" : "CLIQUE P/ ATIVAR"}
              </span>
            </div>
          </div>

          <button
            onClick={toggleMicrophone}
            className={`w-full py-3 px-4 rounded-lg font-bold tracking-wider text-xs uppercase transition-all duration-300 border ${
              isListening
                ? "bg-red-950/80 hover:bg-red-900 border-red-600 text-red-200 shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                : "bg-cyan-950/80 hover:bg-cyan-900 border-cyan-500 text-cyan-100 shadow-[0_0_20px_rgba(0,242,255,0.2)]"
            }`}
          >
            {isListening ? "🔴 DESLIGAR MICROFONE" : "🎙️ LIGAR MICROFONE CONTÍNUO"}
          </button>

          <p className="text-[11px] text-cyan-500 text-center mt-3">
            {statusMessage}
          </p>
        </section>

        {/* Console Telemetry & Web Commands */}
        <section className="md:col-span-2 flex flex-col gap-6">
          
          <div className="bg-[#060c1d]/70 border border-cyan-900/50 rounded-xl p-6 backdrop-blur-md">
            <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase border-b border-cyan-900/50 pb-2 mb-4">
              Comandos em Modo Contínuo (Fala Única)
            </h2>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"Jarvis abre o WhatsApp"</span>
                <span className="text-[10px] text-cyan-500">Abre WhatsApp Web</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"Jarvis abre o Obsidian"</span>
                <span className="text-[10px] text-cyan-500">Abre Obsidian</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"Jarvis toca AC/DC"</span>
                <span className="text-[10px] text-cyan-500">Toca no YouTube</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"Jarvis abre o ChatGPT"</span>
                <span className="text-[10px] text-cyan-500">Abre ChatGPT</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"Jarvis abre o GitHub"</span>
                <span className="text-[10px] text-cyan-500">Abre GitHub</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"Jarvis"</span>
                <span className="text-[10px] text-cyan-500">Escuta silenciosa</span>
              </div>
            </div>
          </div>

          <div className="bg-[#060c1d]/70 border border-cyan-900/50 rounded-xl p-6 flex-1 backdrop-blur-md flex flex-col">
            <div className="flex justify-between items-center border-b border-cyan-900/50 pb-2 mb-3">
              <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                Console de Reconhecimento
              </h2>
              {lastHeard && (
                <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                  Última fala: "{lastHeard}"
                </span>
              )}
            </div>

            <div className="bg-[#02040a] border border-cyan-950 p-4 rounded-lg flex-1 font-mono text-xs space-y-2 overflow-y-auto max-h-60">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-3">
                  <span className="text-cyan-700">[{log.time}]</span>
                  <span className="text-cyan-400 font-bold">[{log.type}]</span>
                  <span className="text-cyan-100">{log.message}</span>
                </div>
              ))}
            </div>
          </div>

        </section>
      </main>

      <footer className="border-t border-cyan-900/50 bg-[#060b18]/80 backdrop-blur-md px-6 py-3 text-xs flex justify-between items-center text-cyan-600 z-10">
        <div>DEPLOY: VERCEL WEB HUD</div>
        <div>JARVIS AI SYSTEM &copy; STARK ARCHITECTURE</div>
      </footer>
    </div>
  );
}
