import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';

import { API_BASE, bffHeaders } from '@/lib/backend';

type BackendUser = {
  id: number;
  email: string;
  name?: string | null;
  image_url?: string | null;
};

async function postBackendUser(path: string, body: Record<string, unknown>): Promise<BackendUser | null> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: bffHeaders(),
    body: JSON.stringify(body),
    cache: 'no-store',
  });

  if (!response.ok) return null;
  return response.json();
}

const providers = [
  Credentials({
    credentials: {
      email: { label: 'Email', type: 'email' },
      password: { label: 'Password', type: 'password' },
    },
    async authorize(credentials) {
      const email = String(credentials?.email || '').trim();
      const password = String(credentials?.password || '');
      if (!email || !password) return null;

      const user = await postBackendUser('/api/auth/login', { email, password });
      if (!user) return null;

      return {
        id: String(user.id),
        email: user.email,
        name: user.name || user.email,
        image: user.image_url || undefined,
      };
    },
  }),
  ...(process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET ? [Google] : []),
];

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers,
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
  },
  trustHost: true,
  callbacks: {
    async signIn({ user, account, profile }) {
      if (account?.provider !== 'google') return true;
      if (!user.email || !account.providerAccountId) return false;

      const googleProfile = profile as { email_verified?: boolean } | undefined;
      const backendUser = await postBackendUser('/api/auth/oauth/google', {
        email: user.email,
        google_sub: account.providerAccountId,
        email_verified: googleProfile?.email_verified === true,
        name: user.name,
        image_url: user.image,
      });

      if (!backendUser) return false;

      user.id = String(backendUser.id);
      user.email = backendUser.email;
      user.name = backendUser.name || backendUser.email;
      user.image = backendUser.image_url || user.image;
      return true;
    },
    jwt({ token, user }) {
      if (user?.id) token.userId = user.id;
      return token;
    },
    session({ session, token }) {
      if (session.user && token.userId) {
        session.user.id = String(token.userId);
      }
      return session;
    },
  },
});
