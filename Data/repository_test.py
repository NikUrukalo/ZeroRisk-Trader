from repository import Repo
from models import *


# V tej datoteki lahko testiramo funkcionalnost repozitorija,
# brez da zaganjamo celoten projekt.


repo = Repo()

# Get all assets
assets = repo.get_all_assets()
for t in assets:
    print(t)

repo.create_account('test_user', 'test_user', 'password')

repo.log_in('test_user', 'password_')



