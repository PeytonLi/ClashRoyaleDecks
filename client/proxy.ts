import { NextResponse } from 'next/server';

import { auth } from './src/auth';

const protectedRoutes = ['/recommend', '/results', '/payment'];
const authRoutes = ['/login', '/signup'];

export default auth((request) => {
  const { pathname } = request.nextUrl;
  const isProtected = protectedRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`));
  const isAuthRoute = authRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`));

  if (isProtected && !request.auth) {
    const loginUrl = new URL('/login', request.nextUrl);
    loginUrl.searchParams.set('callbackUrl', `${pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthRoute && request.auth) {
    return NextResponse.redirect(new URL('/recommend', request.nextUrl));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ['/((?!api/auth|_next/static|_next/image|favicon.ico|.*\\..*).*)'],
};
