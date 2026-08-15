from repository import Repo
from models import *


# V tej datoteki lahko testiramo funkcionalnost repozitorija,
# brez da zaganjamo celoten projekt.


repo = Repo()

# Get all assets
assets = repo.get_all_assets()
for t in assets:
    print(t)