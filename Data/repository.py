######################################
# repository.py
# Functions to interact with database.
######################################

import psycopg2, psycopg2.extensions, psycopg2.extras # PostgreSQL database adapter for the Python and extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # a fix for šumniki (č, š, ž)
from Data import auth_public as auth
import os

from Data.models import *
from typing import List, Optional # library for type hints

DB_PORT = os.environ.get('POSTGRES_PORT', 5432) # default PostgreSQL port


class Repo:
    def __init__(self):
        self.conn = psycopg2.connect(database=auth.db, # opens a connection to PostgreSQL
                                     host=auth.host,
                                     user=auth.user,
                                     password=auth.password,
                                     port=DB_PORT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # cursor to execute SQL
                                                                               # rows come back as dictionaries, not tuples


    # app_user

    def insert_user(self, user_name: str, email: str, password_hash: str) -> int:
        self.cur.execute("""
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
        self.cur.execute("""
            SELECT user_id, user_name, email, password_hash, created_at
            FROM app_user
            WHERE user_name = %s
        """, (username,)) # this is single element tuple

        row = self.cur.fetchone() # returns a dictionary or None
        return App_User.from_dict(row) if row else None # turns dictionary into python object


    # portfolio 

    def insert_portfolio(self, user_id: int, initial_balance: float) -> int:
        self.cur.execute("""
            INSERT INTO portfolio (user_id, virtual_balance, created_at)
            VALUES (%s, %s, NOW())
            RETURNING portfolio_id;
        """, (user_id, initial_balance))

        portfolio_id = self.cur.fetchone()['portfolio_id']
        self.conn.commit()
        return portfolio_id

    def show_balance(self, user_id: int) -> float:
        self.cur.execute("""
            SELECT virtual_balance
            FROM portfolio
            WHERE user_id = %s
        """, (user_id,))

        dictionary = self.cur.fetchone()
        return dictionary['virtual_balance']

    def get_portfolio_id(self, user_id: int) -> Optional[int]:
        self.cur.execute('''
            SELECT portfolio_id
            FROM portfolio
            WHERE user_id = %s
        ''', (user_id,))

        dictionary = self.cur.fetchone()
        return dictionary['portfolio_id'] if dictionary else None

    def update_balance(self, user_id: int, delta: float) -> None:
        self.cur.execute("""
            UPDATE portfolio
            SET virtual_balance = virtual_balance + %s
            WHERE user_id = %s
        """, (delta, user_id))

        self.conn.commit()


    # assets 

    def get_all_assets(self) -> List[Asset]: # a list where every element is an Asset object
        self.cur.execute("""
            SELECT a.asset_id, m.asset_name, a.asset_symbol, m.asset_type,
                   a.price, a.date_stamp, a.time_stamp
            FROM asset a
            JOIN asset_master m ON a.asset_symbol = m.asset_symbol
            WHERE (a.date_stamp, a.time_stamp) = (
                SELECT date_stamp, time_stamp
                FROM asset
                ORDER BY date_stamp DESC, time_stamp DESC
                LIMIT 1
            )
        """)

        dictionary = self.cur.fetchall()
        return [Asset.from_dict(a) for a in dictionary]

    def get_latest_price(self, asset_symbol: str) -> Optional[float]:
        self.cur.execute("""
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
        self.cur.execute("""
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
        self.cur.execute("""
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
        self.cur.execute("""
            INSERT INTO trade (portfolio_id, asset_symbol, trade_type, quantity, price)
            VALUES (%s, %s, %s, %s, %s)
        """, (portfolio_id, asset_symbol, trade_type, quantity, price))

        self.conn.commit()

    def get_buy_trades(self, portfolio_id: int, asset_symbol: str) -> List[Trade]:
        self.cur.execute("""
            SELECT trade_id, portfolio_id, asset_symbol, quantity, price, trade_type, created_at
            FROM trade
            WHERE portfolio_id = %s
            AND asset_symbol = %s
            AND trade_type = 'BUY'
        """, (portfolio_id, asset_symbol))

        return [Trade.from_dict(row) for row in self.cur.fetchall()]

    def delete_all_trades_of_specific_user(self, portfolio_id: int) -> None:
        self.cur.execute("""
            DELETE FROM trade
            WHERE portfolio_id = %s
        """, (portfolio_id,))

        self.conn.commit()

    def get_trades(self, portfolio_id: int, asset_symbol: str) -> List[Trade]:
        """
        All trades (BUY and SELL) for this asset, oldest first. Used to
        figure out when a position was last fully closed and reopened.
        """
        self.cur.execute("""
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
        self.cur.execute("""
            SELECT t.trade_id, t.portfolio_id, a.asset_name, t.asset_symbol, t.quantity, t.price, t.trade_type, t.created_at
            FROM trade t
            JOIN asset_master a ON t.asset_symbol = a.asset_symbol
            WHERE portfolio_id = %s
            ORDER BY created_at DESC
        """, (portfolio_id,))
        
        return [Trade.from_dict(row) for row in self.cur.fetchall()]


    # positions 

    def get_position(self, portfolio_id: int, asset_symbol: str) -> Optional[Position]:
        self.cur.execute("""
            SELECT position_id, portfolio_id, asset_symbol, quantity, avg_buy_price
            FROM position
            WHERE portfolio_id = %s AND asset_symbol = %s
        """, (portfolio_id, asset_symbol))

        row = self.cur.fetchone()
        return Position.from_dict(row) if row else None

    def get_positions(self, portfolio_id: int) -> List[Position]:
        self.cur.execute("""
            SELECT position_id, portfolio_id, asset_symbol, quantity, avg_buy_price
            FROM position
            WHERE portfolio_id = %s 
        """, (portfolio_id,))

        rows = self.cur.fetchall()
        return [Position.from_dict(row) for row in rows]

    def insert_position(self, portfolio_id: int, asset_symbol: str,
                         quantity: float, avg_buy_price: float) -> None:
        self.cur.execute("""
            INSERT INTO position (portfolio_id, asset_symbol, quantity, avg_buy_price)
            VALUES (%s, %s, %s, %s)
        """, (portfolio_id, asset_symbol, quantity, avg_buy_price))

        self.conn.commit()

    def update_position(self, portfolio_id: int, asset_symbol: str,
                         quantity: float, avg_buy_price: float) -> None:
        self.cur.execute("""
            UPDATE position
            SET quantity = %s, avg_buy_price = %s
            WHERE portfolio_id = %s AND asset_symbol = %s
        """, (quantity, avg_buy_price, portfolio_id, asset_symbol))

        self.conn.commit()

    def delete_position(self, portfolio_id: int, asset_symbol: str) -> None:
        self.cur.execute("""
            DELETE FROM position
            WHERE portfolio_id = %s AND asset_symbol = %s
        """, (portfolio_id, asset_symbol))

        self.conn.commit()