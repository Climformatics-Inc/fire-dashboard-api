import { getSettings } from "./config.js";

export async function sendPasswordResetEmail(recipientEmail: string, resetUrl: string): Promise<void> {
  const settings = getSettings();
  if (!settings.resendApiKey) {
    throw new Error("RESEND_API_KEY is not configured");
  }
  if (!settings.passwordResetFromEmail) {
    throw new Error("PASSWORD_RESET_FROM_EMAIL is not configured");
  }

  const payload = {
    from: settings.passwordResetFromEmail,
    to: [recipientEmail],
    subject: settings.passwordResetEmailSubject,
    html: [
      "<p>You requested a password reset for Fire Weather Dashboard.</p>",
      `<p><a href="${resetUrl}">Reset your password</a></p>`,
      `<p>This link expires in ${Math.floor(settings.passwordResetTokenTtlSeconds / 60)} minutes.</p>`,
      "<p>If you did not request this, you can ignore this email.</p>",
    ].join(""),
  };

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${settings.resendApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Resend request failed with ${response.status}`);
  }
}
