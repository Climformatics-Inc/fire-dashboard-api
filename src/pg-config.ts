import type pg from "pg";

function usesManagedPostgres(connectionString: string): boolean {
  return (
    connectionString.includes("ondigitalocean.com") ||
    connectionString.includes("sslmode=require") ||
    process.env.DATABASE_SSL === "true"
  );
}

export function createPgClientConfig(connectionString: string): pg.ClientConfig {
  if (!usesManagedPostgres(connectionString)) {
    return { connectionString };
  }

  const normalized = connectionString
    .replace(/([?&])sslmode=[^&]*&?/g, "$1")
    .replace(/[?&]$/, "");

  return {
    connectionString: normalized,
    ssl: { rejectUnauthorized: false },
  };
}
