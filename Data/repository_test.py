from repository import Repo
from models import *


repo = Repo()

# Get all assets
assets = repo.get_all_assets()
for t in assets:
    print(t)





