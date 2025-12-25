"""Tools to help manage buffers for fast operations.
"""

import typing

import numba
from numba.typed import List  # pylint: disable=no-member, no-name-in-module
from numba.types import ListType, FunctionType
import numpy
from numpy.typing import NDArray
import pandas



# Define explicit type so we can type hint to numba so it compiles correctly.
CalcRowFuncType = FunctionType(numba.void(
    numba.float64, numba.float64[:], numba.float64[:], numba.float64[:]))
CalcRowFuncListType = ListType(CalcRowFuncType)

# Define explicit type so we can type hint to numba so it compiles correctly.
PostProcRowFuncType = FunctionType(numba.void(
    numba.float64, numba.float64[:], numba.float64[:]))
PostProcRowFuncListType = ListType(PostProcRowFuncType)


@numba.njit(numba.void(numba.float64, numba.float64[:],
                       numba.float64[:]), cache=True)
def noop_post_process_state(index_value: numpy.float64,
                            state: NDArray[numpy.float64],
                            inputs: NDArray[numpy.float64]) -> None:
    """Placeholder for post_process_state method that does nothing.

    Mainly used to be able to compare functions in _apply_inner_loop
    """
    _, _, _ = index_value, state, inputs  # pragma: no cover


def prep_states_array(tx_chain, dataframe):
    """Prepare states array for tx_chain and dataframe.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  A rectangular numpy array, `states`, where `states[i]`
              is an array for the state for `tx_chain[i]`. Since
              numba requires homogenous input, we must make this rectangular
              even thought `tx_chain[i]` may have a different length state
              than `tx_chain[j]`. We solve this by adding the original size
              of the state array as an extra element to the end so that
              later code can pass the correct sized state to each transform.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Prepare states for tx_chain and dataframe suitable for numba.

    """
    states_list = []
    for t_num, tx in enumerate(tx_chain):
        new_state = tx.startup(dataframe)
        assert new_state is not None, (
            f'startup for {tx} must return (possibly empty) array not None')
        states_list.append(new_state)

    s_len = numpy.asarray([len(s) for s in states_list])
    states = numpy.full((len(tx_chain), max(s_len)), numpy.nan)

    for t_num, tx in enumerate(tx_chain):
        if s_len[t_num]:
            states[t_num, :s_len[t_num]] = states_list[t_num]

    return states, s_len


def prepare_cols(dataframe: pandas.DataFrame,
                 tx_chain: typing.List['FastTx']) -> typing.Tuple[
                     numba.int64[:, :],
                     numba.int64[:, :],
                     typing.Dict[typing.Any, int],
                 ]:
    """Helper for apply_chain to prepare various columns.

    :param dataframe:    DataFrame to work on.

    :param tx_chain:   List of transforms to prepare to run on chain.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  The tuple (input_cols, output_cols, maincols) such that

         - The array, `input_cols`, is a homogenous numpy array of
           ints with input_cols[t] being the indexes needed by
           tx_chain[t] with input_cols[t][-1] being the number of
           inputs needed for tx_chain[t]. Entries past `input_cols[t][-1]`
           are set to nan. These indexes are relative to the `maincols`
           dict since we will only be working with those columns.
         - The array, `output_cols`, is a homogenous numpy array of
           ints with output_cols[t] being the indexes that tx_chain[t]
           will write to as outputs with output_cols[t][-1] being the number of
           outputs produced by tx_chain[t]. Entries past `output_cols[t][-1]`
           are set to nan. These indexes are relative to the `maincols`
           dict since we will only be working with those columns.
         - The `maincols` dict has keys as column keys (which could be strings
           or more complicated types of column keys) and values are the integer
           index for that column for all the input/output columns needed
           by the transforms in `tx_chain`.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:   Prepare information for columns as needed by apply_chain.
               See also `_make_buffers` since the columns produced here
               are also needed in there.

    """
    input_cols = []
    output_cols = []
    for tx in tx_chain:
        input_cols.extend(tx.input_col_names())
        output_cols.extend(tx.output_col_names())

    new_cols = set(output_cols) - set(dataframe)
    new_cols = {c: 1 for c in output_cols if c in new_cols}
    dataframe[list(new_cols)] = numpy.nan
    full_cols = list(set(input_cols).union(output_cols))

    maincols = {n: i for i, n in enumerate(full_cols)}

    input_cols = numpy.full((len(tx_chain), 1+max(len(tx.input_col_names())
                                                  for tx in tx_chain)), -1)
    output_cols = numpy.full((len(tx_chain), 1+max(len(tx.output_col_names())
                                                   for tx in tx_chain)), -1)
    for i, tx in enumerate(tx_chain):
        input_cols[i, :len(tx.input_col_names())] = [
            maincols[n] for n in tx.input_col_names()]
        output_cols[i, :len(tx.output_col_names())] = [
            maincols[n] for n in tx.output_col_names()]
        output_cols[i, -1] = -len(tx.output_col_names())

    return input_cols, output_cols, maincols


def prepare_tx_lists(tx_chain, base_func, noop_func):
    """Helper for apply_chain to extract functions to call as lists.

    For numba JIT compilation, we need arrays of functions of the same
    type. This function produces those.
    """
    calc_tx_list = List.empty_list(numba.void(
        numba.float64, numba.float64[:], numba.float64[:], numba.float64[:]
    ).as_type())
    post_process_tx_list = List.empty_list(numba.void(
        numba.float64, numba.float64[:], numba.float64[:]).as_type())

    for tx in tx_chain:
        calc_tx_list.append(tx.calc_row)
        if tx.post_process_state is base_func:
            post_process_tx_list.append(noop_func)
        else:
            post_process_tx_list.append(tx.post_process_state)

    return calc_tx_list, post_process_tx_list


def make_buffers(dataframe, maincols, input_cols, output_cols):
    """Helper for apply_chain to prepare buffers.

    :param dataframe:    Main DataFame to operate on.

    :param maincols:     Iterable of column keys to use for main buffer.

    :param input_cols:   Array of indexes needed for inputs.

    :param output_cols:  Array of indexes needed for outputs.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  The tuple (index, input_buffer, output_buffer, mainbuffer):

         - The array, `index`, is the dataframe index converted to float
           form if necessary so we can pass to numba jit compliation.
         - The array `input_buffer` is an array of floats big enough to
           to hold the longest input array needed by any transform from
           `input_cols`.
         - The array `output_buffer` is an array of floats big enough to
           to hold the longest output array needed by any transform from
           `output_cols`.
         - The 2-d array, `mainbuffer`, is all the input/output values from
           the main columns of the dataframe that we are going to work on.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  We want to prepare `mainbuffer` as just the parts of the
              dataframe we are going to work on. The input_buffer and
              output_buffer are store locations to use for transforms.
              The `index` is a float array suitable for numba. Basically
              we are getting things in a form for fast, efficient, numba
              JIT compiled operation.

    """

    mainbuffer = dataframe[list(maincols)].values

    if isinstance(dataframe.index, pandas.DatetimeIndex):
        index = numpy.array([d.timestamp() for d in dataframe.index])
    else:
        index = dataframe.index.to_numpy()

    input_buffer = numpy.empty(max(len(p) for p in input_cols),
                               dtype=numpy.float64)
    output_buffer = numpy.empty(max(len(p) for p in output_cols),
                                dtype=numpy.float64)

    return index, input_buffer, output_buffer, mainbuffer


@numba.njit(numba.void(numba.float64[:], numba.float64[:, :],
                       numba.float64[:], numba.float64[:],
                       numba.float64[:, :], numba.int64[:],
                       CalcRowFuncListType, PostProcRowFuncListType,
                       numba.int64[:, :], numba.int64[:, :]),
            cache=True)
def apply_inner_loop(
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        index, mainbuffer, input_buffer, output_buffer,
        states, state_len, calc_tx_list, post_process_tx_list,
        input_cols, output_cols):
    """Do inner loop for apply_chain method.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  This implements the inner loop for the `apply_chain` function.
              Basically, we take as input the cleaned up and standardized
              versions of everything and then iterate overall all the
              rows of mainbuffer to call `calc_row` for everything and
              then `post_process_state` for everything. This is JIT compiled
              so that looping is efficient but therefore requires all the
              inputs to be relatively standardized types and sizes.

               NOTE: JIT compiling this function is pretty essential.
               NOTE: If you JIT the transforms but not this, its worse
               NOTE: than using no JIT at all.
    """
    for r_num, row in enumerate(mainbuffer):
        for t_num, tx_func in enumerate(calc_tx_list):
            i = 0
            while input_cols[t_num][i] >= 0:
                input_buffer[i] = row[input_cols[t_num, i]]
                i += 1
            tx_func(index[r_num], states[t_num][:state_len[t_num]],
                    input_buffer[:i], output_buffer[:-output_cols[t_num, -1]])
            i = 0
            while output_cols[t_num][i] >= 0:
                row[output_cols[t_num][i]] = output_buffer[i]
                i += 1
        for t_num, tx_func in enumerate(post_process_tx_list):
            if tx_func is noop_post_process_state:
                continue
            i = 0
            while input_cols[t_num][i] >= 0:
                input_buffer[i] = row[input_cols[t_num][i]]
                i += 1
            tx_func(index[r_num], states[t_num][:state_len[t_num]],
                    input_buffer[:i])
