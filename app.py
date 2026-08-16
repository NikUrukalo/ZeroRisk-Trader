from bottle import Bottle, run, template

app = Bottle()

@app.route('/login')
def login():
    return template('Presentation/views/login', napaka=None)

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)