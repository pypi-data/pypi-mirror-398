from pathlib import Path
import sys

from setuptools import setup

# Ensure the source tree is importable when setuptools runs this file from a
# temporary working directory (e.g. pip PEP 517 build steps).
ROOT = Path(__file__).resolve().parent
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

from aesthetic._style_install import PostInstallMoveFile

if __name__ == "__main__":
    setup(cmdclass={"install": PostInstallMoveFile})
