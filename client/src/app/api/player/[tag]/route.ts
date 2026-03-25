import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ tag: string }> }
) {
  const { tag } = await params;

  try {
    const res = await fetch(`${API_BASE}/api/players/${encodeURIComponent(tag)}`, {
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || 'Player not found' },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 502 }
    );
  }
}
