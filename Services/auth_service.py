from Data.repository import Repo
from Data.models import *
import bcrypt
from typing import Optional
import time
import threading
import subprocess
import sys
from pathlib import Path

class AuthService:
    repo: Repo

    LAST_REFRESH = 0          # timestamp of last refresh
    REFRESH_INTERVAL = 600    # 10 minutes

    def __init__(self):
        self.repo = Repo()

    def insert_user(self, user_name: str, email: str, password: str) -> AppUserDto:
        bytes_pw = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(bytes_pw, salt).decode('utf-8')

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

    def logout_user(self, username: str) -> None:
        """
        Handles any server-side cleanup needed during logout
        (e.g., invalidating tokens, clearing active sessions).
        """
        pass

    def _run_fill_asset(self):
        """Runs fill_asset.py as a subprocess (blocking call, meant to run in a background thread)."""
        script = Path(__file__).resolve().parent.parent / "Data" / "data_fill" / "fill_asset.py"
        subprocess.run([sys.executable, str(script)])

    def refresh_assets(self):
        """Refreshes the data if enough time has passed since the last refresh."""
        now = time.time()

        if now - AuthService.LAST_REFRESH < self.REFRESH_INTERVAL:
            return

        AuthService.LAST_REFRESH = now

        threading.Thread(target=self._run_fill_asset, daemon=True).start()