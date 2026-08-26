import os

import bottle
from bottleext import (
    Bottle,
    run,
    template,
    static_file,
    request,
    response,
    redirect,
    url,
    set_cookie,
    get_cookie,
    clear_cookie
)
from functools import wraps
import traceback

import psycopg2
import psycopg2.errors

from Services.auth_service import AuthService
from Services.trading_services import TradingService
from Services import price_service
from Services.streak_service import StreakService


# Setting up the app
trading_service = TradingService()
auth = AuthService()
streaks = StreakService()

bottle.TEMPLATE_PATH.insert(0, 'Presentation/views/')
app = Bottle()


# Cookie
def cookie_required(f):
    """
    Decorator that requires a valid cookie.
    If the cookie is missing, redirects the user to the login page.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        cookie = get_cookie("user")

        if cookie:
            return f(*args, **kwargs)

        # redirect() takes a bare path - see bottleext.py
        return redirect('/login')

    return decorated



def parse_quantity(raw):
    """Form field -> float, or ValueError with a message for the user."""
    raw = (raw or '').strip().replace(',', '.')

    if not raw:
        raise ValueError("Please enter a quantity.")

    try:
        quantity = float(raw)
    except ValueError:
        raise ValueError(f"'{raw}' is not a valid number.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    return quantity


def quiz_error(exc):
    """
    Turn a database failure on the quiz page into something readable.

    Without this the page returns a blank "Internal Server Error" and the only
    clue is in the log. The traceback still goes to /tmp/zerorisk.log.
    """
    traceback.print_exc()

    if isinstance(exc, psycopg2.errors.InsufficientPrivilege):
        return ("The database account the app uses may not read the quiz "
                "tables. Run Data/grants.sql on the database, as the owner "
                "of those tables.")

    if isinstance(exc, psycopg2.errors.UndefinedTable):
        return ("The quiz tables are missing. Run Data/create_database.sql "
                "and Data/trivia_questions.sql on the database.")

    return ("The quiz is unavailable right now. The reason is in "
            "/tmp/zerorisk.log.")


# Static files
@app.route('/static/<filename:path>')
def serve_static(filename):
    return static_file(
        filename,
        root='Presentation/static/'
    )


# =========================
# LOGIN
# =========================

@app.route('/')
@app.route('/login', name='login')
def login_get():
    # Kick off a price refresh in the background when someone opens the app.
    # Returns straight away; the page is never held up by it.
    price_service.maybe_refresh()

    return template(
        'login',
        user=None,
        success=None,
        error=None
    )


@app.post('/login')
def login_post():
    """
    Sign in user.
    """
    username = request.forms.get('username')
    password = request.forms.get('password')

    log_in = auth.login_user(username, password)

    if log_in:
        set_cookie("user", username)
        set_cookie("user_id", log_in.user_id)

        message = streaks.claim(log_in.user_id)
        if message:
            set_cookie("flash", message)

        # auth.refresh_assets()

        return redirect('/overview')

    else:
        return template(
            'login',
            user=None,
            success=None,
            error="Unsuccessful login; wrong username or password. Please, try again."
        )


# =========================
# REGISTER
# =========================

@app.route('/register', name='register')
def register_get():
    return template(
        'register',
        user=None,
        success=None,
        error=None
    )


@app.post('/register')
def register_post():

    username = request.forms.get('username')
    email = request.forms.get('email')
    password = request.forms.get('password')

    # Catch invalid emails before hitting the database
    if '@' not in email or '.' not in email:
        return template(
            'register',
            user=None,
            success=None,
            error="Please enter a valid email address."
        )

    # Password requirements
    has_min_length = len(password) >= 8
    has_digit = any(char.isdigit() for char in password)
    has_uppercase = any(char.isupper() for char in password)

    if not (has_min_length and has_digit and has_uppercase):
        return template(
            'register',
            user=None,
            success=None,
            error="Error; password must be at least 8 characters long, contain at least one number, and one uppercase letter."
        )

    try:
        user_id = auth.insert_user(
            username,
            email,
            password
        )

        return template(
            'login',
            user=None,
            success="Account created successfully. You can now log in.",
            error=None
        )

    except psycopg2.errors.UniqueViolation:

        return template(
            'register',
            user=None,
            success=None,
            error="That username or e-mail address is already taken."
        )

    except Exception as e:

        return template(
            'register',
            user=None,
            success=None,
            error="An unexpected error occurred. Please try again."
        )


# =========================
# OVERVIEW
# =========================

@app.route('/overview', name='overview')
@cookie_required
def overview():

    username = get_cookie("user")
    user = auth.get_user_by_username(username)

    data = trading_service.get_overview(
        user.user_id
    )

    # One-shot message from the login redirect (the streak reward).
    message = get_cookie("flash")
    if message:
        clear_cookie("flash")

    return template(
        'overview',
        user=username,
        success=message,
        error=None,
        streak=streaks.status(user.user_id),
        **data
    )


# =========================
# TRADE
# =========================

@app.route('/trade', name='trade')
@cookie_required
def trade():

    username = get_cookie("user")
    user = auth.get_user_by_username(username)

    assets = trading_service.get_all_assets()
    top_movers = trading_service.get_top_5_movers()

    return template(
        'trade',
        user=username,
        assets=assets,
        top_movers=top_movers,
        prices=price_service.status(),
        error=None,
        success=None
    )


@app.post('/trade/buy')
@cookie_required
def trade_buy():

    username = get_cookie("user")
    user = auth.get_user_by_username(username)

    asset_symbol = request.forms.get('asset_symbol')

    assets = trading_service.get_all_assets()
    top_movers = trading_service.get_top_5_movers()

    try:

        quantity = parse_quantity(
            request.forms.get('quantity')
        )

        message = trading_service.buy_asset(
            user.user_id,
            asset_symbol,
            quantity
        )

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            prices=price_service.status(),
            error=None,
            success=message
        )

    except ValueError as e:

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            prices=price_service.status(),
            error=str(e),
            success=None
        )


@app.post('/trade/sell')
@cookie_required
def trade_sell():

    username = get_cookie("user")
    user = auth.get_user_by_username(username)

    asset_symbol = request.forms.get('asset_symbol')

    assets = trading_service.get_all_assets()
    top_movers = trading_service.get_top_5_movers()

    try:

        quantity = parse_quantity(
            request.forms.get('quantity')
        )

        message = trading_service.sell_asset(
            user.user_id,
            asset_symbol,
            quantity
        )

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            prices=price_service.status(),
            error=None,
            success=message
        )

    except ValueError as e:

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            prices=price_service.status(),
            error=str(e),
            success=None
        )


@app.post('/prices/refresh')
@cookie_required
def prices_refresh():
    price_service.maybe_refresh(force=True)
    return redirect('/trade')


# =========================
# ADD BALANCE
# =========================

@app.route('/add_balance', name='add_balance')
@cookie_required
def add_balance_get():

    username = get_cookie("user")
    user = auth.get_user_by_username(username)

    balance = trading_service.get_balance(
        user.user_id
    )

    question = None
    cooldown_remaining = None
    error = None

    try:

        question = trading_service.get_trivia_question(
            user.user_id
        )

    except ValueError:

        # on cooldown, or no questions in the table
        try:

            cooldown_remaining = (
                trading_service
                .get_trivia_cooldown_remaining(
                    user.user_id
                )
            )

        except Exception as exc:
            error = quiz_error(exc)

    except Exception as exc:

        # anything that is not a ValueError used to escape this route and
        # turn the whole page into a 500, so it never loaded at all
        error = quiz_error(exc)

    return template(
        'add_balance',
        user=username,
        balance=balance,
        question=question,
        cooldown_remaining=cooldown_remaining,
        error=error,
        success=None
    )


@app.post('/trivia/answer')
@cookie_required
def trivia_answer_post():

    username = get_cookie("user")
    user = auth.get_user_by_username(username)

    question_id_raw = request.forms.get('question_id')

    submitted_option = request.forms.get(
        'submitted_option'
    )

    error = None
    success = None
    question = None
    cooldown_remaining = None

    try:

        if not question_id_raw or not str(question_id_raw).strip().isdigit():
            raise ValueError(
                "That question is no longer available. Please reload the page."
            )

        question_id = int(question_id_raw)

        result = trading_service.submit_trivia_answer(
            user.user_id,
            question_id,
            submitted_option
        )

        if result['was_correct']:

            success = (
                f"Correct! You earned "
                f"€{result['reward_amount']:.2f}."
            )

        else:

            error = (
                f"Not quite — the correct answer was "
                f"{result['correct_option']}."
            )

        cooldown_remaining = (
            trading_service
            .get_trivia_cooldown_remaining(
                user.user_id
            )
        )

    except ValueError as e:

        error = str(e)

        try:

            cooldown_remaining = (
                trading_service
                .get_trivia_cooldown_remaining(
                    user.user_id
                )
            )

        except Exception as exc:
            error = quiz_error(exc)

    except Exception as exc:

        error = quiz_error(exc)

    balance = trading_service.get_balance(
        user.user_id
    )

    return template(
        'add_balance',
        user=username,
        balance=balance,
        question=question,
        cooldown_remaining=cooldown_remaining,
        error=error,
        success=success
    )


# =========================
# LOGOUT
# =========================

@app.route('/logout', name='logout')
@cookie_required
def logout_confirm():
    return template(
        'logout',
        user=get_cookie("user"),
        success=None,
        error=None
    )


@app.post('/logout')
def logout_post():
    # POST only: with a GET route any prefetch or <img src="/logout"> would
    # log the user out.
    clear_cookie("user")
    clear_cookie("user_id")

    return redirect('/login')


# =========================
# START APPLICATION
# =========================

if __name__ == '__main__':

    run(
        app,
        host=os.environ.get("BOTTLE_HOST", "0.0.0.0"),
        port=int(os.environ.get("BOTTLE_PORT", 8080)),
        debug=os.environ.get("BOTTLE_DEBUG", "0") == "1",
        reloader=os.environ.get("BOTTLE_RELOADER", "0") == "1"
    )