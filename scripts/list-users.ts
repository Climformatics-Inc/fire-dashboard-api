import "dotenv/config";
import pg from "pg";
import { createPgClientConfig } from "../src/pg-config.js";

async function main() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is not configured in .env");
  }

  const client = new pg.Client(createPgClientConfig(databaseUrl));
  await client.connect();

  const users = await client.query(`
    SELECT
      u.email,
      u.created_at,
      COALESCE(s.status, 'none') AS subscription_status,
      s.plan_id
    FROM users u
    LEFT JOIN LATERAL (
      SELECT status, plan_id
      FROM subscriptions
      WHERE user_id = u.id
      ORDER BY updated_at DESC, created_at DESC
      LIMIT 1
    ) s ON true
    ORDER BY u.created_at DESC
    LIMIT 50
  `);

  if (users.rows.length === 0) {
    console.log("No users found.");
  } else {
    console.table(users.rows);
  }

  await client.end();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
