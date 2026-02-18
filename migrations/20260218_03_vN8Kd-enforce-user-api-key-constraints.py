"""
Enforce users.api_key constraints
"""

from yoyo import step

__depends__ = {'20250612_02_xIkiy-create-images'}

steps = [
    step(
            """
            WITH ranked AS (
                SELECT
                    id,
                    api_key,
                    row_number() OVER (PARTITION BY api_key ORDER BY created_at, id) AS rn
                FROM users
            )
            UPDATE users AS u
            SET api_key = 'API-' || upper(substr(
                md5(random()::text || clock_timestamp()::text || u.id::text)
                || md5(clock_timestamp()::text || random()::text || u.id::text),
                1,
                60
            ))
            FROM ranked AS r
            WHERE u.id = r.id
              AND (u.api_key IS NULL OR u.api_key = '' OR r.rn > 1);

            ALTER TABLE users
                ALTER COLUMN api_key SET NOT NULL;

            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'users_api_key_key'
                      AND conrelid = 'users'::regclass
                ) THEN
                    ALTER TABLE users
                        ADD CONSTRAINT users_api_key_key UNIQUE (api_key);
                END IF;
            END
            $$;
            """,
            """
            ALTER TABLE users
                ALTER COLUMN api_key DROP NOT NULL;

            ALTER TABLE users
                DROP CONSTRAINT IF EXISTS users_api_key_key;
            """
    )
]
