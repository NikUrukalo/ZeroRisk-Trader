/* Table Creation */

CREATE TABLE IF NOT EXISTS app_user (
    user_id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL, -- each e-mail address can only be used once
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio (
    portfolio_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES app_user(user_id) ON DELETE CASCADE, -- one portfolio per user
    virtual_balance NUMERIC(10, 2) NOT NULL CHECK (virtual_balance >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset_master (
    asset_symbol TEXT PRIMARY KEY,
    asset_name TEXT NOT NULL,
    asset_type TEXT NOT NULL -- e.g., stock, ETF, cryptocurrency
);

CREATE TABLE IF NOT EXISTS asset (
    asset_id SERIAL PRIMARY KEY,
    asset_symbol TEXT NOT NULL REFERENCES asset_master(asset_symbol) ON DELETE CASCADE,
    price NUMERIC(10, 2) NOT NULL,
    date_stamp DATE NOT NULL,
    time_stamp TIME NOT NULL
);

CREATE TABLE IF NOT EXISTS trade (
    trade_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    asset_symbol TEXT NOT NULL REFERENCES asset_master(asset_symbol) ON DELETE CASCADE,
    trade_type TEXT NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    quantity NUMERIC(10, 4) NOT NULL CHECK (quantity > 0),
    price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS position (
    position_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    asset_symbol TEXT NOT NULL REFERENCES asset_master(asset_symbol) ON DELETE CASCADE,
    quantity NUMERIC(10, 4) NOT NULL CHECK (quantity > 0),
    avg_buy_price NUMERIC(10, 2) NOT NULL,
    UNIQUE (portfolio_id, asset_symbol) -- one position per asset per portfolio
);

CREATE TABLE IF NOT EXISTS trivia_question (
    question_id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option CHAR(1) NOT NULL CHECK (correct_option IN ('A','B','C','D')),
    reward_amount NUMERIC(10, 2) NOT NULL DEFAULT 250.00
);

CREATE TABLE IF NOT EXISTS trivia_attempt (
    attempt_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES trivia_question(question_id) ON DELETE CASCADE,
    was_correct BOOLEAN NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- user_name must be unique too, case-insensitively.
CREATE UNIQUE INDEX IF NOT EXISTS app_user_user_name_key ON app_user (lower(user_name));

-- Indexes for the queries the application runs.
CREATE INDEX IF NOT EXISTS asset_symbol_time_idx ON asset (asset_symbol, date_stamp DESC, time_stamp DESC);
CREATE INDEX IF NOT EXISTS trade_portfolio_idx   ON trade (portfolio_id, created_at DESC);
CREATE INDEX IF NOT EXISTS position_portfolio_idx ON position (portfolio_id);
