# fire-dashboard-api

Node.js port of the Monthly Rain 8-SI auth API for the Fire Weather Dashboard.

## Features

Same auth surface as `monthly-rain-8si-dashboard-api`:

- Sign up / sign in / sign out
- Session cookies and `X-Session-Token` header
- Plans and placeholder subscription checkout
- Access-code signup and activation
- Password reset (via Resend)
- Admin user management

## Stack

- Express + TypeScript
- PostgreSQL (`pg`)
- Argon2 password hashing

## Setup

```bash
cp .env.example .env
npm install
npm run migrate
npm run dev
```

The API listens on `http://localhost:3001` by default.

## Environment variables

See `.env.example`.

Required for local dev:

- `DATABASE_URL` — PostgreSQL connection string
- `FRONTEND_ORIGIN` — e.g. `http://localhost:5173`
- `SESSION_SECRET` — random secret for session tokens

Optional:

- `RESEND_API_KEY` + `PASSWORD_RESET_FROM_EMAIL` — password reset emails
- `ADMIN_EMAIL` + `ADMIN_PASSWORD` — bootstrap admin sign-in without DB user

## Wire fire-dashboard frontend

Add to fire-dashboard `.env`:

```bash
VITE_AUTH_API_URL=http://localhost:3001
```

Then replace fake `AuthGate` logic with calls to the same endpoints used by Monthly Rain (`/auth/signup`, `/auth/signin`, `/auth/me`, etc.).

## API routes

| Method | Path |
|--------|------|
| GET | `/` |
| POST | `/auth/signup` |
| POST | `/auth/signup-and-subscribe` |
| POST | `/auth/signup-with-access-code` |
| POST | `/auth/signin` |
| POST | `/auth/signout` |
| GET | `/auth/me` |
| POST | `/auth/forgot-password` |
| POST | `/auth/reset-password` |
| GET | `/plans` |
| POST | `/plans/select` |
| POST | `/plans/activate-with-access-code` |
| POST | `/checkout/placeholder/start` |
| POST | `/checkout/placeholder/complete` |
| GET | `/admin/users` |
| POST | `/admin/users/:userId/disable` |
| POST | `/admin/users/:userId/enable` |
| POST | `/admin/users/:userId/delete` |
| POST | `/admin/users/:userId/subscription` |
| POST | `/admin/users/:userId/password-reset` |

## Production

```bash
npm run build
npm start
```

Deploy as a Node service (Railway, Render, Fly.io, etc.) with `DATABASE_URL` and the env vars from `.env.example`.
