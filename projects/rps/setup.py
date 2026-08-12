from setuptools import setup
import os

APP = ['rps_gui.py']
DATA_FILES = ['rps.py']
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'RPS',
        'CFBundleShortVersionString': '0.1',
        'CFBundleVersion': '0.1',
        'CFBundleIdentifier': 'com.example.rps',
    },
}

# Add optional icon and resources only if the assets folder / icon exists
if os.path.isdir('assets'):
    OPTIONS['resources'] = ['assets']
icon_path = os.path.join('assets', 'RPS.icns')
if os.path.exists(icon_path):
    OPTIONS['iconfile'] = icon_path

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
