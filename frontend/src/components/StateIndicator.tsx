"use client";

import { motion } from "framer-motion";

interface Props {
  state: 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING';
  connected: boolean;
}

export default function StateIndicator({ state, connected }: Props) {
  
  const getColor = () => {
    if (!connected) return "bg-red-500";
    switch (state) {
      case 'IDLE': return "bg-slate-500";
      case 'LISTENING': return "bg-blue-500";
      case 'PROCESSING': return "bg-yellow-500";
      case 'SPEAKING': return "bg-green-500";
      default: return "bg-slate-500";
    }
  };

  const getLabel = () => {
    if (!connected) return "OFFLINE";
    return state;
  };

  // Shadow class based on state
  const getShadow = () => {
      if (!connected) return "";
      switch (state) {
        case 'LISTENING': return "shadow-[0_0_15px_rgba(59,130,246,0.6)] animate-pulse";
        case 'PROCESSING': return "shadow-[0_0_15px_rgba(234,179,8,0.6)]";
        case 'SPEAKING': return "shadow-[0_0_15px_rgba(34,197,94,0.6)] animate-[pulse_0.5s_ease-in-out_infinite]";
        default: return "";
      }
  }

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="inline-flex items-center gap-3 px-5 py-2 rounded-full border border-white/5 bg-white/5 backdrop-blur-md mb-4 shadow-lg"
    >
      <div className="relative flex items-center justify-center w-3 h-3">
        {/* Glow behind */}
        <div className={`absolute inset-0 rounded-full ${getColor()} ${getShadow()} opacity-70`} />
        {/* Core dot */}
        <div className={`relative w-2 h-2 rounded-full ${getColor()}`} />
      </div>
      
      <span className="text-[10px] sm:text-xs font-bold tracking-[0.4em] uppercase text-slate-300">
        Status: <span className="text-white">{getLabel()}</span>
      </span>
    </motion.div>
  );
}
