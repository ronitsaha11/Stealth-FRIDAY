import { AccessToken } from 'livekit-server-sdk';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const roomName = `raptor-${Date.now()}`;
    const participantName = `user-${Math.floor(Math.random() * 1000)}`;

    if (!process.env.LIVEKIT_API_KEY || !process.env.LIVEKIT_API_SECRET) {
        return NextResponse.json({ error: 'Server misconfigured' }, { status: 500 });
    }

    const at = new AccessToken(
      process.env.LIVEKIT_API_KEY,
      process.env.LIVEKIT_API_SECRET,
      {
        identity: participantName,
        name: participantName,
      }
    );

    at.addGrant({ roomJoin: true, room: roomName });

    const token = await at.toJwt();
    return NextResponse.json({ token, url: process.env.NEXT_PUBLIC_LIVEKIT_URL });
  } catch {
    return NextResponse.json({ error: 'Failed to generate token' }, { status: 500 });
  }
}
