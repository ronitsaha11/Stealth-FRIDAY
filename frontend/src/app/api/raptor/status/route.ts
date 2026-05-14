import { NextResponse } from "next/server";
import net from "node:net";

export const runtime = "nodejs";

function canReachRaptorBridge(timeoutMs = 600): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port: 8765 });
    const finish = (online: boolean) => {
      socket.removeAllListeners();
      socket.destroy();
      resolve(online);
    };

    socket.setTimeout(timeoutMs);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false));
    socket.once("error", () => finish(false));
  });
}

export async function GET() {
  const online = await canReachRaptorBridge();
  return NextResponse.json({ online, wsUrl: process.env.NEXT_PUBLIC_RAPTOR_WS_URL || "ws://localhost:8765" });
}
