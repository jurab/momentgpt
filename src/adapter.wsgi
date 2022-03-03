
import bottle
import os, sys

dirname = os.path.dirname(os.path.abspath(os.path.basename(__file__))) + '/src'
sys.path = [dirname] + sys.path
os.chdir(dirname)

from routes import *

application = bottle.default_app()
