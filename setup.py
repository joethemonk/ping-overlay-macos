
from setuptools import setup

APP = ['ping_app.py']
OPTIONS = {
    'includes': ['rumps', 'ping3'],
    'plist': {
        'LSUIElement': True,
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
