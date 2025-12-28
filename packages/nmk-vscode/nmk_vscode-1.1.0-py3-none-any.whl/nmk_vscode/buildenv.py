"""
Python module for **buildenv** extension and tasks
"""

import logging
import shutil
import subprocess
from pathlib import Path

from buildenv import BuildEnvExtension

from nmk_vscode import __version__

# Logger instance
_logger = logging.getLogger("buildenv")


class BuildEnvInit(BuildEnvExtension):
    """
    Buildenv extension for **nmk-vscode**
    """

    def init(self, force: bool):
        """
        Buildenv init call back for nmk-vscode

        When called, this method:

        * looks for **vscode** shell init script path
        * adds an activation script to call it
        """

        # Check for code command
        code_cmd = shutil.which("code")
        if code_cmd is not None:
            # Ask for init script
            cp = subprocess.run(
                [code_cmd, "--locate-shell-integration-path", "bash"],
                capture_output=True,
                check=False,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            if cp.returncode == 0:
                # Check for returned script path
                script_path = cp.stdout.splitlines()[0].strip()
                if Path(script_path).is_file():
                    # Add activation script
                    self.manager.add_activation_file("vscode", ".sh", Path(__file__).parent / "templates" / "vscode.sh.jinja", {"vscodeScript": script_path})
                else:
                    _logger.warning(f"nmk-vscode: bash init script not found: {script_path}")
            else:
                _logger.warning("nmk-vscode: 'code --locate-shell-integration-path bash' command failed!")
        else:
            _logger.warning("nmk-vscode: 'code' command not found!")

    def get_version(self) -> str:
        """
        Get extension version
        """

        return __version__
