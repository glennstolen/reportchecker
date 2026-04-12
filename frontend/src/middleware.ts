import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const session = request.cookies.get("session");
  if (!session) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Beskytt alle ruter unntatt /login, /auth/*, og Next.js interne ressurser
  matcher: ["/((?!_next/static|_next/image|favicon.ico|login|auth).*)"],
};
