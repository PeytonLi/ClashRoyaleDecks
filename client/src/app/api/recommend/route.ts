import { NextRequest, NextResponse } from 'next/server';

import { auth } from '@/auth';
import { API_BASE, bffHeaders } from '@/lib/backend';

export async function POST(request: NextRequest) {
  const session = await auth();
  const userId = session?.user?.id;
  if (!userId) {
    return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  }

  const quotaKey = `user:${userId}`;

  // --- 1. Check quota against the persistent backend store ---
  try {
    const checkRes = await fetch(`${API_BASE}/api/usage/check`, {
      method: 'POST',
      headers: bffHeaders(),
      body: JSON.stringify({ ip_address: quotaKey }),
      cache: 'no-store',
    });

    if (checkRes.ok) {
      const quota = await checkRes.json();
      if (!quota.allowed) {
        return NextResponse.json(
          {
            error: 'Free usage limit reached',
            usage_count: quota.usage_count,
            limit: quota.limit,
          },
          { status: 402 },
        );
      }
    }
  } catch {
    // If the usage service is down, allow the request through rather than
    // blocking all users.  The backend BFF-secret check still protects
    // against unauthenticated direct access.
  }

  // --- 2. Parse request body ---
  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body' },
      { status: 400 },
    );
  }

  // --- 3. Forward to FastAPI recommend endpoint ---
  try {
    const res = await fetch(`${API_BASE}/api/predict/recommend`, {
      method: 'POST',
      headers: bffHeaders(userId),
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || 'Recommendation failed' },
        { status: res.status },
      );
    }

    // --- 4. Increment usage on success ---
    let usageMeta = { count: 0, limit: 20, remaining: 20 };
    try {
      const incRes = await fetch(`${API_BASE}/api/usage/increment`, {
        method: 'POST',
        headers: bffHeaders(),
        body: JSON.stringify({ ip_address: quotaKey }),
        cache: 'no-store',
      });
      if (incRes.ok) {
        const inc = await incRes.json();
        usageMeta = {
          count: inc.usage_count,
          limit: inc.limit,
          remaining: inc.remaining,
        };
      }
    } catch {
      // Non-fatal — the recommendation already succeeded.
    }

    return NextResponse.json({
      ...data,
      _usage: usageMeta,
    });
  } catch {
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 502 },
    );
  }
}
