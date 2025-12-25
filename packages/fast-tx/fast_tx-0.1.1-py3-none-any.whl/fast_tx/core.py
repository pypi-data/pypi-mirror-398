"""Module defining the FastTx class for DataFrame transformations.

# Introduction

The main goal of this module are to provide the `FastTx` class and the
`apply_chain` function to apply a chain of `FastTx` instances to a
dataframe to do some row operations.

The `FastTx` class is designed so that you can create sub-classes with
a structure that allows numba just-in-time (JIT) compilation into very
fast numerical operations. You need relatively large dataframes or
relatively complicated transforms to see the benefits of JIT, but once
you get there, the speed-ups can be pretty dramatic.

Making this work correctly is complicated because numba needs
homogenous structures (arrays and functions) to be able to JIT compile
effectively.

# Testing

If you are testing numba related code, you may want to set the
enviroment variable `NUMBA_DISABLE_JIT=1` to prevent JIT
compiling. That will allow you to use pdb and generally get better
error information.

# Motivation

The FastTx infrastructure is mainly useful when you have mixed row and
column operations. If you just have operations on rows of a column
(e.g., rolling mean), you can just call your functions/operations and
compose similar operations. You can even use numba's guvectorize to
relatively painlessly vectorize your operations.

If you have operations on columns of a row (e.g., adding one column to
another), you can just call those operations/functions as needed.

The complicated case is when you have a mix of row and column
operations and you want to be able to compose such operations or let
people mix in their own versions of such operations. As a very simple
example, imagine you have some time series data in a[t] (represented
as a pandas DataFrame) and you want to implement a system which
evolves according to:

   b[t]=c[t-1]/a[t]  c[t]=a[t]+b[t]

While c[t] is just the sum of two columns, b[t] is an operation which
depends on the previous row. So you have mixed row and column
operations. This case is trivial, but if you have a more complicated
DataFrame and want users to be able to create, compose, and calculate
mixed row and column operations, you may have poor performance in a
naive implementation.

The FastTx infrastructure is designed to let you write almost
arbitrary functions in a relatively simple way which can be easily
combined and composed but still run quickly.

While I have not experimented with Polars, I think that Polars
provides benefits mainly for cases when you can parallelize
operations. The use cases for fast_tx are mainly when you have mixed
operations like the above with many inter/intra row/column
dependancies and so parallization would not work.

# Copyright

Copyright (c) 2025, Emin Martinian - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
See AOCKS_LICENSE at the top-level of this distribution for more information
or write to emin.martinian@gmail.com for more information.

"""

import doctest
import logging
import typing

import numba
import numpy
from numpy.typing import NDArray
import pandas

from fast_tx import buffer_tools


class FastTx:
    """Fast row transform for a DataFrame.

    FastTx is an abstract class (really a protocol) for defining fast
    row transformations to apply to a dataframe. The key goals are:

      1. Enable efficient operations.
      2. Provide a structure where we can have a chain of N `FastTx`
         instances such that for each row, we can efficiently apply each
         instance to the row (including results of previous `FastTx`
         applied to the row).

    See methods for further documentation and see `apply_chain` for how
    to apply a chain of such transforms to a DataFrame.


>>> from fast_tx.core import (
...     pandas, RowShiftTx, SimpleEWA, apply_chain)
>>> df = pandas.DataFrame({
...    'a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'b': [10.0, 20.5, 30.1, 40.8, 50.2],
...    'c': [0.12, 0.34, 0.56, 0.78, 0.90],
...    'd': [1, 2, 3, 4, 5]})
>>> print(df)
     a     b     c  d
0  1.1  10.0  0.12  1
1  2.2  20.5  0.34  2
2  3.3  30.1  0.56  3
3  4.4  40.8  0.78  4
4  5.5  50.2  0.90  5
>>> apply_chain(df, [RowShiftTx(list(df)), RowShiftTx(list(df))])
>>> print(df)
      a    b    c     d
0  0.12  1.0  1.1  10.0
1  0.34  2.0  2.2  20.5
2  0.56  3.0  3.3  30.1
3  0.78  4.0  4.4  40.8
4  0.90  5.0  5.5  50.2
    """

    def __init__(self, input_col_names, output_col_names=None):
        """Initializer.

    :param input_col_names:   Either a list of strings indicating the
                              names of input columns or a dictionary
                              where keys are internal names for groups
                              of columns and values are list of strings
                              indicating the columns for that group.

                              For example, you could provide something like
                              ['price_ABC', 'price_XYZ', 'vol_ABC', 'vol_XYZ']

                              or

                              {'price': ['price_ABC', 'price_XYZ'],
                               'volume': ['vol_ABC', 'vol_XYZ']}

                              where the latter is preferable since it
                              allows using the islice method.

    :param output_col_names=None:  Optional list of output columns.

        """
        if isinstance(input_col_names, dict):
            self._input_col_dict = dict(input_col_names)
            self._input_col_names = sum(input_col_names.values(), [])
        else:
            self._input_col_dict = None
            self._input_col_names = input_col_names
        self._output_col_names = output_col_names if (
            output_col_names is not None) else input_col_names
        self._islice_dict = {}

    def startup(self, dataframe: pandas.DataFrame) -> NDArray[numpy.float64]:
        """Take dataframe as input and prepare startup. Return 1d state array.

        *IMPORTANT*:  The resulting state *MUST* be a 1-d array of float64
                      for numba JIT compiling to work correctly. You can
                      internally reshape/ravel/unravel the 1-d but when
                      passing it around it must satisfiy the type signature.

        Most transforms will not need to do anything here, but the dataframe
        is provided as input if needed. The `dataframe` should **NOT** be
        modified in any way since that is what the `calc_row` method is for.

        Mainly this should compute a state array (which must be a numpy
        array of type float64) which will be repeatedly passed to the
        `calc_row` method.
        """
        _ = dataframe
        return numpy.array([], dtype=numpy.float64)

    def shutdown(self, dataframe: pandas.DataFrame):
        """Called after we have finished processing a dataframe.

        Most transforms will not need to do anything here, but the dataframe
        is provided as input if needed. The `dataframe` should **NOT** be
        modified in any way since that is what the `calc_row` method is for.
        """

    def input_col_names(self) -> list:
        """Return a list of the input column names needed by `calc_row`.

        These input columns will be provided as the `inputs` argument
        to `calc_row`.
        """
        return self._input_col_names

    def output_col_names(self) -> list:
        """Return a list of the output column names produced by `calc_row`.

        These output columns will be provided as the `outputs` argument
        to `calc_row` which it will modify in place.
        """
        return self._output_col_names

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        """Calculate the transformed results for a row.

        :param index_value:    Value of the dataframe index we are currently
                               working on (as type numpy.float64).

        :param state:  State array produced by the `startup`
                       method. This state can be modified in place to
                       pass state to subsequent calls to `calc_row` and/or
                       `post_process_state`.

        :param inputs:  Array of inputs for the current row as named by
                        the `input_col_names` method.

        :param outputs:  Array of output for the current row as named by
                         the `output_col_names` method. The function should
                         write outputs to this array.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:   Do main calculations.

                   *IMPORTANT*:  Your function must *EXACTLY* match the type
                                 signature (including decorators) for numba
                                 JIT compiling to work.

        """
        raise ValueError('Subclass must override')  # pragma: no cover

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:]), cache=True)
    def post_process_state(index_value: numpy.float64,
                           state: NDArray[numpy.float64],
                           inputs: NDArray[numpy.float64]) -> None:
        """Post process state at end of each row.

        :param index_value:    Value of the dataframe index we are currently
                               working on (as type numpy.float64).

        :param state:  State array produced by the `startup`
                       method. This state can be modified in place to
                       pass state to subsequent calls to `calc_row` and/or
                       `post_process_state`.

        :param inputs:  Array of inputs for the current row as named by
                        the `input_col_names` method.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Sometimes you want to update your state based on the
                  final results of a row. The `calc_row` method for
                  each transform in a chain is called in order and
                  hence each transform in the chain may see different
                  inputs. After all `calc_row` methods have been called,
                  we then do a second pass and call `post_process_state`
                  for each transform. No transform should modify the
                  row via `post_process_state` (but may modify its own
                  internal state). This allows transforms to "see" the
                  final value of a row.
        """

    def islice(self, name: str):
        """Return a slice object for the column group matching `name`.

        :param name:  String name of a column group passed to `__init__`
                      (i.e., a key of the dictionary passed to `__init__`
                       for `input_col_names`).

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  A slice object indicating the start and end of
                  that column group in `self.input_col_names()`.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  If you pass a dict to `__init__` indicating groups
                  of column names, this method gets you a slice for
                  the desired group.

        """
        result = self._islice_dict.get(name, None)
        if result is not None:
            return result
        start = 0
        for group_name, col_names in self._input_col_dict.items():
            if group_name == name:
                result = slice(start, start + len(col_names))
                self._islice_dict[name] = result
                return result
            start += len(col_names)
        raise KeyError(f'{name=} not in found in {self._input_col_dict}')

    def index(self, name: str):
        """Return index of first element in column group with given `name`.

        :param name:  String name of column group to find.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  Starting index of first item in given column group.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Basically like calling self.islice(name).start; see
                  docs for `islice` for details.

        """
        return self.islice(name).start

    @classmethod
    def modify_calc_row(cls):
        """Modify (or create) calc_row method.

This method will be called by `__init_subclass__`. The default version
checks if the class has a `calc_row_py` method and if so it will JIT-compile
the `calc_row_py` with numba and set `self.calc_row` to the complied
function. This makes it so you can sub-class FastTx and just define
a pure python sub-class with the `calc_row_py` method.
        """
        if hasattr(cls, 'calc_row_py'):
            logging.debug('Overriding calc_row for cls %s from calc_row_py',
                          cls)
            try:  # Try to njit with cache=True since that is faster
                cls.calc_row = staticmethod(numba.njit(
                    numba.void(numba.float64, numba.float64[:],
                               numba.float64[:], numba.float64[:]),
                    cache=True)(cls.calc_row_py))
            except RuntimeError as problem:  # but retry if cache fails
                if str(problem).startswith('cannot cache function'):
                    logging.warning(
                        'Cannot cache %s: %s; will try njit w/o cache',
                        cls.calc_row_py, problem)
                    cls.calc_row = staticmethod(numba.njit(
                        numba.void(numba.float64, numba.float64[:],
                                   numba.float64[:], numba.float64[:]),
                        cache=False)(cls.calc_row_py))
                else:
                    raise

    @classmethod
    def modify_post_process_state(cls):
        """Modify (or create) post_process_state method.

This method will be called by `__init_subclass__`. The default version
checks if the class has a `post_process_state_py` method and if so it
will JIT-compile the `post_process_state_py` with numba and set
`self.post_process_state` to the complied function. This makes it so
you can sub-class FastTx and just define a pure python sub-class with
the `post_process_state_py` method.

        """
        if hasattr(cls, 'post_process_state_py'):
            logging.debug('Overriding %s for cls %s from %s',
                          'post_process_state', cls,
                          'post_process_state_py')
            cls.post_process_state = staticmethod(numba.njit(
                numba.void(numba.float64, numba.float64[:],
                           numba.float64[:]), cache=True)(
                               cls.post_process_state_py))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.modify_calc_row()
        cls.modify_post_process_state()


class RowShiftTx(FastTx):
    """Simple example of FastTx to just circular shift a row.


>>> from fast_tx.core import (
...     pandas, RowShiftTx, apply_chain)
>>> df = pandas.DataFrame({
...    'a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'b': [10.0, 20.5, 30.1, 40.8, 50.2],
...    'c': [0.12, 0.34, 0.56, 0.78, 0.90]})
>>> tx = RowShiftTx(['a','b','c'])
>>> apply_chain(df, [tx])
>>> print(df)
      a    b     c
0  0.12  1.1  10.0
1  0.34  2.2  20.5
2  0.56  3.3  30.1
3  0.78  4.4  40.8
4  0.90  5.5  50.2
    """

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        outputs[0] = inputs[-1]
        outputs[1:] = inputs[:-1]


class SimpleEWA(FastTx):
    """Simple example of FastTx to just circular shift a row.

    The following illustrates example usage:

>>> from fast_tx.core import (pandas, SimpleEWA, apply_chain)
>>> df = pandas.DataFrame({
...    'a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'b': [10.0, 20.5, 30.1, 40.8, 50.2],
...    'c': [0.12, 0.34, 0.56, 0.78, 0.90]})
>>> zp_df = pandas.concat([pandas.DataFrame({'a':0,'b':0,'c':0},index=[-1]),
...     df])  # zero padded for use in verifying EWM
>>> tx = SimpleEWA([.1, .2, .3], ['a','b','c'], [f'out_{n}' for n in df])
>>> apply_chain(df, [tx])
>>> print(df)
     a     b     c     out_a    out_b     out_c
0  1.1  10.0  0.12  0.110000   2.0000  0.036000
1  2.2  20.5  0.34  0.319000   5.7000  0.127200
2  3.3  30.1  0.56  0.617100  10.5800  0.257040
3  4.4  40.8  0.78  0.995390  16.6240  0.413928
4  5.5  50.2  0.90  1.445851  23.3392  0.559750
>>> all([(zp_df['a'].ewm(alpha=.1,adjust=0).mean().iloc[1:]==df.out_a).all(),
...      (zp_df['b'].ewm(alpha=.2,adjust=0).mean().iloc[1:]==df.out_b).all(),
...      (zp_df['c'].ewm(alpha=.3,adjust=0).mean().iloc[1:]==df.out_c).all()])
True
    """

    def __init__(self, alphas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alphas = numpy.asarray(alphas)

    def startup(self, dataframe):
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        # Make sure to use outputs[:] so we assign into the outputs array
        # and don't just create a new variable named `outputs`.
        alphas = state[:len(outputs)]
        prev_out = state[len(outputs):]
        outputs[:] = alphas * inputs + (1-alphas) * prev_out
        state[len(outputs):] = outputs[:]


class SafeSum(FastTx):
    """Sum inputs (ignoring na) to produce output.

    Should only use single output column since all outputs get same value.
    """

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        outputs[:] = sum([  # pylint: disable=consider-using-generator
            i for i in inputs if not numpy.isnan(i)])


class Accumulate(FastTx):
    """Sum inputs (ignoring nan) and add to previous output.

>>> from fast_tx.core import (pandas, numpy, Accumulate,
...     apply_chain)
>>> df = pandas.DataFrame({
...    'a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'b': [10.0, 20.5, 30.1, 40.8, 50.2],
...    'c': [0.12, 0.34, 0.56, 0.78, 0.90]})
>>> tx = Accumulate(['a','b','c'], ['acc'])
>>> apply_chain(df, [tx])
>>> assert df['acc'].iloc[0] == sum(df.iloc[0][['a','b','c']])
>>> assert numpy.max(numpy.abs((df.iloc[1:][['a','b','c']].sum(axis=1)
...     + df.acc.shift(1).iloc[1:]).values - df.acc.iloc[1:].values)) < 1e-9


    """

    def startup(self, dataframe):
        state = numpy.zeros(1)
        return state

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        outputs[0] = sum([  # pylint: disable=consider-using-generator
            i for i in inputs if not numpy.isnan(i)]) + state[0]
        state[0] = outputs[0]


class Lag(FastTx):
    """Simple example of FastTx to lag a row (like shift in pandas).

    This is slightly tricky because what we want to do is capture the
    value of a row *AFTER* all calculations and then apply it *BEFORE*
    new calculations. This requires implementing post_process_state.

    The following illustrates example usage:

>>> from fast_tx.core import (pandas, Lag, SafeSum,
...     apply_chain)
>>> df = pandas.DataFrame({
...    'a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'b': [10.0, 20.5, 30.1, 40.8, 50.2],
...    'c': [0.12, 0.34, 0.56, 0.78, 0.90]})
>>> tx = Lag(1, ['a','b','d'], ['lag_a', 'lag_b', 'lag_d'])
>>> apply_chain(df, [tx, SafeSum(['lag_b','c'], ['d']),
...     SafeSum(['lag_d','c'], ['e'])])
>>> print(df)
     a     b     c  lag_a  lag_b  lag_d      d      e
0  1.1  10.0  0.12    0.0    0.0   0.00   0.12   0.12
1  2.2  20.5  0.34    1.1   10.0   0.12  10.34   0.46
2  3.3  30.1  0.56    2.2   20.5  10.34  21.06  10.90
3  4.4  40.8  0.78    3.3   30.1  21.06  30.88  21.84
4  5.5  50.2  0.90    4.4   40.8  30.88  41.70  31.78

Note in the above that `lag_d` is correct. This may seem trivial, but
is a bit tricky (and hence why we needed to implement
post_process_state) since `lag_d` is computed by the 2nd transform
(which comes **AFTER** the Lag transform). The Lag transform must come
**BEFORE** everything else in the chain so it can put its values into
the row before the other transforms process the row, but the Lag
transform must update its state **AFTER** all calculations so it
captures the final state of the row. This is achieved by having a
seprate function for post_process_state vs calc_row.


We can also verify that Lag matches pandas shift:


>>> for s in range(1, 4):  # check lag matches shift
...     apply_chain(df, [Lag(s, tx.input_col_names(), tx.output_col_names())])
...     assert not (df.shift(s)[tx.input_col_names()].values
...                 - df[tx.output_col_names()].values)[s:].any()
...

    """
    def __init__(self, lag_length, *args, **kwargs):
        self.lag_length = lag_length
        assert lag_length > 0
        super().__init__(*args, **kwargs)

    def startup(self, dataframe):
        state = numpy.zeros(1 + self.lag_length * len(self._input_col_names))
        state[-1] = self.lag_length
        return state

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:], numba.float64[:]), cache=True)
    def calc_row(index_value: numpy.float64, state: NDArray[numpy.float64],
                 inputs: NDArray[numpy.float64],
                 outputs: NDArray[numpy.float64]) -> None:
        outputs[:] = state[-len(outputs)-1:-1]

    @staticmethod
    @numba.njit(numba.void(numba.float64, numba.float64[:],
                           numba.float64[:]), cache=True)
    def post_process_state(index_value, state, inputs):
        lag_length = state[-1]
        if lag_length > 1:
            state[len(inputs):-1] = state[
                :-len(inputs)-1]
        state[:len(inputs)] = inputs[:]


def apply_chain(dataframe: pandas.DataFrame,
                tx_chain: typing.List[FastTx]):
    """Apply given transform chain to dataframe.

    :param dataframe:  DataFrame to modify.

    :param tx_chain:  List of `FastTx` instances to apply to dataframe.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Apply the `tx_chain`.  See docs for `FastTx` and example
              transforms like `Lag` for example usage.

    """
    input_cols, output_cols, maincols = buffer_tools.prepare_cols(
        dataframe, tx_chain)
    states, state_len = buffer_tools.prep_states_array(tx_chain, dataframe)

    index, input_buffer, output_buffer, mainbuffer = buffer_tools.make_buffers(
        dataframe, maincols, input_cols, output_cols)

    calc_tx_list, post_process_tx_list = buffer_tools.prepare_tx_lists(
        tx_chain, FastTx.post_process_state,
        buffer_tools.noop_post_process_state)

    # If original dataframe has mixed types, mainbuffer may not be float.
    # We must force float for numba, but warn the user about that so they
    # can maybe try to fix type themselves.

    if mainbuffer.dtype != 'float64':  # pragma: no cover
        logging.warning('Buffer dataframe has type %s; will force float64',
                        mainbuffer.dtype)
        mainbuffer = mainbuffer.astype(numpy.float64)

    buffer_tools.apply_inner_loop(
        index.astype(numpy.float64), mainbuffer, input_buffer, output_buffer,
        states, state_len, calc_tx_list, post_process_tx_list,
        input_cols, output_cols)
    dataframe[list(maincols)] = mainbuffer

    for tx in tx_chain:
        tx.shutdown(dataframe)


if __name__ == '__main__':    # pragma: no cover
    doctest.testmod()         # pragma: no cover
    print('Finished tests')   # pragma: no cover
