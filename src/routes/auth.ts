import { randomUUID, timingSafeEqual } from "node:crypto";
import type { PoolClient } from "pg";
import type { Request, Response } from "express";
import {
  createUserSession,
  currentUser,
  revokeSessionFromRequest,
  serializeUser,
} from "../auth.js";
import { getSettings } from "../config.js";
import { withClient } from "../db.js";
import { sendPasswordResetEmail } from "../email.js";
import * as repository from "../repository.js";
import {
  generateOneTimeToken,
  hashPassword,
  hashSessionToken,
  normalizeEmail,
  validatePassword,
  verifyPassword,
} from "../security.js";
import { bootstrapAdminToken, buildClearCookie, buildSessionCookie } from "../session.js";

function param(value: string | string[]): string {
  return Array.isArray(value) ? value[0] : value;
}


async function validPlan(client: PoolClient, planId: string) {
  const plan = await repository.getPlan(client, planId);
  return plan?.is_active ? plan : null;
}

async function validAccessCode(client: PoolClient, accessCodeValue: string) {
  const accessCode = await repository.getAccessCode(client, accessCodeValue);
  return accessCode?.is_active ? accessCode : null;
}

function setSessionHeaders(res: Response, token: string) {
  // HttpOnly cookie only — do not expose session tokens to JavaScript via headers.
  res.setHeader("Set-Cookie", buildSessionCookie(token));
}

function safeEqualString(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  if (leftBuffer.length !== rightBuffer.length) {
    return false;
  }
  return timingSafeEqual(leftBuffer, rightBuffer);
}

function error(res: Response, statusCode: number, code: string, message?: string) {
  const payload: Record<string, string> = { error: code };
  if (message) {
    payload.message = message;
  }
  return res.status(statusCode).json(payload);
}

async function requireAdmin(req: Request, res: Response) {
  const user = await currentUser(req, { requireActive: false });
  if (!user?.is_admin) {
    error(res, 403, "forbidden");
    return null;
  }
  return user;
}

async function issuePasswordReset(user: { id: string; email: string }) {
  const settings = getSettings();
  if (!settings.frontendOrigin) {
    throw new Error("FRONTEND_ORIGIN is not configured");
  }

  const rawToken = generateOneTimeToken();
  const tokenHash = hashSessionToken(rawToken, settings.sessionSecret);
  const expiresAt = new Date(Date.now() + settings.passwordResetTokenTtlSeconds * 1000);

  await withClient(async (client) => {
    await repository.invalidatePasswordResetTokensForUser(client, user.id);
    await repository.createPasswordResetToken(client, {
      tokenId: randomUUID(),
      userId: user.id,
      tokenHash,
      expiresAt,
    });
  });

  const resetUrl = `${settings.frontendOrigin.replace(/\/$/, "")}/reset-password?token=${rawToken}`;
  await sendPasswordResetEmail(user.email, resetUrl);
}

export async function handleSignup(req: Request, res: Response) {
  const email = normalizeEmail(String(req.body.email ?? ""));
  const password = String(req.body.password ?? "");

  if (!email || !email.includes("@")) {
    return error(res, 400, "invalid_email");
  }

  const passwordError = validatePassword(password);
  if (passwordError) {
    return error(res, 400, "invalid_password", passwordError);
  }

  const result = await withClient(async (client) => {
    if (await repository.getUserByEmail(client, email)) {
      return null;
    }
    const created = await repository.createUser(client, {
      userId: randomUUID(),
      email,
      passwordHash: await hashPassword(password),
    });
    const userView = await repository.getUserViewById(client, created.id);
    const token = await createUserSession(created.id, client);
    return { userView, token };
  });

  if (!result?.userView) {
    return error(res, 409, "email_exists");
  }

  setSessionHeaders(res, result.token);
  return res.status(201).json({
    userId: result.userView.id,
    email: result.userView.email,
    status: "created",
    user: serializeUser(result.userView),
  });
}

export async function handleSignupAndSubscribe(req: Request, res: Response) {
  const email = normalizeEmail(String(req.body.email ?? ""));
  const password = String(req.body.password ?? "");
  const planId = String(req.body.planId ?? "");

  if (!email || !email.includes("@")) {
    return error(res, 400, "invalid_email");
  }

  const passwordError = validatePassword(password);
  if (passwordError) {
    return error(res, 400, "invalid_password", passwordError);
  }

  if (!planId) {
    return error(res, 400, "plan_required");
  }

  const now = new Date();
  const result = await withClient(async (client) => {
    if (await repository.getUserByEmail(client, email)) {
      return null;
    }
    const plan = await validPlan(client, planId);
    if (!plan) {
      return { kind: "plan_not_found" as const };
    }

    const created = await repository.createUser(client, {
      userId: randomUUID(),
      email,
      passwordHash: await hashPassword(password),
    });
    await repository.activatePlaceholderSubscription(client, {
      subscriptionId: randomUUID(),
      userId: created.id,
      planId,
      now,
    });
    const userView = await repository.getUserViewById(client, created.id);
    const token = await createUserSession(created.id, client);
    return { kind: "ok" as const, userView, token };
  });

  if (result?.kind === "plan_not_found") {
    return error(res, 404, "plan_not_found");
  }
  if (!result?.userView) {
    return error(res, 409, "email_exists");
  }

  setSessionHeaders(res, result.token);
  return res.status(201).json({ user: serializeUser(result.userView) });
}

export async function handleSignupWithAccessCode(req: Request, res: Response) {
  const email = normalizeEmail(String(req.body.email ?? ""));
  const password = String(req.body.password ?? "");
  const accessCodeValue = String(req.body.accessCode ?? "");

  if (!email || !email.includes("@")) {
    return error(res, 400, "invalid_email");
  }

  const passwordError = validatePassword(password);
  if (passwordError) {
    return error(res, 400, "invalid_password", passwordError);
  }

  if (!accessCodeValue) {
    return error(res, 400, "access_code_required");
  }

  const now = new Date();
  const result = await withClient(async (client) => {
    if (await repository.getUserByEmail(client, email)) {
      return null;
    }
    const accessCode = await validAccessCode(client, accessCodeValue);
    if (!accessCode) {
      return { kind: "invalid_access_code" as const };
    }

    const created = await repository.createUser(client, {
      userId: randomUUID(),
      email,
      passwordHash: await hashPassword(password),
    });
    await repository.activatePlaceholderSubscription(client, {
      subscriptionId: randomUUID(),
      userId: created.id,
      planId: accessCode.target_plan_id,
      now,
    });
    const userView = await repository.getUserViewById(client, created.id);
    const token = await createUserSession(created.id, client);
    return { kind: "ok" as const, userView, token };
  });

  if (result?.kind === "invalid_access_code") {
    return error(res, 400, "invalid_access_code");
  }
  if (!result?.userView) {
    return error(res, 409, "email_exists");
  }

  setSessionHeaders(res, result.token);
  return res.status(201).json({ user: serializeUser(result.userView) });
}

export async function handleSignin(req: Request, res: Response) {
  const email = normalizeEmail(String(req.body.email ?? ""));
  const password = String(req.body.password ?? "");
  const settings = getSettings();

  const adminEmail = settings.adminEmail ? normalizeEmail(settings.adminEmail) : "";
  if (adminEmail && email === adminEmail && settings.adminPassword) {
    if (!safeEqualString(password, settings.adminPassword)) {
      return error(res, 401, "invalid_credentials");
    }
    const token = bootstrapAdminToken(adminEmail, settings.sessionSecret);
    setSessionHeaders(res, token);
    return res.json({
      user: serializeUser({
        id: "bootstrap-admin",
        email: adminEmail,
        subscription_status: "active",
        plan_id: settings.adminPlanId,
        is_admin: true,
      }),
    });
  }

  const result = await withClient(async (client) => {
    const user = await repository.getUserByEmail(client, email);
    if (!user?.password_hash || !(await verifyPassword(user.password_hash, password))) {
      return { kind: "invalid_credentials" as const };
    }
    const userView = await repository.getUserViewById(client, user.id);
    if (!userView || userView.is_disabled) {
      return { kind: "user_disabled" as const };
    }
    const token = await createUserSession(user.id, client);
    return { kind: "ok" as const, userView, token };
  });

  if (result.kind === "invalid_credentials") {
    return error(res, 401, "invalid_credentials");
  }
  if (result.kind === "user_disabled") {
    return error(res, 403, "user_disabled");
  }

  setSessionHeaders(res, result.token!);
  return res.json({ user: serializeUser(result.userView!) });
}

export async function handleSignout(req: Request, res: Response) {
  await revokeSessionFromRequest(req);
  res.setHeader("Set-Cookie", buildClearCookie());
  return res.json({ status: "signed_out" });
}

export async function handleMe(req: Request, res: Response) {
  const user = await currentUser(req, { requireActive: false });
  return res.json({ user: user ? serializeUser(user) : null });
}

export async function handlePlans(_req: Request, res: Response) {
  const plans = await withClient((client) => repository.listActivePlans(client));
  return res.json({ plans });
}

export async function handlePlanSelect(req: Request, res: Response) {
  const user = await currentUser(req, { requireActive: false });
  if (!user) {
    return error(res, 401, "unauthorized");
  }

  const planId = String(req.body.planId ?? "");
  if (!planId) {
    return error(res, 400, "plan_required");
  }

  const now = new Date();
  const result = await withClient(async (client) => {
    const plan = await validPlan(client, planId);
    if (!plan) {
      return null;
    }
    await repository.activatePlaceholderSubscription(client, {
      subscriptionId: randomUUID(),
      userId: user.id,
      planId,
      now,
    });
    return repository.getUserViewById(client, user.id);
  });

  if (!result) {
    return error(res, 404, "plan_not_found");
  }

  return res.json({ user: serializeUser(result) });
}

export async function handleActivateWithAccessCode(req: Request, res: Response) {
  const user = await currentUser(req, { requireActive: false });
  if (!user) {
    return error(res, 401, "unauthorized");
  }

  const accessCodeValue = String(req.body.accessCode ?? "");
  if (!accessCodeValue) {
    return error(res, 400, "access_code_required");
  }

  const now = new Date();
  const result = await withClient(async (client) => {
    const accessCode = await validAccessCode(client, accessCodeValue);
    if (!accessCode) {
      return null;
    }
    await repository.activatePlaceholderSubscription(client, {
      subscriptionId: randomUUID(),
      userId: user.id,
      planId: accessCode.target_plan_id,
      now,
    });
    return repository.getUserViewById(client, user.id);
  });

  if (!result) {
    return error(res, 400, "invalid_access_code");
  }

  return res.json({ user: serializeUser(result) });
}

export async function handleForgotPassword(req: Request, res: Response) {
  const email = normalizeEmail(String(req.body.email ?? ""));

  if (email && email.includes("@")) {
    await withClient(async (client) => {
      const user = await repository.getUserByEmail(client, email);
      if (user && !user.is_disabled) {
        try {
          await issuePasswordReset(user);
        } catch (err) {
          if (getSettings().isProduction) {
            throw err;
          }
          console.warn("Password reset email skipped:", err);
        }
      }
    });
  }

  return res.json({ status: "password_reset_requested" });
}

export async function handleResetPassword(req: Request, res: Response) {
  const token = String(req.body.token ?? "").trim();
  const password = String(req.body.password ?? "");

  if (!token) {
    return error(res, 400, "token_required");
  }
  const passwordError = validatePassword(password);
  if (passwordError) {
    return error(res, 400, "invalid_password", passwordError);
  }

  const settings = getSettings();
  const tokenHash = hashSessionToken(token, settings.sessionSecret);
  const now = new Date();

  const result = await withClient(async (client) => {
    const resetToken = await repository.getPasswordResetToken(client, tokenHash);
    if (!resetToken) {
      return { kind: "invalid_reset_token" as const };
    }
    if (resetToken.consumed_at) {
      return { kind: "reset_token_consumed" as const };
    }
    if (new Date(resetToken.expires_at) <= now) {
      return { kind: "reset_token_expired" as const };
    }

    await repository.updateUserPassword(client, resetToken.user_id, await hashPassword(password));
    await repository.consumePasswordResetToken(client, resetToken.id, now);
    await repository.revokeSessionsForUser(client, resetToken.user_id, now);
    return { kind: "ok" as const };
  });

  if (result.kind !== "ok") {
    return error(res, 400, result.kind);
  }

  return res.json({ status: "password_reset" });
}

export async function handlePlaceholderStart(req: Request, res: Response) {
  const email = normalizeEmail(String(req.body.email ?? ""));
  const planId = String(req.body.planId ?? "");

  const result = await withClient(async (client) => {
    const user = await repository.getUserByEmail(client, email);
    const plan = await repository.getPlan(client, planId);
    return { user, plan };
  });

  if (!result.user) {
    return error(res, 404, "user_not_found");
  }
  if (!result.plan?.is_active) {
    return error(res, 404, "plan_not_found");
  }

  return res.json({ checkoutId: randomUUID(), planId, status: "started" });
}

export async function handlePlaceholderComplete(req: Request, res: Response) {
  const settings = getSettings();
  if (settings.isProduction) {
    return error(res, 403, "disabled");
  }

  const email = normalizeEmail(String(req.body.email ?? ""));
  const planId = String(req.body.planId ?? "");
  const checkoutId = String(req.body.checkoutId ?? "");

  if (!checkoutId) {
    return error(res, 400, "missing_checkout_id");
  }

  const now = new Date();
  const result = await withClient(async (client) => {
    const user = await repository.getUserByEmail(client, email);
    const plan = await repository.getPlan(client, planId);
    if (!user) {
      return { kind: "user_not_found" as const };
    }
    if (!plan?.is_active) {
      return { kind: "plan_not_found" as const };
    }

    await repository.activatePlaceholderSubscription(client, {
      subscriptionId: randomUUID(),
      userId: user.id,
      planId,
      now,
    });
    return { kind: "ok" as const };
  });

  if (result.kind === "user_not_found") {
    return error(res, 404, "user_not_found");
  }
  if (result.kind === "plan_not_found") {
    return error(res, 404, "plan_not_found");
  }

  return res.json({ status: "paid", subscriptionStatus: "active", planId });
}

export async function handleAdminUsers(req: Request, res: Response) {
  const admin = await requireAdmin(req, res);
  if (!admin) {
    return;
  }

  const users = await withClient((client) => repository.listUsers(client));
  return res.json({
    users: users.map((user) => ({
      id: user.id,
      email: user.email,
      isAdmin: Boolean(user.is_admin),
      isDisabled: Boolean(user.is_disabled),
      subscriptionStatus: user.subscription_status ?? "inactive",
      planId: user.plan_id,
      createdAt: user.createdAt ? new Date(user.createdAt).toISOString() : null,
      updatedAt: user.updatedAt ? new Date(user.updatedAt).toISOString() : null,
    })),
  });
}

export async function handleAdminDisableUser(req: Request, res: Response) {
  const admin = await requireAdmin(req, res);
  if (!admin) {
    return;
  }

  const userId = param(req.params.userId);
  const updated = await withClient(async (client) => {
    const target = await repository.getUserById(client, userId);
    if (!target) {
      return false;
    }
    await repository.setUserDisabled(client, userId, true);
    await repository.revokeSessionsForUser(client, userId, new Date());
    return true;
  });

  if (!updated) {
    return error(res, 404, "user_not_found");
  }
  return res.json({ status: "disabled" });
}

export async function handleAdminEnableUser(req: Request, res: Response) {
  const admin = await requireAdmin(req, res);
  if (!admin) {
    return;
  }

  const userId = param(req.params.userId);
  const updated = await withClient(async (client) => {
    const target = await repository.getUserById(client, userId);
    if (!target) {
      return false;
    }
    await repository.setUserDisabled(client, userId, false);
    return true;
  });

  if (!updated) {
    return error(res, 404, "user_not_found");
  }
  return res.json({ status: "enabled" });
}

export async function handleAdminDeleteUser(req: Request, res: Response) {
  const admin = await requireAdmin(req, res);
  if (!admin) {
    return;
  }

  const userId = param(req.params.userId);
  if (admin.id === userId) {
    return error(res, 400, "cannot_delete_current_admin");
  }

  const deleted = await withClient(async (client) => {
    const target = await repository.getUserById(client, userId);
    if (!target) {
      return false;
    }
    await repository.deleteUser(client, userId);
    return true;
  });

  if (!deleted) {
    return error(res, 404, "user_not_found");
  }
  return res.json({ status: "deleted" });
}

export async function handleAdminSubscription(req: Request, res: Response) {
  const admin = await requireAdmin(req, res);
  if (!admin) {
    return;
  }

  const userId = param(req.params.userId);
  const planId = String(req.body.planId ?? "");
  const status = String(req.body.status ?? "");

  if (status !== "active" && status !== "inactive") {
    return error(res, 400, "invalid_subscription_status");
  }
  if (!planId) {
    return error(res, 400, "plan_required");
  }

  const now = new Date();
  const result = await withClient(async (client) => {
    const target = await repository.getUserById(client, userId);
    if (!target) {
      return { kind: "user_not_found" as const };
    }
    const plan = await validPlan(client, planId);
    if (!plan) {
      return { kind: "plan_not_found" as const };
    }
    await repository.updateSubscriptionStatus(client, {
      userId,
      planId,
      status,
      now,
    });
    const userView = await repository.getUserViewById(client, userId);
    return { kind: "ok" as const, userView };
  });

  if (result.kind === "plan_not_found") {
    return error(res, 404, "plan_not_found");
  }
  if (result.kind === "user_not_found") {
    return error(res, 404, "user_not_found");
  }

  return res.json({ user: serializeUser(result.userView!) });
}

export async function handleAdminPasswordReset(req: Request, res: Response) {
  const admin = await requireAdmin(req, res);
  if (!admin) {
    return;
  }

  const userId = param(req.params.userId);
  const user = await withClient(async (client) => repository.getUserById(client, userId));

  if (!user) {
    return error(res, 404, "user_not_found");
  }

  if (!user.is_disabled) {
    try {
      await issuePasswordReset(user);
    } catch (err) {
      if (getSettings().isProduction) {
        throw err;
      }
      console.warn("Password reset email skipped:", err);
    }
  }

  return res.json({ status: "password_reset_requested" });
}
