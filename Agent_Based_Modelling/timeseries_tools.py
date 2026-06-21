"Tools for working with time series"

import bisect
import collections.abc

import numpy as np
import heapq
from itertools import groupby


class TimeSeriesStepFunction:
    "A 0-order-hold step function; with values stored at the beginning of the step, as a time series"

    def __init__(self, timepoints:list[float], values:list[float]):
        assert len(timepoints) == len(values)
        self.timepoints = timepoints
        self.values = values

    def insert(self, time, value):
        "helper function to insert new data"
        self.timepoints.append(time)
        self.values.append(value)

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

    def __add__(self, other):
        merged_timepoints = heapq.merge(self.timepoints, other.timepoints)
        merged_timepoints_deduped = [k for k, _ in groupby(merged_timepoints)]
        added_values = [self.evaluate(t) + other.evaluate(t) for t in merged_timepoints_deduped]
        return TimeSeriesStepFunction(merged_timepoints_deduped, added_values)

    # necessary so we can use the built-in "sum(...)"
    def __radd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)


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
