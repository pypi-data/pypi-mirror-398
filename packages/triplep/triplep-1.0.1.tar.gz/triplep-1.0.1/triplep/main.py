import io
import logging
import tomllib
from contextlib import contextmanager
from typing import IO, Any, Iterator

from .models import Project
from .utils import StrPath, find_pyproject, is_file_or_fifo

logger = logging.getLogger(__name__)


class PyProject:
    def __init__(self, pyproject_path: StrPath | None):
        self.pyproject_path = pyproject_path

        self.parse()

    @contextmanager
    def _get_fp(self) -> Iterator[IO[bytes]]:
        if self.pyproject_path and is_file_or_fifo(self.pyproject_path):
            with open(self.pyproject_path, mode="rb") as fp:
                yield fp

        else:
            if self.verbose:
                logger.info(
                    "TripleP could not find configuration file %s.",
                    self.pyproject_path or "pyproject.toml",
                )
            yield io.BytesIO(b"")

    def load(self) -> dict[str, Any]:
        """Returns contents of pyproject TOML file as dict"""

        with self._get_fp() as fp:
            return tomllib.load(fp)

    def parse(self):
        """Loads/reloads and parses contents of pyproject TOML file as dataclass entities"""
        self.raw = self.load()
        self.project = Project(**(self.raw["project"]))


def load_pyproject(
    pyproject_path: StrPath | None = None,
) -> PyProject:
    """Parse a pyproject.toml file and return contents

    Parameters:
        pyproject_path: Absolute or relative path to pyproject.toml file.
    Returns:
        PyProject: A class defining parsed and war contents of pyproject file.

    If `pyproject_path` is `None`, `find_pyproject()` is used to find the
    pyproject.toml file with it's default parameters. If you need to change the default parameters
    of `find_pyproject()`, you can explicitly call `find_pyproject()` and pass the result
    to this function as `pyproject_path`.
    """

    if pyproject_path is None:
        pyproject_path = find_pyproject()

    return PyProject(pyproject_path=pyproject_path)
