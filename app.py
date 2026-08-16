import bottle
from bottle import Bottle, run, template, static_file, request, response, redirect, url

from Services.auth_service import AuthService

auth = AuthService()

bottle.TEMPLATE_PATH.insert(0, 'Presentation/views/')

app = Bottle()

# Serve static CSS / JS
@app.route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root='Presentation/public/')

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
        response.set_cookie("uporabnik", username)
        return redirect(url('login'))
    else:
        return template('login', user=None, success=None, error="Unsuccessful login. Wrong username or password.")


if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)