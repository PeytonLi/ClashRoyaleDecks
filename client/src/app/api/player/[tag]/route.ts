import { NextRequest, NextResponse } from 'next/server';

import { auth } from '@/auth';
import { API_BASE, bffHeaders } from '@/lib/backend';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ tag: string }> }
) {
  const session = await auth();
  const userId = session?.user?.id;
  if (!userId) {
    return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  }

  const { tag } = await params;

  try {
    const res = await fetch(`${API_BASE}/api/players/${encodeURIComponent(tag)}`, {
      headers: bffHeaders(userId),
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
