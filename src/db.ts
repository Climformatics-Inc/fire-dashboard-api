import pg from "pg";
import { getSettings } from "./config.js";

const { Pool } = pg;

let pool: pg.Pool | null = null;

export function getPool(): pg.Pool {
  if (pool) {
    return pool;
  }

  const settings = getSettings();
  if (!settings.databaseUrl) {
    throw new Error("DATABASE_URL is not configured");
  }

  pool = new Pool({ connectionString: settings.databaseUrl });
  return pool;
}

export async function withClient<T>(fn: (client: pg.PoolClient) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try {
    return await fn(client);
  } finally {
    client.release();
  }
}
