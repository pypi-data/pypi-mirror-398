"""Tools to work with stock transforms and stock data.
"""

import types
import typing

import pandas

from fast_tx.core import Lag, Accumulate
from fast_tx.utils import date_to_utctimestamp
from fast_tx.stk_tx import (
    TradeFlagOnDiff, StkTradeWithSplitsExecTx, FastTradeCashFlowTx,
    WeightedPositionsTx, FastDivCashFlowTx, FastStkEquityCalc,
    DynamicWeightedPositionsTx)


class NameManager:
    """Class to manage names for stock calculations or other tasks.

    The idea is that you initialize this with a list of string assets
    you are interested in and then you can use it to make names
    as illustrated below:

>>> from fast_tx.stk_tools import NameManager
>>> mngr = NameManager(['SPY', 'GLD'])
>>> mngr.open.n, mngr.close.n
(['SPY_open', 'GLD_open'], ['SPY_close', 'GLD_close'])

    Sub-classes can override the name_for and name_list method if
    desired to control how names are created for assets.
    """

    def __init__(self, asset_list: typing.Sequence[str], specials=(
            ('overall', ('cash', 'cash_deposit', 'div_cash_flow',
                         'equity', 'trade_cash_flow')),)):
        """Initializer.

        :param asset_list:  List of strings reprsenting assets you care about.

        """
        self.asset_list = asset_list
        self.specials = dict(specials)

    @classmethod
    def name_for(cls, element, field, info=None):
        """Utility to generate a name for a field of some element.

        :param element:      Thing we are talking about (e.g., an asset).

        :param field:        Field we want.

        :param info=None:    Extra information

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  String name.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  The following illustrates example usage:

>>> NameManager.name_for('SPY', 'close')
'SPY_close'
>>> NameManager.name_for('SPY', 'close', 'lagged')
'SPY_close_lagged'

        """
        _ = cls
        result = f'{element}_{field}'
        if info is not None:
            result += '_' + info
        return result

    @classmethod
    def name_list(cls, asset_list, field, info=None):
        "Syntatic sugar to call cls.name_for for everything in asset_list."

        return [cls.name_for(a, field, info) for a in asset_list]

    def __getattr__(self, name):
        result = types.SimpleNamespace()
        if name in self.specials:
            for value in self.specials[name]:
                setattr(result, value, self.name_for(name, value))
        else:
            setattr(result, 'n', self.name_list(self.asset_list, name))
        setattr(self, name, result)  # basically caching this result
        return result


class StkCalcManager:
    """Helper to create transforms to manage stock calculations.
    """

    def __init__(self, names: NameManager):
        """Initializer.

        :param names: NameManager instance to use to generate names.

        """
        self.names = names

    def prep_divs(self, data: pandas.DataFrame, div_pay_dt_offset: int):
        """Prepare canoncial fields required for dividend info.

        :param data:         Dataframe with raw dividend data.

        :param div_pay_dt_offset:  How many days later to pay the dividend.
                                   Setting 0 makes the dividend paid the
                                   same day as the ex-dividend date. This
                                   can be useful for trying to match
                                   adjusted close calculations but is not
                                   realistic so you may want to set longer
                                   offsets.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Adds div_total and div_pay_dt fields to `data`.

        """
        for i, name in enumerate(self.names.divCash.n):
            divs = data[name]
            div_total = self.names.div_total.n[i]
            div_pay_dt = self.names.div_pay_dt.n[i]
            for ex_date, payment in divs.loc[divs != 0].items():
                iloc = data.index.get_loc(ex_date)
                data.loc[ex_date, div_total] = payment
                data.loc[ex_date, div_pay_dt] = date_to_utctimestamp(
                    data.index[iloc+div_pay_dt_offset].date())

    def make_tx_dict(self, weights, trade_threshold=None, pre_tx_dict=None):
        """Make dictionary of transforms to compute weighted stock positions.

        :param weights:  Either a list of floats for static weights or
                         the string, `'dynamic'` indicating we should look
                         for columns named `self.names.weights.n` for
                         weights.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  Dictionary of transforms to provide to apply_chain.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Create a dictionary of transforms to implement the
                  calculations for investing in the given assets based on
                  the given weights applied to the `self.names.overall.equity`
                  field. You will need to prepare a DataFrame with the
                  appropriate data.  See some example usage in
                  the `test_stock_calcs.py` file.

        """
        names = self.names
        if pre_tx_dict:
            tx_list = list(pre_tx_dict.items())
        else:
            tx_list = []
        if trade_threshold:
            tx_list.append(('trade_flag_tx', TradeFlagOnDiff(
                names.position.n, names.close.n, names.post_trade_pos.n,
                names.overall.equity, names.trade_flag.n, trade_threshold)))
        tx_list.extend([
            ('lag_tx', Lag(1, names.next_target.n, names.position.n)),
            ('exec_tx', StkTradeWithSplitsExecTx(
                names.splitFactor.n, names.pre_trade_pos.n, names.position.n,
                names.trade_flag.n, names.post_trade_pos.n)),
            ('trade_cash_flow_tx', FastTradeCashFlowTx(
                names.close.n, names.pre_trade_pos.n, names.post_trade_pos.n,
                names.overall.trade_cash_flow)),
            ('div_cash_flow_tx', FastDivCashFlowTx(
                names.div_total.n, names.div_pay_dt.n, names.pre_trade_pos.n,
                names.overall.div_cash_flow)),
            ('cash_acc_tx', Accumulate([
                names.overall.div_cash_flow, names.overall.trade_cash_flow,
                names.overall.cash_deposit], [names.overall.cash])),
            ('equity_tx', FastStkEquityCalc(
                names.close.n, names.post_trade_pos.n, names.overall.cash,
                names.overall.equity))])
        if weights == 'dynamic':
            tx_list.append(('wt_tx', DynamicWeightedPositionsTx(
                names.weights.n, names.close.n, names.overall.equity,
                names.next_target.n)))
        elif isinstance(weights, list):
            tx_list.append(('wt_tx', WeightedPositionsTx(
                weights, names.close.n, names.overall.equity,
                names.next_position_targets.n)))

        return dict(tx_list)
