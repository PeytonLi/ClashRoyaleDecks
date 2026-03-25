import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';

const API_BASE = process.env.FASTAPI_URL || 'http://localhost:8000';
const FREE_LIMIT = parseInt(process.env.FREE_USAGE_LIMIT || '3', 10);

/**
 * Simple in-memory usage tracker.
 * In production, replace with a database or Redis.
 */
const usageMap = new Map<string, { count: number; firstUsed: number }>();

function getClientIP(request: NextRequest): string {
  // Check common proxy headers
  const forwarded = request.headers.get('x-forwarded-for');
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }

  const realIp = request.headers.get('x-real-ip');
  if (realIp) return realIp;

  // Fallback
  return '127.0.0.1';
}

export async function POST(request: NextRequest) {
  const ip = getClientIP(request);

  // Check usage limit
  const usage = usageMap.get(ip) || { count: 0, firstUsed: Date.now() };

  if (usage.count >= FREE_LIMIT) {
    return NextResponse.json(
      {
        error: 'Free usage limit reached',
        usage_count: usage.count,
        limit: FREE_LIMIT,
      },
      { status: 402 }
    );
  }

  // Parse request body
  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body' },
      { status: 400 }
    );
  }

  // Forward to FastAPI
  try {
    const res = await fetch(`${API_BASE}/api/predict/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || 'Recommendation failed' },
        { status: res.status }
      );
    }

    // Increment usage on success
    usage.count += 1;
    usageMap.set(ip, usage);

    return NextResponse.json({
      ...data,
      _usage: {
        count: usage.count,
        limit: FREE_LIMIT,
        remaining: FREE_LIMIT - usage.count,
      },
    });
  } catch {
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 502 }
    );
  }
}
