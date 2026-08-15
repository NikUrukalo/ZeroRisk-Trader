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
        """, (username,))

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


    def top_movers():
        pass

    def balance_check(self):
        '''Checks if user has enough balance on virtual_balance to make a trade'''

    def change_balance_in_portfolio():
        '''Reduces or increases virtual_balance in user portfolio'''
        pass

    def insert_trade():
        '''Every new trade gets added to the table trade'''
        pass

    def get_position():
        pass

    def add_new_position():
        pass

    def delete_position():
        pass

    def update_position():
        pass

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







    


        