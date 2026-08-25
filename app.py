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
    url
)
from functools import wraps
import psycopg2

from Services.auth_service import AuthService
from Services.trading_services import TradingService


# Setting up the app
trading_service = TradingService()
auth = AuthService()

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
        cookie = request.get_cookie("user")

        if cookie:
            return f(*args, **kwargs)

        # bottleext.redirect() takes a bare path and turns it into an absolute
        # URL itself - do NOT wrap it in url(), or the proxy prefix ends up on
        # the Location header twice.
        return redirect('/login')

    return decorated



def parse_quantity(raw):
    """
    Turn the quantity field into a float, or raise ValueError with a message
    meant for the user.

    The old code called float(request.forms.get('quantity')) directly. An
    empty box or a typo raised
        ValueError: could not convert string to float: ''
    which Bottle turned into a 500 page with a traceback on it. Both trade
    routes already catch ValueError and show `error=str(e)`, so raising a
    readable ValueError here is all that is needed.
    """
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
        response.set_cookie("user", username)
        response.set_cookie("user_id", str(log_in.user_id))

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

        # Rollback the broken database transaction
        # so the connection works again
        auth.repo.conn.rollback()

        return template(
            'register',
            user=None,
            success=None,
            error="Registration failed. An account with this email or username already exists."
        )

    except Exception as e:

        # Rollback any other database error
        auth.repo.conn.rollback()

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

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    data = trading_service.get_overview(
        user.user_id
    )

    return template(
        'overview',
        user=username,
        success=None,
        error=None,
        **data
    )


# =========================
# TRADE
# =========================

@app.route('/trade', name='trade')
@cookie_required
def trade():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    assets = trading_service.get_all_assets()
    top_movers = trading_service.get_top_5_movers()

    return template(
        'trade',
        user=username,
        assets=assets,
        top_movers=top_movers,
        error=None,
        success=None
    )


@app.post('/trade/buy')
@cookie_required
def trade_buy():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    asset_symbol = request.forms.get('asset_symbol')

    assets = trading_service.get_all_assets()
    top_movers = trading_service.get_top_5_movers()

    try:

        # Inside the try, so a bad quantity shows the same red banner as
        # "Insufficient balance" instead of a 500 page.
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
            error=None,
            success=message
        )

    except ValueError as e:

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            error=str(e),
            success=None
        )


@app.post('/trade/sell')
@cookie_required
def trade_sell():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    asset_symbol = request.forms.get('asset_symbol')

    assets = trading_service.get_all_assets()
    top_movers = trading_service.get_top_5_movers()

    try:

        # Inside the try, so a bad quantity shows the same red banner as
        # "Insufficient balance" instead of a 500 page.
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
            error=None,
            success=message
        )

    except ValueError as e:

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            error=str(e),
            success=None
        )


# =========================
# ADD BALANCE
# =========================

@app.route('/add_balance', name='add_balance')
@cookie_required
def add_balance_get():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    balance = trading_service.get_balance(
        user.user_id
    )

    question = None
    cooldown_remaining = None

    try:

        question = trading_service.get_trivia_question(
            user.user_id
        )

    except ValueError:

        cooldown_remaining = (
            trading_service
            .get_trivia_cooldown_remaining(
                user.user_id
            )
        )

    return template(
        'add_balance',
        user=username,
        balance=balance,
        question=question,
        cooldown_remaining=cooldown_remaining,
        error=None,
        success=None
    )


@app.post('/trivia/answer')
@cookie_required
def trivia_answer_post():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    question_id = int(
        request.forms.get('question_id')
    )

    submitted_option = request.forms.get(
        'submitted_option'
    )

    error = None
    success = None
    question = None
    cooldown_remaining = None

    try:

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

        cooldown_remaining = (
            trading_service
            .get_trivia_cooldown_remaining(
                user.user_id
            )
        )

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


@app.post('/add_balance')
@cookie_required
def add_balance_post():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    try:

        amount = float(
            request.forms.get('amount')
        )

        trading_service.add_balance(
            user.user_id,
            amount
        )

        balance = trading_service.get_balance(
            user.user_id
        )

        return template(
            'add_balance',
            user=username,
            balance=balance,
            # add_balance.html reads `question` and `cooldown_remaining`.
            # Leaving them out raised NameError inside the template, so every
            # use of this route was a 500.
            question=None,
            cooldown_remaining=None,
            error=None,
            success=(
                f"Successfully added "
                f"€{amount:.2f} to your balance."
            )
        )

    except ValueError as e:

        balance = trading_service.get_balance(
            user.user_id
        )

        return template(
            'add_balance',
            user=username,
            balance=balance,
            question=None,
            cooldown_remaining=None,
            error=str(e),
            success=None
        )


# =========================
# LOGOUT
# =========================

@app.route('/logout', name='logout')
def logout():

    # Remove both user cookies
    response.set_cookie(
        "user",
        "",
        expires=0
    )

    response.set_cookie(
        "user_id",
        "",
        expires=0
    )

    return redirect('/login')


# =========================
# START APPLICATION
# =========================

if __name__ == '__main__':

    # Read the port and host from the environment so that binder/start can
    # set them without editing this file.
    run(
        app,
        host=os.environ.get("BOTTLE_HOST", "0.0.0.0"),
        port=int(os.environ.get("BOTTLE_PORT", 8080)),
        debug=os.environ.get("BOTTLE_DEBUG", "0") == "1",
        reloader=os.environ.get("BOTTLE_RELOADER", "0") == "1"
    )