import os
import sys

# Set path to the application directory
sys.path.insert(0, os.path.dirname(__file__))

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bahariponno.settings")

# Import the WSGI application
from bahariponno.wsgi import application
