export type Settings = {
  databaseUrl: string | undefined;
  frontendOrigin: string | undefined;
  environment: string;
  sessionCookieName: string;
  sessionSecret: string;
  sessionTtlSeconds: number;
  resendApiKey: string | undefined;
  passwordResetFromEmail: string | undefined;
  passwordResetTokenTtlSeconds: number;
  passwordResetEmailSubject: string;
  adminEmail: string | undefined;
  adminPassword: string | undefined;
  adminPlanId: string;
  port: number;
  isProduction: boolean;
};

export function getSettings(): Settings {
  const environment = process.env.ENVIRONMENT ?? "development";
  return {
    databaseUrl: process.env.DATABASE_URL,
    frontendOrigin: process.env.FRONTEND_ORIGIN,
    environment,
    sessionCookieName: process.env.SESSION_COOKIE_NAME ?? "fire_dashboard_session",
    sessionSecret: process.env.SESSION_SECRET ?? "local-dev-session-secret",
    sessionTtlSeconds: Number(process.env.SESSION_TTL_SECONDS ?? String(7 * 24 * 60 * 60)),
    resendApiKey: process.env.RESEND_API_KEY,
    passwordResetFromEmail: process.env.PASSWORD_RESET_FROM_EMAIL,
    passwordResetTokenTtlSeconds: Number(process.env.PASSWORD_RESET_TOKEN_TTL_SECONDS ?? "3600"),
    passwordResetEmailSubject:
      process.env.PASSWORD_RESET_EMAIL_SUBJECT ?? "Reset your Fire Weather Dashboard password",
    adminEmail: process.env.ADMIN_EMAIL,
    adminPassword: process.env.ADMIN_PASSWORD,
    adminPlanId: process.env.ADMIN_PLAN_ID ?? "pro",
    port: Number(process.env.PORT ?? "3001"),
    isProduction: environment.toLowerCase() === "production",
  };
}
