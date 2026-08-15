######################################
# models.py - how the data looks like in the database
# We use dataclasses to define the structure of the data
######################################

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import datetime


### AppUser
@dataclass_json
@dataclass
class App_User:
    user_id : int = field(default=0)  # for each field we specify the type and default value
    user_name : str = field(default='')  # matches app_user.user_name in the DB
    email: str = field(default='') 
    password_hash: str = field(default='')
    created_at: datetime = field(default=None) 

@dataclass_json
@dataclass
class AppUserDto:
    user_id : int = field(default=0) 
    user_name : str = field(default='')
    email: str = field(default='') 
   

### Portfolio
@dataclass_json
@dataclass
class Portfolio:
    portfolio_id: int = field(default=0)
    user_id: int = field(default=0)
    virtual_balance: float = field(default=0.0)
    created_at: datetime = field(default=None)

@dataclass_json
@dataclass
class PortfolioDto:
    portfolio_id: int = field(default=0)
    virtual_balance: float = field(default=0)

@dataclass_json
@dataclass
class AssetMaster:
    asset_symbol: str = field(default='')
    asset_name: str = field(default='')
    asset_type: str = field(default='')

# This is the *joined* view (asset_master + asset price snapshot),
# not a 1:1 mapping to a single table anymore. The repository builds this
# by joining asset with asset_master. asset_id here is the id of the
# specific price snapshot row, not the symbol's identity.
@dataclass_json
@dataclass
class Asset:
    asset_id: int = field(default=0)
    asset_name: str = field(default='')
    asset_symbol: str = field(default='')
    asset_type: str = field(default='')
    price: float = field(default=0.0)
    date_stamp: datetime.date = field(default=None)
    time_stamp: datetime.time = field(default=None)

@dataclass_json
@dataclass
class AssetDto:
    asset_name: str = field(default='')
    asset_symbol: str = field(default='')
    asset_type: str = field(default='')
    price: float = field(default=0.0)
    date_stamp: datetime.date = field(default=None)
    time_stamp: datetime.time = field(default=None)


### Position
@dataclass_json
@dataclass
class Position:
    position_id: int = field(default=0)
    portfolio_id: int = field(default=0)
    asset_symbol: str = field(default='')  # matches position.asset_symbol in the DB
    quantity: float = field(default=0.0)
    avg_buy_price: float = field(default=0.0)  # matches position.avg_buy_price in the DB

@dataclass_json
@dataclass
class PositionDto:
    position_id: int = field(default=0)
    asset_symbol: str = field(default='')
    quantity: float = field(default=0.0)
    avg_buy_price: float = field(default=0.0)


### Trade
@dataclass_json
@dataclass
class Trade:
    trade_id: int = field(default=0)
    portfolio_id: int = field(default=0)
    asset_symbol: str = field(default='')  # matches trade.asset_symbol in the DB
    quantity: float = field(default=0.0)
    price: float = field(default=0.0)
    trade_type: str = field(default='')   # BUY or SELL
    created_at: datetime = field(default=None)

@dataclass_json
@dataclass
class TradeDto:
    trade_id: int = field(default=0)
    asset_symbol: str = field(default='')
    quantity: float = field(default=0.0)
    price: float = field(default=0.0)
    trade_type: str = field(default='')