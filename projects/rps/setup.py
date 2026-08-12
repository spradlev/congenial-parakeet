from setuptools import setup

APP = ['rps_gui.py']
DATA_FILES = ['rps.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'assets/RPS.icns',
    'resources': ['assets'],
    'plist': {
        'CFBundleName': 'RPS',
        'CFBundleShortVersionString': '0.1',
        'CFBundleVersion': '0.1',
        'CFBundleIdentifier': 'com.example.rps',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
