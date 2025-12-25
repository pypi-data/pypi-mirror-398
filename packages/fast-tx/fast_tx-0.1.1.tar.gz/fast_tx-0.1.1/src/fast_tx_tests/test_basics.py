"""Some simple tests for the fast_tx package.

Note: If you have problems or want to debug, you should set NUMBA_DISABLE_JIT=1
      as an environment variable and then run tests. That will disable the
      NUMBA jit compliation so you can use pdb and get better error info.
"""

import cProfile
import io
import pstats
from pstats import SortKey

import numba
import numpy
import pandas

from fast_tx.core import (FastTx, Lag, SafeSum, apply_chain)


class TargetPosition(FastTx):
    """Compute a target position for stock.

    Target is previous holding plus use opening cash / price to buy more.
    """

    def __init__(self, input_cols=('open_cash', 'price', 'prev_shares'),
                 output_cols=('shares',)):
        super().__init__(input_cols, output_cols)

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value, state, inputs, outputs):
        outputs[0] = round(numpy.floor(inputs[0]/inputs[1]), 2)
        if not numpy.isnan(inputs[2]):
            outputs[0] += inputs[2]


class TotalCash(FastTx):
    """Compute total cash.

    Cash is cash from the open plus previous dividends (times previous shares)
    plus cost of any shares we are buying now.
    """

    def __init__(self, input_cols=(
            'open_cash', 'prev_div', 'price', 'prev_shares', 'shares'),
                 output_cols=('close_cash',)):
        super().__init__(input_cols, output_cols)

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value, state, inputs, outputs):
        outputs[0] = (inputs[0]              # cash we had at the open
                      + inputs[1]*inputs[3]  # dividends received
                      ) - inputs[2] * (inputs[4]-inputs[3])  # shares bought


def slow_price_div(frame):
    """Compute shares to own in a safe (but slow) way for the given frame.

    This is intended as a helper function to check the fast calculation
    using transforms.
    """
    fcopy = frame.copy()
    for i in range(1, len(fcopy.index)):
        fcopy.loc[fcopy.index[i], 'open_cash'] = (
            fcopy.iloc[i-1]['close_cash'] + fcopy.iloc[i-1]['deposit'])
        fcopy.loc[fcopy.index[i], 'shares'] = (
            round(numpy.floor(
                fcopy.iloc[i]['open_cash']/fcopy.iloc[i]['price']), 2)
            + fcopy.iloc[i-1]['shares'])
        fcopy.loc[fcopy.index[i], 'close_cash'] = fcopy.iloc[
            i]['open_cash'] - (
                fcopy.iloc[i]['shares'] - fcopy.iloc[i-1]['shares']
                ) * fcopy.iloc[i]['price'] + (
                    fcopy.iloc[i-1]['div'] * fcopy.iloc[i-1]['shares'])
    return fcopy


def check_price_div(frame, check_diff=True):
    """Helper to check price/dividend math as a test case.

    :param frame:    Input DataFrame with 'div' and 'price' columns.

    :param check_diff=True:   Whether to validate result with `slow_price_div`.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:   Run some transforms on `frame` to verify that the transforms
               correctly to some price/dividind and buying math.

    """
    frame[['shares', 'open_cash', 'close_cash', 'deposit']] = 0.0
    frame.loc[frame.index[0], 'deposit'] = 100.0
    fcopy = None
    if check_diff:
        fcopy = slow_price_div(frame)

    frame[['prev_shares']] = 0
    apply_chain(frame, [
        Lag(1, ['shares', 'div', 'close_cash', 'deposit'], [
            'prev_shares', 'prev_div', 'prev_close_cash', 'prev_deposit']),
        SafeSum(['prev_close_cash', 'prev_deposit'], ['open_cash']),
        TargetPosition(), TotalCash()])

    if check_diff and fcopy is not None:
        diff = fcopy.sub(frame[list(fcopy)])
        diff = diff.loc[diff.abs().sum(axis=1) > 1e-6]
        assert diff.empty


def test_price_div_small():
    """Test small example we have verified by hand.
    """
    frame = pandas.DataFrame([
        [.5, 4],
        [0,  5],
        [.7, 6.8],
        [0, 7.5],
        [.95, 8.25]], columns=['div', 'price'])
    check_price_div(frame)


def test_price_div_big(size=int(1e2)):
    """Run a larger version of the price/div test.

    The main purpose of this test is that you can change the `size`
    parameter and run with the environment variable
    `NUMBA_DISABLE_JIT=1` (and probably use `-k test_price_div_big` to
    just test this function) and without to compare the speed of using
    numba and not using numba. This example is fairly trivial, so you
    will need large sizes (e.g., on the order of `size=int(1e6)`) to
    really see a difference.

    Note that we automatically set check_diff to False for large sizes
    so that manually checking correctness does not confuse the timing.
    """
    check_diff = size < 10000  # do not check diff for big sizes
    state = numpy.random.RandomState(123)  # pylint: disable=no-member
    prices = 100 * numpy.cumprod(state.lognormal(0, .01, size))
    divs = [(1 if i else 0) for i in (state.uniform(0, 1, size) > .9)]
    frame = pandas.DataFrame({'price': prices, 'div': divs})
    check_price_div(frame, check_diff=check_diff)


def do_profile(preprocess_compile=False, trials=1):  # pragma: no cover
    """Do profiling for test_price_div_big function.

    :param preprocess_compile=False:  If True, we do a small run
                                      outside the profiler to force
                                      numba to JIT compile and read
                                      from the cache first.
                                      Supposedly using `cache=True` in
                                      JIT compiling will cache things,
                                      but even with that, there still
                                      seems to be an initial startup
                                      hit. See the following thread on
                                      https://numba.discourse.group/t/:

      understanding-initial-execution-delay-in-numba-cached-functions/2783/9

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Do profiling.

    """
    if preprocess_compile:
        test_price_div_big(10)

    print('Doing profiling')
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(trials):
        test_price_div_big(30000)
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


if __name__ == '__main__':  # pragma: no cover
    do_profile(preprocess_compile=True, trials=20)
