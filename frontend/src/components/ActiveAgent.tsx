"use client";

import { useConnectionState, useVoiceAssistant, BarVisualizer, VoiceAssistantControlBar, RoomAudioRenderer } from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export default function ActiveAgent() {
  const state = useConnectionState();
  const { state: agentState, audioTrack } = useVoiceAssistant();

  // Create a pleasant, dynamic UI based on agent state
  const isConnecting = state === ConnectionState.Connecting;
  const isDisconnected = state === ConnectionState.Disconnected;
  const isSpeaking = agentState === "speaking";

  if (isDisconnected) {
    return null;
  }

  return (
    <div className="relative flex flex-col items-center justify-center w-full h-[300px] border border-cyan-500/20 bg-black/40 backdrop-blur-xl rounded-3xl overflow-hidden shadow-[0_0_80px_rgba(0,255,255,0.05)]">
      <RoomAudioRenderer />
      
      {/* Background ambient glow matching speaking state */}
      <motion.div
        animate={{
          opacity: isSpeaking ? 0.3 : 0.05,
          scale: isSpeaking ? 1.2 : 1,
        }}
        transition={{ duration: 1.5, repeat: Infinity, repeatType: "mirror" }}
        className="absolute w-[400px] h-[400px] bg-cyan-500 rounded-full blur-[100px] pointer-events-none"
      />

      {isConnecting ? (
        <div className="flex flex-col items-center gap-4 text-cyan-400">
          <Loader2 className="w-8 h-8 animate-spin" />
          <p className="text-sm tracking-[0.2em] uppercase font-medium">Booting Raptor Core...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center z-10 w-full h-full p-8">
          
          <div className="flex-1 flex items-center justify-center w-full">
             <BarVisualizer
               state={agentState}
               barCount={7}
               trackRef={audioTrack}
               className="w-full h-24"
               options={{ minHeight: 12 }}
             />
          </div>

          <div className="mt-8">
            <VoiceAssistantControlBar />
          </div>

          <p className="mt-6 text-cyan-500/50 text-xs tracking-[0.3em] uppercase">
            {agentState === "speaking" ? "Transmitting..." : "Listening..."}
          </p>
        </div>
      )}
    </div>
  );
}
