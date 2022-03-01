
import bottle
import os, sys

dirname = os.path.dirname(os.path.abspath(os.path.basename(__file__)))
sys.path = [dirname] + sys.path
os.chdir(dirname)

from src.routes import *

application = bottle.default_app()
