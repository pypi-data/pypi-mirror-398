"""Tests for stock related calculations.
"""

import cProfile
import io
import pstats
from pstats import SortKey

from pathlib import Path

import numpy
import pandas

import fast_tx_tests
from fast_tx.core import apply_chain
from fast_tx.utils import date_to_utctimestamp
from fast_tx import stk_tools
from fast_tx.stk_tx import CashToFracSharesTx
from fast_tx.stk_tools import NameManager

name_for = NameManager.name_for
name_list = NameManager.name_list


def tpath() -> str:
    "Get test path."
    return fast_tx_tests.__path__[0]  # type: ignore


def load_stock_file(asset):
    """Load stock data for a specified asset from a compressed CSV file.

    :param asset: The name or identifier of the asset for which to load data.

    :return: A pandas DataFrame containing the loaded stock data.

    PURPOSE: Load and label stock data from a compressed CSV file,
             parsing the index as dates and renaming columns using a
             predefined naming convention.
    """
    fname = Path(tpath()) / 'data' / f'test_data_{asset}.csv'
    data = pandas.read_csv(fname, index_col=0, parse_dates=True)
    data.columns = [name_for(asset, n) for n in data.columns]
    return data


def prep_position(data, asset, pos_locs=((.2, .4, 1), (.6, .8, 1))):
    """Prepare position data for specified asset.

    :param data:      DataFrame to modify.
    :param asset:     Asset name for labeling.
    :param pos_locs:  Tuple of (start, end, val) locations for positions.
                      Each window is set to have position be `val` between
                      the start and end points (interpreted as floating
                      point fractions of the date index).

    PURPOSE: Set positions in data for given asset based on pos_locs.
    """
    data[name_for(element=asset, field='position')] = 0
    for start_pos_loc, end_pos_loc, val in pos_locs:
        if isinstance(start_pos_loc, float):
            start_pos_loc = int(round(len(data.index) * start_pos_loc))
        if isinstance(end_pos_loc, float):
            end_pos_loc = int(round(len(data.index) * end_pos_loc))
        data.loc[data.index[start_pos_loc]:data.index[end_pos_loc],
                 name_for(element=asset, field='position')] = val

    # Fast calculations will generally want float arrays so we
    # convert bool to float.
    data[name_for(element=asset, field='trade_flag')] = [
        float(d.weekday() == 2) for d in data.index]


def prep_full_stock_pnl(asset_list, div_pay_dt_offset=1):
    """Prepare and process stock data for profit and loss calculations.

    :param asset_list: List of asset names or identifiers to process.

    :return: DataFrame with processed stock data.

    PURPOSE: Load, label, and prepare stock data for PnL calculations.
    """
    data = pandas.concat([load_stock_file(asset) for asset in asset_list],
                         axis=1)
    stk_tools.StkCalcManager(stk_tools.NameManager(asset_list)).prep_divs(
        data, div_pay_dt_offset=div_pay_dt_offset)
    for asset in asset_list:
        prep_position(data, asset)
    return data


def check_against_golden_file(data, golden_file, check_fields, tol=1e-6):
    """Check that data matches golden_file

    :param data:   DataFrame to check.

    :param golden_file:   Optional path to golden file.

    :param check_fields:   List of columns to check.

    :param tol:  Tolerance for differences.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  DataFrame showing locations where differences exceed tol.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  If `golden_file` is provided, check that it matches `data`.

    """
    diff = None
    if golden_file:
        golden = pandas.read_csv(golden_file, index_col=0, parse_dates=True)
        diff = data[check_fields].loc[data[check_fields].sub(
            golden[check_fields]).abs().sum(axis=1) > tol]
        assert diff.empty, f'Too many diffs vs golden:\n{diff}'

    return diff


def make_stk_prof_tx_dict(asset_list, weights, **kwargs):
    """Make dictionary of transforms for stock calculations.

    :param asset_list:    List of assets to work on.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  Dictionary of transforms for stock calculations.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Create a dictionary of transforms to do stock calculations
              so we can use these in testing.

    NOTE:  If you really wanted to handle dividends correctly, you
           would need to deal with a number of additional
           complications. One issues is that when stock settlement
           went from T+2 to T+1 the ex-date became the same as the
           record-date.  For example, see the URL below (it is just
           one URL split across 3 lines; just combine all the lines:

                 https://web.archive.org/web/20250611200750/\
                     https://www.sifma.org/wp-content/uploads/2024/05/\
                        SIFMA-T1-Dividend-Processing-FAQ.pdf

    """
    names = NameManager(asset_list)
    stk_mngr = stk_tools.StkCalcManager(names)
    tx_dict = stk_mngr.make_tx_dict(weights=weights, **kwargs)
    return tx_dict


def make_full_stock_pnl_info(asset_list, div_pay_dt_offset=1,
                             start_cash=10000):
    """Prepare DataFrame for stock profit and loss calculations.

    :param asset_list:  List of assets to include.

    :param div_pay_dt_offset=1:  How many days after the dividend record date
                                 the dividend will be received.

    :param start_cash=10000:     How much cash to start with.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  DataFrame with test data prepared.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Prepare data for testing.

    """
    data = prep_full_stock_pnl(asset_list, div_pay_dt_offset=div_pay_dt_offset)
    data.drop(columns=name_list(asset_list, 'position'), inplace=True)

    cash_dep_name = name_for(field='cash_deposit', element='overall')
    data[cash_dep_name] = 0
    data.loc[data.index[int(len(data.index)*.05)], cash_dep_name] = start_cash
    data[name_list(asset_list, 'trade_flag')] = numpy.float64(
        data[name_list(asset_list, 'trade_flag')])
    for name in name_list(asset_list, 'div_pay_dt'):
        data[name] = [d if isinstance(d, float) else date_to_utctimestamp(d)
                      for d in data[name]]

    return data


def check_fixme(asset_list, golden_file, start_cash=100000000, **kwargs):
    """Verify equity calculations match adjusted close.

    :param asset:    Single asset to check (e.g., `'SPY'`).

    :param golden_file:   Optional path to golden file to check.

    :param start_cash=100000000:   Amount of starting cash.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  The tuple (data, diff).

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  This function puts together a DataFrame for the given `asset`
              where we immediately invest any cash deposit or dividend back
              into the asset. This is kind of cheating because:

                 1. In reality, you would not immediately receive until later.
                 2. You may not actually be able to invest all your cash
                    exactly at the current close price because you would not
                    know the close price beforehand and so would not know how
                    to setup the shares/price of a market/limit order.

              Still cheating about the above is a way to verify our
              calculations against a vendor provided adjusted close.
    """
    data = make_full_stock_pnl_info(
        asset_list, div_pay_dt_offset=1, start_cash=start_cash)

    if kwargs.get('trade_threshold', None) or kwargs.get(
            'pre_tx_dict', {}).get('trade_flag_tx', None):  # type: ignore
        # trading will be controled by threshold or transform
        data[name_list(asset_list, 'trade_flag')] = numpy.nan
    else:  # no threshold so turn on trade flag
        data[name_list(asset_list, 'trade_flag')] = 1.0
    size = float(len(asset_list))/2.0 * (len(asset_list) + 1)
    for i, name in enumerate(name_list(asset_list, 'weights')):
        data[name] = .99*(i+1.0)/size
        data.loc[data.index[-100]:, name] = .99*(len(asset_list)-i)/size

    orig_tx_dict = make_stk_prof_tx_dict(asset_list, weights='dynamic',
                                         **kwargs)
    apply_chain(data, list(orig_tx_dict.values()))

    diff = check_against_golden_file(data, golden_file, (
        list(set(orig_tx_dict['exec_tx'].input_col_names() +
                 orig_tx_dict['exec_tx'].output_col_names())
             ) + [name_for('overall', 'equity')]))

    return data, diff


def check_cheat_equity_calc_tx(asset, golden_file, start_cash=100000000):
    """Verify equity calculations match adjusted close.

    :param asset:    Single asset to check (e.g., `'SPY'`).

    :param golden_file:   Optional path to golden file to check.

    :param start_cash=100000000:   Amount of starting cash.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  The tuple (data, diff).

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  This function puts together a DataFrame for the given `asset`
              where we immediately invest any cash deposit or dividend back
              into the asset. This is kind of cheating because:

                 1. In reality, you would not immediately receive until later.
                 2. You may not actually be able to invest all your cash
                    exactly at the current close price because you would not
                    know the close price beforehand and so would not know how
                    to setup the shares/price of a market/limit order.

              Still cheating about the above is a way to verify our
              calculations against a vendor provided adjusted close.
    """
    assert isinstance(asset, str), f'Require single asset; got {asset=}'
    data = make_full_stock_pnl_info(
        [asset], div_pay_dt_offset=0, start_cash=start_cash)

    data[name_for(asset, 'trade_flag')] = 1.0
    orig_tx_dict = make_stk_prof_tx_dict([asset], [.99])

    # Build our new tx dict starting with div cash flow
    tx_dict = {'div_cash_flow_tx': orig_tx_dict['div_cash_flow_tx']}

    # Next add a tx to spend dividends or cash deposits immediately
    # to buy as many shares (including fractional shares) as we can
    tx_dict['spend_cash_tx'] = CashToFracSharesTx(
        name_list([asset], 'close'),
        [name_for(field=n, element='overall') for n in [
            'div_cash_flow', 'cash_deposit']],
        name_list([asset], 'position'))

    # Now add transforms to calculate trade execution, trade cash flow,
    # accumulate cash, and compute equity.
    for name in ('exec_tx', 'trade_cash_flow_tx', 'cash_acc_tx', 'equity_tx'):
        tx_dict[name] = orig_tx_dict[name]

    apply_chain(data, list(tx_dict.values()))

    verify_equity_vs_adj_close(data, asset, start_cash)
    diff = check_against_golden_file(data, golden_file, (
        list(set(tx_dict['exec_tx'].input_col_names() +
                 tx_dict['exec_tx'].output_col_names()))))

    return data, diff


def verify_equity_vs_adj_close(data, asset, start_cash):
    """Verify that equity calculation matches adjusted close from start to end.

    :param data:        DataFrame with equity and adjusted close where we
                        immediately invest all cash into single asset at
                        the end of the day.

    :param asset:       Single asset we are working on.

    :param start_cash:  Initial starting cash.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  This function checks that our equity calculations match
              adjusted close. Our tolerance for the comparison depends
              on the number of dividends times times the number of
              pennies in starting cash. This is because our
              FastDivCashFlowTx cuts off fractional pennies but the
              adjusted close does not. So the difference between the
              two calculations will be larger if you use smaller
              start_cash. That error can compound over a long time but
              a few multiples of a penny per dividend is about the
              order of the acceptable error.

    """
    num_divs = len(data.loc[data[name_for(asset, 'divCash')] != 0])
    eq_name = name_for('overall', 'equity')
    equity_start = min(i for i, v in enumerate(data[eq_name].to_list()) if v)
    eq_change = data[eq_name].iloc[-1]/data[eq_name].iloc[equity_start]
    adj_close_name = name_for(asset, 'adjClose')
    adj_close_chg = data[adj_close_name].iloc[-1]/data[adj_close_name].iloc[
        equity_start]
    assert abs(adj_close_chg - eq_change) < (1.1+num_divs)/(100*start_cash)


def test_cheat_equity_spy():
    "Run check_cheat_equity_calc_tx for SPY ETF."
    check_cheat_equity_calc_tx('SPY', Path(
        tpath()) / 'data' / 'golden_cheat_SPY.csv')


def test_cheat_equity_tlt():
    "Run check_cheat_equity_calc_tx for TLT ETF."
    check_cheat_equity_calc_tx('TLT', Path(
        tpath()) / 'data' / 'golden_cheat_TLT.csv')


def test_spy_tlt():
    "Test weighting between SPY and TLT ETFs."
    check_fixme(['SPY', 'TLT'], Path(
        tpath()) / 'data' / 'golden_SPY_TLT.csv')


def test_spy_tlt_lazy():
    "Test weighting between SPY and TLT ETFs with lazy rebalance."

    asset_list = ['SPY', 'TLT']
    pre_tx_dict = {'trade_flag_tx': stk_tools.TradeFlagOnDiff(
        name_list(asset_list, 'position'),
        name_list(asset_list, 'close'),
        name_list(asset_list, 'post_trade_pos'), name_for('overall', 'equity'),
        name_list(asset_list, 'trade_flag'))}
    check_fixme(['SPY', 'TLT'], Path(
        tpath()) / 'data' / 'golden_SPY_TLT_lazy.csv', pre_tx_dict=pre_tx_dict)
    check_fixme(['SPY', 'TLT'], Path(
        tpath()) / 'data' / 'golden_SPY_TLT_lazy.csv', trade_threshold=0.01)


# pylint: disable=duplicate-code


def do_profile(preprocess_compile=False, trials=1, func_list=(
        test_cheat_equity_spy,)):  # pragma: no cover
    """Do profiling.

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
        _ = [f() for f in func_list]

    print('Doing profiling')
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(trials):
        _ = [f() for f in func_list]
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


if __name__ == '__main__':
    do_profile(preprocess_compile=True, trials=50)  # pragma: no cover
