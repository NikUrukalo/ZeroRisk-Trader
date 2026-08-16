import bottle
from bottle import Bottle, run, template, static_file, request, response, redirect, url
from functools import wraps

from Services.auth_service import AuthService

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
        return redirect(url('login'))
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
    Prijavi uporabnika v aplikacijo. Če je prijava uspešna, ustvari piškotke o uporabniku.
    Drugače sporoči, da je prijava neuspešna.
    """
    username = request.forms.get('username')
    password = request.forms.get('password')

    prijava = auth.login_user(username, password)

    if prijava:
        response.set_cookie("user", username)
        return redirect(url('login'))
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

    try:
        auth.insert_user(username, email, password)
    except Exception:
        return template('register', user=None, success=None, error="Email or username already exists.")

    return redirect(url('login'))

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)