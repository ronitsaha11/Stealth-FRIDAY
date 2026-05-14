"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Terminal, BotMessageSquare } from "lucide-react";
import { useEffect, useState } from "react";

interface Props {
  command: string;
  response: string;
  state: string;
}

export default function CommandPanel({ command, response, state }: Props) {
  // Typing effect state for response
  const [displayedResponse, setDisplayedResponse] = useState("");
  
  useEffect(() => {
    if (!response) {
      setDisplayedResponse("");
      return;
    }
    
    // Quick typing effect
    let i = 0;
    setDisplayedResponse("");
    const interval = setInterval(() => {
      setDisplayedResponse(response.slice(0, i + 1));
      i++;
      if (i >= response.length) clearInterval(interval);
    }, 15);
    
    return () => clearInterval(interval);
  }, [response]);

  return (
    <div className="flex flex-col gap-4 w-full p-6 border flex-1 rounded-3xl border-cyan-500/10 bg-slate-900/40 backdrop-blur-md shadow-[0_0_30px_rgba(0,255,255,0.02)]">
      
      {/* Command User row */}
      <div className="flex flex-col gap-1">
        <div className="text-[10px] text-slate-500 tracking-[0.2em] uppercase font-bold flex items-center gap-2">
          <Terminal className="w-3 h-3 text-cyan-500" />
          Last Directive
        </div>
        <div className="min-h-[2rem] flex items-center">
          <AnimatePresence mode="wait">
            <motion.p
              key={command}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className={`text-sm sm:text-base font-mono ${state === 'LISTENING' ? 'text-cyan-400 animate-pulse' : 'text-slate-300'}`}
            >
              {state === 'LISTENING' && !command ? 'Listening...' : (command || '---')}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>

      <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent" />

      {/* Response row */}
      <div className="flex flex-col gap-1 flex-1">
        <div className="text-[10px] text-slate-500 tracking-[0.2em] uppercase font-bold flex items-center gap-2">
          <BotMessageSquare className="w-3 h-3 text-cyan-500" />
          System Response
        </div>
        <div className="min-h-[3rem] mt-1 text-sm sm:text-base text-cyan-100 font-light leading-relaxed">
          {displayedResponse || (state === 'PROCESSING' ? (
              <span className="flex items-center gap-2 text-cyan-500/50">
                  <span className="inline-block w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="inline-block w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="inline-block w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
          ) : '---')}
        </div>
      </div>

    </div>
  );
}
