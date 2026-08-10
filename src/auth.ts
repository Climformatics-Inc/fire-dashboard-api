import { randomUUID } from "node:crypto";
import type pg from "pg";
import type { Request } from "express";
import { getSettings } from "./config.js";
import { withClient } from "./db.js";
import * as repository from "./repository.js";
import { generateSessionToken, hashSessionToken, normalizeEmail } from "./security.js";
import { bootstrapAdminToken, resolveSessionToken } from "./session.js";

export type SessionUser = {
  id: string;
  email: string;
  subscription_status: string | null;
  plan_id: string | null;
  is_admin: boolean;
  is_disabled?: boolean;
};

export function serializeUser(user: SessionUser) {
  return {
    id: user.id,
    email: user.email,
    subscriptionStatus: user.subscription_status ?? "inactive",
    planId: user.plan_id,
    isAdmin: Boolean(user.is_admin),
  };
}

function bootstrapAdminUser(req: Request): SessionUser | null {
  const settings = getSettings();
  const adminEmail = settings.adminEmail ? normalizeEmail(settings.adminEmail) : null;
  if (!adminEmail) {
    return null;
  }

  const token = resolveSessionToken(req, settings);
  if (!token) {
    return null;
  }

  const expected = bootstrapAdminToken(adminEmail, settings.sessionSecret);
  if (token !== expected) {
    return null;
  }

  return {
    id: "bootstrap-admin",
    email: adminEmail,
    subscription_status: "active",
    plan_id: settings.adminPlanId,
    is_admin: true,
  };
}

export async function currentUser(
  req: Request,
  options: { requireActive: boolean }
): Promise<SessionUser | null> {
  const adminUser = bootstrapAdminUser(req);
  if (adminUser) {
    return adminUser;
  }

  const settings = getSettings();
  const token = resolveSessionToken(req, settings);
  if (!token) {
    return null;
  }

  const tokenHash = hashSessionToken(token, settings.sessionSecret);
  const user = await withClient((client) => repository.getSessionUser(client, tokenHash, new Date()));
  if (!user || user.is_disabled) {
    return null;
  }
  // Subscription gate — re-enable when plans are required for dashboard access:
  // if (options.requireActive && user.subscription_status !== "active") {
  //   return null;
  // }
  return user;
}

export async function createUserSession(userId: string, client?: pg.PoolClient): Promise<string> {
  const settings = getSettings();
  const token = generateSessionToken();
  const tokenHash = hashSessionToken(token, settings.sessionSecret);
  const expiresAt = new Date(Date.now() + settings.sessionTtlSeconds * 1000);

  const persist = async (db: pg.PoolClient) => {
    await repository.createSession(db, {
      sessionId: randomUUID(),
      userId,
      sessionTokenHash: tokenHash,
      expiresAt,
    });
  };

  if (client) {
    await persist(client);
  } else {
    await withClient(persist);
  }

  return token;
}

export async function revokeSessionFromRequest(req: Request): Promise<void> {
  const settings = getSettings();
  const token = resolveSessionToken(req, settings);
  if (!token) {
    return;
  }
  const tokenHash = hashSessionToken(token, settings.sessionSecret);
  await withClient((client) => repository.revokeSession(client, tokenHash, new Date()));
}

export async function revokeAllUserSessions(userId: string): Promise<void> {
  await withClient((client) => repository.revokeSessionsForUser(client, userId, new Date()));
}
