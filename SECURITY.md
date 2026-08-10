# Security notes — fire-dashboard-api

## What is already solid

- **Passwords:** Argon2 hashing; plaintext passwords are never stored or logged.
- **Sessions:** Random 256-bit tokens; only HMAC-SHA256 hashes stored in Postgres.
- **SQL injection:** Parameterized queries throughout `repository.ts`.
- **Password reset:** Tokens are hashed, expire, are single-use, and all sessions are revoked after reset.
- **Forgot password:** Same response whether or not the email exists (no account enumeration on that endpoint).
- **Admin routes:** Require `is_admin` on the authenticated session.
- **Disable user:** Revokes all active sessions immediately.
- **CORS:** Locked to `FRONTEND_ORIGIN` with credentials.

## Hardening applied in code

- Production startup fails if `SESSION_SECRET` is missing, too short, or a known default.
- Rate limits on sign-in, sign-up, password reset, and admin actions.
- `helmet` security headers.
- Request body size capped at 16kb.
- Session tokens no longer returned in `X-Session-Token` or accepted in query strings.
- Frontend uses HttpOnly cookies only (removed `localStorage` session copy).
- Password max length (128) to reduce Argon2 DoS risk.
- Old password-reset tokens invalidated when a new one is issued.
- Production 500 responses no longer leak internal error messages.
- Admin password comparison uses timing-safe equality.

## Before production — required

| Item | Action |
|------|--------|
| `SESSION_SECRET` | Set a random string **≥ 32 characters** (e.g. `openssl rand -base64 48`) |
| `ENVIRONMENT` | Set to `production` |
| `FRONTEND_ORIGIN` | Exact dashboard URL (e.g. `https://dashboard.example.com`) |
| HTTPS | Terminate TLS at your reverse proxy; cookies use `Secure` in production |
| Postgres | Use a managed DB with backups enabled so accounts are not lost to disk failure |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Prefer a real DB admin user; bootstrap admin is for emergencies only |

## Remaining risks (acceptable for now / address later)

| Risk | Severity | Notes |
|------|----------|-------|
| Open signup (no email verification) | Medium | Anyone can register; add verification before public launch if needed. |
| `email_exists` on signup | Low | Reveals registered emails; can use a generic error message later. |
| No CAPTCHA | Medium | Rate limits help; add CAPTCHA if you see bot signups. |
| Bootstrap admin env login | Medium | Remove `ADMIN_PASSWORD` in prod once a DB admin exists. |
| Dashboard data API unauthenticated | High* | Auth protects the UI only; FWI API URLs are still public if known. |
| Session accumulation on re-login | Low | Old sessions expire; optional cleanup job later. |

\*The fire weather chart API is separate from this auth service. Locking that down is a follow-up if the data itself must be private.

## Account loss scenarios

Users **will not lose accounts** from normal auth operations. Accounts can only be deleted via admin `DELETE` or direct DB action. Prevent data loss with:

1. Automated Postgres backups (daily minimum).
2. Never run migrations against production without a backup.
3. Avoid sharing one DB between dev and prod.

## If a session is stolen

1. Rotate `SESSION_SECRET` (invalidates all sessions).
2. User resets password (revokes all their sessions).
3. Admin disables the account.
