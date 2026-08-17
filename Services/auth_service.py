from Data.repository import Repo
from Data.models import *
import bcrypt
from datetime import date
from typing import Optional


class AuthService:
    repo : Repo
    def __init__(self):
         self.repo = Repo()

    def insert_user(self, user_name: str, email: str, password: str) -> AppUserDto:

        # Encoding the password.
        bytes_pw = password.encode('utf-8')
        salt = bcrypt.gensalt()
    
        # Hashing the password, then decode back to str for DB storage.
        password_hash = bcrypt.hashpw(bytes_pw, salt).decode('utf-8')

        # Creating user and adding it to app_user and portfolio tables
        user_id = self.repo.insert_user(user_name, email, password_hash)
        self.repo.insert_portfolio(user_id, 0)

        return AppUserDto(user_id=user_id, user_name=user_name, email=email)


    
    def get_user_by_username(self, user_name: str) -> Optional[App_User]:
        return self.repo.get_user_by_username(user_name)
        


    def login_user(self, app_user: str, password: str) -> AppUserDto | bool:
        user = self.repo.get_user_by_username(app_user)

        if user is None:
            return False

        password_bytes = password.encode('utf-8')
        succ = bcrypt.checkpw(password_bytes, user.password_hash.encode('utf-8'))

        if succ:
            return AppUserDto(user_id=user.user_id, user_name=user.user_name, email=user.email)

        return False 


    