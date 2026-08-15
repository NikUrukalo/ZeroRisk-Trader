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
    name : str = field(default='')
    email: str = field(default='') 
    password_hash: str = field(default='')
    created_at: datetime = field(default=None) 

@dataclass_json
@dataclass
class AppUserDto:
    user_id : int = field(default=0) 
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


### Asset
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
    asset_id: int = field(default=0)
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
    asset_id: int = field(default=0)
    quantity: float = field(default=0.0)
    average_price: float = field(default=0.0)
    created_at: datetime = field(default=None)

@dataclass_json
@dataclass
class PositionDto:
    position_id: int = field(default=0)
    asset_id: int = field(default=0)
    quantity: float = field(default=0.0)
    average_price: float = field(default=0.0)


### Trade
@dataclass_json
@dataclass
class Trade:
    trade_id: int = field(default=0)
    portfolio_id: int = field(default=0)
    asset_id: int = field(default=0)
    quantity: float = field(default=0.0)
    price: float = field(default=0.0)
    trade_type: str = field(default='')   # BUY or SELL
    created_at: datetime = field(default=None)

@dataclass_json
@dataclass
class TradeDto:
    trade_id: int = field(default=0)
    asset_id: int = field(default=0)
    quantity: float = field(default=0.0)
    price: float = field(default=0.0)
    trade_type: str = field(default='')

    