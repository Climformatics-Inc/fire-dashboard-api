import { randomUUID } from "node:crypto";
import type pg from "pg";
import type { SessionUser } from "./auth.js";

export type DbUser = {
  id: string;
  email: string;
  password_hash?: string;
  is_disabled: boolean;
  is_admin: boolean;
};

export type DbPlan = {
  id: string;
  name: string;
  description: string | null;
  price_cents: number;
  currency: string;
  billing_interval: string;
  is_active: boolean;
};

export async function createUser(
  client: pg.PoolClient,
  input: { userId: string; email: string; passwordHash: string }
): Promise<DbUser> {
  const result = await client.query<DbUser>(
    `
      INSERT INTO users (id, email, password_hash, password_hash_algorithm)
      VALUES ($1, $2, $3, 'argon2id')
      RETURNING id::text AS id, email, is_disabled, is_admin
    `,
    [input.userId, input.email, input.passwordHash]
  );
  return result.rows[0];
}

export async function getUserByEmail(client: pg.PoolClient, email: string): Promise<DbUser | null> {
  const result = await client.query<DbUser>(
    `
      SELECT id::text AS id, email, password_hash, is_disabled, is_admin
      FROM users
      WHERE email = $1
    `,
    [email]
  );
  return result.rows[0] ?? null;
}

export async function getUserById(client: pg.PoolClient, userId: string): Promise<DbUser | null> {
  const result = await client.query<DbUser>(
    `
      SELECT id::text AS id, email, password_hash, is_disabled, is_admin
      FROM users
      WHERE id = $1
    `,
    [userId]
  );
  return result.rows[0] ?? null;
}

export async function getUserViewById(client: pg.PoolClient, userId: string): Promise<SessionUser | null> {
  const result = await client.query<SessionUser>(
    `
      SELECT
        u.id::text AS id,
        u.email,
        u.is_disabled,
        u.is_admin,
        s.status AS subscription_status,
        s.plan_id
      FROM users u
      LEFT JOIN LATERAL (
        SELECT plan_id, status
        FROM subscriptions
        WHERE user_id = u.id
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
      ) s ON true
      WHERE u.id = $1
    `,
    [userId]
  );
  return result.rows[0] ?? null;
}

export async function listUsers(client: pg.PoolClient) {
  const result = await client.query(
    `
      SELECT
        u.id::text AS id,
        u.email,
        u.is_disabled,
        u.is_admin,
        u.created_at AS "createdAt",
        u.updated_at AS "updatedAt",
        s.status AS subscription_status,
        s.plan_id
      FROM users u
      LEFT JOIN LATERAL (
        SELECT plan_id, status
        FROM subscriptions
        WHERE user_id = u.id
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
      ) s ON true
      ORDER BY u.created_at DESC, u.id DESC
    `
  );
  return result.rows;
}

export async function listActivePlans(client: pg.PoolClient) {
  const result = await client.query(
    `
      SELECT
        id,
        name,
        description,
        price_cents AS "priceCents",
        currency,
        billing_interval AS "billingInterval"
      FROM plans
      WHERE is_active = true
      ORDER BY id
    `
  );
  return result.rows;
}

export async function getPlan(client: pg.PoolClient, planId: string): Promise<DbPlan | null> {
  const result = await client.query<DbPlan>(
    `
      SELECT id, name, description, price_cents, currency, billing_interval, is_active
      FROM plans
      WHERE id = $1
    `,
    [planId]
  );
  return result.rows[0] ?? null;
}

export async function getAccessCode(client: pg.PoolClient, code: string) {
  const result = await client.query(
    `
      SELECT code, target_plan_id, is_active
      FROM access_codes
      WHERE code = $1 COLLATE "C"
    `,
    [code]
  );
  return result.rows[0] ?? null;
}

export async function activatePlaceholderSubscription(
  client: pg.PoolClient,
  input: { subscriptionId: string; userId: string; planId: string; now: Date }
) {
  const existing = await client.query<{ id: string }>(
    `
      SELECT id::text AS id
      FROM subscriptions
      WHERE user_id = $1
      ORDER BY updated_at DESC, created_at DESC
      LIMIT 1
    `,
    [input.userId]
  );

  if (existing.rows[0]) {
    await client.query(
      `
        UPDATE subscriptions
        SET plan_id = $1,
            status = 'active',
            provider = 'placeholder',
            current_period_start = $2,
            current_period_end = NULL,
            updated_at = $2
        WHERE id = $3
      `,
      [input.planId, input.now, existing.rows[0].id]
    );
    return;
  }

  await client.query(
    `
      INSERT INTO subscriptions (
        id, user_id, plan_id, status, provider, current_period_start, current_period_end
      )
      VALUES ($1, $2, $3, 'active', 'placeholder', $4, NULL)
    `,
    [input.subscriptionId, input.userId, input.planId, input.now]
  );
}

export async function updateSubscriptionStatus(
  client: pg.PoolClient,
  input: { userId: string; planId: string; status: string; now: Date }
) {
  const existing = await client.query<{ id: string }>(
    `
      SELECT id::text AS id
      FROM subscriptions
      WHERE user_id = $1
      ORDER BY updated_at DESC, created_at DESC
      LIMIT 1
    `,
    [input.userId]
  );

  if (existing.rows[0]) {
    await client.query(
      `
        UPDATE subscriptions
        SET plan_id = $1,
            status = $2,
            provider = 'placeholder',
            current_period_start = $3,
            current_period_end = NULL,
            updated_at = $3
        WHERE id = $4
      `,
      [input.planId, input.status, input.now, existing.rows[0].id]
    );
    return;
  }

  await client.query(
    `
      INSERT INTO subscriptions (
        id, user_id, plan_id, status, provider, current_period_start, current_period_end
      )
      VALUES ($1, $2, $3, $4, 'placeholder', $5, NULL)
    `,
    [randomUUID(), input.userId, input.planId, input.status, input.now]
  );
}

export async function setUserDisabled(client: pg.PoolClient, userId: string, isDisabled: boolean) {
  await client.query(
    `
      UPDATE users
      SET is_disabled = $1,
          updated_at = now()
      WHERE id = $2
    `,
    [isDisabled, userId]
  );
}

export async function deleteUser(client: pg.PoolClient, userId: string) {
  await client.query("DELETE FROM users WHERE id = $1", [userId]);
}

export async function updateUserPassword(client: pg.PoolClient, userId: string, passwordHash: string) {
  await client.query(
    `
      UPDATE users
      SET password_hash = $1,
          password_hash_algorithm = 'argon2id',
          updated_at = now()
      WHERE id = $2
    `,
    [passwordHash, userId]
  );
}

export async function invalidatePasswordResetTokensForUser(client: pg.PoolClient, userId: string) {
  await client.query(
    `
      UPDATE password_reset_tokens
      SET consumed_at = COALESCE(consumed_at, now())
      WHERE user_id = $1
        AND consumed_at IS NULL
    `,
    [userId]
  );
}

export async function createPasswordResetToken(
  client: pg.PoolClient,
  input: { tokenId: string; userId: string; tokenHash: string; expiresAt: Date }
) {
  await client.query(
    `
      INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at)
      VALUES ($1, $2, $3, $4)
    `,
    [input.tokenId, input.userId, input.tokenHash, input.expiresAt]
  );
}

export async function getPasswordResetToken(client: pg.PoolClient, tokenHash: string) {
  const result = await client.query(
    `
      SELECT
        id::text AS id,
        user_id::text AS user_id,
        expires_at,
        consumed_at
      FROM password_reset_tokens
      WHERE token_hash = $1
    `,
    [tokenHash]
  );
  return result.rows[0] ?? null;
}

export async function consumePasswordResetToken(client: pg.PoolClient, tokenId: string, consumedAt: Date) {
  await client.query(
    `
      UPDATE password_reset_tokens
      SET consumed_at = $1
      WHERE id = $2
    `,
    [consumedAt, tokenId]
  );
}

export async function createSession(
  client: pg.PoolClient,
  input: { sessionId: string; userId: string; sessionTokenHash: string; expiresAt: Date }
) {
  await client.query(
    `
      INSERT INTO sessions (id, user_id, session_token_hash, expires_at)
      VALUES ($1, $2, $3, $4)
    `,
    [input.sessionId, input.userId, input.sessionTokenHash, input.expiresAt]
  );
}

export async function revokeSession(client: pg.PoolClient, sessionTokenHash: string, revokedAt: Date) {
  await client.query(
    `
      UPDATE sessions
      SET revoked_at = $1
      WHERE session_token_hash = $2
        AND revoked_at IS NULL
    `,
    [revokedAt, sessionTokenHash]
  );
}

export async function revokeSessionsForUser(client: pg.PoolClient, userId: string, revokedAt: Date) {
  await client.query(
    `
      UPDATE sessions
      SET revoked_at = $1
      WHERE user_id = $2
        AND revoked_at IS NULL
    `,
    [revokedAt, userId]
  );
}

export async function getSessionUser(
  client: pg.PoolClient,
  sessionTokenHash: string,
  now: Date
): Promise<SessionUser | null> {
  const result = await client.query<SessionUser>(
    `
      SELECT
        u.id::text AS id,
        u.email,
        u.is_disabled,
        u.is_admin,
        s.status AS subscription_status,
        s.plan_id
      FROM sessions sess
      JOIN users u ON u.id = sess.user_id
      LEFT JOIN LATERAL (
        SELECT plan_id, status
        FROM subscriptions
        WHERE user_id = u.id
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
      ) s ON true
      WHERE sess.session_token_hash = $1
        AND sess.revoked_at IS NULL
        AND sess.expires_at > $2
    `,
    [sessionTokenHash, now]
  );
  return result.rows[0] ?? null;
}
