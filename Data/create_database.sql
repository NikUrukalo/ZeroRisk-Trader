/* Permissions */

GRANT ALL ON DATABASE sem2026_nejczi TO nikuru WITH GRANT OPTION;
GRANT ALL ON DATABASE sem2026_nejczi TO javnost WITH GRANT OPTION;
GRANT CONNECT ON DATABASE sem2026_nejczi TO nikuru;
GRANT CONNECT ON DATABASE sem2026_nejczi TO javnost;


/* Table Creation */

CREATE TABLE IF NOT EXISTS app_user (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL, -- each e-mail address can only be used once
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio (
    portfolio_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE, -- if a user is deleted, their portfolios are also deleted
    virtual_balance NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset (
    asset_id SERIAL PRIMARY KEY,
    asset_name TEXT NOT NULL,
    asset_symbol TEXT UNIQUE NOT NULL,
    asset_type TEXT NOT NULL, -- e.g., stock, bond, cryptocurrency
    price NUMERIC(10, 2) NOT NULL,
    date_stamp DATE NOT NULL,
    time_stamp TIME NOT NULL
);

CREATE TABLE IF NOT EXISTS trade (
	trade_id SERIAL PRIMARY KEY,
	portfolio_id INTEGER NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
	asset_id INTEGER NOT NULL REFERENCES asset(asset_id) ON DELETE CASCADE,
	trade_type TEXT NOT NULL CHECK (trade_type in ('BUY', 'SELL')),
	quantity NUMERIC(10, 4) NOT NULL CHECK (quantity > 0),
	price NUMERIC(10, 2) NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS position (
	position_id SERIAL PRIMARY KEY,
	portfolio_id INTEGER NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
	asset_id INTEGER NOT NULL REFERENCES asset(asset_id) ON DELETE CASCADE,
	quantity NUMERIC(10, 4) NOT NULL CHECK (quantity > 0),
	avg_buy_price NUMERIC(10, 2) NOT NULL,
	UNIQUE (portfolio_id, asset_id) -- so that we have all assets in a portfolio together
);

INSERT INTO asset (asset_name, asset_symbol, asset_type, price, date_stamp, time_stamp)
VALUES ('test_etf', 'TEST4', 'ETF', 424.2, '2026-08-12', '21:49:20');

select * from asset
