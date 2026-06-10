# Implement a classic GGk queue, where arrival and service times can follow an arbitrary positive distribution.
# Test different distributions and parameters, and plot time-dependent statistics (e.g. mean,
# confidence intervals, etc.) for the queue length and server utilisation.
import heapq
import numpy as np
import matplotlib.pyplot as plt
from bisect import bisect_left
import sys
if sys.platform == "win32":
    sys.path.append(r"..\Agent_Based_Modelling")
elif sys.platform == "linux":
    sys.path.append(r"../Agent_Based_Modelling")
import timeseries_tools


class Event:

    def __init__(self, type="arrival", scheduled_time=0.0):
        self.type = type
        self.scheduled_time = scheduled_time

    def __lt__(self, other):
        return self.scheduled_time < other.scheduled_time


def run_simulation(k, arrival_time, service_time, T):
    event_list = []
    sim_time = 0
    Q = 0
    S = k
    timepoints = []
    Q_data = []
    S_data = []

    heapq.heappush(event_list, Event("start", 0.0))

    while event_list[0].scheduled_time < T:

        current_event = heapq.heappop(event_list)
        sim_time = current_event.scheduled_time

        if current_event.type == "start":
            new_arrival = sim_time + arrival_time()
            heapq.heappush(event_list, Event("arrival", new_arrival))
            # print(f"Start. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(k-S)

        if current_event.type == "arrival":
            Q += 1
            if S > 0:
                heapq.heappush(event_list, Event("start_service", sim_time))
            new_arrival = sim_time + arrival_time()
            heapq.heappush(event_list, Event("arrival", new_arrival))
            # print(f"Arrival. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(k-S)

        if current_event.type == "start_service":
            S -= 1
            Q -= 1
            if S < 0 or Q < 0:
                print(f"ERROR S = {S}, Q = {Q}")
            end_time = sim_time + service_time()
            heapq.heappush(event_list, Event("end_service", end_time))
            # print(f"Started Service. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(k-S)

        if current_event.type == "end_service":
            S += 1
            # print(f"Ended Service. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(k-S)
            if Q > 0:  # i do not even put SS on the event list, but do it immediately
                S -= 1
                Q -= 1
                if S < 0 or Q < 0:
                    print(f"ERROR S = {S}, Q = {Q}")
                end_time = sim_time + service_time()
                heapq.heappush(event_list, Event("end_service", end_time))
                # print(f"Started Service. Q = {Q}, S = {S}, time = {sim_time}")
                timepoints.append(sim_time)
                Q_data.append(Q)
                S_data.append(k-S)

    return timepoints, Q_data, S_data


# run a given number of Monte Carlo simulations and calculate mean and var of data
def MonteCarlo(runs, k, arrival_time, service_time, T):

    queue_length_data = []
    server_utilisation_data = []

    for i in range(1, runs+1):

        timepoints, Q_data, S_data = run_simulation(k, arrival_time, service_time, T)
        queue_length_data.append(timeseries_tools.TimeSeriesStepFunction(timepoints, Q_data))
        server_utilisation_data.append(timeseries_tools.TimeSeriesStepFunction(timepoints, S_data))

    return queue_length_data, server_utilisation_data


def plot_queue_length_statistics(q_data, T):
    t_eval = np.linspace(0, T, T+1)
    queue_length_mean = timeseries_tools.time_series_mean(q_data, t_eval)
    queue_length_std = timeseries_tools.time_series_std_deviation(q_data, t_eval)
    queue_length_median = timeseries_tools.time_series_quantile(q_data, t_eval, 0.5)
    queue_length_1st_quantile = timeseries_tools.time_series_quantile(q_data, t_eval, 0.25)
    queue_length_3rd_quantile = timeseries_tools.time_series_quantile(q_data, t_eval, 0.75)

    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)

    ax[0].plot(t_eval, queue_length_mean, label='Queue length mean')
    ax[0].fill_between(t_eval, queue_length_mean - queue_length_std, queue_length_mean + queue_length_std, alpha=0.3, label='+-std')
    ax[0].legend()

    ax[1].step(t_eval, queue_length_median, label='Queue length median')
    ax[1].fill_between(t_eval, queue_length_1st_quantile, queue_length_3rd_quantile, step='post', alpha=0.3, label='1st and 3rd quartile')
    ax[1].legend()


def plot_server_utilisation_statistics(s_data, T):
    t_eval = np.linspace(0, T, T+1)
    server_util_mean = timeseries_tools.time_series_mean(s_data, t_eval)
    server_util_std = timeseries_tools.time_series_std_deviation(s_data, t_eval)
    server_util_median = timeseries_tools.time_series_quantile(s_data, t_eval, 0.5)
    server_util_1st_quantile = timeseries_tools.time_series_quantile(s_data, t_eval, 0.25)
    server_util_3rd_quantile = timeseries_tools.time_series_quantile(s_data, t_eval, 0.75)

    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)

    ax[0].plot(t_eval, server_util_mean, label='Server utilisation mean +- std')
    ax[0].fill_between(t_eval, server_util_mean - server_util_std, server_util_mean + server_util_std, alpha=0.3)
    ax[0].legend()

    ax[1].plot(t_eval, server_util_median, label='Server utilisation median')
    ax[1].fill_between(t_eval, server_util_1st_quantile, server_util_3rd_quantile, alpha=0.3, label='1st and 3rd quartile')
    ax[1].legend()


np.random.seed(4627)
k = 2  # number of servers

"""# exp exp
scale_arr = 0.13
scale_serv = 6  # mean of exp(scale) = scale
arrival_time = lambda : np.random.exponential(scale_arr)
service_time = lambda : np.random.exponential(scale_serv)
"""

"""# gamma gamma. expectation = shape*scale. if shape=1: gives exp(scale)
shape1 = 0.3
scale1 = 0.28
shape2 = 4
scale2 = 2
arrival_time = lambda : np.random.gamma(shape1, scale1)
service_time = lambda : np.random.gamma(shape2, scale2)
"""

# chi chi
df1 = 2
df2 = 4
arrival_time = lambda : np.random.chisquare(df1)
service_time = lambda : np.random.chisquare(df2)

T = 120
"""timepoints, Q_data, S_data = run_simulation(k, arrival_time, service_time, T)
plt.step(timepoints, Q_data, where='post', label='Queue length')
plt.step(timepoints, S_data, where='post', label='Server utilisation')
plt.legend()
plt.show()"""

# Monte Carlo Sim
runs = 1000
q_data, s_data = MonteCarlo(runs, k, arrival_time, service_time, T)
plot_queue_length_statistics(q_data, T)
plot_server_utilisation_statistics(s_data, T)
plt.show()


# observed behaviour:
# 1) we can either get a small variance for server utilisation OR for queue length, not both.
# either the queue is always very short with small var and high fluctuation in server utilisation (=large var)
# or the queue grows, has a high var, and all servers are always busy (=small var)
# 2) it is obvious that the variance will be large for a small number of servers or a short queue,
# as our values are discrete (unless the queue is almost always zero or all servers are almost always busy)
# 3) gamma might give a smaller var for the same mean value
# but otherwise, i don't see a big difference between the two
# 4) i modeled a supermarkt-like situation (k=2, k=5) and a more callcenter-like situation (k=100)
