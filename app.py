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



if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)