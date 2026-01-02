from __future__ import annotations

from pathlib import Path

from setuptools import setup
from setuptools.command.install_lib import install_lib as _install_lib


class install_lib(_install_lib):
    def run(self) -> None:
        super().run()

        src = Path(__file__).parent / "data" / "vlaamscodex_autoload.pth"
        dst = Path(self.install_dir) / "vlaamscodex_autoload.pth"
        if not src.exists():
            raise FileNotFoundError(str(src))

        # Install into purelib (site-packages) root so `site` executes it at startup.
        dst.parent.mkdir(parents=True, exist_ok=True)
        self.copy_file(str(src), str(dst))


setup(cmdclass={"install_lib": install_lib})

