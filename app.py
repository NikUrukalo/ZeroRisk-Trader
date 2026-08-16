from bottle import Bottle, run, template
import bottle

bottle.TEMPLATE_PATH.insert(0, 'Presentation/views/')

app = Bottle()

@app.route('/')
@app.route('/login')
def login():
    return template('login', error=None)

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)