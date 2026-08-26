######################################
# repository.py
# Functions to interact with database.
######################################

from contextlib import contextmanager

import psycopg2, psycopg2.extensions, psycopg2.extras # PostgreSQL database adapter for the Python and extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # a fix for šumniki (č, š, ž)
from Data import auth_public as auth
import os

from Data.models import *
from typing import List, Optional # library for type hints

DB_PORT = os.environ.get('POSTGRES_PORT', 5432) # default PostgreSQL port


class Repo:
    def __init__(self):
        self._connect()

    def _connect(self):
        self.conn = psycopg2.connect(database=auth.db,
                                     host=auth.host,
                                     user=auth.user,
                                     password=auth.password,
                                     port=DB_PORT,
                                     connect_timeout=10,
                                     keepalives=1,
                                     keepalives_idle=30)
        # rows come back as dictionaries, not tuples
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def _run(self, sql, params=()):
        """
        Run one statement.

        Rolls back on failure, so a broken query cannot leave the connection in
        the "current transaction is aborted" state where every later request
        fails too. If the connection itself died, reconnect once and retry.
        """
        try:
            self.cur.execute(sql, params)
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self._connect()
            self.cur.execute(sql, params)
        except Exception:
            try:
                self.conn.rollback()
            except Exception:
                pass
            raise

    @contextmanager
    def transaction(self):
        """Everything inside the block commits together, or not at all."""
        try:
            yield self.cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise


    # app_user

    def insert_user(self, user_name: str, email: str, password_hash: str) -> int:
        self._run("""
            INSERT INTO app_user (user_name, email, password_hash, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING user_id;
        """, (user_name, email, password_hash))

        user_id = self.cur.fetchone()['user_id']
        self.conn.commit() # apply changes 
        return user_id

    def get_user_by_username(self, username: str) -> Optional[App_User]:
        '''
            Returns:
            - AppUser object if user exists
            - None if user does not exist
        '''
        self._run("""
            SELECT user_id, user_name, email, password_hash, created_at
            FROM app_user
            WHERE user_name = %s
        """, (username,)) # this is single element tuple

        row = self.cur.fetchone() # returns a dictionary or None
        return App_User.from_dict(row) if row else None # turns dictionary into python object


    # portfolio 

    def insert_portfolio(self, user_id: int, initial_balance: float) -> int:
        self._run("""
            INSERT INTO portfolio (user_id, virtual_balance, created_at)
            VALUES (%s, %s, NOW())
            RETURNING portfolio_id;
        """, (user_id, initial_balance))

        portfolio_id = self.cur.fetchone()['portfolio_id']
        self.conn.commit()
        return portfolio_id

    def show_balance(self, user_id: int) -> float:
        self._run("""
            SELECT virtual_balance
            FROM portfolio
            WHERE user_id = %s
        """, (user_id,))

        dictionary = self.cur.fetchone()
        return dictionary['virtual_balance']

    def get_portfolio_id(self, user_id: int) -> Optional[int]:
        self._run('''
            SELECT portfolio_id
            FROM portfolio
            WHERE user_id = %s
        ''', (user_id,))

        dictionary = self.cur.fetchone()
        return dictionary['portfolio_id'] if dictionary else None

    def update_balance(self, user_id: int, delta: float) -> None:
        self._run("""
            UPDATE portfolio
            SET virtual_balance = virtual_balance + %s
            WHERE user_id = %s
        """, (delta, user_id))

        self.conn.commit()


    # assets 

    def get_all_assets(self) -> List[Asset]: # a list where every element is an Asset object
        self._run("""
            SELECT DISTINCT ON (a.asset_symbol)
                   a.asset_id, m.asset_name, a.asset_symbol, m.asset_type,
                   a.price, a.date_stamp, a.time_stamp
            FROM asset a
            JOIN asset_master m ON a.asset_symbol = m.asset_symbol
            ORDER BY a.asset_symbol, a.date_stamp DESC, a.time_stamp DESC
        """)

        dictionary = self.cur.fetchall()
        return [Asset.from_dict(a) for a in dictionary]

    def get_all_asset_symbols(self) -> List[str]:
        self._run("SELECT asset_symbol FROM asset_master ORDER BY asset_symbol")
        return [row['asset_symbol'] for row in self.cur.fetchall()]

    def insert_asset_prices(self, rows) -> int:
        """Insert one price snapshot. rows = [(symbol, price, date, time), ...]"""
        if not rows:
            return 0

        psycopg2.extras.execute_values(self.cur, """
            INSERT INTO asset (asset_symbol, price, date_stamp, time_stamp)
            VALUES %s
        """, rows)

        self.conn.commit()
        return len(rows)

    def get_latest_price(self, asset_symbol: str) -> Optional[float]:
        self._run("""
            SELECT price
            FROM asset
            WHERE asset_symbol = %s
            ORDER BY date_stamp DESC, time_stamp DESC
            LIMIT 1
        """, (asset_symbol,))

        row = self.cur.fetchone()
        return row['price'] if row else None

    def get_latest_two_timestamps(self) -> List[dict]:
        """
        Returns 2 most recent (date_stamp, time_stamp) pairs found in
        the asset table.
        """
        self._run("""
            SELECT DISTINCT date_stamp, time_stamp
            FROM asset
            ORDER BY date_stamp DESC, time_stamp DESC
            LIMIT 2;
        """)

        return self.cur.fetchall()

    def get_assets_by_timestamp(self, date_stamp, time_stamp) -> List[Asset]:
        """
        Returns every asset's price at one specific (date_stamp, time_stamp).
        """
        self._run("""
            SELECT a.asset_id, m.asset_name, a.asset_symbol, m.asset_type,
                   a.price, a.date_stamp, a.time_stamp
            FROM asset a
            JOIN asset_master m ON a.asset_symbol = m.asset_symbol
            WHERE a.date_stamp = %s AND a.time_stamp = %s
        """, (date_stamp, time_stamp))

        return [Asset.from_dict(row) for row in self.cur.fetchall()]


    # trades 

    def insert_trade(self, portfolio_id: int, asset_symbol: str, quantity: float,
                      price: float, trade_type: str) -> None:
        self._run("""
            INSERT INTO trade (portfolio_id, asset_symbol, trade_type, quantity, price)
            VALUES (%s, %s, %s, %s, %s)
        """, (portfolio_id, asset_symbol, trade_type, quantity, price))

        self.conn.commit()

    def get_buy_trades(self, portfolio_id: int, asset_symbol: str) -> List[Trade]:
        self._run("""
            SELECT trade_id, portfolio_id, asset_symbol, quantity, price, trade_type, created_at
            FROM trade
            WHERE portfolio_id = %s
            AND asset_symbol = %s
            AND trade_type = 'BUY'
        """, (portfolio_id, asset_symbol))

        return [Trade.from_dict(row) for row in self.cur.fetchall()]

    def delete_all_trades_of_specific_user(self, portfolio_id: int) -> None:
        self._run("""
            DELETE FROM trade
            WHERE portfolio_id = %s
        """, (portfolio_id,))

        self.conn.commit()

    def get_trades(self, portfolio_id: int, asset_symbol: str) -> List[Trade]:
        """
        All trades (BUY and SELL) for this asset, oldest first. Used to
        figure out when a position was last fully closed and reopened.
        """
        self._run("""
            SELECT trade_id, portfolio_id, asset_symbol, quantity, price, trade_type, created_at
            FROM trade
            WHERE portfolio_id = %s
            AND asset_symbol = %s
            ORDER BY created_at ASC
        """, (portfolio_id, asset_symbol))
 
        return [Trade.from_dict(row) for row in self.cur.fetchall()]


    def get_all_trades(self, portfolio_id: int) -> List[Trade]:
        """
                All trades (BUY and SELL) of this user newest first.
                Used to see history.
        """
        self._run("""
            SELECT t.trade_id, t.portfolio_id, a.asset_name, t.asset_symbol, t.quantity, t.price, t.trade_type, t.created_at
            FROM trade t
            JOIN asset_master a ON t.asset_symbol = a.asset_symbol
            WHERE portfolio_id = %s
            ORDER BY created_at DESC
        """, (portfolio_id,))
        
        return [Trade.from_dict(row) for row in self.cur.fetchall()]


    # positions 

    def get_position(self, portfolio_id: int, asset_symbol: str) -> Optional[Position]:
        self._run("""
            SELECT position_id, portfolio_id, asset_symbol, quantity, avg_buy_price
            FROM position
            WHERE portfolio_id = %s AND asset_symbol = %s
        """, (portfolio_id, asset_symbol))

        row = self.cur.fetchone()
        return Position.from_dict(row) if row else None

    def get_positions(self, portfolio_id: int) -> List[Position]:
        self._run("""
            SELECT position_id, portfolio_id, asset_symbol, quantity, avg_buy_price
            FROM position
            WHERE portfolio_id = %s 
        """, (portfolio_id,))

        rows = self.cur.fetchall()
        return [Position.from_dict(row) for row in rows]

    def insert_position(self, portfolio_id: int, asset_symbol: str,
                         quantity: float, avg_buy_price: float) -> None:
        self._run("""
            INSERT INTO position (portfolio_id, asset_symbol, quantity, avg_buy_price)
            VALUES (%s, %s, %s, %s)
        """, (portfolio_id, asset_symbol, quantity, avg_buy_price))

        self.conn.commit()

    def update_position(self, portfolio_id: int, asset_symbol: str,
                         quantity: float, avg_buy_price: float) -> None:
        self._run("""
            UPDATE position
            SET quantity = %s, avg_buy_price = %s
            WHERE portfolio_id = %s AND asset_symbol = %s
        """, (quantity, avg_buy_price, portfolio_id, asset_symbol))

        self.conn.commit()

    def delete_position(self, portfolio_id: int, asset_symbol: str) -> None:
        self._run("""
            DELETE FROM position
            WHERE portfolio_id = %s AND asset_symbol = %s
        """, (portfolio_id, asset_symbol))

        self.conn.commit()


    # positions + prices in one query, and atomic buy / sell

    def get_positions_with_prices(self, portfolio_id: int) -> List[dict]:
        """
        Every holding together with its current price - one query instead of
        one extra price lookup per position.
        """
        self._run("""
            SELECT p.asset_symbol,
                   m.asset_name,
                   p.quantity,
                   p.avg_buy_price,
                   lp.price AS current_price
            FROM   position p
            JOIN   asset_master m ON m.asset_symbol = p.asset_symbol
            JOIN   LATERAL (
                       SELECT a.price
                       FROM   asset a
                       WHERE  a.asset_symbol = p.asset_symbol
                       ORDER  BY a.date_stamp DESC, a.time_stamp DESC
                       LIMIT  1
                   ) lp ON TRUE
            WHERE  p.portfolio_id = %s
            ORDER  BY m.asset_name
        """, (portfolio_id,))

        return [dict(row) for row in self.cur.fetchall()]

    def execute_buy(self, user_id: int, portfolio_id: int, asset_symbol: str,
                    quantity, price, new_avg_price):
        """
        Take the money, log the trade and update the position - all or nothing.

        The balance check lives inside the UPDATE. PostgreSQL locks the row
        while it updates it, so the test and the subtraction are one step and
        two browser tabs cannot spend the same euro. If the balance was too
        low the UPDATE matches no rows and we raise.
        """
        cost = quantity * price

        with self.transaction() as cur:
            cur.execute("""
                UPDATE portfolio
                SET    virtual_balance = virtual_balance - %s
                WHERE  user_id = %s
                  AND  virtual_balance >= %s
                RETURNING virtual_balance
            """, (cost, user_id, cost))

            if cur.fetchone() is None:
                raise ValueError("Insufficient balance for this trade.")

            cur.execute("""
                INSERT INTO trade (portfolio_id, asset_symbol, trade_type, quantity, price)
                VALUES (%s, %s, 'BUY', %s, %s)
            """, (portfolio_id, asset_symbol, quantity, price))

            cur.execute("""
                SELECT position_id FROM position
                WHERE portfolio_id = %s AND asset_symbol = %s
            """, (portfolio_id, asset_symbol))

            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO position (portfolio_id, asset_symbol, quantity, avg_buy_price)
                    VALUES (%s, %s, %s, %s)
                """, (portfolio_id, asset_symbol, quantity, price))
            else:
                cur.execute("""
                    UPDATE position
                    SET    quantity = quantity + %s, avg_buy_price = %s
                    WHERE  portfolio_id = %s AND asset_symbol = %s
                """, (quantity, new_avg_price, portfolio_id, asset_symbol))

    def execute_sell(self, user_id: int, portfolio_id: int, asset_symbol: str,
                     quantity, price):
        """Mirror of execute_buy. Selling the whole holding removes the row."""
        proceeds = quantity * price

        with self.transaction() as cur:
            cur.execute("""
                SELECT quantity, avg_buy_price
                FROM   position
                WHERE  portfolio_id = %s AND asset_symbol = %s
                FOR UPDATE
            """, (portfolio_id, asset_symbol))

            row = cur.fetchone()
            if row is None or row['quantity'] < quantity:
                raise ValueError("You don't own enough of this asset.")

            remaining = row['quantity'] - quantity

            if remaining <= 0:
                cur.execute("""
                    DELETE FROM position
                    WHERE portfolio_id = %s AND asset_symbol = %s
                """, (portfolio_id, asset_symbol))
            else:
                cur.execute("""
                    UPDATE position SET quantity = %s
                    WHERE portfolio_id = %s AND asset_symbol = %s
                """, (remaining, portfolio_id, asset_symbol))

            cur.execute("""
                INSERT INTO trade (portfolio_id, asset_symbol, trade_type, quantity, price)
                VALUES (%s, %s, 'SELL', %s, %s)
            """, (portfolio_id, asset_symbol, quantity, price))

            cur.execute("""
                UPDATE portfolio SET virtual_balance = virtual_balance + %s
                WHERE user_id = %s
            """, (proceeds, user_id))

    # trivia 

    def get_random_trivia_question(self) -> Optional[TriviaQuestion]:
        self._run("""
            SELECT question_id, question_text, option_a, option_b,
                   option_c, option_d, correct_option, reward_amount
            FROM trivia_question
            ORDER BY RANDOM()
            LIMIT 1
        """)

        row = self.cur.fetchone()
        return TriviaQuestion.from_dict(row) if row else None

    def get_trivia_question_by_id(self, question_id: int) -> Optional[TriviaQuestion]:
        self._run("""
            SELECT question_id, question_text, option_a, option_b,
                   option_c, option_d, correct_option, reward_amount
            FROM trivia_question
            WHERE question_id = %s
        """, (question_id,))

        row = self.cur.fetchone()
        return TriviaQuestion.from_dict(row) if row else None

    def insert_trivia_question(self, question_text: str, option_a: str, option_b: str,
                                option_c: str, option_d: str, correct_option: str,
                                reward_amount: float = 250.00) -> int:
        self._run("""
            INSERT INTO trivia_question
                (question_text, option_a, option_b, option_c, option_d, correct_option, reward_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING question_id;
        """, (question_text, option_a, option_b, option_c, option_d, correct_option, reward_amount))

        question_id = self.cur.fetchone()['question_id']
        self.conn.commit()
        return question_id

    def get_last_trivia_attempt(self, portfolio_id: int) -> Optional[TriviaAttempt]:
        self._run("""
            SELECT attempt_id, portfolio_id, question_id, was_correct, attempted_at
            FROM trivia_attempt
            WHERE portfolio_id = %s
            ORDER BY attempted_at DESC
            LIMIT 1
        """, (portfolio_id,))

        row = self.cur.fetchone()
        return TriviaAttempt.from_dict(row) if row else None

    def get_seconds_since_last_trivia_attempt(self, portfolio_id: int) -> Optional[int]:
        """
        How long ago this portfolio last answered, measured entirely by the
        DATABASE clock. Returns None if they have never answered.

        Why not do the subtraction in Python: attempted_at is written by the
        database with CURRENT_TIMESTAMP, i.e. in the database server's local
        time (CEST). datetime.now() on Binder is UTC. Subtracting one from the
        other is off by two hours, which made the cooldown either far too long
        or negative depending on the direction. Asking PostgreSQL to subtract
        two of its own timestamps removes the second clock from the problem.
        """
        self._run("""
            SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(attempted_at)))::int AS seconds
            FROM trivia_attempt
            WHERE portfolio_id = %s
        """, (portfolio_id,))

        row = self.cur.fetchone()
        return row['seconds'] if row and row['seconds'] is not None else None

    def insert_trivia_attempt(self, portfolio_id: int, question_id: int, was_correct: bool) -> None:
        self._run("""
            INSERT INTO trivia_attempt (portfolio_id, question_id, was_correct)
            VALUES (%s, %s, %s)
        """, (portfolio_id, question_id, was_correct))

        self.conn.commit()

    def credit_portfolio_balance(self, portfolio_id: int, amount: float) -> float:
        """
        Adds `amount` to virtual_balance for a given portfolio_id and
        returns the new balance. 
        """
        self._run("""
            UPDATE portfolio
            SET virtual_balance = virtual_balance + %s
            WHERE portfolio_id = %s
            RETURNING virtual_balance;
        """, (amount, portfolio_id))

        new_balance = self.cur.fetchone()['virtual_balance']
        self.conn.commit()
        return new_balance