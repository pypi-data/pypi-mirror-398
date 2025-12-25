"""Simple profiling tests for Exponentially Weighted Moving Average.
"""


import cProfile
import io
import os
import pstats
from pstats import SortKey
import timeit

import numba
from numba.types import UniTuple, Tuple
import numpy
import pandas
import pytest



from fast_tx.core import (FastTx, SimpleEWA, apply_chain, NDArray)


class CleanEWA(FastTx):#FIXME: need docs

    def __init__(self, alphas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alphas = numpy.asarray(alphas)

    def startup(self, dataframe):
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state

    @staticmethod
    def calc_row_py(index_value, state, inputs, outputs):
        alphas = state[:len(outputs)]
        prev_out = state[len(outputs):]
        outputs[:] = alphas * inputs + (1-alphas) * prev_out
        state[len(outputs):] = outputs[:]


class FullEWA(FastTx):#FIXME: need docs

    def __init__(self, alphas, *args, **kwargs):
        super().__init__(*([args[0]+args[1]] + list(args[1:])), **kwargs)
        self.alphas = numpy.asarray(alphas)

    def startup(self, dataframe):
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state

    @staticmethod
    def calc_row_py(index_value, state, inputs, outputs):
        l_o = len(outputs)
        alphas = state[:l_o]
        prev_out = state[l_o:]
        outputs[:] = alphas * inputs[:l_o] + (1-alphas) * prev_out

    @staticmethod
    def post_process_state_py(index_value, state, inputs):
        l_o = len(inputs)//2
        state[l_o:] = inputs[l_o:]


class ClosureEWA(FastTx):#FIXME: need docs

    def __init__(self, alphas, *args, **kwargs):
        super().__init__(*([args[0]+args[1]] + list(args[1:])), **kwargs)
        self.alphas = numpy.asarray(alphas)

        alphas = self.alphas
        l_o = len(alphas)
        my_state = numpy.zeros(l_o)
        #print(f'making {l_o=}')
        foo = 5.0
        @numba.njit(numba.void(numba.float64, numba.float64[:],
                               numba.float64[:], numba.float64[:]),
                    cache=True)
        def calc_row_py(index_value, state, inputs, outputs):
            prev_out = state[l_o:]
            outputs[:] = alphas * inputs[:l_o] + (1-alphas) * prev_out
        self.calc_row = calc_row_py

    def startup(self, dataframe):
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state

    @staticmethod
    def post_process_state_py(index_value, state, inputs):
        l_o = len(inputs)//2
        state[l_o:] = inputs[l_o:]


class CrazyEWA(FastTx):#FIXME: need docs

    def __init__(self, alphas, *args, **kwargs):
        super().__init__(*([args[0]+args[1]] + list(args[1:])), **kwargs)
        self.alphas = numpy.asarray(alphas)

        alphas = self.alphas
        l_o = len(alphas)
        my_state = numpy.zeros(l_o)
        #print(f'making {l_o=}')


        @numba.njit(Tuple((
            numba.float64, numba.float64[:], numba.float64[:]))(
                numba.float64[:]), cache=True)
        def unpack(state):
            l_o = len(state)//2
            alphas = state[:l_o]        
            prev_out = state[l_o:]
            return l_o, alphas, prev_out


        @numba.njit(numba.void(numba.float64, numba.float64[:],
                               numba.float64[:], numba.float64[:]),
                    cache=False)
        def calc_row_py(index_value, state, inputs, outputs):
            l_o, alphas, prev_out = unpack(state)
            outputs[:] = alphas * inputs[:l_o] + (1-alphas) * prev_out
        self.calc_row = calc_row_py



    def startup(self, dataframe):
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state

    @staticmethod
    def post_process_state_py(index_value, state, inputs):
        l_o = len(inputs)//2
        state[l_o:] = inputs[l_o:]


class DynamicClosureEWA(FastTx):#FIXME: need docs

    def __init__(self, alphas, input_col_names, output_col_names, **kwargs):
        assert len(input_col_names) == len(output_col_names)
        assert len(alphas) == len(input_col_names)
        self.alphas = numpy.asarray(alphas)
        self.patch_calc_row()
        super().__init__(input_col_names, output_col_names, **kwargs)

    def startup(self, dataframe):
        # We store alphas at end of state array.
        # We will use an `unpack` closure to extract in modify_calc_row
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state
        
    def patch_calc_row(self):
        l_o = len(self.alphas)  # can define variable for closure

        @numba.njit(Tuple((
            numba.float64, numba.float64[:], numba.float64[:]))(
                numba.float64[:]), cache=True)
        def unpack(state):
            alphas = state[:l_o]  # l_o is closure variable
            prev_out = state[l_o:]
            return l_o, alphas, prev_out

        @numba.njit(numba.void(numba.float64, numba.float64[:],
                               numba.float64[:], numba.float64[:]),
                    cache=False)
        def calc_row_py(index_value, state, inputs, outputs):
            l_o, alphas, prev_out = unpack(state)
            outputs[:] = alphas * inputs[:l_o] + (1-alphas) * prev_out
            prev_out[:] = outputs[:]  # updates state for next row calc
        self.calc_row = calc_row_py

class HackDynamicClosureEWA(FastTx):#FIXME: need docs

    def __init__(self, alphas, input_col_names, output_col_names, **kwargs):
        assert len(input_col_names) == len(output_col_names)
        assert len(alphas) == len(input_col_names)
        self.alphas = numpy.asarray(alphas)
        self.make_tx()
        super().__init__(input_col_names, output_col_names, **kwargs)

    def startup(self, dataframe):
        # We store alphas at end of state array.
        # We will use an `unpack` closure to extract in modify_calc_row
        state = numpy.zeros(2*len(self._output_col_names))
        state[:len(self._output_col_names)] = self.alphas
        return state
        
    def make_tx(self):
        @numba.njit(Tuple((numba.float64, numba.float64[:],
                           numba.float64[:]))(numba.float64[:]))
        def unpack(state):            
            l_o = len(state)//2
            alphas = state[:l_o]
            prev_out = state[l_o:]
            return l_o, alphas, prev_out

        @numba.njit
        def calc_row_py(index_value, state, inputs, outputs):  # can reference l_o above
            l_o, alphas, prev = unpack(state)
            outputs[:] = alphas * inputs + (1-alphas) * prev
            state[l_o:] = outputs[:]

        self.calc_row = calc_row_py
    

EWM_ENGINE_TO_CLS = {
    'fast_tx': SimpleEWA,
    'fast_tx_clean': CleanEWA,
    'fast_tx_full': FullEWA,
    'fast_tx_closure': ClosureEWA,
    'fast_tx_dynamic_closure': DynamicClosureEWA,
    'fast_tx_crazy': CrazyEWA,
    'fast_tx_hack': HackDynamicClosureEWA,
    }

def check_ewm(df, engine, incol='data', outcol='result', alpha=0.1,
              tx_list=None, verify=False):

    if tx_list is not None:
        apply_chain(df, tx_list)
    elif engine in EWM_ENGINE_TO_CLS:
        tx_list = [EWM_ENGINE_TO_CLS[engine]([alpha], [incol], [outcol])]
        apply_chain(df, tx_list)
    elif engine == 'apply_closure':
        def make_func(my_alpha, my_incol):
            prev = [0.0]  # need mutable container or nonlocal
            # performance is same for nonlocal or list or numpy array
            def my_func(row):
                prev[0] = row[my_incol]*my_alpha + (1-my_alpha)*prev[0]
                return prev[0]
            return my_func
        df[outcol] = df.apply(make_func(alpha, incol), axis=1)
    elif engine == 'apply_cls':
        class MyEWM:
            def __init__(self):
                self.prev = 0
            def __call__(self, row):
                self.prev = row[incol]*alpha + (1-alpha)*self.prev
                return self.prev
        my_thing = MyEWM()
        df[outcol] = df.apply(my_thing, axis=1)
    elif engine in ('numba', 'cython'):
        df[outcol] = pandas.concat([pandas.DataFrame(
            {incol: 0, outcol: numpy.nan}, index=[-1]), df])[incol].ewm(
                alpha=alpha, adjust=0).mean(engine=engine).iloc[1:]
    else:
        raise ValueError(f'unknown {engine=}')
    if verify:
        check_accuracy(df, incol, outcol, alpha)
    return tx_list
    

def check_accuracy(my_frame, incol='data', outcol='result', alpha=0.1):
    check_frame = my_frame.copy()
    check_frame[outcol] = numpy.nan
    check_frame = pandas.concat([pandas.DataFrame(
        {incol: 0, outcol: numpy.nan}, index=[-1]), check_frame])
    check_frame[outcol] = check_frame[incol].ewm(alpha=alpha, adjust=0
                                                 ).mean()
    assert all((check_frame.iloc[1:] == my_frame).all())


def prep_for_check_ewm(preprocess_compile, engine=None, size=136,
                       verify=False):
    engine = engine or 'fast_tx'
    size = int(os.environ.get('FAST_TX_TEST_SIZE', size))
    state = numpy.random.RandomState(123)  # pylint: disable=no-member
    data = 100 * numpy.cumprod(state.lognormal(0, .01, size))
    frame = pandas.DataFrame({'data': data})
    frame['result'] = numpy.nan
    
    if preprocess_compile:
        tx_list = check_ewm(frame.iloc[:10].copy(), engine)

    return {'df': frame, 'engine': engine, 'tx_list': tx_list,
            'verify': verify}

def do_profile(preprocess_compile=False, trials=1, engine=None):  # pragma: no cover
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
    kwargs = prep_for_check_ewm(preprocess_compile, engine=engine)
    tx_list = kwargs['tx_list']
    print(f'Doing profiling with engine: ' + kwargs['engine'])
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(trials):
        my_frame = kwargs['df'].copy()
        tx_list = check_ewm(my_frame, kwargs['engine'], tx_list=tx_list)
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    my_func = ps.get_stats_profile().func_profiles['check_ewm']
    check_accuracy(my_frame)
    print(my_func)
    if os.environ.get('FAST_TX_SHOW_FULL_PROFILE', '0').strip() not in [
            '1', 'yes', 'YES', 'Yes', 'true', 'True']:
        return
    ps.print_stats()
    print(s.getvalue())

    
def do_timeit(preprocess_compile=True, engine=None, number=None, **kwargs):
    kwargs = prep_for_check_ewm(preprocess_compile, engine=engine, **kwargs)
    my_timer = timeit.Timer('check_ewm(**kwargs)', globals={
        'kwargs': kwargs, 'check_ewm': check_ewm})
    if number is None:
        number, total = my_timer.autorange()
    else:
        total = my_timer.timeit(number=number)
    avg = total/float(number)
    result = (f'{avg=:.4f} seconds in {number} trials for engine ' + kwargs[
        'engine'])
    return result


def main(engine=None, doprint=print, mode=None, **kwargs):
    result = []
    mode = mode or os.environ.get('FAST_TX_PROFILE_MODE', 'timeit')
    engine = engine or os.environ.get('FAST_TX_ENGINE', 'fast_tx')
    if ',' in engine:
        result = sum([main(engine=e.strip(), doprint=doprint, mode=mode,
                           **kwargs) for e in engine.split(',')],[])
    elif engine == '__all__':
        engine = ','.join(list(EWM_ENGINE_TO_CLS) + [
            'cython', 'apply_cls', 'apply_closure'])
        return main(engine=engine, doprint=doprint, mode=mode, **kwargs)
    elif mode == 'timeit':
        result = [do_timeit(engine=engine, **kwargs)]
        doprint(result[0])
    elif mode == 'profile':
        result = [do_profile(
            preprocess_compile=True, trials=int(os.environ.get(
                'FAST_TX_NUM_TRIALS', '20')), engine=engine)]
        doprint(result[0])
    else:
        raise ValueError(f'Bad {mode=}')
    return result


def test_all():
    """Test everything in this file (mainly for coverage).

    This function will test everything in the file (mainly to ensure
    code coverage).
    """
    with pytest.raises(ValueError) as exc_info:
        main(mode='broken')        
    assert exc_info.type == ValueError
    with pytest.raises(ValueError) as exc_info:
        main(engine='broken')
    assert exc_info.type == ValueError
    main(engine='__all__', size=100, verify=False, number=None)    
    main(engine='__all__', size=10, verify=True, number=1)
    main(engine='fast_tx', size=100, mode='profile', verify=True)


if __name__ == '__main__':  # pragma: no cover
    main()
