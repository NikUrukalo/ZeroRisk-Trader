-- Run once against an existing database, as its owner.
-- Safe to run again: it checks before it changes anything.

-- 1. user_name must be unique, case-insensitively.
--    Without this two accounts can share a name and get_user_by_username
--    returns whichever row the planner happens to pick.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM app_user
               GROUP BY lower(user_name) HAVING COUNT(*) > 1) THEN
        RAISE WARNING 'app_user has duplicate user_name values - '
                      'resolve them, then run this file again.';
    ELSE
        CREATE UNIQUE INDEX IF NOT EXISTS app_user_user_name_key
            ON app_user (lower(user_name));
    END IF;
END $$;

-- 2. One portfolio per user.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM portfolio GROUP BY user_id HAVING COUNT(*) > 1) THEN
        RAISE WARNING 'portfolio has more than one row for some user_id.';
    ELSE
        BEGIN
            ALTER TABLE portfolio ADD CONSTRAINT portfolio_user_id_key UNIQUE (user_id);
        EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
        END;
    END IF;
END $$;

-- 3. A balance can never go negative.
DO $$ BEGIN
    ALTER TABLE portfolio ADD CONSTRAINT portfolio_balance_nonneg
        CHECK (virtual_balance >= 0);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 4. Indexes for the queries the app actually runs.
CREATE INDEX IF NOT EXISTS asset_symbol_time_idx
    ON asset (asset_symbol, date_stamp DESC, time_stamp DESC);
CREATE INDEX IF NOT EXISTS trade_portfolio_idx
    ON trade (portfolio_id, created_at DESC);
CREATE INDEX IF NOT EXISTS position_portfolio_idx
    ON position (portfolio_id);
