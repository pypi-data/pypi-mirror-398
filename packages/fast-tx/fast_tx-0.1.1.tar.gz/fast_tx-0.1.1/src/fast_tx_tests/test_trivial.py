"""Test some trivial things.
"""

import numba
import numpy
import pandas
import pytest

from fast_tx.core import (FastTx, Lag, SafeSum, apply_chain)


def test_lookups():

    tx = Lag(1, {'prices': ['a','b','c']}, ['l_a','l_b','l_c'])
    islice = tx.islice('prices')
    assert islice == slice(0, 3)

    # The following verifies code coverage by taking a different
    # path in `islice` via caching.
    assert tx.islice('prices') == slice(0, 3)
    
    with pytest.raises(KeyError) as exc_info:
        tx.islice('unknown')
    assert exc_info.type == KeyError

        
