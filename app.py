import bottle
from bottle import Bottle, run, template, static_file, request, response, redirect
from functools import wraps

from Services.auth_service import AuthService
from Services.trading_services import TradingService

trading_service = TradingService()
auth = AuthService()

bottle.TEMPLATE_PATH.insert(0, 'Presentation/views/')

app = Bottle()

def cookie_required(f):
    """
    Decorator that requires a valid cookie. If the cookie is missing,
    redirects the user to the login page.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        cookie = request.get_cookie("user")
        if cookie:
            return f(*args, **kwargs)
        return redirect('/login')
    return decorated

# Serve static CSS / JS
@app.route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root='Presentation/static/')

@app.route('/')
@app.route('/login', name='login')
def login_get():
    return template('login', user=None, success=None, error=None)

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
        return redirect('/overview')
    else:
        return template('login', user=None, success=None, error="Unsuccessful login. Wrong username or password.")


@app.route('/register', name='register')
def register_get():
    return template('register', user=None, success=None, error=None)

@app.post('/register')
def register_post():
    username = request.forms.get('username')
    email = request.forms.get('email')
    password = request.forms.get('password')

    user_id = auth.insert_user(username, email, password)

    return redirect('/login')


@app.route('/overview', name='overview')
@cookie_required
def overview():
    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)
    data = trading_service.get_overview(user.user_id)
    return template('overview', user=username, success=None, error=None, **data)


@app.route('/trade')
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
    quantity = float(request.forms.get('quantity'))

    try:
        trading_service.buy_asset(
            user.user_id,
            asset_symbol,
            quantity
        )

        return redirect('/trade')

    except ValueError as e:
        assets = trading_service.get_all_assets()
        top_movers = trading_service.get_top_5_movers()

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
    quantity = float(request.forms.get('quantity'))

    try:
        trading_service.sell_asset(
            user.user_id,
            asset_symbol,
            quantity
        )

        return redirect('/trade')

    except ValueError as e:
        assets = trading_service.get_all_assets()
        top_movers = trading_service.get_top_5_movers()

        return template(
            'trade',
            user=username,
            assets=assets,
            top_movers=top_movers,
            error=str(e),
            success=None
        )


@app.route('/add_balance')
@cookie_required
def add_balance_get():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    balance = trading_service.get_balance(user.user_id)

    return template(
        'add_balance',
        user=username,
        balance=balance,
        error=None,
        success=None
    )


@app.post('/add_balance')
@cookie_required
def add_balance_post():

    username = request.get_cookie("user")
    user = auth.get_user_by_username(username)

    try:
        amount = float(request.forms.get('amount'))

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
            error=None,
            success=f"Successfully added €{amount:.2f} to your balance."
        )

    except ValueError as e:

        balance = trading_service.get_balance(
            user.user_id
        )

        return template(
            'add_balance',
            user=username,
            balance=balance,
            error=str(e),
            success=None
        )


if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)