from Data.repository import Repo
from Data.models import *
from typing import List

class TradingService:
    def __init__(self) -> None:
        # instance of the repository
        self.repo = Repo()

    # assets 

    def get_all_assets(self) -> List[Asset]:
        return self.repo.get_all_assets()


    # balance 

    def get_balance(self, user_id: int) -> float:
        return self.repo.show_balance(user_id)

    def add_balance(self, user_id: int, amount: float) -> None:
        """
        Used by the "add balance" button on the UI.
        """
        if amount <= 0:
            raise ValueError("Amount to add must be positive.")

        self.repo.update_balance(user_id, amount)


    # positions 

    def get_positions(self, user_id: int) -> List[dict]:
        """
        Returns the user's current assets, each with the current
        market price and growth since purchase.
        """
        portfolio_id = self.repo.get_portfolio_id(user_id)
        positions = self.repo.get_positions(portfolio_id)

        result = []
        for p in positions:
            current_price = self.repo.get_latest_price(p.asset_symbol)
            current_value = current_price * p.quantity
            growth_amount = (current_price - p.avg_buy_price) * p.quantity
            growth_percent = ((current_price - p.avg_buy_price) / p.avg_buy_price) * 100

            result.append({
                "asset_symbol": p.asset_symbol,
                "quantity": p.quantity,
                "avg_buy_price": p.avg_buy_price,
                "current_price": current_price,
                "current_value": current_value,
                "growth_amount": growth_amount,
                "growth_percent": growth_percent,
            })

        return result

    def get_total_assets_value(self, user_id: int) -> float:
        """
        Current value of every held asset 
        """
        positions = self.get_positions(user_id)
        holdings_value = sum(p["current_value"] for p in positions)

        return holdings_value


    # trading 

    def buy_asset(self, user_id: int, asset_symbol: str, quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        portfolio_id = self.repo.get_portfolio_id(user_id)

        price = self.repo.get_latest_price(asset_symbol)
        if price is None:
            raise ValueError(f"No price data available for {asset_symbol}.")

        cost = price * quantity
        balance = self.repo.show_balance(user_id)
        if balance < cost:
            raise ValueError("Insufficient balance for this trade.")

        existing_position = self.repo.get_position(portfolio_id, asset_symbol)

        # record the trade first so calculate-average-price below can see it
        self.repo.insert_trade(portfolio_id, asset_symbol, quantity, price, "BUY")

        if existing_position is None:
            self.repo.insert_position(portfolio_id, asset_symbol, quantity, price)
        else:
            new_quantity = existing_position.quantity + quantity
            new_avg_price = self._calculate_avg_buy_price(portfolio_id, asset_symbol)
            self.repo.update_position(portfolio_id, asset_symbol, new_quantity, new_avg_price)

        self.repo.update_balance(user_id, -cost)

    def sell_asset(self, user_id: int, asset_symbol: str, quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        portfolio_id = self.repo.get_portfolio_id(user_id)
        position = self.repo.get_position(portfolio_id, asset_symbol)

        if position is None or position.quantity < quantity:
            raise ValueError("You don't own enough of this asset.")

        price = self.repo.get_latest_price(asset_symbol)
        if price is None:
            raise ValueError(f"No price data available for {asset_symbol}.")

        proceeds = price * quantity
        self.repo.insert_trade(portfolio_id, asset_symbol, quantity, price, "SELL")

        remaining_quantity = position.quantity - quantity
        if remaining_quantity < 1e-9:
            self.repo.delete_position(portfolio_id, asset_symbol)
        else:
            # avg_buy_price doesn't change on a sell, only quantity shrinks
            self.repo.update_position(portfolio_id, asset_symbol, remaining_quantity, position.avg_buy_price)

        self.repo.update_balance(user_id, proceeds)


    # internal helper 

    def _calculate_avg_buy_price(self, portfolio_id: int, asset_symbol: str) -> float:
        """
        Weighted average of BUY trades made since the position was last
        fully closed (quantity hit 0). This matters because a position that
        was fully sold and later reopened shouldn't have its average price
        polluted by the earlier, already-closed-out trades - e.g. buy 2,
        sell both, buy 1 again: the average should be based only on that
        last buy, not blended with the original purchase.
        """
        all_trades = self.repo.get_trades(portfolio_id, asset_symbol)  # chronological, BUY+SELL
 
        running_quantity = 0.0
        reset_index = 0
        for i, t in enumerate(all_trades):
            running_quantity += t.quantity if t.trade_type == "BUY" else -t.quantity
            if abs(running_quantity) < 1e-9:  # fully closed out at this point
                reset_index = i + 1
 
        current_streak_buys = [t for t in all_trades[reset_index:] if t.trade_type == "BUY"]
 
        total_quantity = sum(t.quantity for t in current_streak_buys)
        total_cost = sum(t.quantity * t.price for t in current_streak_buys)
 
        return total_cost / total_quantity