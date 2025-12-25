import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dew_gwdata import utils


def test_chunk():
    assert list(utils.chunk([1, 2, 3], 2)) == [[1, 2], [3]]
