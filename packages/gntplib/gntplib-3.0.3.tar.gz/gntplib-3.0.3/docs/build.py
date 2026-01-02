# build_docs.py
from sphinxcolor.colorizer import install_hook
install_hook()

# import os
import subprocess
import sys

subprocess.run([
    sys.executable, "-m", "sphinx",
    "-b", "html",
    "docs",
    "docs/_build"
], check=True)