"""Helpers for copying the packaged style sheets into matplotlib's stylelib."""

import os
from importlib import resources

from setuptools.command.install import install

STYLE_PACKAGE = "aesthetic.styles"
STYLE_SUFFIX = ".mplstyle"


def _style_names():
    for name in resources.contents(STYLE_PACKAGE):
        if name.endswith(STYLE_SUFFIX):
            yield name


def install_styles():
    try:
        import matplotlib
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "matplotlib is required to install the aesthetic style sheets."
        ) from exc

    stylelib_dir = os.path.join(matplotlib.get_configdir(), "stylelib")
    os.makedirs(stylelib_dir, exist_ok=True)

    print("Installing styles into", stylelib_dir)
    for name in _style_names():
        data = resources.read_binary(STYLE_PACKAGE, name)
        destination = os.path.join(stylelib_dir, name)
        with open(destination, "wb") as target:
            target.write(data)
        print(name)


class PostInstallMoveFile(install):
    """Install command that copies the packaged style files to matplotlib."""

    def run(self):
        super().run()
        install_styles()
