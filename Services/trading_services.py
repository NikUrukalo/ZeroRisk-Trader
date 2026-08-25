from Data.repository import Repo
from Data.models import *
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta

TRIVIA_COOLDOWN_MINUTES = 60


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

    def buy_asset(self, user_id: int, asset_symbol: str, quantity: float) -> str:
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

        self.repo.insert_trade(portfolio_id, asset_symbol, quantity, price, "BUY")

        existing_position = self.repo.get_position(portfolio_id, asset_symbol)
        if existing_position is None:
            self.repo.insert_position(portfolio_id, asset_symbol, quantity, price)
        else:
            new_quantity = Decimal(str(existing_position.quantity)) + qty_dec
            new_avg_price = self._calculate_avg_buy_price(portfolio_id, asset_symbol)
            self.repo.update_position(portfolio_id, asset_symbol, new_quantity, new_avg_price)

        self.repo.update_balance(user_id, -float(cost))

        return f"Bought {quantity} {asset_symbol} at €{price:.2f} (total €{cost:.2f})."


    def sell_asset(self, user_id: int, asset_symbol: str, quantity: float) -> str:
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

        return f"Sold {quantity} {asset_symbol} at €{price:.2f} (total €{proceeds:.2f})."

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
        raw_trades = self.repo.get_all_trades(portfolio_id)[:10]

        # Dictionary mapping symbols to asset names for quick lookup
        assets = {a.asset_symbol: a.asset_name for a in self.repo.get_all_assets()}

        # Trade processing for HTML display.
        formatted_trades = []
        for t in raw_trades:
            formatted_trades.append({
                "asset_symbol": t.asset_symbol,
                "asset_name": assets.get(t.asset_symbol, t.asset_symbol),
                "trade_type": t.trade_type,
                "quantity": t.quantity,
                "price": float(t.price),
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(t.created_at, "strftime") else str(t.created_at)[:16]
            })

        return {
            "balance": float(balance),
            "positions": positions,
            "holdings_value": float(holdings_value),
            "total_value": float(total_value),
            "trades": formatted_trades,
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

    # trivia
    
    def get_trivia_question(self, user_id: int) -> dict:
        """
        Returns a random trivia question (without the correct answer)
        if the user isn't on cooldown, otherwise raises ValueError.
        """
        portfolio_id = self.repo.get_portfolio_id(user_id)

        remaining = self._trivia_cooldown_remaining(portfolio_id)
        if remaining is not None:
            raise ValueError(f"Trivia is on cooldown for {remaining} more minutes.")

        question = self.repo.get_random_trivia_question()
        if question is None:
            raise ValueError("No trivia questions available.")

        return {
            "question_id": question.question_id,
            "question_text": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "reward_amount": float(question.reward_amount),
        }

    def submit_trivia_answer(self, user_id: int, question_id: int, submitted_option: str) -> dict:
        """
        Grades the submitted answer, logs the attempt, and credits the
        portfolio's balance if correct. Returns the result.
        """
        portfolio_id = self.repo.get_portfolio_id(user_id)

        remaining = self._trivia_cooldown_remaining(portfolio_id)
        if remaining is not None:
            raise ValueError(f"Trivia is on cooldown for {remaining} more minutes.")

        question = self.repo.get_trivia_question_by_id(question_id)
        if question is None:
            raise ValueError("Trivia question not found.")

        # (submitted_option or '') - the browser sends nothing at all when no
        # radio was selected, and None.strip() is an AttributeError, which the
        # route's `except ValueError` does not catch. That was a 500 page.
        submitted = (submitted_option or '').strip().upper()
        if submitted not in ('A', 'B', 'C', 'D'):
            raise ValueError("Please choose one of the four answers.")

        was_correct = question.correct_option.strip().upper() == submitted
        self.repo.insert_trivia_attempt(portfolio_id, question_id, was_correct)

        new_balance = None
        if was_correct:
            new_balance = self.repo.credit_portfolio_balance(portfolio_id, float(question.reward_amount))

        return {
            "was_correct": was_correct,
            "correct_option": question.correct_option,
            "reward_amount": float(question.reward_amount) if was_correct else 0.0,
            "new_balance": float(new_balance) if new_balance is not None else float(self.get_balance(user_id)),
        }

    # internal helper 

    def _trivia_cooldown_remaining(self, portfolio_id):
        """
        Returns remaining cooldown in whole seconds, or None if the
        user is free to attempt trivia right now.
        """
        elapsed_seconds = self.repo.get_seconds_since_last_trivia_attempt(portfolio_id)
        if elapsed_seconds is None:              # never answered anything yet
            return None

        cooldown_seconds = TRIVIA_COOLDOWN_MINUTES * 60
        if elapsed_seconds >= cooldown_seconds:
            return None

        # Round UP, and never report 0: add_balance.html shows the cooldown box
        # with `% elif cooldown_remaining:`, and a 0 is falsy, so the last
        # minute of the wait used to render an empty card.
        remaining_minutes = (cooldown_seconds - elapsed_seconds + 59) // 60
        return max(1, remaining_minutes)

    def get_trivia_cooldown_remaining(self, user_id):
        portfolio_id = self.repo.get_portfolio_id(user_id)
        return self._trivia_cooldown_remaining(portfolio_id)