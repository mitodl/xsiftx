"""
Test utilities
"""

import contextlib
import shutil
import sys
import tempfile


@contextlib.contextmanager
def nostderr():
    """
    Replace standard error with nothing
    as a context manager so it is restored properly
    """
    # pylint: disable=r0903
    savestderr = sys.stderr

    class Devnull(object):
        """
        Fake dev null by skipping write operations.
        """
        def write(self, _):
            """
            Just pass on write
            """
            pass
    sys.stderr = Devnull()
    try:
        yield
    finally:
        sys.stderr = savestderr


def mkdtemp_clean(test_class):
    """
    Make a temp directory and add a cleanup action to it
    """
    temp_dir = tempfile.mkdtemp()
    test_class.addCleanup(shutil.rmtree, temp_dir)
    return temp_dir
