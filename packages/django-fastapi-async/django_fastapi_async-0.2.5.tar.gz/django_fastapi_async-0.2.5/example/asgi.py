"""
ASGI config for example project.
"""

import os
import sys

# Add example directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastdjango import FastDjango

os.environ.setdefault("FASTDJANGO_SETTINGS_MODULE", "settings")

app = FastDjango(settings_module="settings")
application = app.app
