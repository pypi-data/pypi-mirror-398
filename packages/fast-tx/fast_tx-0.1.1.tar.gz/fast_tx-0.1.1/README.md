
# Introduction

The `fast_tx` package provides tools and examples for fast mixed row
and column operations in pandas.

## Motivation

Imagine you have a pandas DataFrame and want to be able to mix
and match various operations on the rows. For example, each row might
represent the price of various stocks on a given day. You might want
to do something like apply a moving average maybe followed by a
non-liner operation like thresholding.

There are many ways to do this in pandas that will work be fast for
simple cases but I am not aware of an easy way to combine arbitrary
row operations which runs quickly (e.g., see the FAQ section
below). This package provides such tools.

For example, imagine you want a function called `apply_chain` which
takes as input a DataFrame and a sequence of row transformations and
applies them to each row. The code snippet below shows what this might
look like for a simple stock trading strategy:

```python
    price = ['SPY', 'TLT']  # names of columns for stock prices
    moving_avg = [s + '_ma' for s in price]
    signal = [s + '_ind' for s in price]
    position = [s + '_pos' for s in price]
    cash, equity = ['cash'], ['equity']  # names of cols for cash/equity
    apply_chain(df, [
        MovingAverage(price, moving_avg)
        AboveMA(price, moving_avg, signal)
        WeightedPosition(price, signal, cash, equity, position)
        UpdatePortfolio(position, equity, cash)])
```		

Notice that each of the operations (compute the moving average,
compare price to that average to determine the buy signal, update the
portfolio value) needs to be applied in sequence to each row. While we
could in theory apply `MovingAverage` and `AboveMA` separately to each
column, the `WeightedPosition` and `UpdatePortfolio` need to be
applied sequentially for each row since they interact (the target
position depends on the current price, signal as well as current cash
and equity but the cash and equity depend on the position we took
previously).

This package provides an `apply_chain` function as well as a generic
`FastTx` class which you can sub-class to define your arbitrary row
operations. Provided you follow the protocol for `FastTx`, you can
define pretty much whaterver type of operation you want on whichever
columns you want and mix and match `FastTx` instances as you like and
still get good performance.

# Install

You can install `fast_tx` in the usual way:
```sh
    pip install fast_tx
```
(or use `uv` or whatever other method you prefer to install from pypi.

# Usage

## Sub-classing FastTx

You can create your own classes by sub-classing `FastTx`. The only
required method you need to implement is `calc_row_py` (which is pure
python) or `calc_row` (which requires you to JIT-compile using numba).

For example, imagine you want a class that turns on a flag if current
and target signal values differ by more than 1%. You could do
something like the following:

```python
>>> import pandas, numpy
>>> from fast_tx.core import FastTx, apply_chain
>>> class FlagOnDiff(FastTx):
...     "Turn on flag if % difference exceeds 1%."
...     
...     def calc_row_py(
...             index_value,  # time index value; not used here
...             state,   # persistent state; not used here
...             inputs,  # array of input values
...             outputs): # array of output values
...         current = inputs[:len(inputs)//2]
...         target = inputs[len(inputs)//2:]
...         diff = numpy.sum(numpy.abs(current - target))
...         gross = numpy.sum(numpy.abs(target))
...         outputs[0] = diff/gross * 100  # percent difference
...         outputs[1] = 1 if outputs[0] > 1 else 0  # flag
...

```

We can then use the `apply_chain` function to apply a list of such
classes to a DataFrame as shown below:

```python
>>> df = pandas.DataFrame({
...    'current_a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'current_b': [10.0, 20.5, 30.1, 40.8, 50.2]})
>>> df['target_a'] = df['current_a'] + .05
>>> df['target_b'] = df['current_b'] + .1
>>> apply_chain(df, [FlagOnDiff(
...     ['current_a', 'current_b', 'target_a', 'target_b'],  # input columns
...     ['pct_diff', 'flag'])])
>>> print(df)
   current_a  current_b  target_a  target_b  pct_diff  flag
0        1.1       10.0      1.15      10.1  1.333333   1.0
1        2.2       20.5      2.25      20.6  0.656455   0.0
2        3.3       30.1      3.35      30.2  0.447094   0.0
3        4.4       40.8      4.45      40.9  0.330761   0.0
4        5.5       50.2      5.55      50.3  0.268577   0.0

```

## Explicit Numba JIT-compiling

In the previous example, the `calc_row_py` method is automatically
JIT-compiled. If desired you could explicitly JIT-compile it via a definition like:
```python
class FlagOnDiff(FastTx):
    # ...
	@staticmethod
    @numba.njit
    def calc_row(index_value, state, inputs, outputs):
	    # ...
```

Explicitly JIT-compiling can sometimes be useful if you want to pass
special flags to njit or have more preceise control over type
definitions.

## Storing Parameters in State

```python
>>> import pandas, numpy
>>> from fast_tx.core import FastTx, apply_chain
>>> class FlagOnDiff(FastTx):
...     "Turn on flag if % difference exceeds 1%."
...     
...     def __init__(self, threshold, *args, **kwargs):
...         self.threshold = threshold
...         super().__init__(*args, **kwargs)
...     
...     def startup(self, dataframe):
...          state = numpy.array([float(self.threshold)])
...          return state
...     
...     def calc_row_py(
...             index_value,  # time index value; not used here
...             state,   # persistent state prepared by startup
...             inputs,  # array of input values
...             outputs): # array of output values
...         current = inputs[:len(inputs)//2]
...         target = inputs[len(inputs)//2:]
...         diff = numpy.sum(numpy.abs(current - target))
...         gross = numpy.sum(numpy.abs(target))
...         outputs[0] = diff/gross * 100  # percent difference
...         outputs[1] = 1 if outputs[0] > state[0] else 0  # flag
...

```

We can now instantiate the class with whatever threshold we like:

```python
>>> df = pandas.DataFrame({
...    'current_a': [1.1, 2.2, 3.3, 4.4, 5.5],
...    'current_b': [10.0, 20.5, 30.1, 40.8, 50.2]})
>>> df['target_a'] = df['current_a'] + .05
>>> df['target_b'] = df['current_b'] + .1
>>> apply_chain(df, [FlagOnDiff(0.5, # threshold
...     ['current_a', 'current_b', 'target_a', 'target_b'],  # input columns
...     ['pct_diff', 'flag'])])
>>> print(df)
   current_a  current_b  target_a  target_b  pct_diff  flag
0        1.1       10.0      1.15      10.1  1.333333   1.0
1        2.2       20.5      2.25      20.6  0.656455   1.0
2        3.3       30.1      3.35      30.2  0.447094   0.0
3        4.4       40.8      4.45      40.9  0.330761   0.0
4        5.5       50.2      5.55      50.3  0.268577   0.0

```

## Changing State

Now imagine that we want to compute the percent difference between
either the current signal vs target or the previous target vs current
target (whichever is larger). To do so, we would need to track the
previous signal. We can do that by storing it in a state variable as
shown below:

```python
>>> import pandas, numpy
>>> from fast_tx.core import FastTx, apply_chain
>>> class FlagOnDiff(FastTx):
...     "Turn on flag if % difference exceeds 1%."
...     
...     def __init__(self, threshold, *args, **kwargs):
...         self.threshold = threshold
...         super().__init__(*args, **kwargs)
...     
...     def startup(self, dataframe):
...          state = numpy.zeros(len(self.input_col_names()))
...          state[-1] = self.threshold
...          return state
...     
...     def calc_row_py(
...             index_value,  # time index value; not used here
...             state,   # persistent state prepared by startup
...             inputs,  # array of input values
...             outputs): # array of output values
...         size = len(inputs)//2
...         previous = state[:size]
...         current = inputs[:size]
...         target = inputs[size:]
...         diff = max(numpy.sum(numpy.abs(current - target)),
...                    numpy.sum(numpy.abs(previous - target)))
...         gross = numpy.sum(numpy.abs(target))
...         outputs[0] = diff/gross * 100  # percent difference
...         outputs[1] = 1 if outputs[0] > state[0] else 0  # flag
...         state[:size] = target  # update state
...

```

We can apply the transform as shown below:

```python
>>> df = pandas.DataFrame({
...    'current_a': [1.1, 2.2, 4.2, 4.4, 4.5],
...    'current_b': [10.0, 20.5, 40.7, 40.8, 40.9]})
>>> df['target_a'] = df['current_a'] + .05
>>> df['target_b'] = df['current_b'] + .1
>>> apply_chain(df, [FlagOnDiff(0.5, # threshold
...     ['current_a', 'current_b', 'target_a', 'target_b'],  # input columns
...     ['pct_diff', 'flag'])])
>>> print(df)
   current_a  current_b  target_a  target_b    pct_diff  flag
0        1.1       10.0      1.15      10.1  100.000000   1.0
1        2.2       20.5      2.25      20.6   50.765864   1.0
2        4.2       40.7      4.25      40.8   49.278579   1.0
3        4.4       40.8      4.45      40.9    0.661521   0.0
4        4.5       40.9      4.55      41.0    0.439078   0.0

```

## Post Processing State

When you have a large list of transforms, sometimes you want to update
your state based on the final results of a row. The `calc_row_py` method
for each transform in a chain is called in order and hence each
transform in the chain may see different inputs. After all `calc_row_py`
methods have been called, we then do a second pass and call
`post_process_state_py` for each transform. No transform should modify
the row via `post_process_state_py` (but may modify its own internal
state). This allows transforms to "see" the final value of a row.

As with `calc_row_py`, you can either define a pure python
`post_process_state_py` or a jitted `post_process_state`.

See examples in the `fast_tx.core` and `fast_tx.stk_tools` modules for
details.

## More Details

See docstrings and examples in `fast_tx.core`, `fast_tx.stk_tx`,
`fast_tx.stk_tools`, and (if you're brave) the various tests in
`fast_tx_tests/`.

The docstring for the `FastTx` class (and its methods) in
`fast_tx.core` is the best place to start.


# Tricks and Pythonic Tools

Making `apply_chain` run fast requires a specific interface for the
`calc_row_py` and `calc_row` methods. These work but can be a little
difficult to program to at first. In the following we describe some
tricks and more pythonic approaches.

## Closures

Closures can make writing `calc_row` easier. For example, the
`TradeFlagOnDiff` class in `fast_tx.stk_tx` defines a `bind_calc_row`
method (which is called by is `__init__` method). The `bind_calc_row`
method looks something like below.

Notice that we set some variables like `size` and `flag_slice` in
`bind_calc_row` based on `self` and then create the jitted `calc_row`
method to use these values. This is easier than passing parameters
around in `state`. It's also easier to unpack the desired values from
the `inputs` argument if we have stored the desired slice.

```python

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
```

See the source code for the rest of `TradeFlagOnDiff` for more examples.

# FAQ

## Why not use `for` loops?

For loops are generally not vectorized and will be very slow.

## Why not use `iterrows`?

The `iterrows` method can work but has terrible performance since it
works with Series objects.

## Why not use `apply`?

The `apply` method will have a lot of overhead calling your functions
and will be slow.

## Why not use `itertuples`?

Using `itertuples` is generally better than many alternatives but will
still generally not be vectorized and will be slow.

## Why not use rolling apply?

Use rolling windows and apply can be surprisingly fast for simple
cases (especially if you use `raw=True`). But it does not work when
you have multiple operations each referencing a different combination
of columns.


