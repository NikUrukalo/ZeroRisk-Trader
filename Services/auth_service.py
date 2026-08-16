from Data.repository import Repo
from Data.models import *
import bcrypt


class AuthService:
    repo : Repo
    def __init__(self):
         self.repo = Repo()

    def insert_user(self, user_name: str, email: str, password: str) -> AppUserDto:

        # Encoding the password.
        bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        
        #hashing the password
        password_hash = bcrypt.hashpw(bytes, salt)

        # Creating user and adding it to the database.
        user_id = self.repo.insert_user(user_name, email, password_hash)
        return AppUserDto(user_id=user_id, user_name=user_name, email=email)


test = AuthService().insert_user('testuser324', 'testuser324@gmail.com', 'mucki123')