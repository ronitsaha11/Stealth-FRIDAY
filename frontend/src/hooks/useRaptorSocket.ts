import { useState, useEffect, useCallback, useRef } from 'react';

export interface RaptorState {
  state: 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING';
  last_command: string;
  last_response: string;
  active_module: string;
  timestamp: number;
}

export function useRaptorSocket(url = process.env.NEXT_PUBLIC_RAPTOR_WS_URL || 'ws://localhost:8765') {
  const [raptorState, setRaptorState] = useState<RaptorState>({
    state: 'IDLE',
    last_command: '',
    last_response: '',
    active_module: 'none',
    timestamp: 0,
  });
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const generationRef = useRef(0);
  const connectRef = useRef<() => WebSocket | null>(() => null);

  const connect = useCallback(() => {
    generationRef.current += 1;
    const generation = generationRef.current;

    if (retryTimer.current) {
      clearTimeout(retryTimer.current);
      retryTimer.current = null;
    }

    socketRef.current?.close();
    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('[Raptor] WebSocket Connected');
      if (generation !== generationRef.current) return;
      setConnected(true);
      setConnecting(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'state_update') {
          setRaptorState((prev) => {
            // Only update if newer
            if (data.timestamp >= prev.timestamp) {
              return {
                state: data.state || prev.state,
                last_command: data.last_command,
                last_response: data.last_response !== undefined ? data.last_response : prev.last_response,
                active_module: data.active_module || prev.active_module,
                timestamp: data.timestamp,
              };
            }
            return prev;
          });
        }
      } catch (err) {
        console.error('[Raptor] Failed to parse message', err);
      }
    };

    ws.onclose = () => {
      console.log('[Raptor] WebSocket Disconnected. Reconnecting in 3s...');
      if (generation !== generationRef.current) return;
      setConnected(false);
      setConnecting(false);
      retryTimer.current = setTimeout(() => {
        connectRef.current();
      }, 3000);
    };

    ws.onerror = (err) => {
      console.error('[Raptor] WebSocket Error:', err);
      ws.close();
    };

    return ws;
  }, [url]);

  const reconnect = useCallback(() => {
    setConnecting(true);
    connect();
  }, [connect]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    const ws = connect();
    return () => {
      generationRef.current += 1;
      if (retryTimer.current) clearTimeout(retryTimer.current);
      ws.onclose = null; // Prevent reconnect loop on unmount
      ws.close();
    };
  }, [connect]);

  return { raptorState, connected, connecting, reconnect };
}
