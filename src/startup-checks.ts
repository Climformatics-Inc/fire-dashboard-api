import { getSettings } from "./config.js";

const INSECURE_SECRETS = new Set([
  "local-dev-session-secret",
  "change-me",
  "secret",
  "changeme",
]);

export function assertSecureStartupConfig(): void {
  const settings = getSettings();

  if (!settings.databaseUrl) {
    throw new Error("DATABASE_URL is required");
  }

  if (!settings.frontendOrigin) {
    throw new Error("FRONTEND_ORIGIN is required");
  }

  if (settings.isProduction) {
    if (!settings.sessionSecret || settings.sessionSecret.length < 32) {
      throw new Error("SESSION_SECRET must be at least 32 characters in production");
    }

    if (INSECURE_SECRETS.has(settings.sessionSecret)) {
      throw new Error("SESSION_SECRET must not use a default or known insecure value in production");
    }

    if (settings.adminPassword && settings.adminPassword.length < 12) {
      throw new Error("ADMIN_PASSWORD must be at least 12 characters in production when set");
    }
  } else if (INSECURE_SECRETS.has(settings.sessionSecret)) {
    console.warn(
      "[security] Using default SESSION_SECRET — acceptable for local dev only. Set a strong secret before deploying."
    );
  }
}
