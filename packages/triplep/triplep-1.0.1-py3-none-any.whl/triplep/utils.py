"""
Copyright (c) 2014, Saurabh Kumar (python-dotenv), 2013, Ted Tieken (django-dotenv-rw), 2013, Jacob Kaplan-Moss (django-dotenv)

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

- Neither the name of django-dotenv nor the names of its contributors
  may be used to endorse or promote products derived from this software
  without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import stat
import sys
from typing import Iterator, Union

# A type alias for a string path to be used for the paths in this file.
# These paths may flow to `open()` and `shutil.move()`; `shutil.move()`
# only accepts string paths, not byte paths or file descriptors. See
# https://github.com/python/typeshed/pull/6832.
StrPath = Union[str, "os.PathLike[str]"]


def is_file_or_fifo(path: StrPath) -> bool:
    """Return True if `path` exists and is either a regular file or a FIFO"""

    if os.path.isfile(path):
        return True

    try:
        st = os.stat(path)
    except (FileNotFoundError, OSError):
        return False

    return stat.S_ISFIFO(st.st_mode)


def walk_to_root(path: str) -> Iterator[str]:
    """Yield directories starting from the given directory up to the root"""

    if not os.path.exists(path):
        raise IOError("Starting path not found")

    if os.path.isfile(path):
        path = os.path.dirname(path)

    last_dir = None
    current_dir = os.path.abspath(path)
    while last_dir != current_dir:
        yield current_dir
        parent_dir = os.path.abspath(os.path.join(current_dir, os.path.pardir))
        last_dir, current_dir = current_dir, parent_dir


def find_pyproject(
    filename: str = "pyproject.toml",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """Search in increasingly higher folders for the given file

    Returns path to the file if found, or an empty string otherwise
    """

    def _is_interactive():
        """Decide whether this is running in a REPL or IPython notebook"""
        if hasattr(sys, "ps1") or hasattr(sys, "ps2"):
            return True
        try:
            main = __import__("__main__", None, None, fromlist=["__file__"])
        except ModuleNotFoundError:
            return False
        return not hasattr(main, "__file__")

    def _is_debugger():
        return sys.gettrace() is not None

    if usecwd or _is_interactive() or _is_debugger() or getattr(sys, "frozen", False):
        # Should work without __file__, e.g. in REPL or IPython notebook.
        path = os.getcwd()
    else:
        # will work for .py files
        frame = sys._getframe()
        current_file = __file__

        while frame.f_code.co_filename == current_file or not os.path.exists(
            frame.f_code.co_filename
        ):
            assert frame.f_back is not None
            frame = frame.f_back
        frame_filename = frame.f_code.co_filename
        path = os.path.dirname(os.path.abspath(frame_filename))

    for dirname in walk_to_root(path):
        check_path = os.path.join(dirname, filename)
        if is_file_or_fifo(check_path):
            return check_path

    if raise_error_if_not_found:
        raise IOError("File not found")

    return ""
