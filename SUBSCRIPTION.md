# Subscription endpoints (commented out in src/index.ts)

Restore these routes when subscription/plans are enabled:

- `POST /auth/signup-and-subscribe`
- `POST /auth/signup-with-access-code`
- `GET /plans`
- `POST /plans/select`
- `POST /plans/activate-with-access-code`
- `POST /checkout/placeholder/start`
- `POST /checkout/placeholder/complete`
- `POST /admin/users/:userId/subscription`

Also uncomment in:

- `src/index.ts` — route registrations and imports
- `src/auth.ts` — `requireActive` subscription check in `currentUser`
- `src/AuthGate.tsx` (fire-dashboard) — subscription redirect to `/plans`

Handler stubs remain in `src/routes/auth.ts` as `subscriptionDisabled()` placeholders.
Full implementations live in `monthly-rain-8si-dashboard-api` if you need to copy them back.
