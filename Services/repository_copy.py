######################################
# repository.py
# Functions to interact with database
######################################

# libraries

import psycopg2, psycopg2.extensions, psycopg2.extras # PostgreSQL database adapter for the Python and extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # a fix for šumniki (č, š, ž) 
from psycopg2 import IntegrityError
import auth_public as auth
import datetime
import os
import bcrypt

from models import *
from typing import List # library for type hints

DB_PORT = os.environ.get('POSTGRES_PORT', 5432) # default PostgreSQL port



# class definition

class Repo:
    def __init__(self):
        self.conn = psycopg2.connect(database=auth.db, # opens a connection to PostgreSQL
                                     host=auth.host, 
                                     user=auth.user, 
                                     password=auth.password, 
                                     port=DB_PORT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # cursor to execute SQL
                                                                               # rows come back as dictionaries, not tuples 


    def create_account(self, user_name: str, email: str, password: str):
        '''
        create_account() securely registers a new user by hashing their password, 
        inserting them into app_user, creating an associated portfolio, committing 
        both operations as a single transaction, and returning the new user_id; 
        if the username or email already exists, it rolls back and returns None
        '''

        # hash the password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # try to insert a new row into app_user and portfolio
        try:
            self.cur.execute("""
                INSERT INTO app_user (user_name, email, password_hash, created_at) 
                VALUES (%s, %s, %s, NOW())
                RETURNING user_id;
            """, (user_name, email, hashed_pw)) # %s is a placeholder for the values in tuple

            user_row = self.cur.fetchone() # dictionary because of DictCursor
            user_id = user_row['user_id']

            self.cur.execute("""
                INSERT INTO portfolio (user_id, virtual_balance, created_at)
                VALUES (%s, %s, NOW())
                RETURNING portfolio_id;
            """, (user_id, 0)
            )

            portfolio_row = self.cur.fetchone()
            portfolio_id = portfolio_row['portfolio_id']

            self.conn.commit() # save all changes permanentely
            return user_id, portfolio_id

        except IntegrityError as e:
            self.conn.rollback()
            print("User already exists (username or email taken):", e)
            return None
        

    def log_in(self, username: str, password: str):
        """
            Attempts to log in a user:
            - fetches user by username
            - compares plain password with stored hash using bcrypt
            - returns user_id if login is successful
            - returns None if login fails
        """

        # fetch user from database
        self.cur.execute("""
            SELECT user_id, password_hash
            FROM app_user
            WHERE user_name = %s
        """, (username,)) # single element tuple is needed

        user_row = self.cur.fetchone()

        # if no user found, login fails
        if user_row is None:
            print("No existing user.")
            return None

        stored_hash = user_row['password_hash']
        user_id = user_row['user_id']

        # check password
        password_correct = bcrypt.checkpw(
            password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )

        if not password_correct:
            print("Incorrect password. Try again.")
            return None

        # login successful
        print("Login successful.")
        return user_id
        

    def get_all_assets(self) -> List[Asset]:
        self.cur.execute("""
            SELECT *
            FROM asset
            WHERE date_stamp = (
                SELECT DISTINCT MAX(date_stamp)
                FROM asset
            )
        """)
        
        assets = [Asset.from_dict(t) for t in self.cur.fetchall()]
        return assets


    def top_movers(self) -> List[Asset]:
        """
        Returns top 5 assets with the biggest price growth between the last two timestamps.
        """

        # get last two timestamps 
        self.cur.execute("""
            SELECT DISTINCT date_stamp, time_stamp
            FROM asset
            ORDER BY date_stamp DESC, time_stamp DESC
            LIMIT 2;
        """)

        # if there is not enough data available
        timestamps = self.cur.fetchall()
        if len(timestamps) < 2:
            return [] 

        newest = timestamps[0]
        previous = timestamps[1]

        newest_date, newest_time = newest['date_stamp'], newest['time_stamp']
        prev_date, prev_time = previous['date_stamp'], previous['time_stamp']

        # compute growth 
        self.cur.execute("""
            SELECT 
                a_new.asset_id,
                a_new.asset_name,
                a_new.asset_symbol,
                a_new.asset_type,
                a_new.price AS new_price,
                a_old.price AS old_price,
                (a_new.price - a_old.price) AS growth,
                a_new.date_stamp,
                a_new.time_stamp
            FROM asset a_new
            JOIN asset a_old
                ON a_new.asset_id = a_old.asset_id
            WHERE a_new.date_stamp = %s AND a_new.time_stamp = %s
            AND a_old.date_stamp = %s AND a_old.time_stamp = %s
            ORDER BY growth DESC
            LIMIT 5;
        """, (newest_date, newest_time, prev_date, prev_time))

        rows = self.cur.fetchall()

        # convert to Asset objects
        movers = []
        for row in rows:
            asset_dict = {
                'asset_id': row['asset_id'],
                'asset_name': row['asset_name'],
                'asset_symbol': row['asset_symbol'],
                'asset_type': row['asset_type'],
                'price': row['new_price'],
                'date_stamp': row['date_stamp'],
                'time_stamp': row['time_stamp']
            }
            movers.append(Asset.from_dict(asset_dict))

        return movers


    def show_balance(self, user_id: int) -> float:
        """
        Returns the user's current virtual balance.
        Used to display balance in the upper-right corner of the UI.
        """

        self.cur.execute("""
            SELECT virtual_balance
            FROM portfolio
            WHERE user_id = %s
        """, (user_id,))

        row = self.cur.fetchone()
        return row['virtual_balance']


    def check_balance(self, user_id: int, cost: float) -> bool:
        """
        Checks if the user has enough virtual_balance to make a trade.
        Returns True if balance >= cost, otherwise False.
        """

        self.cur.execute("""
            SELECT virtual_balance
            FROM portfolio
            WHERE user_id = %s
        """, (user_id,))

        row = self.cur.fetchone()
        balance = row['virtual_balance']

        return balance >= cost


    def change_balance_in_portfolio(self, user_id: int, amount: float, mode: str) -> None:
        """
        Updates the user's virtual_balance (increases or decreases).
        """

        if mode == "increase":
            delta = amount
        elif mode == "decrease":
            delta = -amount
        else:
            raise ValueError("mode must be 'increase' or 'decrease'")

        self.cur.execute("""
            UPDATE portfolio
            SET virtual_balance = virtual_balance + %s
            WHERE user_id = %s
        """, (delta, user_id))

        self.conn.commit()


    def insert_trade(self, portfolio_id: int, asset_symbol: str, quantity: float, trade_type: str) -> bool:
        """
        Inserts a new trade into the trade table using the newest price
        from the asset table.
        Only allows trade_type 'BUY' or 'SELL'.
        Returns True if executed successfully, False otherwise.
        """

        # validate trade_type
        if trade_type not in ("BUY", "SELL"):
            print("ERROR: Invalid trade_type. Must be BUY or SELL.\n")
            return False

        try:
            # get newest price AND asset_id
            self.cur.execute("""
                SELECT asset_id, price
                FROM asset
                WHERE asset_symbol = %s
                ORDER BY date_stamp DESC, time_stamp DESC
                LIMIT 1
            """, (asset_symbol,))

            row = self.cur.fetchone()
            if row is None:
                print(f"No price found for asset_symbol {asset_symbol}")
                return False

            asset_id = row['asset_id']
            newest_price = row['price']

            # insert trade
            self.cur.execute("""
                INSERT INTO trade (portfolio_id, asset_id, trade_type, quantity, price)
                VALUES (%s, %s, %s, %s, %s)
            """, (portfolio_id, asset_id, trade_type, quantity, newest_price))

            self.conn.commit()
            print("Trade inserted successfully.")
            return True

        except Exception as e:
            print(f"Error inserting trade: {e}")
            return False


    def calculate_avg_price(self, portfolio_id: int, asset_symbol: str) -> float:
        """
        Calculates the average buy price for the user's current position
        in the given asset. Only BUY trades are included.
        """

        # get all BUY trades for this asset using JOIN
        self.cur.execute("""
            SELECT t.quantity, t.price
            FROM trade t
            JOIN asset a ON t.asset_id = a.asset_id
            WHERE t.portfolio_id = %s
            AND a.asset_symbol = %s
            AND t.trade_type = 'BUY'
        """, (portfolio_id, asset_symbol))

        trades = self.cur.fetchall()
        if not trades:
            print(f"No BUY trades found for asset {asset_symbol}")
            return 0.0

        total_quantity = 0
        total_cost = 0

        for t in trades:
            q = float(t['quantity'])
            p = float(t['price'])
            total_quantity += q
            total_cost += q * p

        return total_cost / total_quantity


    def get_position():
        pass


    def add_new_position(self, portfolio_id: int, asset_symbol: str, quantity: float, trade_type: str) -> bool:
        """
        Creates a new position for the user in the given asset.
        Only allowed when the user does not already own the asset.
        BUY  -> create new position
        SELL -> invalid (cannot sell an asset you don't own)
        Returns True if successful, False otherwise.
        """

        try:
            # SELL cannot create a new position
            if trade_type == "SELL":
                print("Cannot SELL an asset when no position exists.")
                return False

            if trade_type != "BUY":
                print("trade_type must be BUY or SELL")
                return False

            # calculate avg_buy_price from BUY trades
            avg_buy_price = self.calculate_avg_price(portfolio_id, asset_symbol)

            # insert new position
            self.cur.execute("""
                INSERT INTO position (portfolio_id, asset_symbol, quantity, avg_buy_price)
                VALUES (%s, %s, %s, %s)
            """, (portfolio_id, asset_symbol, quantity, avg_buy_price))

            self.conn.commit()
            print("New position created successfully.")
            return True

        except Exception as e:
            print(f"Error creating new position: {e}")
            return False





    def update_position(self, portfolio_id: int, asset_symbol: str, quantity: float, trade_type: str) -> bool:
        """
        Updates an existing position when the user buys or sells an asset.
        BUY  -> increase quantity + recalc avg_buy_price
        SELL -> decrease quantity + delete position if quantity becomes 0
        """

        try:
            # get current position
            self.cur.execute("""
                SELECT quantity, avg_buy_price
                FROM position
                WHERE portfolio_id = %s AND asset_symbol = %s
            """, (portfolio_id, asset_symbol))

            pos = self.cur.fetchone()
            if pos is None:
                print("Position does not exist. Use add_new_position() instead.")
                return False

            old_quantity = float(pos['quantity'])

            # BUY logic
            if trade_type == "BUY":
                new_quantity = old_quantity + quantity
                new_avg_price = self.calculate_avg_price(portfolio_id, asset_symbol)

                self.cur.execute("""
                    UPDATE position
                    SET quantity = %s, avg_buy_price = %s
                    WHERE portfolio_id = %s AND asset_symbol = %s
                """, (new_quantity, new_avg_price, portfolio_id, asset_symbol))

                self.conn.commit()
                print("Position updated (BUY).")
                return True

            # SELL logic
            elif trade_type == "SELL":
                new_quantity = old_quantity - quantity

                if new_quantity < 0:
                    print("Error: cannot sell more than current quantity.")
                    return False

                # If user sells everything → delete position
                if new_quantity == 0:
                    self.cur.execute("""
                        DELETE FROM position
                        WHERE portfolio_id = %s AND asset_symbol = %s
                    """, (portfolio_id, asset_symbol))

                    self.conn.commit()
                    print("Position deleted (sold all).")
                    return True

                # Otherwise update quantity only
                self.cur.execute("""
                    UPDATE position
                    SET quantity = %s
                    WHERE portfolio_id = %s AND asset_symbol = %s
                """, (new_quantity, portfolio_id, asset_symbol))

                self.conn.commit()
                print("Position updated (SELL).")
                return True

            else:
                print("trade_type must be BUY or SELL")
                return False

        except Exception as e:
            print(f"Error updating position: {e}")
            return False





    def buy_asset():
        pass

    def sell_asset():
        pass

    def reward_user(self, user_id: int, amount: int):
        self.cur.execute("""
            UPDATE portfolio
            SET virtual_balance = virtual_balance + %s
            WHERE user_id = %s
        """, (amount, user_id))
        self.conn.commit()







    


        