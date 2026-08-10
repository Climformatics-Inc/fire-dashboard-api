import type { Request } from "express";
import { getSettings, type Settings } from "./config.js";
import { hashSessionToken } from "./security.js";

export function buildSessionCookie(token: string, settings: Settings = getSettings()): string {
  const parts = [
    `${settings.sessionCookieName}=${token}`,
    "Path=/",
    "HttpOnly",
    `Max-Age=${settings.sessionTtlSeconds}`,
  ];
  if (settings.isProduction) {
    parts.push("Secure", "SameSite=None");
  } else {
    parts.push("SameSite=Lax");
  }
  return parts.join("; ");
}

export function buildClearCookie(settings: Settings = getSettings()): string {
  const parts = [`${settings.sessionCookieName}=`, "Path=/", "HttpOnly", "Max-Age=0"];
  if (settings.isProduction) {
    parts.push("Secure", "SameSite=None");
  } else {
    parts.push("SameSite=Lax");
  }
  return parts.join("; ");
}

export function resolveSessionToken(req: Request, settings: Settings = getSettings()): string | null {
  const cookieToken = req.cookies?.[settings.sessionCookieName];
  if (typeof cookieToken === "string" && cookieToken.trim()) {
    return cookieToken.trim();
  }

  // Header fallback for non-browser clients only. Do not accept tokens in query strings —
  // they leak via logs, referrers, and browser history.
  const headerToken = req.get("x-session-token");
  if (headerToken?.trim()) {
    return headerToken.trim();
  }

  const authorization = req.get("authorization") ?? "";
  if (authorization.startsWith("Bearer ")) {
    return authorization.slice("Bearer ".length).trim();
  }

  return null;
}

export function bootstrapAdminToken(email: string, secret: string): string {
  return `bootstrap-admin:${hashSessionToken(email, secret)}`;
}
