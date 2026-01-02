# -*- coding: utf-8 -*-
import os.path
from setuptools import setup
import shutil
from pathlib import Path
import traceback
# try:
#     from . __version__ import version
# except:
#     from __version__ import version

NAME = "gntplib"

def get_version():
    """
    Get the version of the ddf module.
    Version is taken from the __version__.py file if it exists.
    The content of __version__.py should be:
    version = "0.33"
    """
    try:
        version_file = Path(__file__).parent / "__version__.py"
        if not version_file.is_file():
            version_file = Path(__file__).parent / NAME / "__version__.py"
        if version_file.is_file():
            with open(version_file, "r") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        parts = line.split("=")
                        if len(parts) == 2:
                            return parts[1].strip().strip('"').strip("'")
    except Exception as e:
        if os.getenv('TRACEBACK') and os.getenv('TRACEBACK') in ['1', 'true', 'True']:
            print(traceback.format_exc())
        else:
            print(f"ERROR: {e}")

    return "3.0.0"


try:
    shutil.copy2("__version__.py", "gntplib/__version__.py")
except IOError:
    pass
except Exception as e:
    print("Unexpected error:", e)

here = os.path.dirname(os.path.abspath(__file__))


setup(name='gntplib',
    version=get_version(),
    description=('A Growl Notification Transport Protocol (GNTP), client library for Python 3.'),
    long_description=open(os.path.join(here, 'README.md')).read(),
    long_description_content_type="text/markdown",
    author='Hadi Cahyadi',
    author_email='cumulus13@gmail.com',
    maintainer='cumulus13',
    maintainer_email='cumulus13@gmail.com',
    url='http://github.com/cumulus13/gntplib',
    packages=['gntplib'],
    extras_require={'extra': ['tornado'], 'async': ['tornado'], 'ciphers': ['pycryptodome'], 'all': ['tornado', 'pycryptodome']},
    keywords='gntp growl async notification advanced',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    platforms='any',
    license='MIT',
    license_files=['LICENSE']
)
