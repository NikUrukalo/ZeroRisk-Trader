"""Daily login reward.

    day 1   ->  10 EUR
    day 2   ->  12 EUR
    ...     ->  +2 per consecutive day
    day 11+ ->  30 EUR (capped)
    every 7th day: +50 EUR on top

Miss a day and the streak restarts at day 1.

The formula lives here because it is a design decision we may want to tune.
The guarantee that it is paid at most once per day lives in the database, as
UNIQUE (portfolio_id, bonus_date).
"""

from decimal import Decimal

from Data.repository import Repo

BASE_BONUS = Decimal('10.00')
STREAK_STEP = Decimal('2.00')
MAX_DAILY_BONUS = Decimal('30.00')
MILESTONE_EVERY = 7
MILESTONE_BONUS = Decimal('50.00')


def bonus_for_day(streak_day: int) -> Decimal:
    amount = min(BASE_BONUS + STREAK_STEP * (streak_day - 1), MAX_DAILY_BONUS)
    if streak_day % MILESTONE_EVERY == 0:
        amount += MILESTONE_BONUS
    return amount.quantize(Decimal('0.01'))


class StreakService:
    def __init__(self):
        self.repo = Repo()

    def status(self, user_id: int) -> dict:
        """What the streak card on the overview shows."""
        portfolio_id = self.repo.get_portfolio_id(user_id)
        state = self.repo.get_streak_state(portfolio_id)
        streak = state['login_streak']

        next_day = streak if state['claimed_today'] else (
            streak + 1 if state['streak_alive'] else 1)

        return {
            'streak': streak,
            'claimed_today': state['claimed_today'],
            'next_day': next_day,
            'next_amount': bonus_for_day(next_day),
            'days_to_milestone': (MILESTONE_EVERY - next_day % MILESTONE_EVERY)
                                 % MILESTONE_EVERY,
            'dots': MILESTONE_EVERY if (streak and streak % MILESTONE_EVERY == 0)
                    else streak % MILESTONE_EVERY,
        }

    def claim(self, user_id: int):
        """
        Award today's bonus on login. Returns a message, or None if today's
        bonus was already given.
        """
        portfolio_id = self.repo.get_portfolio_id(user_id)
        if portfolio_id is None:
            return None

        state = self.repo.get_streak_state(portfolio_id)
        if state['claimed_today']:
            return None

        streak_day = state['login_streak'] + 1 if state['streak_alive'] else 1
        amount = bonus_for_day(streak_day)

        if self.repo.award_daily_bonus(portfolio_id, amount, streak_day) is None:
            return None

        message = (f"Welcome back! Day {streak_day} of your streak "
                   f"earned you EUR {amount:.2f}.")
        if streak_day % MILESTONE_EVERY == 0:
            message += f" That includes a EUR {MILESTONE_BONUS:.2f} weekly milestone."
        return message
