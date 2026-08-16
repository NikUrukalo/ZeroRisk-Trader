import bottle
from bottle import Bottle, run, template, static_file

bottle.TEMPLATE_PATH.insert(0, 'Presentation/views/')

app = Bottle()

# Serve static CSS / JS
@app.route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root='Presentation/public/')

@app.route('/')
@app.route('/login', name='login')
def login():
    return template('login', user=None, success=None, error=None)

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)