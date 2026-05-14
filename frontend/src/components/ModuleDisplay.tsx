"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Cloud, Globe, Trophy, Mail, Music, ActivitySquare, Terminal, Compass } from "lucide-react";

interface Props {
  module: string;
}

export default function ModuleDisplay({ module }: Props) {
  
  const getModuleInfo = () => {
    switch (module) {
      case "weather": return { icon: Cloud, label: "Meteorology", color: "text-sky-400", bg: "bg-sky-500/10", border: "border-sky-500/20" };
      case "world_monitor": return { icon: Globe, label: "World Monitor", color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20" };
      case "sports": return { icon: Trophy, label: "Sports Desk", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" };
      case "email": return { icon: Mail, label: "Comm Link", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" };
      case "music": return { icon: Music, label: "Audio System", color: "text-fuchsia-400", bg: "bg-fuchsia-500/10", border: "border-fuchsia-500/20" };
      case "stock": return { icon: ActivitySquare, label: "Financials", color: "text-green-400", bg: "bg-green-500/10", border: "border-green-500/20" };
      case "browser": return { icon: Compass, label: "Browser Link", color: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/20" };
      default: return { icon: Terminal, label: "Core Kernel", color: "text-cyan-500", bg: "bg-cyan-500/5", border: "border-cyan-500/10" };
    }
  };

  const info = getModuleInfo();
  const Icon = info.icon;

  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-3xl border border-white/5 bg-slate-900/40 backdrop-blur-md shadow-[0_0_30px_rgba(0,0,0,0.5)] min-w-[140px]">
      <div className="text-[10px] text-slate-500 tracking-[0.2em] uppercase font-bold mb-4">
        Active Subsys
      </div>
      
      <AnimatePresence mode="wait">
        <motion.div
          key={module}
          initial={{ opacity: 0, scale: 0.5, rotate: -20 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          exit={{ opacity: 0, scale: 0.5, rotate: 20 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
          className={`flex items-center justify-center w-16 h-16 rounded-full border ${info.border} ${info.bg} mb-3`}
        >
          <Icon className={`w-8 h-8 ${info.color}`} />
        </motion.div>
      </AnimatePresence>
      
      <AnimatePresence mode="wait">
         <motion.div
            key={info.label}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className={`text-xs font-mono font-bold tracking-widest uppercase ${info.color}`}
         >
             {info.label}
         </motion.div>
      </AnimatePresence>
    </div>
  );
}
