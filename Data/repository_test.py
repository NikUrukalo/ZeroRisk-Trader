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

repo.insert_trade(1, 'AAPL', 2, 'BUY')

repo.add_new_position(1, 'AAPL', 2, 'BUY')




