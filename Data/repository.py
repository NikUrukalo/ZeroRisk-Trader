######################################
# repository.py
# Functions to interact with database
######################################

# libraries

import psycopg2, psycopg2.extensions, psycopg2.extras # PostgreSQL database adapter for the Python and extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # a fix for šumniki (č, š, ž) 
import Data.auth_public as auth
import datetime
import os

from Data.models import App_User, Portfolio, Trade, Asset, Position
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

    def get_all_assets(self) -> ...:
        self.cur.execute("""
            SELECT asset_id, asset_name, asset_symbol, asset_type, price, date_stamp, time_stamp
            FROM asset
            WHERE date_stamp = (
                SELECT DISTINCT MAX(date_stamp)
                FROM asset
            )
        """)
        
        assets = [Asset.from_dict(t) for t in self.cur.fetchall()]
        return assets


    


        