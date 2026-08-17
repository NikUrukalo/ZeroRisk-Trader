from Data.repository import Repo
from Data.models import *
from typing import List
from decimal import Decimal


class TradingService:
    def __init__(self) -> None:
        self.repo = Repo()

    # assets 

    def get_all_assets(self) -> List[Asset]:
        return self.repo.get_all_assets()

    # balance 

    def get_balance(self, user_id: int) -> Decimal:
        balance = self.repo.show_balance(user_id)
        return Decimal(str(balance)) if balance is not None else Decimal("0.00")

    def add_balance(self, user_id: int, amount: float) -> None:
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
            # Safely convert database ORM attributes to Decimal
            current_price = Decimal(str(self.repo.get_latest_price(p.asset_symbol)))
            quantity = Decimal(str(p.quantity))
            avg_buy_price = Decimal(str(p.avg_buy_price))

            current_value = current_price * quantity
            growth_amount = (current_price - avg_buy_price) * quantity
            
            if avg_buy_price > 0:
                growth_percent = ((current_price - avg_buy_price) / avg_buy_price) * Decimal("100")
            else:
                growth_percent = Decimal("0.00")

            result.append({
                "asset_symbol": p.asset_symbol,
                "quantity": float(quantity),
                "avg_buy_price": float(avg_buy_price),
                "current_price": float(current_price),
                "current_value": float(current_value),
                "growth_amount": float(growth_amount),
                "growth_percent": float(growth_percent),
            })

        return result

    def get_total_assets_value(self, user_id: int) -> float:
        positions = self.get_positions(user_id)
        return sum(p["current_value"] for p in positions)

    # trading 

    def buy_asset(self, user_id: int, asset_symbol: str, quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        qty_dec = Decimal(str(quantity))
        portfolio_id = self.repo.get_portfolio_id(user_id)

        raw_price = self.repo.get_latest_price(asset_symbol)
        if raw_price is None:
            raise ValueError(f"No price data available for {asset_symbol}.")
        price = Decimal(str(raw_price))

        cost = price * qty_dec
        balance = Decimal(str(self.repo.show_balance(user_id)))
        if balance < cost:
            raise ValueError("Insufficient balance for this trade.")

        existing_position = self.repo.get_position(portfolio_id, asset_symbol)

        self.repo.insert_trade(portfolio_id, asset_symbol, quantity, price, "BUY")

        if existing_position is None:
            self.repo.insert_position(portfolio_id, asset_symbol, quantity, price)
        else:
            new_quantity = Decimal(str(existing_position.quantity)) + qty_dec
            new_avg_price = self._calculate_avg_buy_price(portfolio_id, asset_symbol)
            self.repo.update_position(portfolio_id, asset_symbol, new_quantity, new_avg_price)

        self.repo.update_balance(user_id, -float(cost))

    def sell_asset(self, user_id: int, asset_symbol: str, quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        qty_dec = Decimal(str(quantity))
        portfolio_id = self.repo.get_portfolio_id(user_id)
        position = self.repo.get_position(portfolio_id, asset_symbol)

        if position is None or Decimal(str(position.quantity)) < qty_dec:
            raise ValueError("You don't own enough of this asset.")

        raw_price = self.repo.get_latest_price(asset_symbol)
        if raw_price is None:
            raise ValueError(f"No price data available for {asset_symbol}.")
        price = Decimal(str(raw_price))

        proceeds = price * qty_dec
        self.repo.insert_trade(portfolio_id, asset_symbol, quantity, price, "SELL")

        remaining_quantity = Decimal(str(position.quantity)) - qty_dec
        if remaining_quantity < Decimal("1e-9"):
            self.repo.delete_position(portfolio_id, asset_symbol)
        else:
            self.repo.update_position(portfolio_id, asset_symbol, remaining_quantity, position.avg_buy_price)

        self.repo.update_balance(user_id, float(proceeds))

    # internal helper 

    def _calculate_avg_buy_price(self, portfolio_id: int, asset_symbol: str) -> float:
        all_trades = self.repo.get_trades(portfolio_id, asset_symbol)

        running_quantity = Decimal("0.0")
        reset_index = 0
        for i, t in enumerate(all_trades):
            trade_qty = Decimal(str(t.quantity))
            running_quantity += trade_qty if t.trade_type == "BUY" else -trade_qty
            if abs(running_quantity) < Decimal("1e-9"):
                reset_index = i + 1

        current_streak_buys = [t for t in all_trades[reset_index:] if t.trade_type == "BUY"]

        total_quantity = sum(Decimal(str(t.quantity)) for t in current_streak_buys)
        total_cost = sum(Decimal(str(t.quantity)) * Decimal(str(t.price)) for t in current_streak_buys)

        if total_quantity == Decimal("0"):
            return 0.0

        return float(total_cost / total_quantity)

    def get_overview(self, user_id: int) -> dict:
        balance = self.get_balance(user_id)
        positions = self.get_positions(user_id)

        holdings_value = sum(Decimal(str(p["current_value"])) for p in positions) if positions else Decimal("0.00")
        total_value = balance + holdings_value

        portfolio_id = self.repo.get_portfolio_id(user_id)
        trades = self.repo.get_all_trades(portfolio_id)

        return {
            "balance": float(balance),
            "positions": positions,
            "holdings_value": float(holdings_value),
            "total_value": float(total_value),
            "trades": trades[:10],
        }

    def get_top_5_movers(self) -> List[dict]:
        timestamps = self.repo.get_latest_two_timestamps()
        if len(timestamps) < 2:
            return []

        latest = timestamps[0]
        previous = timestamps[1]
        latest_assets = self.repo.get_assets_by_timestamp(
            latest["date_stamp"],
            latest["time_stamp"]
        )
        previous_assets = self.repo.get_assets_by_timestamp(
            previous["date_stamp"],
            previous["time_stamp"]
        )
        previous_prices = {
            asset.asset_symbol: Decimal(str(asset.price))
            for asset in previous_assets
        }

        movers = []
        for asset in latest_assets:
            price = Decimal(str(asset.price))
            previous_price = previous_prices.get(asset.asset_symbol)
            if previous_price is None or previous_price == Decimal("0"):
                continue
            movement = ((price - previous_price) / previous_price) * Decimal("100")
            movers.append({
                "asset_name": asset.asset_name,
                "asset_symbol": asset.asset_symbol,
                "price": float(price),
                "previous_price": float(previous_price),
                "movement": float(movement)
            })
        movers.sort(
            key=lambda x: abs(x["movement"]),
            reverse=True
        )
        return movers[:5]