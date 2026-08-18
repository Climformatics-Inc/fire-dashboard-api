import "dotenv/config";
import cookieParser from "cookie-parser";
import cors from "cors";
import express from "express";
import helmet from "helmet";
import { getSettings } from "./config.js";
import { adminActionLimiter, authActionLimiter, passwordResetLimiter } from "./rate-limit.js";
import {
  handleActivateWithAccessCode,
  handleAdminDeleteUser,
  handleAdminDisableUser,
  handleAdminEnableUser,
  handleAdminPasswordReset,
  handleAdminSubscription,
  handleAdminUsers,
  handleForgotPassword,
  handleMe,
  handlePlaceholderComplete,
  handlePlaceholderStart,
  handlePlanSelect,
  handlePlans,
  handleResetPassword,
  handleSignin,
  handleSignout,
  handleSignup,
  handleSignupAndSubscribe,
  handleSignupWithAccessCode,
} from "./routes/auth.js";
import { assertSecureStartupConfig } from "./startup-checks.js";

assertSecureStartupConfig();

const settings = getSettings();
const app = express();

app.set("trust proxy", 1);

app.use(
  helmet({
    crossOriginResourcePolicy: { policy: "cross-origin" },
  })
);

app.use(
  cors({
    origin(origin, callback) {
      if (!origin) {
        callback(null, true);
        return;
      }

      const allowed = settings.frontendOrigin;
      if (!settings.isProduction) {
        const isLocalDev =
          /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin) ||
          (allowed != null && origin === allowed);
        if (isLocalDev) {
          callback(null, origin);
          return;
        }
      }

      if (allowed != null && origin === allowed) {
        callback(null, origin);
        return;
      }

      callback(new Error(`CORS blocked for origin: ${origin}`));
    },
    credentials: true,
    allowedHeaders: ["Content-Type", "Accept", "Authorization", "X-Session-Token"],
  })
);
app.use(express.json({ limit: "16kb" }));
app.use(cookieParser());

app.get("/", (_req, res) => {
  res.json({ status: "ok" });
});

app.post("/auth/signup", authActionLimiter, handleSignup);
app.post("/auth/signup-and-subscribe", authActionLimiter, handleSignupAndSubscribe);
app.post("/auth/signup-with-access-code", authActionLimiter, handleSignupWithAccessCode);
app.post("/auth/signin", authActionLimiter, handleSignin);
app.post("/auth/signout", handleSignout);
app.get("/auth/me", handleMe);
app.post("/auth/forgot-password", passwordResetLimiter, handleForgotPassword);
app.post("/auth/reset-password", authActionLimiter, handleResetPassword);

app.get("/plans", handlePlans);
app.post("/plans/select", authActionLimiter, handlePlanSelect);
app.post("/plans/activate-with-access-code", authActionLimiter, handleActivateWithAccessCode);
app.post("/checkout/placeholder/start", authActionLimiter, handlePlaceholderStart);
app.post("/checkout/placeholder/complete", authActionLimiter, handlePlaceholderComplete);

app.get("/admin/users", adminActionLimiter, handleAdminUsers);
app.post("/admin/users/:userId/disable", adminActionLimiter, handleAdminDisableUser);
app.post("/admin/users/:userId/enable", adminActionLimiter, handleAdminEnableUser);
app.post("/admin/users/:userId/delete", adminActionLimiter, handleAdminDeleteUser);
app.post("/admin/users/:userId/password-reset", passwordResetLimiter, handleAdminPasswordReset);
app.post("/admin/users/:userId/subscription", adminActionLimiter, handleAdminSubscription);

app.use((error: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error(error);
  if (settings.isProduction) {
    return res.status(500).json({ error: "server_error" });
  }
  if (error instanceof Error) {
    return res.status(500).json({ error: "server_error", message: error.message });
  }
  return res.status(500).json({ error: "server_error" });
});

app.listen(settings.port, () => {
  console.log(`Fire dashboard auth API listening on http://localhost:${settings.port}`);
});
