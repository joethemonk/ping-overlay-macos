
from setuptools import setup

APP = ['ping_app.py']
OPTIONS = {
    'includes': ['rumps', 'ping3'],
    'iconfile': 'ping_app.icns',
    'plist': {
        'CFBundleName': 'Ping Overlay',
        'CFBundleDisplayName': 'Ping Overlay',
        'CFBundleIdentifier': 'com.joethemonk.pingoverlay',
        'CFBundleVersion': '1.0.0',
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
