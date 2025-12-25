"""Experimental features.

This module includes experimental features such as those which
rely on the numba jitclass decorator (which itself is experimental).
"""

import logging

import numba
import numpy
import pandas

from fast_tx import buffer_tools


def apply_chain_jc(dataframe: pandas.DataFrame,
                   jc_list):
    """Apply given transform chain (of jitted classes) to dataframe.

    :param dataframe:  DataFrame to modify.

    :param jc_list:   List numba jitted classes with calc_row methods
                      to apply to dataframe.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Apply list of jitted classes in `jc_list` to the given
              `dataframe`.
    """
    input_cols, output_cols, maincols = buffer_tools.prepare_cols(
        dataframe, jc_list)
    index, input_buffer, output_buffer, mainbuffer = buffer_tools.make_buffers(
        dataframe, maincols, input_cols, output_cols)

    # If original dataframe has mixed types, mainbuffer may not be float.
    # We must force float for numba, but warn the user about that so they
    # can maybe try to fix type themselves.

    if mainbuffer.dtype != 'float64':  # pragma: no cover
        logging.warning('Buffer dataframe has type %s; will force float64',
                        mainbuffer.dtype)
        mainbuffer = mainbuffer.astype(numpy.float64)

    _apply_inner_loop_jc(jc_list, index.astype(numpy.float64),
                         mainbuffer, input_buffer, output_buffer,
                         input_cols, output_cols)
    dataframe[list(maincols)] = mainbuffer


def _apply_inner_loop_jc(
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        jc_list, index, mainbuffer, input_buffer, output_buffer,
        input_cols, output_cols):
    for r_num, row in enumerate(mainbuffer):
        t_num = 0
        for tx_func in numba.literal_unroll(jc_list):
            i = 0
            while input_cols[t_num][i] >= 0:
                input_buffer[i] = row[input_cols[t_num, i]]
                i += 1
            tx_func.calc_row(index[r_num], input_buffer[:i],
                             output_buffer[:-output_cols[t_num, -1]])
            i = 0
            while output_cols[t_num][i] >= 0:
                row[output_cols[t_num][i]] = output_buffer[i]
                i += 1
            t_num += 1
