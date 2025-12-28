"""
Python tests builder
"""

import shutil
import subprocess
import sys

from nmk.model.builder import NmkTaskBuilder
from nmk.model.keys import NmkRootConfig


class PytestBuilder(NmkTaskBuilder):
    """
    Python tests builder
    """

    def build(self, pytest_args: dict[str, str]):
        """
        Invoke pytest with specified options

        :param pytest_args: extra pytest command line args
        """

        # Clean outputs
        for p in self.outputs:
            if p.is_dir():
                shutil.rmtree(p)
            elif p.is_file():  # pragma: no cover
                p.unlink()

        # Compute extra args
        args = []
        for opt_k, opt_v in pytest_args.items():
            if isinstance(opt_v, bool):
                if opt_v:
                    # Simple option
                    args.append(f"--{opt_k}")
            else:
                # Key + value
                args.append(f"--{opt_k}={opt_v}")

        # Invoke pytest
        all_args = [sys.executable, "-m", "pytest"] + args
        self.logger.debug(f"Running subprocess: {' '.join(all_args)}")
        subprocess.run(all_args, check=True, cwd=self.model.config[NmkRootConfig.PROJECT_DIR].value)
