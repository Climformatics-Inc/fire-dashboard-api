# Deploy Fire Dashboard on DigitalOcean

This project uses the same low-cost pattern as Monthly Rain 8-SI:

| Component | Product | Repo |
|-----------|---------|------|
| Frontend | App Platform **Static Site** | `fire-dashboard` |
| Auth API | **Functions** (`auth_api`) | `fire-dashboard-api` (this repo) |
| Database | Managed **Postgres** (already set up) | — |

The Node/Express app in `src/` is for **local development**. Production auth runs from `packages/fire_dashboard/auth_api/` (Python on DO Functions).

---

## 1. Create a Functions namespace (one time)

```bash
doctl auth init
doctl serverless install
doctl serverless namespaces list
```

Create a dedicated namespace (recommended):

```bash
doctl serverless namespaces create fire-dashboard --region sfo
```

Note the namespace ID (e.g. `fn-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

---

## 2. GitHub secrets (repo: `fire-dashboard-api`)

Add these under **Settings → Secrets and variables → Actions**:

| Secret | Example / notes |
|--------|-----------------|
| `DIGITALOCEAN_ACCESS_TOKEN` | DO personal access token (read + write) |
| `FUNCTIONS_NAMESPACE` | `fn-xxxxxxxx-...` from step 1 |
| `DATABASE_URL` | Fire Dashboard Postgres URL (`?sslmode=require`) |
| `FRONTEND_ORIGIN` | `https://your-frontend.ondigitalocean.app` or custom domain |
| `SESSION_SECRET` | `openssl rand -base64 48` (32+ chars) |
| `ENVIRONMENT` | `production` |
| `SESSION_COOKIE_NAME` | `fire_dashboard_session` |
| `SESSION_TTL_SECONDS` | `604800` |
| `RESEND_API_KEY` | `re_...` |
| `PASSWORD_RESET_FROM_EMAIL` | `onboarding@resend.dev` until domain verified |
| `PASSWORD_RESET_TOKEN_TTL_SECONDS` | `3600` |
| `PASSWORD_RESET_EMAIL_SUBJECT` | `Reset your Fire Weather Dashboard password` |
| `ADMIN_EMAIL` | optional bootstrap admin |
| `ADMIN_PASSWORD` | optional, 12+ chars in production |
| `ADMIN_PLAN_ID` | `pro` |

Push to `main` (or run **Deploy Functions** workflow manually) to deploy.

---

## 3. Manual deploy (without GitHub Actions)

From this repo root, with env vars exported:

```bash
export DATABASE_URL="postgresql://..."
export FRONTEND_ORIGIN="https://..."
export SESSION_SECRET="..."
export ENVIRONMENT="production"
# ... other vars from .env.example

doctl serverless connect "$FUNCTIONS_NAMESPACE"
doctl serverless deploy .
```

---

## 4. Run migrations (one time per DB)

Migrations are still applied with the Node script (local or CI):

```bash
npm install
npm run migrate
```

Use the **Fire Dashboard** Postgres `DATABASE_URL`, not Monthly Rain’s database.

---

## 5. Get the auth API URL

After deploy:

```bash
doctl serverless functions list fire_dashboard/auth_api
```

Or in the DO control panel: **Functions → your namespace → fire_dashboard → auth_api**.

The web URL looks like:

```text
https://faas-sfo3-<namespace-id>.doserverless.co/api/v1/web/fn-<namespace-id>/fire_dashboard/auth_api
```

Test:

```bash
curl "https://YOUR-AUTH-URL/" 
# {"status":"ok"}
```

---

## 6. Deploy the frontend (Static Site)

In repo `fire-dashboard`, create an App Platform app:

- **Type:** Static Site  
- **Build:** `npm install && npm run build`  
- **Output:** `dist`  
- **SPA catchall:** route all paths to `index.html`

**Build-time env vars:**

```env
VITE_USE_LOCAL_ADMIN=false
VITE_AUTH_MODE=api
VITE_AUTH_API_URL=https://YOUR-AUTH-URL-FROM-STEP-5
```

See `fire-dashboard/.do/app.yaml` for a spec template.

After the frontend URL is live, update the API secret `FRONTEND_ORIGIN` to match exactly and redeploy the function.

---

## 7. Verify end-to-end

1. Open frontend → Sign in  
2. Plans / custom access code flow  
3. Forgot password → email → `/reset-password?token=...`  
4. Sign out  

---

## Local development

**Option A — Node API (default):**

```bash
cp .env.example .env
npm install && npm run migrate && npm run dev
```

**Option B — Test Python function locally** (limited; no full DO runtime):

Handlers are in `packages/fire_dashboard/auth_api/__main__.py`. Production behavior is validated on DO after deploy.

---

## Cost

- **Functions:** free tier for low traffic (typical for early launch)  
- **Static Site:** ~$0–3/mo  
- **Postgres:** existing managed DB cost  
- **No $24/mo Web Service** required for auth  
