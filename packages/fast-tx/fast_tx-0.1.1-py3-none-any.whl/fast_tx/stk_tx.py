"""This module provides sub-classes of FastTx related to stocks.

These transforms are useful on their own as well as for illustrating
how and why to use the FastTx infrastructure.
"""

import numba
from numba.types import Tuple
import numpy
from numpy.typing import NDArray
import pandas


from fast_tx.core import FastTx


class FastStkEquityCalc(FastTx):
    """Compute equity for stocks (basically value of stocks plus cash).

    The following illustrates example usage:

>>> import pandas
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import FastStkEquityCalc
>>> df = pandas.DataFrame({
...    'price_ABC':  [10.00, 10.20, 10.45, 9.80, 11.35],
...    'price_XYZ':  [20.10, 22.22, 21.11, 19.80, 19.35],
...    'shares_ABC': [0, 0, 100, 100, 200],
...    'shares_XYZ': [200, 100, 100, 0, 0]})
>>> df['cash'] = 10000 - (df.shares_ABC.diff() * df.price_ABC) - (
...         df.shares_XYZ.diff() * df.price_XYZ)
>>> df.iloc[0, -1] = 10000
>>> apply_chain(df, [FastStkEquityCalc(
...     ['price_ABC', 'price_XYZ'], ['shares_ABC', 'shares_XYZ'], 'cash',
...     'equity')])
>>> print(df)
   price_ABC  price_XYZ  shares_ABC  shares_XYZ     cash   equity
0      10.00      20.10         0.0       200.0  10000.0  14020.0
1      10.20      22.22         0.0       100.0  12222.0  14444.0
2      10.45      21.11       100.0       100.0   8955.0  12111.0
3       9.80      19.80       100.0         0.0  11980.0  12960.0
4      11.35      19.35       200.0         0.0   8865.0  11135.0

    """

    def __init__(self, close_fields, post_trade_names,
                 cash_name, equity_name):
        """Initializer.

        :param close_fields:   List of names for columns representing closing
                               prices of assets.

        :param post_trade_names:   List of names for columns representing
                                   "post trade" positions. These are basically
                                   the number of shares or units after the
                                   market closes (e.g., after you execute any
                                   trades for the day/bar).

        :param cash_name:          Name of column representing cash owned
                                   after market closes.

        :param equity_name:        Output name representing total equity
                                   after the close. This is basically
                                   the value of cash and stocks and
                                   other assets with equity value (but
                                   not things like futures).

        """
        assert len(close_fields) == len(post_trade_names)

        super().__init__(close_fields + post_trade_names + [cash_name],
                         [equity_name])

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        """Implement calc_row to compute equity.
        """
        size = len(inputs) >> 1

        start_idx = 0
        closes = inputs[:size]
        start_idx += size
        post_trade_pos = inputs[start_idx:(start_idx+size)]
        equity = inputs[-1]  # inputs[-1] is cash so start with that

        for (close_pos, close_price) in zip(post_trade_pos, closes):
            if not (numpy.isnan(close_pos) or numpy.isnan(close_price)):
                equity += close_pos * close_price

        outputs[0] = equity


class FastTradeCashFlowTx(FastTx):
    """Compute cash flow caused by trading.

>>> import pandas
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import FastTradeCashFlowTx
>>> df = pandas.DataFrame({
...     'price_ABC':  [10.0, 10.2, 10.45, 9.8, 11.35],
...     'pre_trade_shares_ABC': [0, 100, 200, 100, 0]})
>>> df['post_trade_shares_ABC'] = df['pre_trade_shares_ABC'].shift(-1)
>>> df.iloc[-1, -1] = 0
>>> apply_chain(df, [FastTradeCashFlowTx(
...     ['price_ABC'], ['pre_trade_shares_ABC'], ['post_trade_shares_ABC'],
...     'cash_flow')])
>>> print(df)  # cash flow is negative when buying and positive when selling
   price_ABC  pre_trade_shares_ABC  post_trade_shares_ABC  cash_flow
0      10.00                   0.0                  100.0    -1000.0
1      10.20                 100.0                  200.0    -1020.0
2      10.45                 200.0                  100.0     1045.0
3       9.80                 100.0                    0.0      980.0
4      11.35                   0.0                    0.0        0.0

    """

    def __init__(self, close_fields, pre_trade_names,
                 post_trade_names, cashflow_name):
        """Initializer.

        :param close_fields:   List of names for columns representing closing
                               prices of assets.

        :param post_trade_names:   List of names for columns representing
                                   "post trade" positions. These are basically
                                   the number of shares or units after the
                                   market closes (e.g., after you execute any
                                   trades for the day/bar).

        :param pre_trade_names:    List of names for columns representing
                                   "pre trade" positions. These are basically
                                   the number of shares or units before the
                                   market opened. The difference in between
                                   values of post_trade_names and
                                   pre_trade_names is interpreted as the
                                   number of units traded. (Splits, stock
                                   dividends or other ways of changing the
                                   share count that do not include trading
                                   should be reflected as a change from
                                   yesterday's post_trade_names to today's
                                   pre_trade_names).

        :param cashflow_name:      Output name representing cash flow
                                   from trading.

        """

        assert len(set(map(len, [
            close_fields, post_trade_names]))) == 1, (
                f'Main input names to {self.__class__} must have same length.')
        self._size = len(close_fields)

        super().__init__(
            close_fields + pre_trade_names + post_trade_names, [cashflow_name])

    def startup(self, dataframe):
        """Slight hack to store number of assets as size of state array.
        """
        return numpy.empty(self._size)

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        """Implement calc_row to compute cash flow.
        """
        size = len(state)
        start_idx = 0
        closes = inputs[:size]
        start_idx += size
        pre_trade_pos = inputs[start_idx:(start_idx+size)]
        start_idx += size
        post_trade_pos = inputs[start_idx:(start_idx+size)]

        cash_flow = 0
        for i, (close_pos, close_price) in enumerate(zip(
                post_trade_pos, closes)):
            if not (numpy.isnan(close_pos) or numpy.isnan(close_price)):
                pre_pos = 0 if numpy.isnan(pre_trade_pos[i]) else (
                    pre_trade_pos[i])
                bought = close_pos - pre_pos
                cash_flow -= close_price * bought

        assert not numpy.isnan(cash_flow)

        outputs[0] = cash_flow


class FastDivCashFlowTx(FastTx):
    """Compute cash flow from dividends.

    See also the docs for the calc_row and post_process_state methods
    since there are some subtelties to this calculation.

The following illustrates example usage.

>>> import pandas, numpy
>>> from fast_tx.core import apply_chain
>>> from fast_tx.utils import date_to_utctimestamp
>>> from fast_tx.stk_tx import FastDivCashFlowTx
>>> df = pandas.DataFrame({
...     'shares_ABC': [100, 200, 100, 0, 0],
...     'div_ABC': [0, 0, .2, 0, 0],
...     'pay_div_date_ABC': [numpy.nan, numpy.nan,
...             pandas.Timestamp('2025-05-23'), numpy.nan, numpy.nan]},
...     index=[pandas.Timestamp(p)
...     for p in [f'2025-05-{i}' for i in range(19, 24)]])
>>> print(df)
            shares_ABC  div_ABC pay_div_date_ABC
2025-05-19         100      0.0              NaT
2025-05-20         200      0.0              NaT
2025-05-21         100      0.2       2025-05-23
2025-05-22           0      0.0              NaT
2025-05-23           0      0.0              NaT
>>> # Above represents case where ex-dividend date is 2025-05-21,
>>> # and dividend amount is 20 cents per share to be paid on 2025-05-23.
>>> df['pay_div_date_ABC'] = [date_to_utctimestamp(d)  # convert date column
...     for d in df['pay_div_date_ABC']]               # to float for numba
>>> apply_chain(df, [FastDivCashFlowTx(
...     ['div_ABC'], ['pay_div_date_ABC'], ['shares_ABC'],
...     'div_cash_flow_ABC')])
>>> print(df)
            shares_ABC  div_ABC  pay_div_date_ABC  div_cash_flow_ABC
2025-05-19       100.0      0.0               NaN                0.0
2025-05-20       200.0      0.0               NaN                0.0
2025-05-21       100.0      0.2      1.747958e+09                0.0
2025-05-22         0.0      0.0               NaN                0.0
2025-05-23         0.0      0.0               NaN               40.0

Note that the dividend of 20 cents per share which is ex-dividend on
2025-05-21 is applied to the 200 shares owned immediately **BEFORE**
the ex-dividend date for a total payment of $40 received on the payment
date of 2025-05-23.

    """

    def __init__(self, div_totals, div_pay_dts,
                 post_trade_names, cashflow_name):
        """Initializer.

        :param div_totals:   List of columns indicating the total dividends
                             on a given record date.

        :param div_pay_dts:  List of columns indicating the payment date
                             for a dividend on a given ex-dividend date.

        :param post_trade_names:  List of columns showing how much stock
                                  is owned at the close. We will use this
                                  value on the day **BEFORE** the ex-dividend
                                  date to determine how many shares to use
                                  in computing the dividend.

        :param cashflow_name:     Output name for the total dividend cash flow.

        """
        assert len(set(map(len, [
            div_totals, div_pay_dts, post_trade_names]))) == 1, (
                f'Main input names to {self.__class__} must have same length.')
        self._size = len(div_totals)

        super().__init__(
            div_totals + div_pay_dts + post_trade_names, [cashflow_name])

    def startup(self, dataframe):
        result = numpy.full(3*self._size + 1, numpy.nan)
        result[-1] = self._size
        return result

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        """Implement calculate row.

        If there is a dividend, we will want to know the payment date
        and save that payment date in the state so we can pay out the
        dividend on that date. We also need to know how many shares
        to use to compute the total dividend (see below).

        The post_process_state method will look at the post_trade_pos
        after all information for a row has been processed and put that into
        the state so this method can look at the post_trade_pos from the
        previous row. That is the amount of shares we owned **BEFORE** the
        ex-dividend date and can be used to determine the dividend amount.

        So this function first checks if there is a dividend to remember
        and then checks if there are dividends remembered to pay out.
        """
        size = numpy.int64(state[-1])
        start_idx = 0
        divs = inputs[start_idx:(size+start_idx)]
        pending_div_vals = state[start_idx:(size+start_idx)]
        start_idx += size
        div_dates = inputs[start_idx:(size+start_idx)]
        pending_div_dates = state[start_idx:(size+start_idx)]
        start_idx += size
        prev_pos = state[start_idx:(size+start_idx)]

        cash_flow = 0
        for i in range(size):  # Check if we have non-zero div + previous pos
            if not (numpy.isnan(divs[i]) or divs[i] == 0
                    or numpy.isnan(prev_pos[i])):
                assert numpy.isnan(pending_div_dates[i]), (
                    'Cannot have more than 1 pending dividend')
                pending_div_dates[i] = div_dates[i]    # Save div in state
                pending_div_vals[i] = numpy.floor(     # to check in future.
                    100*divs[i]*prev_pos[i])/100.0     # Drop fractional cents.

            if index_value >= pending_div_dates[i]:  # div received now
                cash_flow += pending_div_vals[i]
                pending_div_dates[i] = numpy.nan  # this will clear state since
                pending_div_vals[i] = numpy.nan  # pending div is processed

        assert not numpy.isnan(cash_flow)
        outputs[0] = cash_flow

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:]), cache=True)
    def post_process_state(index_value, state, inputs):
        """Post process the row to determine the state.

        We have to update the state **AFTER** the row has been fully
        processed so we can see the post trade position. We will then
        save the post trade position for this row into the state so that
        when `calc_row` is executed on the next row it can look at the
        state to get the previous row's post trade position.
        """
        size = numpy.int64(state[-1])
        sizex2 = size << 1
        sizex3 = sizex2 + size
        post_trade_pos = inputs[sizex2:sizex3]
        prev_pos = state[sizex2:sizex3]

        for i in range(size):
            prev_pos[i] = post_trade_pos[i]  # save post trade pos in state


class StkTradeExecTx(FastTx):
    """Compute calculating stock trade executions.

    See StkTradeWithSplitsExecTx if you need to handle stock splits.

    Basically this takes in some target positions and trade flags and
    produces the pre and post trade positions. This is useful for when
    you have a quantitative strategy computing target positions all the
    time but you only want to actually trade occaionsally (e.g., every
    Tuesday or every month end or when target positions are far enough
    from current positions).

    The following illustrates example usage:

>>> import pandas
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import StkTradeExecTx
>>> df = pandas.DataFrame({
...     'target_shares':  [100*i for i in range(6)],
...     'trade_flag': [0, 1, 0, 0, 1, 0]})
>>> apply_chain(df, [StkTradeExecTx(
...     ['pre_trade_shares'], ['target_shares'], ['trade_flag'],
...     ['post_trade_shares'])])
>>> print(df)  # cash flow is negative when buying and positive when selling
   target_shares  trade_flag  pre_trade_shares  post_trade_shares
0            0.0         0.0               0.0                0.0
1          100.0         1.0               0.0              100.0
2          200.0         0.0             100.0              100.0
3          300.0         0.0             100.0              100.0
4          400.0         1.0             100.0              400.0
5          500.0         0.0             400.0              400.0

Notice that while the target shares is changing each day, we only
actually trade on days indicated by `trade_flag`.

    """
    def __init__(self, pre_trade_names, target_names, trade_flag_names,
                 post_trade_names):
        """Initializer.

        :param pre_trade_names:    List of names for columns representing
                                   "pre trade" positions. These are basically
                                   the number of shares or units before the
                                   market opened. The difference in between
                                   values of post_trade_names and
                                   pre_trade_names is interpreted as the
                                   number of units traded. (Splits, stock
                                   dividends or other ways of changing the
                                   share count that do not include trading
                                   should be reflected as a change from
                                   yesterday's post_trade_names to today's
                                   pre_trade_names).


        :param target_names:       List of names indicating the target
                                   position to adopt when indicated by
                                   trade flag.

        :param trade_flag_names:   List of names indicating when to trade.

        :param post_trade_names:   List of names for columns representing
                                   "post trade" positions. These are basically
                                   the number of shares or units after the
                                   market closes (e.g., after you execute any
                                   trades for the day/bar).

        """
        assert len(pre_trade_names) == len(post_trade_names)
        assert len(pre_trade_names) == len(trade_flag_names)
        assert len(target_names) == len(pre_trade_names)
        super().__init__(target_names + trade_flag_names,
                         pre_trade_names + post_trade_names)

    def startup(self, dataframe: pandas.DataFrame) -> NDArray[numpy.float64]:
        out_size = len(self.output_col_names())
        result = numpy.zeros(1 + out_size//2)
        result[0] = out_size//2
        return result

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        size = numpy.int32(state[0])
        targets = inputs[:size]
        flags = inputs[size:]
        for i, f in enumerate(flags):
            outputs[i] = state[i+1]  # set pre trade pos based on previous day
            if f:  # trade flag says to trade
                outputs[i+size] = targets[i]  # set post trade position to tgt
            else:
                outputs[i+size] = outputs[i]  # set post trade position to pre
            state[i+1] = outputs[i+size]  # save post trade pos in state


class WeightedPositionsTx(FastTx):
    """Take weighted positions in assets based on current equity.

    The following illustrates example usage:

>>> import pandas, numpy
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import (
...     WeightedPositionsTx, FastStkEquityCalc, StkTradeExecTx)
>>> df = pandas.DataFrame({
...    'price_ABC':  [10, 10, 10, 9, 11],
...    'price_XYZ':  [20, 22, 21, 19, 19],
...    'trade_flag_ABC': [0, 1, 0, 1, 0],
...    'trade_flag_XYZ': [0, 1, 0, 1, 0],
...    'shares_ABC': [0, 0, 100, 100, 200],
...    'shares_XYZ': [200, 100, 100, 0, 0]})
>>> df['cash'] = 10000
>>> df.iloc[1:, -1] = 10000 - ((df.shares_ABC.diff() * df.price_ABC) - (
...         df.shares_XYZ.diff() * df.price_XYZ)).iloc[1:]
>>> apply_chain(df, [FastStkEquityCalc(
...     ['price_ABC', 'price_XYZ'], ['shares_ABC', 'shares_XYZ'], 'cash',
...     'equity'), WeightedPositionsTx([.25, .75],
...     ['price_ABC', 'price_XYZ'], 'equity', ['target_ABC', 'target_XYZ']),
...     StkTradeExecTx(['pre_trd_ABC','pre_trd_XYZ'],
...         ['target_ABC', 'target_XYZ'], ['trade_flag_ABC', 'trade_flag_XYZ'],
...         ['post_trd_ABC','post_trd_XYZ'])])
>>> print(df.iloc[:,10:])
   pre_trd_ABC  pre_trd_XYZ  post_trd_ABC  post_trd_XYZ
0          0.0          0.0           0.0           0.0
1          0.0          0.0         250.0         340.0
2        250.0        340.0         250.0         340.0
3        250.0        340.0         250.0         355.0
4        250.0        355.0         250.0         355.0

    """

    def __init__(self, weights, price_names, equity_name, position_names):
        """Initializer.

        :param weights:      Names indicating weights for each asset.

        :param price_names:  Names indicating prices for each asset.

        :param equity_name:  Name indicating total equity.

        :param position_names:  Target positions to compute.

        """
        assert len(weights) == len(position_names)
        assert len(weights) == len(price_names)
        self._weights = weights
        super().__init__(price_names + [equity_name], position_names)

    def startup(self, dataframe: pandas.DataFrame) -> NDArray[numpy.float64]:
        return numpy.array(self._weights, dtype=numpy.float64)

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        equity = inputs[-1]
        for i, weight in enumerate(state):
            outputs[i] = numpy.floor(weight * equity / inputs[i])


class DynamicWeightedPositionsTx(FastTx):
    """Take weighted positions in assets based on current equity.

    The following illustrates example usage:

>>> import pandas, numpy
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import (
...     DynamicWeightedPositionsTx, FastStkEquityCalc, StkTradeExecTx)
>>> df = pandas.DataFrame({
...    'price_ABC':  [10, 10, 10, 9, 11],
...    'price_XYZ':  [20, 22, 21, 19, 19],
...    'weight_ABC':  [.1, .1, .5, .9, .9],
...    'weight_XYZ':  [.9, .9, .5, .1, .1],
...    'trade_flag_ABC': [0, 1, 0, 1, 0],
...    'trade_flag_XYZ': [0, 1, 0, 1, 0],
...    'shares_ABC': [0, 0, 100, 100, 200],
...    'shares_XYZ': [200, 100, 100, 0, 0]})
>>> df['cash'] = 10000
>>> df.iloc[1:, -1] = 10000 - ((df.shares_ABC.diff() * df.price_ABC) - (
...         df.shares_XYZ.diff() * df.price_XYZ)).iloc[1:]
>>> apply_chain(df, [FastStkEquityCalc(
...     ['price_ABC', 'price_XYZ'], ['shares_ABC', 'shares_XYZ'], 'cash',
...     'equity'), DynamicWeightedPositionsTx(['weight_ABC', 'weight_XYZ'],
...     ['price_ABC', 'price_XYZ'], 'equity', ['target_ABC', 'target_XYZ']),
...     StkTradeExecTx(['pre_trd_ABC','pre_trd_XYZ'],
...         ['target_ABC', 'target_XYZ'], ['trade_flag_ABC', 'trade_flag_XYZ'],
...         ['post_trd_ABC','post_trd_XYZ'])])
>>> df['ratio'] = df.price_ABC*df.target_ABC/df.price_XYZ/df.target_XYZ
>>> print(df.iloc[:,12:])
   pre_trd_ABC  pre_trd_XYZ  post_trd_ABC  post_trd_XYZ     ratio
0          0.0          0.0           0.0           0.0  0.111111
1          0.0          0.0         100.0         409.0  0.111136
2        100.0        409.0         100.0         409.0  1.000331
3        100.0        409.0         900.0          47.0  9.070549
4        900.0         47.0         900.0          47.0  9.063521

    """

    def __init__(self, weight_names, price_names, equity_name, position_names):
        """Initializer.

        :param weight_names:  Names indicating weights for each asset.

        :param price_names:   Names indicating prices for each asset.

        :param equity_name:   Name indicating total equity.

        :param position_names:  Target positions to compute.

        """
        assert len(weight_names) == len(position_names)
        assert len(weight_names) == len(price_names)
        super().__init__(price_names + weight_names + [equity_name],
                         position_names)

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        size = len(outputs)
        double_size = size << 1
        weights = inputs[size:double_size]
        equity = inputs[-1]
        for i, price in enumerate(inputs[:size]):
            outputs[i] = numpy.floor(weights[i] * equity / price)


class CashToFracSharesTx(FastTx):
    """Use cash to buy shares and include fractional shares.
    """

    def __init__(self, price_names, cash_names, position_names):
        assert len(price_names) == len(position_names)
        super().__init__(price_names + cash_names, position_names)

    def startup(self, dataframe):
        state = numpy.zeros(len(self.output_col_names()))
        return state

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        size = len(outputs)
        cash = sum(inputs[size:])
        for i, price in enumerate(inputs[:size]):
            outputs[i] = state[i] + cash / price / size
            state[i] = outputs[i]


class StkTradeWithSplitsExecTx(FastTx):
    """Compute calculating stock trade executions including stock splits.

    Similar to StkTradeExecTx but handles splits.

    Basically this takes in some target positions and trade flags and
    produces the pre and post trade positions while taking account
    possible stock splits (and reverse splits). This is useful for when
    you have a quantitative strategy computing target positions all the
    time but you only want to actually trade occaionsally (e.g., every
    Tuesday or every month end or when target positions are far enough
    from current positions).

    The following illustrates example usage:

>>> import pandas
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import StkTradeWithSplitsExecTx
>>> df = pandas.DataFrame({
...     'target_shares':  [100*i for i in range(6)],
...     'split_factor': [1, 1, .5, 1, 2, 1],
...     'trade_flag': [0, 1, 0, 0, 1, 0]})
>>> apply_chain(df, [StkTradeWithSplitsExecTx(
...     ['split_factor'], ['pre_trade_shares'], ['target_shares'],
...     ['trade_flag'], ['post_trade_shares'])])
>>> print(df)  # cash flow is negative when buying and positive when selling
   target_shares  split_factor  trade_flag  pre_trade_shares  post_trade_shares
0            0.0           1.0         0.0               0.0                0.0
1          100.0           1.0         1.0               0.0              100.0
2          200.0           0.5         0.0              50.0               50.0
3          300.0           1.0         0.0              50.0               50.0
4          400.0           2.0         1.0             100.0              400.0
5          500.0           1.0         0.0             400.0              400.0

Notice that while the target shares is changing each day, we only
actually trade on days indicated by `trade_flag`.

    """
    def __init__(self, split_factor_names, pre_trade_names, target_names,
                 trade_flag_names, post_trade_names):
        """Initializer.

        :param split_factor_names:  List of names for columns representing
                                    "split factor". If this is less than
                                    1 it means a reverse split and if it
                                    is greater than 1 it means a split. We
                                    set the pre trade position to the
                                    split factor times the previous post
                                    trade position.

        :param pre_trade_names:    List of names for columns representing
                                   "pre trade" positions. These are basically
                                   the number of shares or units before the
                                   market opened. The difference in between
                                   values of post_trade_names and
                                   pre_trade_names is interpreted as the
                                   number of units traded. (Splits, stock
                                   dividends or other ways of changing the
                                   share count that do not include trading
                                   should be reflected as a change from
                                   yesterday's post_trade_names to today's
                                   pre_trade_names).


        :param target_names:       List of names indicating the target
                                   position to adopt when indicated by
                                   trade flag.

        :param trade_flag_names:   List of names indicating when to trade.

        :param post_trade_names:   List of names for columns representing
                                   "post trade" positions. These are basically
                                   the number of shares or units after the
                                   market closes (e.g., after you execute any
                                   trades for the day/bar).

        """
        assert len(split_factor_names) == len(pre_trade_names)
        assert len(pre_trade_names) == len(post_trade_names)
        assert len(pre_trade_names) == len(trade_flag_names)
        assert len(target_names) == len(pre_trade_names)
        super().__init__(target_names + trade_flag_names + split_factor_names,
                         pre_trade_names + post_trade_names)

    def startup(self, dataframe: pandas.DataFrame) -> NDArray[numpy.float64]:
        out_size = len(self.output_col_names())
        result = numpy.zeros(1 + out_size//2)
        result[0] = out_size//2
        return result

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        size = numpy.int32(state[0])
        double_size = size << 1
        targets = inputs[:size]
        flags = inputs[size:double_size]
        split_factors = inputs[double_size:]
        for i, f in enumerate(flags):
            # set pre trade pos based on previous day
            outputs[i] = state[i+1] * split_factors[i]
            if f:  # trade flag says to trade
                outputs[i+size] = targets[i]  # set post trade position to tgt
            else:
                outputs[i+size] = outputs[i]  # set post trade position to pre
            state[i+1] = outputs[i+size]  # save post trade pos in state


class TradeFlagOnDiff(FastTx):
    """Generate trade flags based on difference in positions.

This transform is designed to generate a trade flag (value = 1) if
the sum of absolute differences between the target and post_trade
positions (weighted by price) exceeds some threshold of equity.

The following illustrates example usage:

>>> import pandas
>>> from fast_tx.core import apply_chain
>>> from fast_tx.stk_tx import TradeFlagOnDiff, FastStkEquityCalc
>>> df = pandas.DataFrame({
...     't_ABC':  [100*i + 1 for i in range(6)],
...     't_XYZ':  [200*i + 1 for i in range(6)],
...     'pos_ABC':  [100*i for i in range(6)],
...     'pos_XYZ':  [200*i for i in range(6)],
...     'price_ABC':  [(10 + i*.1) for i in range(6)],
...     'price_XYZ':  [(20 - i*.15) for i in range(6)],
...     'cash': [100]*6})
>>> df.loc[4,'price_XYZ'] = 2
>>> df.loc[4,'pos_XYZ'] = 700
>>> apply_chain(df, [FastStkEquityCalc(['price_ABC', 'price_XYZ'],
...     ['pos_ABC', 'pos_XYZ'], 'cash', 'equity'),
... TradeFlagOnDiff(
...     ['t_ABC', 't_XYZ'], ['price_ABC', 'price_XYZ'],
...     ['pos_ABC', 'pos_XYZ'], 'equity',
...     ['flag_ABC', 'flag_XYZ'])])
>>> print(df[[n for n in df if n not in ('cash','equity')]])
   t_ABC   t_XYZ  pos_ABC  pos_XYZ  price_ABC  price_XYZ  flag_ABC  flag_XYZ
0    1.0     1.0      0.0      0.0       10.0      20.00       0.0       0.0
1  101.0   201.0    100.0    200.0       10.1      19.85       1.0       1.0
2  201.0   401.0    200.0    400.0       10.2      19.70       0.0       0.0
3  301.0   601.0    300.0    600.0       10.3      19.55       0.0       0.0
4  401.0   801.0    400.0    700.0       10.4       2.00       0.0       0.0
5  501.0  1001.0    500.0   1000.0       10.5      19.25       1.0       1.0

Notice that we have a trade triggered at index 1 because of the big difference
between position and target on index 0 and again on index 5 because of the big
difference between position and target on index 5.

    """
    def __init__(self, target_names, price_names, post_trade_names,
                 equity_name, trade_flag_names, threshold=0.01):
        """Initializer.

        :param target_names:       List of names indicating the target
                                   position to adopt if we trade.

        :param price_names:        Prices corresponding to target_names

        :param post_trade_names:   List of names indicating post trade
                                   positions.

        :param equity:             String name indicating equity column.

        :param trade_flag_names:   List of names indicating when to trade.
                                   If these exist prior to applying this
                                   transform, we "OR" the operation of this
                                   transform with existing flags. This lets
                                   do something like let you set trade flags
                                   for the start of the month yourself and
                                   then apply this class to get threshold
                                   based trades in addition.

        :param threshold:          Minimum threshold above which trade flags
                                   are turned on.
        """
        assert len(price_names) == len(target_names)
        assert len(price_names) == len(post_trade_names)
        assert len(price_names) == len(trade_flag_names)
        assert threshold > 0
        self._threshold = threshold
        super().__init__({'target': target_names, 'price': price_names,
                          'post_trade': post_trade_names,
                          'trade_flags': trade_flag_names,
                          'equity': [equity_name]}, trade_flag_names)
        self.bind_unpack()
        self.bind_post_process_state()
        self.bind_calc_row()

    def startup(self, dataframe: pandas.DataFrame) -> NDArray[numpy.float64]:
        """Implement as required by parent.

We return a buffer with the same size as the output trade flags.  It
will be used by post_process_state to capture the intended value of
the output trade flags. See bind_post_process_state and
post_process_state for details of how the state works.
        """
        out_size = len(self.output_col_names())
        result = numpy.zeros(out_size)
        return result

    def bind_calc_row(self):
        """Bind a function for the calc_row method.

We dynamically bind the calc_row method as a closure so the numba
compiled version can easily see the size and sizex4 variables.
        """
        size = len(self.output_col_names())
        flag_slice = self.islice('trade_flags')
        @numba.njit(numba.void(numba.float64, numba.float64[:],
                               numba.float64[:], numba.float64[:]),
                    cache=True)
        def calc_row(_index_value: numpy.float64,
                     state: NDArray[numpy.float64],
                     inputs: NDArray[numpy.float64],
                     outputs: NDArray[numpy.float64]) -> None:
            """Calculte the trade flags for the row.

We set the output trade flags based on the flag values saved to the state
by post_process_state combined with the logical AND of the trade flag
values seen as input. See docs of post_process_state for more details.
            """
            flags = inputs[flag_slice]
            for i in range(size):
                outputs[i] = state[i] or (  # also check if flag is
                    (not numpy.isnan(flags[i])) and flags[i])  # already on
        self.calc_row = calc_row

    def bind_unpack(self):
        """Dynamacially bind the unpack method.
        """
        threshold = self._threshold
        size = len(self.output_col_names())  # used in closure below
        target_slice = self.islice('target')
        price_slice = self.islice('price')
        post_trade_slice = self.islice('post_trade')
        equity_idx = self.index('equity')

        @numba.njit(Tuple((
            numba.float64, numba.float64, numba.float64,
            numba.float64[:], numba.float64[:], numba.float64[:]))(
                numba.float64[:], numba.float64[:]), cache=True)
        def unpack(_state, inputs):
            """Helper to unpack state and inputs into needed variables.
            """
            equity = inputs[equity_idx]
            targets = inputs[target_slice]
            prices = inputs[price_slice]
            post_trade = inputs[post_trade_slice]
            return (threshold, size, equity, targets, prices, post_trade)
        self.unpack = unpack

    def bind_post_process_state(self):
        """Dynamically bind the post_process_state method.
        """
        unpack = self.unpack

        @numba.njit(numba.void(numba.float64, numba.float64[:],
                               numba.float64[:]), cache=True)
        def post_process_state(_index_value, state, inputs):
            """Post process row to get post trade positions, equity, etc..

We update state *AFTER* row has been fully processed so we can see the
post trade position, equity, and so on. We then save post trade
position for row into state so when `calc_row` is executed on next
row, it can look at the state to get the previous row's post trade
position.
            """
            (threshold, size, equity, targets, prices, post_trade
             ) = unpack(state, inputs)
            abs_diff = 0
            for i in range(size):
                abs_diff += abs(
                    (0 if numpy.isnan(targets[i]) else targets[i]
                     ) - (0 if numpy.isnan(post_trade[i]) else post_trade[i])
                ) * (0 if numpy.isnan(prices[i]) else prices[i])
            if equity != 0 and abs_diff/equity > threshold:
                for i in range(size):
                    state[i] = 1
            else:
                for i in range(size):
                    state[i] = 0
        self.post_process_state = post_process_state
