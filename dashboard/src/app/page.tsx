"use client";

import React, { useState, useEffect, useRef } from "react";
import Head from "next/head";
export default function JarvisDashboard() {
  const [currentTime, setCurrentTime] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [lastHeard, setLastHeard] = useState("");
  const [textInput, setTextInput] = useState("");
  const [statusMessage, setStatusMessage] = useState("Microfone em espera (Modo Contínuo)");
  const [tunnelStatus, setTunnelStatus] = useState<"CONNECTED" | "DISCONNECTED" | "CHECKING">("CHECKING");
  const [customTunnelUrl, setCustomTunnelUrl] = useState("");
  const [showTunnelInput, setShowTunnelInput] = useState(false);
  const [logs, setLogs] = useState<Array<{ time: string; type: string; message: string }>>([
    { time: new Date().toLocaleTimeString(), type: "SYSTEM", message: "JARVIS Web Core v3.8 - Escuta por Voz e Digitação Ativas." },
  ]);

  const recognitionRef = useRef<any>(null);

  // Load custom tunnel URL from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedUrl = localStorage.getItem("jarvis_custom_tunnel_url");
      if (savedUrl) {
        setCustomTunnelUrl(savedUrl);
      } else if (process.env.NEXT_PUBLIC_JARVIS_TUNNEL_URL) {
        setCustomTunnelUrl(process.env.NEXT_PUBLIC_JARVIS_TUNNEL_URL);
      }
    }
  }, []);

  const getActiveTunnelUrl = () => {
    return customTunnelUrl.trim() || process.env.NEXT_PUBLIC_JARVIS_TUNNEL_URL || "";
  };

  const handleSaveTunnelUrl = (newUrl: string) => {
    const trimmed = newUrl.trim().replace(/\/$/, "");
    setCustomTunnelUrl(trimmed);
    if (typeof window !== "undefined") {
      localStorage.setItem("jarvis_custom_tunnel_url", trimmed);
    }
    addLog("SYSTEM", `Túnel atualizado: ${trimmed || "Desativado"}`);
  };

  useEffect(() => {
    const checkTunnelHealth = async () => {
      const url = getActiveTunnelUrl();
      if (!url) {
        setTunnelStatus("DISCONNECTED");
        return;
      }
      try {
        const res = await fetch(`${url}/health`, { method: "GET", signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          setTunnelStatus("CONNECTED");
        } else {
          setTunnelStatus("DISCONNECTED");
        }
      } catch {
        setTunnelStatus("DISCONNECTED");
      }
    };

    checkTunnelHealth();
    const tunnelInterval = setInterval(checkTunnelHealth, 6000);
    return () => clearInterval(tunnelInterval);
  }, [customTunnelUrl]);

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

  const speakWebOnce = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "pt-BR";
      utterance.rate = 1.05;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleCommandExecution = async (text: string, source: "VOICE" | "TEXT" = "VOICE") => {
    const command = text.toLowerCase().trim();
    if (!command) return;

    setLastHeard(command);
    addLog(source === "VOICE" ? "VOICE_IN" : "TEXT_IN", `Comando (${source}): "${command}"`);

    // Remote backend call via ngrok tunnel if configured
    const tunnelUrl = getActiveTunnelUrl();
    if (tunnelUrl) {
      try {
        const res = await fetch(`${tunnelUrl}/command`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command })
        });
        if (res.ok) {
          const data = await res.json();
          addLog("REMOTE", `✅ Executado no notebook: ${data.message || "OK"}`);
          speakWebOnce(`Comando enviado ao notebook.`);
          return; // Command handled remotely by notebook backend!
        } else {
          addLog("ERROR", `❌ Erro do backend local (HTTP ${res.status})`);
          speakWebOnce("Erro ao comunicar com o notebook.");
        }
      } catch (e) {
        addLog("ERROR", "❌ Backend local desconectado (Verifique se ./run_server.sh e o ngrok estão ativos no notebook)");
        speakWebOnce("Servidor do notebook inacessível.");
      }
    } else {
      addLog("WARNING", "⚠️ Túnel remoto não configurado. Cole o link do ngrok no topo do painel.");
    }


    // Normalize text and strip wake words at start
    let raw = command.toLowerCase().trim();
    raw = raw.replace(/^(chaves|jarvis|charles|davis|ei jarvis|ouvi jarvis)\s*/i, "");

    // Phonetic normalization for AC/DC variants ("a cdc", "ac dc", "coloca cd", etc.)
    const isAcdc = /\b(acdc|ac\/dc|a cdc|ac dc|a c d c|toca cd|coloca cd)\b/i.test(raw);

    // Direct YouTube Homepage Open intent
    const isYouTubeOpenOnly = /^(abra|abrir|open|abrindo)?\s*o?\s*youtube$/i.test(raw) || raw === "no youtube";

    // Media search intent detection
    const hasPlayAction = /\b(toca|tocar|play|coloca|coloque|ouvir|pesquisa|procura|abertura|musica|música|video|vídeo)\b/i.test(raw);
    const isYouTubeSearch = !isYouTubeOpenOnly && (hasPlayAction || (raw.includes("youtube") && raw.replace(/^(abra|abrir|open|abrindo)?\s*o?\s*youtube\s*/i, "").trim().length > 0));

    if (isAcdc) {
      addLog("ACTION", "Tocando AC/DC no YouTube...");
      speakWebOnce("Tocando AC/DC.");
      window.open("https://www.youtube.com/watch?v=pAgnJDJN4VA", "_blank");
    }
    else if (isYouTubeSearch) {
      let query = raw
        .replace(/^(toca|tocar|play|coloca|coloque|ouvir|pesquisa|procura|abrir|abra|abrindo|buscando)\s+(a\s+|o\s+)?(música\s+de|música|vídeo\s+de|vídeo|abertura\s+de|abertura)?\s*/i, "")
        .replace(/\b(no youtube|pelo youtube|youtube|para mim|por favor)\b/gi, "")
        .trim();

      if (query.length > 0) {
        addLog("ACTION", `Buscando no YouTube: "${query}"...`);
        speakWebOnce(`Buscando ${query} no YouTube.`);
        window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`, "_blank");
      } else {
        addLog("ACTION", "Abrindo YouTube...");
        speakWebOnce("Abrindo YouTube.");
        window.open("https://www.youtube.com", "_blank");
      }
    }
    // WHATSAPP
    else if (raw.includes("whatsapp") || raw.includes("zap")) {
      addLog("ACTION", "Abrindo WhatsApp Web...");
      speakWebOnce("Abrindo WhatsApp.");
      window.open("https://web.whatsapp.com", "_blank");
    }
    // OBSIDIAN
    else if (raw.includes("obsidian")) {
      addLog("ACTION", "Abrindo Obsidian...");
      speakWebOnce("Abrindo Obsidian.");
      window.open("obsidian://open", "_blank");
    }
    // YOUTUBE HOMEPAGE
    else if (raw.includes("youtube")) {
      addLog("ACTION", "Abrindo YouTube...");
      speakWebOnce("Abrindo YouTube.");
      window.open("https://www.youtube.com", "_blank");
    }
    // CHATGPT
    else if (raw.includes("chatgpt") || raw.includes("chat gpt")) {
      addLog("ACTION", "Abrindo ChatGPT...");
      speakWebOnce("Abrindo ChatGPT.");
      window.open("https://chatgpt.com", "_blank");
    }
    // GITHUB
    else if (raw.includes("github")) {
      addLog("ACTION", "Abrindo GitHub...");
      speakWebOnce("Abrindo GitHub.");
      window.open("https://github.com", "_blank");
    }
    // GOOGLE
    else if (raw.includes("google")) {
      addLog("ACTION", "Abrindo Google...");
      speakWebOnce("Abrindo Google.");
      window.open("https://www.google.com", "_blank");
    }
    // WAKE WORD ONLY
    else if (raw.includes("jarvis") || raw.includes("chaves")) {
      addLog("JARVIS", "Jarvis pronto.");
    } else {
      addLog("SYSTEM", `Executando busca por '${raw}'...`);
      speakWebOnce(`Buscando ${raw}.`);
      window.open(`https://www.google.com/search?q=${encodeURIComponent(raw)}`, "_blank");
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    handleCommandExecution(textInput, "TEXT");
    setTextInput("");
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
        handleCommandExecution(transcript, "VOICE");
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
    <>
      <Head>
        <title>Jarvis – Assistente de Voz e HUD Web</title>
        <meta name="description" content="Jarvis AI é um assistente pessoal de voz que controla seu computador e serviços web (Obsidian, WhatsApp, YouTube, Google Agenda) via comandos de voz ou texto." />
        <meta property="og:title" content="Jarvis – Assistente de Voz e HUD Web" />
        <meta property="og:description" content="Controle seu desktop e apps web com simples palavras. Experimente agora!" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={process.env.NEXT_PUBLIC_JARVIS_TUNNEL_URL || ""} />
        <meta property="og:image" content="/social-preview.png" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className="min-h-screen bg-[#03060d] text-cyan-400 font-mono flex flex-col justify-between selection:bg-cyan-500 selection:text-black relative overflow-hidden">
        <div className="fixed inset-0 bg-[radial-gradient(#00f2ff_1px,transparent_1px)] [background-size:32px_32px] opacity-10 pointer-events-none" />
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed -bottom-40 -right-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="border-b border-cyan-900/50 bg-[#060b18]/80 backdrop-blur-md px-6 py-4 flex flex-wrap justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <div className={`w-4 h-4 rounded-full ${isListening ? "bg-emerald-400 animate-ping" : "bg-cyan-600"}`} />
          <h1 className="text-xl font-bold tracking-widest text-cyan-200 uppercase flex items-center gap-2">
            J.A.R.V.I.S. <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">WEB HUD v3.8</span>
          </h1>
        </div>

        <div className="flex items-center gap-6 text-sm text-cyan-300">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${tunnelStatus === "CONNECTED" ? "bg-emerald-400 animate-pulse" : "bg-red-500"}`} />
            <span className={tunnelStatus === "CONNECTED" ? "text-emerald-400 font-semibold" : "text-red-400 font-semibold"}>
              NOTEBOOK: {tunnelStatus === "CONNECTED" ? "CONECTADO" : tunnelStatus === "CHECKING" ? "VERIFICANDO..." : "DESCONECTADO"}
            </span>
            <button
              onClick={() => setShowTunnelInput(!showTunnelInput)}
              className="text-xs text-cyan-400 hover:text-cyan-200 underline ml-1 font-mono"
            >
              {showTunnelInput ? "Fechar ⚙️" : "Configurar ⚙️"}
            </button>
          </div>
          <div className="border-l border-cyan-900 h-4" />
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${isListening ? "bg-emerald-400" : "bg-amber-500"}`} />
            <span>MIC: {isListening ? "MODO CONTÍNUO (ATIVO)" : "AGUARDANDO ATIVAÇÃO"}</span>
          </div>
          <div className="border-l border-cyan-900 h-4" />
          <div>HORA: <span className="text-cyan-100 font-bold">{currentTime || "00:00:00"}</span></div>
        </div>
      </header>

      {/* Interactive Tunnel URL Bar */}
      {(showTunnelInput || tunnelStatus === "DISCONNECTED") && (
        <div className="bg-[#050d21] border-b border-cyan-900/60 px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs z-20 shadow-md">
          <div className="flex items-center gap-2 text-cyan-300 w-full sm:w-auto">
            <span>🔗 <strong>Túnel ngrok:</strong></span>
            <input
              type="text"
              placeholder="Ex: https://cdf9-2804-2dc-ff8d-dee0-8b3e-a1be-e99f-bc21.ngrok-free.app"
              value={customTunnelUrl}
              onChange={(e) => setCustomTunnelUrl(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSaveTunnelUrl(customTunnelUrl); }}
              className="bg-[#02050b] border border-cyan-800 rounded px-3 py-1.5 text-cyan-100 text-xs w-full sm:w-96 focus:outline-none focus:border-cyan-400 font-mono shadow-inner"
            />
            <button
              onClick={() => handleSaveTunnelUrl(customTunnelUrl)}
              className="bg-cyan-900 hover:bg-cyan-700 text-cyan-100 px-4 py-1.5 rounded font-bold transition-all border border-cyan-700"
            >
              Salvar Túnel
            </button>
          </div>
          <div className="text-cyan-400/80 text-[11px] font-sans">
            {tunnelStatus === "CONNECTED" ? "🟢 Notebook conectado com sucesso!" : "⚠️ Cole a URL HTTPS do ngrok rodando no seu notebook."}
          </div>
        </div>
      )}

      {/* Main Area */}
      <main className="flex-1 p-6 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl w-full mx-auto z-10">
        
        {/* Arc Reactor Core & Mic Controller */}
        <section className="bg-[#060c1d]/70 border border-cyan-900/50 rounded-xl p-6 flex flex-col items-center justify-between shadow-[0_0_40px_rgba(0,242,255,0.05)] backdrop-blur-md">
          <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase w-full border-b border-cyan-900/50 pb-2 text-center">
            Reator Arc & Captura de Voz
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
              Comandos por Voz e Texto Suportados
            </h2>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"abra o whatsapp"</span>
                <span className="text-[10px] text-cyan-500">Abre WhatsApp Web</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"abra o obsidian"</span>
                <span className="text-[10px] text-cyan-500">Abre Obsidian</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"toca acdc"</span>
                <span className="text-[10px] text-cyan-500">Toca no YouTube</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"chatgpt"</span>
                <span className="text-[10px] text-cyan-500">Abre ChatGPT</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">"github"</span>
                <span className="text-[10px] text-cyan-500">Abre GitHub</span>
              </div>
              <div className="bg-[#09132a] p-2.5 rounded border border-cyan-900/50">
                <span className="text-cyan-200 font-bold block">Qualquer outro texto</span>
                <span className="text-[10px] text-cyan-500">Busca no Google</span>
              </div>
            </div>
          </div>

          <div className="bg-[#060c1d]/70 border border-cyan-900/50 rounded-xl p-6 flex-1 backdrop-blur-md flex flex-col justify-between gap-4">
            <div className="flex justify-between items-center border-b border-cyan-900/50 pb-2">
              <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                Terminal & Entrada Manual de Comandos
              </h2>
              {lastHeard && (
                <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                  Último: "{lastHeard}"
                </span>
              )}
            </div>

            {/* Terminal Logs */}
            <div className="bg-[#02040a] border border-cyan-950 p-4 rounded-lg flex-1 font-mono text-xs space-y-2 overflow-y-auto max-h-48">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-3">
                  <span className="text-cyan-700">[{log.time}]</span>
                  <span className="text-cyan-400 font-bold">[{log.type}]</span>
                  <span className="text-cyan-100">{log.message}</span>
                </div>
              ))}
            </div>

            {/* Input Bar Form */}
            <form onSubmit={handleTextSubmit} className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="> Digite um comando para o Jarvis (ex: 'abra o obsidian', 'whatsapp', 'toca acdc')..."
                className="flex-1 bg-[#02040a] border border-cyan-800/80 rounded-lg px-4 py-2.5 text-xs text-cyan-100 placeholder-cyan-700 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
              />
              <button
                type="submit"
                className="bg-cyan-950 hover:bg-cyan-900 border border-cyan-600 text-cyan-100 text-xs px-5 py-2.5 rounded-lg font-bold tracking-wider transition-all uppercase shadow-[0_0_15px_rgba(0,242,255,0.15)]"
              >
                ENVIAR
              </button>
            </form>
          </div>

        </section>
      </main>

      <footer className="border-t border-cyan-900/50 bg-[#060b18]/80 backdrop-blur-md px-6 py-3 text-xs flex justify-between items-center text-cyan-600 z-10">
        <div>DEPLOY: VERCEL WEB HUD</div>
        <div>JARVIS AI SYSTEM &copy; STARK ARCHITECTURE</div>
      </footer>
      </div>
    </>
  );
}
