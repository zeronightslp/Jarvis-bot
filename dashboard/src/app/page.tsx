"use client";

import React, { useState, useEffect } from "react";

export default function JarvisDashboard() {
  const [currentTime, setCurrentTime] = useState("");
  const [isListening, setIsListening] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString("pt-BR", { hour12: false }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const logs = [
    { time: "19:04:12", type: "SYSTEM", message: "JARVIS Core Systems Operational." },
    { time: "19:04:15", type: "VOICE", message: "LMNT Neural TTS Voice Synthesis initialized (Leah)." },
    { time: "19:04:22", type: "AUDIO", message: "Clap Detection active. Threshold: 0.15 RMS." },
    { time: "19:05:01", type: "INTEGRATION", message: "Obsidian Vault Connected (/home/zeronight/Documentos/Minha mente)." },
    { time: "19:06:40", type: "AUTOMATION", message: "Triggered dual-action: YouTube AC/DC + Obsidian execution." },
  ];

  const skills = [
    { id: "007", name: "Security Audit & Hardening", status: "Active", category: "Cybersecurity" },
    { id: "lmnt-voice", name: "LMNT Streaming TTS", status: "Active", category: "Audio/Voice" },
    { id: "obsidian-sync", name: "Obsidian Mind Graph Sync", status: "Active", category: "Knowledge Base" },
    { id: "clap-sensor", name: "PyAudio Clap Trigger", status: "Active", category: "Physical IoT" },
    { id: "verus-crm", name: "Meta WhatsApp & Lead CRM", status: "Standby", category: "Business" },
  ];

  return (
    <div className="min-h-screen bg-[#050811] text-cyan-400 font-mono flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
      {/* Background Grid Pattern */}
      <div className="fixed inset-0 bg-[radial-gradient(#00f2ff_1px,transparent_1px)] [background-size:32px_32px] opacity-10 pointer-events-none" />

      {/* Header Bar */}
      <header className="border-b border-cyan-900/50 bg-[#080d1a]/80 backdrop-blur-md px-6 py-4 flex flex-wrap justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full bg-cyan-400 animate-ping" />
          <h1 className="text-xl font-bold tracking-widest text-cyan-200 uppercase flex items-center gap-2">
            J.A.R.V.I.S. <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">v3.6 ULTRA</span>
          </h1>
        </div>

        <div className="flex items-center gap-6 text-sm text-cyan-300">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>STATUS: ONLINE</span>
          </div>
          <div className="border-l border-cyan-900 h-4" />
          <div>TIME: <span className="text-cyan-100 font-bold">{currentTime || "00:00:00"}</span></div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 p-6 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl w-full mx-auto z-10">
        
        {/* Left Column: Arc Reactor Core */}
        <section className="bg-[#080e1e]/60 border border-cyan-900/40 rounded-xl p-6 flex flex-col items-center justify-between shadow-[0_0_30px_rgba(0,242,255,0.05)] backdrop-blur-sm">
          <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase w-full border-b border-cyan-900/40 pb-2">
            Core Reactor Pulse
          </h2>

          <div className="relative my-8 flex items-center justify-center">
            {/* Outer Ring */}
            <div className="w-48 h-48 rounded-full border-2 border-cyan-500/30 animate-[spin_10s_linear_infinite] flex items-center justify-center border-dashed" />
            
            {/* Inner Glowing Core */}
            <div className="absolute w-36 h-36 rounded-full border border-cyan-400 shadow-[0_0_50px_#00f2ff] flex flex-col items-center justify-center bg-cyan-950/40">
              <span className="text-2xl font-black text-cyan-100 tracking-tighter">JARVIS</span>
              <span className="text-[10px] text-cyan-400 tracking-widest uppercase mt-1">LMNT Voice Active</span>
            </div>

            {/* Orbiting particle */}
            <div className="absolute w-44 h-44 rounded-full border border-cyan-400/20 animate-[spin_4s_linear_infinite]" />
          </div>

          <div className="w-full space-y-3 text-xs">
            <div className="flex justify-between items-center bg-cyan-950/30 p-2 rounded border border-cyan-900/30">
              <span className="text-cyan-400">Wake Word:</span>
              <span className="text-cyan-100 font-semibold">"JARVIS" / "CHARLES"</span>
            </div>
            <div className="flex justify-between items-center bg-cyan-950/30 p-2 rounded border border-cyan-900/30">
              <span className="text-cyan-400">Clap Threshold:</span>
              <span className="text-emerald-400 font-semibold">0.15 RMS (Double Clap)</span>
            </div>
            <div className="flex justify-between items-center bg-cyan-950/30 p-2 rounded border border-cyan-900/30">
              <span className="text-cyan-400">Obsidian Sync:</span>
              <span className="text-cyan-100 font-semibold">CONNECTED</span>
            </div>
          </div>
        </section>

        {/* Middle & Right: Intelligence & Skill Matrix */}
        <section className="md:col-span-2 flex flex-col gap-6">
          
          {/* Active Skills Overview */}
          <div className="bg-[#080e1e]/60 border border-cyan-900/40 rounded-xl p-6 backdrop-blur-sm">
            <div className="flex justify-between items-center border-b border-cyan-900/40 pb-3 mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase">
                Active Skill Protocol Matrix
              </h2>
              <span className="text-xs bg-cyan-950 border border-cyan-800 text-cyan-300 px-2 py-0.5 rounded">
                5 Skills Loaded
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {skills.map((skill) => (
                <div key={skill.id} className="bg-[#0b1328]/80 border border-cyan-900/50 p-3 rounded-lg flex justify-between items-center hover:border-cyan-400 transition-colors">
                  <div>
                    <p className="text-xs text-cyan-100 font-bold">{skill.name}</p>
                    <p className="text-[10px] text-cyan-500">{skill.category}</p>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    skill.status === "Active" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-zinc-900 text-zinc-400 border border-zinc-700"
                  }`}>
                    {skill.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Realtime Terminal Telemetry */}
          <div className="bg-[#080e1e]/60 border border-cyan-900/40 rounded-xl p-6 flex-1 backdrop-blur-sm flex flex-col">
            <div className="flex justify-between items-center border-b border-cyan-900/40 pb-3 mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-cyan-400 uppercase flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                Live System Telemetry
              </h2>
              <span className="text-[10px] text-cyan-500 font-mono">ENCRYPTED_FEED_STREAM</span>
            </div>

            <div className="bg-[#03060d] border border-cyan-950 p-4 rounded-lg flex-1 font-mono text-xs space-y-2 overflow-y-auto max-h-56">
              {logs.map((log, index) => (
                <div key={index} className="flex gap-3">
                  <span className="text-cyan-600">[{log.time}]</span>
                  <span className="text-cyan-400 font-bold">[{log.type}]</span>
                  <span className="text-cyan-200">{log.message}</span>
                </div>
              ))}
              <div className="text-cyan-500 animate-pulse">_ Awaiting next voice event...</div>
            </div>
          </div>

        </section>
      </main>

      {/* Footer Status */}
      <footer className="border-t border-cyan-900/50 bg-[#080d1a]/80 backdrop-blur-md px-6 py-3 text-xs flex justify-between items-center text-cyan-600 z-10">
        <div>REPO: zeronightslp/Jarvis-bot</div>
        <div>JARVIS AI SYSTEM &copy; 2026 STARK ARCHITECTURE</div>
      </footer>
    </div>
  );
}
