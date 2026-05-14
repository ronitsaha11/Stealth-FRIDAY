"use client";

import RaptorVisualizer, { RaptorState } from "@/components/RaptorVisualizer";
import { Activity, Loader2, Mic, Power, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { useRaptorSocket } from "@/hooks/useRaptorSocket";
import CommandPanel from "@/components/CommandPanel";
import StateIndicator from "@/components/StateIndicator";
import ModuleDisplay from "@/components/ModuleDisplay";
import { useState } from "react";

export default function Home() {
  const { raptorState, connected, connecting, reconnect } = useRaptorSocket();
  const [starting, setStarting] = useState(false);
  const [controlMessage, setControlMessage] = useState("");

  const wakeCore = () => new Promise<string>((resolve, reject) => {
    const wsUrl = process.env.NEXT_PUBLIC_RAPTOR_WS_URL || "ws://localhost:8765";
    const ws = new WebSocket(wsUrl);
    const cleanup = () => {
      window.clearTimeout(timeout);
      ws.close();
    };
    const timeout = window.setTimeout(() => {
      cleanup();
      reject(new Error("Raptor bridge did not acknowledge the wake command."));
    }, 5000);

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "command", command: "wake" }));
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== "command_ack") return;
        cleanup();
        if (data.ok) {
          resolve(data.message || "Wake signal sent.");
        } else {
          reject(new Error(data.message || "Wake command failed."));
        }
      } catch {
        cleanup();
        reject(new Error("Raptor bridge sent an invalid wake response."));
      }
    };
    ws.onerror = () => {
      cleanup();
      reject(new Error("Could not reach the Raptor websocket bridge."));
    };
  });

  const powerCore = async () => {
    setStarting(true);
    setControlMessage(connected ? "Waking Raptor..." : "Starting Raptor core...");

    try {
      const response = await fetch("/api/raptor/start", { method: "POST" });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result.error || `Start request failed with HTTP ${response.status}.`);
      }
      reconnect();
      const wakeMessage = await wakeCore();
      setControlMessage(wakeMessage);
    } catch (error) {
      setControlMessage(error instanceof Error ? error.message : "Could not power Raptor on.");
    } finally {
      setStarting(false);
    }
  };

  const checkCore = async () => {
    setControlMessage("Checking bridge...");

    try {
      const response = await fetch("/api/raptor/status");
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result.error || `Status check failed with HTTP ${response.status}.`);
      }
      setControlMessage(result.online ? "Raptor bridge is reachable." : "Raptor bridge is offline.");
      reconnect();
    } catch (error) {
      setControlMessage(error instanceof Error ? error.message : "Could not check Raptor bridge.");
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center bg-[#05070a] text-white overflow-hidden">
      
      {/* Dynamic Background Grid & Atmosphere */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        <div className="absolute top-0 -left-1/4 w-[1000px] h-[1000px] rounded-full bg-cyan-600/5 blur-[150px]" />
        <div className="absolute bottom-0 -right-1/4 w-[800px] h-[800px] rounded-full bg-blue-600/5 blur-[120px]" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none" />
      </div>

      <div className="z-10 w-full max-w-5xl flex flex-col items-center gap-6 p-8 h-screen pt-12 pb-12">
        
        {/* Header Section */}
        <div className="text-center space-y-4 shrink-0">
          <StateIndicator state={raptorState.state as RaptorState} connected={connected} />
          
          <div className="relative">
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-5xl md:text-6xl font-black tracking-tighter"
            >
              RAPTOR
            </motion.h1>
            <div className="h-[2px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent absolute -bottom-2 left-0 w-full" />
          </div>
          
          <p className="text-slate-500 text-[10px] tracking-widest max-w-md mx-auto uppercase mt-4">
            Autonomous OS Intelligence <span className="text-cyan-800">|</span> Local Protocol 1.0
          </p>
        </div>

        {/* Dashboard Area */}
        <div className="w-full flex-1 flex flex-col gap-6 mt-4 max-w-4xl">
            
            {/* Top Row: Visualizer & Module */}
            <div className="flex gap-6 h-[50vh]">
                <div className="flex-1 border border-cyan-500/10 bg-black/50 backdrop-blur-3xl rounded-[40px] overflow-hidden shadow-[0_0_100px_rgba(0,242,255,0.03)] border-b-cyan-500/30">
                  <RaptorVisualizer state={raptorState.state as RaptorState} />
                </div>
                
                <div className="hidden sm:flex flex-col gap-6 w-[180px]">
                    <ModuleDisplay module={raptorState.active_module} />
                    
                    <div className="flex flex-col flex-1 p-4 rounded-3xl border border-white/5 bg-slate-900/40 backdrop-blur-md justify-center items-center gap-4">
                        <button
                          type="button"
                          title="Reconnect dashboard"
                          aria-label="Reconnect dashboard"
                          onClick={reconnect}
                          className="grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/5 text-slate-400 transition hover:border-cyan-400/40 hover:text-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-400/70"
                        >
                          <RefreshCw className={`h-5 w-5 ${connecting ? "animate-spin" : ""}`} />
                        </button>

                        <button
                          type="button"
                          title="Check core bridge"
                          aria-label="Check core bridge"
                          onClick={checkCore}
                          className="grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/5 text-slate-400 transition hover:border-yellow-400/40 hover:text-yellow-300 focus:outline-none focus:ring-2 focus:ring-yellow-400/70"
                        >
                          <Activity className={`h-5 w-5 ${raptorState.state === "PROCESSING" ? "animate-pulse text-yellow-300" : ""}`} />
                        </button>

                        <button
                          type="button"
                          title="Start or wake Raptor core"
                          aria-label="Start or wake Raptor core"
                          onClick={powerCore}
                          disabled={starting}
                          className={`grid h-12 w-12 place-items-center rounded-full border transition focus:outline-none focus:ring-2 ${
                            connected
                              ? "border-green-400/30 bg-green-500/10 text-green-300 focus:ring-green-400/70"
                              : "border-red-400/30 bg-red-500/10 text-red-300 hover:border-cyan-400/50 hover:text-cyan-200 focus:ring-cyan-400/70"
                          } ${starting ? "cursor-wait opacity-70" : ""}`}
                        >
                          {starting ? <Loader2 className="h-6 w-6 animate-spin" /> : <Power className="h-6 w-6" />}
                        </button>

                        <Mic className={`h-5 w-5 ${raptorState.state === "LISTENING" ? "text-blue-400 animate-pulse" : "text-slate-600"}`} />
                    </div>
                </div>
            </div>

            {/* Bottom Row: Command Panel */}
            <CommandPanel 
                command={raptorState.last_command} 
                response={raptorState.last_response || controlMessage} 
                state={raptorState.state} 
            />

        </div>

      </div>
    </main>
  );
}
