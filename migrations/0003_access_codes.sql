CREATE TABLE IF NOT EXISTS access_codes (
    code TEXT PRIMARY KEY,
    target_plan_id TEXT NOT NULL REFERENCES plans(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO access_codes (code, target_plan_id, is_active)
VALUES
    ('sonoma_clean_power', 'basic', true),
    ('climformatics_inc', 'basic', true)
ON CONFLICT (code) DO UPDATE
SET target_plan_id = EXCLUDED.target_plan_id,
    is_active = EXCLUDED.is_active,
    updated_at = now();
