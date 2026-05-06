export const API_BASE = process.env.FASTAPI_URL || 'http://localhost:8000';

const BFF_SECRET = process.env.BFF_SHARED_SECRET || '';

export function bffHeaders(userId?: string): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (BFF_SECRET) headers['X-BFF-Secret'] = BFF_SECRET;
  if (userId) headers['X-User-Id'] = userId;
  return headers;
}
