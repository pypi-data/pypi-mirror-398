
import typing

import numba
from numba import float64, int64, typeof
from numba.experimental import jitclass
from numba.types import ListType, unicode_type
from numba.typed import List as NumbaList
import numpy
import pandas

from fast_tx.core import FastTx
from fast_tx.experimental import apply_chain_jc


@jitclass([
    ('params', float64[:]),               
    ('_input_col_names', ListType(unicode_type)),
    ('_output_col_names', ListType(unicode_type)),
    ('state', float64[:]),
    ])
class EWM:

    def __init__(self, params, input_col_names, output_col_names):
        self.params = params
        self._input_col_names = input_col_names
        self._output_col_names = output_col_names
        self.state = numpy.zeros(len(input_col_names), dtype=numpy.float64)

    def input_col_names(self):
        return self._input_col_names

    def output_col_names(self):
        return self._output_col_names    

    def calc_row(self, index_value,
                 inputs: float64[:], outputs: float64[:]):
        self.state[:] = (1-self.params)*self.state[:] + self.params*inputs
        outputs[:] = self.state[:]


@jitclass([
    ('threshold', int64[:]),               
    ('_input_col_names', ListType(unicode_type)),
    ('_output_col_names', ListType(unicode_type)),
    ('count', int64[:]),
    ])
class OnlyFirstN:

    def __init__(self, threshold, input_col_names, output_col_names):
        self.threshold = threshold
        self._input_col_names = input_col_names
        self._output_col_names = output_col_names
        self.count = numpy.zeros(len(input_col_names), dtype=numpy.int64)

    def input_col_names(self):
        return self._input_col_names

    def output_col_names(self):
        return self._output_col_names    

    def calc_row(self, index_value,
                 inputs: float64[:], outputs: float64[:]):
        for i in range(len(inputs)):
            if self.count[i] >= self.threshold[i]:
                outputs[i] = 0  # already have N non-null so zero output
            elif numpy.isnan(inputs[i]):  # found a nan so just use 0
                outputs[i] = 0
            else:  # founda non-nan so pass to output and incr count
                outputs[i] = inputs[i]
                self.count[i] += 1


def test_jc_EWM():
    df = pandas.DataFrame({
        'a': [1.1, 2.2, 3.3, 4.4, 5.5],
        'b': [10.0, 20.5, 30.1, 40.8, 50.2],
        'c': [0.12, 0.34, 0.56, 0.78, 0.90]})
    golden = df.copy()
    zp_df = pandas.concat([pandas.DataFrame({'a':0,'b':0,'c':0},index=[-1]),
                           df])  # zero padded for use in verifying EWM
    params = [.1, .2, .3]
    i_cols = NumbaList.empty_list(unicode_type)
    for item in ('a', 'b', 'c'):
        i_cols.append(item)
    o_cols = NumbaList.empty_list(unicode_type)        
    for item in i_cols:
        o_cols.append('out_' + item)
    jc_list = (  # Needs to be a tuple for numba literal_unroll
        EWM(numpy.array(params),i_cols, o_cols),
    )
    apply_chain_jc(df, jc_list)
    for i, name in enumerate(zp_df):
        out_name = 'out_' + name
        golden[out_name] = zp_df[name].ewm(
            alpha=params[i], adjust=0).mean().iloc[1:]
        assert (golden[out_name] == df[out_name]).all()


def numba_s_list(inputs: typing.Sequence[str]):
    """Helper function to create typed list of strings that numba wants.

Numba is cranky about reflected lists and so we need to construct a list
in a way where the types are very explicit. This function takes in a
sequence of strings and produces a numba typed list of strings.    
    """
    result = NumbaList.empty_list(unicode_type)
    for item in inputs:
        result.append(item)
    return result


def test_jc_OnlyFirstN():
    df = pandas.DataFrame({
        'a': [1.1, 2.2, 3.3, 4.4, 5.5],
        'b': [10.0, 20.5, 30.1, 40.8, 50.2],
        'c': [numpy.nan, 0.34, 0.56, 0.78, 0.90]})
    golden = df.copy()
    golden[['out_' + n for n in df]] = 0.0
    golden.loc[:1, 'out_a'] = df['a'].loc[:1]
    golden.loc[:2, 'out_b'] = df['b'].loc[:2]
    golden['out_c'] = df['c']
    golden.loc[0, 'out_c'] = 0.0
    i_cols = numba_s_list(['a', 'b', 'c'])
    o_cols = numba_s_list(['out_' + i for i in i_cols])
    tx = OnlyFirstN(numpy.array([2, 3, 4]), i_cols, o_cols)
    apply_chain_jc(df, [tx])
    assert (df != golden).sum().sum() == 1  # only NaN gives a non-match
    

def test_jc_EWM_OnlyFirstN():
    """Test jitted class with two different kinds of transforms.

This function tests applying jitted classes to a DataFrame with
two different kinds of jitted class with different types of parameters
and states. This verifies that:

    1. We can use heterogeneous classes (same call signature but
       different internal state and calculation).
    2. We can apply a sequence of classes to each row.

    """
    df = pandas.DataFrame({
        'a': [1.1, 2.2, 3.3, 4.4, 5.5],
        'b': [10.0, 20.5, 30.1, 40.8, 50.2],
        'c': [0.12, 0.34, 0.56, 0.78, 0.90]})
    golden = df.copy()
    zp_df = pandas.concat([pandas.DataFrame({'a':0,'b':0,'c':0},index=[-1]),
                           df])  # zero padded for use in verifying EWM
    params = [.1, .2, .3]
    i_cols = numba_s_list(['a', 'b', 'c'])
    o_cols = numba_s_list(['out_' + i for i in i_cols])
    jc_list = (  # Needs to be a tuple for numba literal_unroll
        EWM(numpy.array(params), i_cols, o_cols),
        OnlyFirstN(numpy.array([2, 3, 4]), o_cols, o_cols),
    )
    apply_chain_jc(df, jc_list)
    for i, name in enumerate(zp_df):
        out_name = 'out_' + name
        golden[out_name] = zp_df[name].ewm(
            alpha=params[i], adjust=0).mean().iloc[1:]
        t = jc_list[1].threshold[i]
        assert (golden[out_name].iloc[:t] == df[out_name].iloc[:t]).all()
        assert (df[out_name].iloc[t:] == 0).all()
        

    
                

    
