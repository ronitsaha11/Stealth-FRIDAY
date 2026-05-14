import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";

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

async function waitForBridge(timeoutMs = 12000): Promise<boolean> {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await canReachRaptorBridge()) return true;
    await new Promise((resolve) => setTimeout(resolve, 600));
  }
  return false;
}

export async function POST() {
  if (await canReachRaptorBridge()) {
    return NextResponse.json({ online: true, message: "Raptor core is already online." });
  }

  const workspaceRoot = path.resolve(process.cwd(), "..");
  const launcher = path.join(workspaceRoot, "launch_raptor.bat");

  if (!fs.existsSync(launcher)) {
    return NextResponse.json(
      { online: false, error: `Launcher not found at ${launcher}` },
      { status: 500 },
    );
  }

  try {
    const child = spawn(
      "cmd.exe",
      ["/c", "start", "Raptor Agent - Voice Core", launcher],
      {
        cwd: workspaceRoot,
        detached: true,
        stdio: "ignore",
        windowsHide: false,
      },
    );
    child.unref();

    const online = await waitForBridge();
    return NextResponse.json({
      online,
      message: online ? "Raptor core is online." : "Raptor core is starting, but the bridge is not ready yet.",
    });
  } catch (error) {
    return NextResponse.json(
      { online: false, error: error instanceof Error ? error.message : "Failed to start Raptor core." },
      { status: 500 },
    );
  }
}
