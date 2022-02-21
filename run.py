
from bottle import run
from page.routes import *


run(host='localhost', port=8080, debug=True)
