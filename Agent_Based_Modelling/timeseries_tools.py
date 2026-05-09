"Tools for working with time series"

import bisect
import collections.abc

import numpy as np


class TimeSeriesStepFunction:
    "A step function; with values stored at the beginning of the step, as a time series"

    def __init__(self, timepoints:list[float], values:list[float]):
        assert len(timepoints) == len(values)
        self.timepoints = timepoints
        self.values = values

    def evaluate(self, time):
        "evaluate function(time)"
        # if time is an array, apply to array elements
        if isinstance(time, collections.abc.Iterable):
            return list(map(self.evaluate, time))
        else:
            # if time is not an array, evaluate the step function
            # by finding the last stored value (in terms of self.timepoints) before time
            insertion_index = bisect.bisect_right(self.timepoints, time)
            value = self.values[insertion_index - 1]
            return value

def time_series_mean(multi_timeseries:list[TimeSeriesStepFunction], eval_time):
    "evaluate the mean of instances of TimeSeriesStepFunction, at the time points eval_time"
    multi_values = np.array([timeseries.evaluate(eval_time) for timeseries in multi_timeseries])
    mean = np.mean(multi_values, axis=0)

    return mean

def time_series_std_deviation(multi_timeseries:list[TimeSeriesStepFunction], eval_time):
    "evaluate the standard deviation of instances of TimeSeriesStepFunction, at the time points eval_time"
    multi_values = np.array([timeseries.evaluate(eval_time) for timeseries in multi_timeseries])
    std = np.std(multi_values, axis=0, ddof=1)

    return std

def time_series_quantile(multi_timeseries:list[TimeSeriesStepFunction], eval_time, q):
    "evaluate the pointwise q-th quantile (of instances of TimeSeriesStepFunction, at the time points eval_time)"
    multi_values = np.array([timeseries.evaluate(eval_time) for timeseries in multi_timeseries])
    quantile = np.quantile(multi_values, q=q, axis=0)

    return quantile
