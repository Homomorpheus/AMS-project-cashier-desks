# %%

import time
import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import agents
import events
import timeseries_tools
import mc_statistics


simulation_end_time = 240

# chi chi
df1 = 2
df2 = 3
df3 = 1

amount_cashiers = 5
simulation_size = 5000

def service_time(customer):
    return np.random.chisquare(df2)

def interarr_time():
    return np.random.chisquare(df1)

def time_to_activate():
    return np.random.chisquare(df3)


def simulate_rm(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=2):
    "run the actual, single simulation"

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time) for _ in range(amount_cashiers)]
    queues = [agents.Queue([cashier], [], threshold_lo=0, threshold_hi=3, time_to_activate=time_to_activate, active=False) for cashier in cashiers]
    queues[0]._active = True
    queues[0].threshold_lo = float("-inf")

    # create initial event
    start_event = events.Arrival(scheduled_time=0., interarr_time=interarr_time, queues=queues)

    # run the DES
    des = events.DES(start_event)
    des.run(simulation_end_time)

    # collect data for statistics
    queue_lengths = [timeseries_tools.TimeSeriesStepFunction(queue.timepoints_amounts_customers, queue.amounts_customers) for queue in queues]
    queue_activity = [timeseries_tools.TimeSeriesStepFunction(queue.timepoints_activity_states, [int(state) for state in queue.activity_states]) for queue in queues]
    cashiers_busy = [timeseries_tools.TimeSeriesStepFunction(cashier.timepoints, [int(busy) for busy in cashier.busy_at_time]) for cashier in cashiers]
    cashier_throughputs = [cashier.throughput(0, simulation_end_time) for cashier in cashiers]
    waiting_times = [queue.customer_waiting_times for queue in queues]


    return queue_lengths, cashiers_busy, waiting_times, cashier_throughputs, queue_activity


def simulate(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=2):
    "run the actual, single simulation"

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time) for _ in range(amount_cashiers)]
    queues = [agents.Queue([cashier], []) for cashier in cashiers]

    # create initial event
    start_event = events.Arrival(scheduled_time=0., interarr_time=interarr_time, queues=queues)

    # run the DES
    des = events.DES(start_event)
    des.run(simulation_end_time)

    # collect data for statistics
    queue_lengths = [timeseries_tools.TimeSeriesStepFunction(queue.timepoints_amounts_customers, queue.amounts_customers) for queue in queues]
    queue_activity = [timeseries_tools.TimeSeriesStepFunction(queue.timepoints_activity_states, [int(state) for state in queue.activity_states]) for queue in queues]
    cashiers_busy = [timeseries_tools.TimeSeriesStepFunction(cashier.timepoints, [int(busy) for busy in cashier.busy_at_time]) for cashier in cashiers]
    cashier_throughputs = [cashier.throughput(0, simulation_end_time) for cashier in cashiers]
    waiting_times = [queue.customer_waiting_times for queue in queues]

    return queue_lengths, cashiers_busy, waiting_times, cashier_throughputs, queue_activity


def compare_queue_length_statistics(queue_length_data_rm, queue_length_data_no_rm, simulation_end_time):

    # restructure by queue
    amount_queues = len(queue_length_data_rm[0])
    length_by_queues_rm = [[result[i] for result in queue_length_data_rm] for i in range(amount_queues)]
    length_by_queues_no_rm = [[result[i] for result in queue_length_data_no_rm] for i in range(amount_queues)]
    sum_queue_lengths_rm = [sum([result[k] for k in range(amount_queues)]) for result in queue_length_data_rm]
    sum_queue_lengths_no_rm = [sum([result[k] for k in range(amount_queues)]) for result in queue_length_data_no_rm]

    # plot overall queue length statistics
    x = np.linspace(0, simulation_end_time, simulation_end_time + 1)
    mean_sum_rm = timeseries_tools.time_series_mean(sum_queue_lengths_rm, x)
    median_sum_rm = timeseries_tools.time_series_quantile(sum_queue_lengths_rm, x, 0.5)
    quartile_1_sum_rm = timeseries_tools.time_series_quantile(sum_queue_lengths_rm, x, 0.25)
    quartile_3_sum_rm = timeseries_tools.time_series_quantile(sum_queue_lengths_rm, x, 0.75)
    mean_sum_no_rm = timeseries_tools.time_series_mean(sum_queue_lengths_no_rm, x)
    median_sum_no_rm = timeseries_tools.time_series_quantile(sum_queue_lengths_no_rm, x, 0.5)
    quartile_1_sum_no_rm = timeseries_tools.time_series_quantile(sum_queue_lengths_no_rm, x, 0.25)
    quartile_3_sum_no_rm = timeseries_tools.time_series_quantile(sum_queue_lengths_no_rm, x, 0.75)

    fig, ax = plt.subplots(ncols=2, sharex=True, sharey=True)
    ax[0].plot(x, median_sum_rm, label='Overall queue length median RM')
    ax[0].fill_between(x, quartile_1_sum_rm, quartile_3_sum_rm, alpha=0.2)
    ax[0].plot(x, mean_sum_rm, label='Overall queue length mean RM')
    ax[1].plot(x, median_sum_no_rm, label='Overall queue length median')
    ax[1].fill_between(x, quartile_1_sum_no_rm, quartile_3_sum_no_rm, alpha=0.2)
    ax[1].plot(x, mean_sum_no_rm, label='Overall queue length mean')

    ax[0].legend()
    ax[1].legend()
    plt.show()

    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)

    for i, timeseries in enumerate(length_by_queues_rm):
        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[0].plot(x, mean, label=f'Queue {i+1}')

        # median
        median = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[1].plot(x, median)

        # quartiles
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        quartile_3 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        ax[1].fill_between(x, quartile_3, quartile_1, alpha=0.2)

    ax[0].set_ylabel('Queue length mean RM')
    ax[1].set_ylabel('Queue length median RM')
    fig.legend(loc='upper right')
    plt.show()

    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)

    for i, timeseries in enumerate(length_by_queues_no_rm):
        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[0].plot(x, mean, label=f'Queue {i+1}')

        # median
        median = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[1].plot(x, median)

        # quartiles
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        quartile_3 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        ax[1].fill_between(x, quartile_3, quartile_1, alpha=0.2)

    ax[0].set_ylabel('Queue length mean NO RM')
    ax[1].set_ylabel('Queue length median NO RM')
    fig.legend(loc='upper right')
    plt.show()


def plot_queue_activity(queue_activity_data, queue_length_data, simulation_end_time):
    # restructure by queue
    amount_queues = len(queue_length_data[0])
    activity_by_queues = [[result[i] for result in queue_activity_data] for i in range(amount_queues)]

    fig, ax = plt.subplots(nrows=1 + amount_queues, sharex=True, sharey=True)

    for i, timeseries in enumerate(activity_by_queues):
        x = np.linspace(0, simulation_end_time)
        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[0].plot(x, mean)

        # median
        median = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[1 + i].plot(x, median, label=f"Queue {i+1} activity median")

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        # ax[1].plot(x, quartile_1, label="1. quartile")
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        # ax[1].plot(x, quartile_2, label="3. quartile")
        ax[1 + i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.2)
        ax[i+1].legend()

    plt.show()


def plot_cashiers_busy(cashiers_busy_data, simulation_end_time):
    cashiers_busy_sorted_by_cashiers = [[cashiers_busy_data[j][i] for j in range(len(cashiers_busy_data))] for i in range(len(cashiers_busy_data[0]))]

    amount_cashiers = len(cashiers_busy_sorted_by_cashiers)
    fig, ax = plt.subplots(nrows=amount_cashiers, sharex=True, sharey=True)
    x = np.arange(0, simulation_end_time + 1)

    for i in range(amount_cashiers):
        multi_timeseries = cashiers_busy_sorted_by_cashiers[i]

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(multi_timeseries, x, 0.25)

        # 3. quartile
        quartile_3 = timeseries_tools.time_series_quantile(multi_timeseries, x, 0.75)
        ax[i].fill_between(x, quartile_3, quartile_1, color="blue", alpha=0.3)

        # median
        median = timeseries_tools.time_series_quantile(multi_timeseries, x, 0.5)
        ax[i].plot(x, median, label="Cashier busy: median")

        ax[i].legend()

    plt.show()


# generate simulation seeds
np.random.seed(17)
seeds = np.random.randint(2**31, size=simulation_size)
start_time = time.time()

# run Monte Carlo simulation
simulation_results_rm = list(map(lambda seed: simulate_rm(seed, simulation_end_time, service_time, interarr_time, amount_cashiers), seeds))
simulation_results_no_rm = list(map(lambda seed: simulate(seed, simulation_end_time, service_time, interarr_time, amount_cashiers), seeds))

print(f"simulation runs took {(time.time()-start_time):.2f} seconds")

# plot queue length
queue_length_data_rm = [result[0] for result in simulation_results_rm]
queue_length_data_no_rm = [result[0] for result in simulation_results_no_rm]
compare_queue_length_statistics(queue_length_data_rm, queue_length_data_no_rm, simulation_end_time)

# plot queue activity
queue_activity_data = [result[4] for result in simulation_results_rm]
plot_queue_activity(queue_activity_data, queue_length_data_rm, simulation_end_time)

# print statistics of customer waiting time
print("Customer waiting time in resource management simulation:")
for i in range(amount_cashiers):
    customer_waiting_times_multiqueue = list(itertools.chain.from_iterable(result[2][i] for result in simulation_results_rm))
    print(f"in Queue {i+1}:")
    print(f"\tmean: {np.mean(customer_waiting_times_multiqueue)}")
    print(f"\tstandard deviation: {np.std(customer_waiting_times_multiqueue, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(customer_waiting_times_multiqueue, q=0.25)}")
    print(f"\tmedian: {np.median(customer_waiting_times_multiqueue)}")
    print(f"\t3. quartile: {np.quantile(customer_waiting_times_multiqueue, q=0.75)}")
    print()


# # cashier throughput
cashier_throughput = np.array([result[3] for result in simulation_results_rm]).T
print("Cashier throughput:")
print(f"\tmean: {np.mean(cashier_throughput, axis=1)}")
print(f"\tstandard deviation: {np.std(cashier_throughput, axis=1, ddof=1)}")
print(f"\t1. quartile: {np.quantile(cashier_throughput, axis=1, q=0.25)}")
print(f"\tmedian: {np.median(cashier_throughput, axis=1)}")
print(f"\t3. quartile: {np.quantile(cashier_throughput, axis=1, q=0.75)}")
print()

# plot data for normal multi queue simulation
cashiers_busy_data = [result[1] for result in simulation_results_no_rm]
plot_cashiers_busy(cashiers_busy_data, simulation_end_time)

# print statistics of customer waiting time
print("Customer waiting time in classic multi queue simulation:")
for i in range(amount_cashiers):
    customer_waiting_times_multiqueue = list(itertools.chain.from_iterable(result[2][i] for result in simulation_results_no_rm))
    print(f"in Queue {i+1}:")
    print(f"\tmean: {np.mean(customer_waiting_times_multiqueue)}")
    print(f"\tstandard deviation: {np.std(customer_waiting_times_multiqueue, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(customer_waiting_times_multiqueue, q=0.25)}")
    print(f"\tmedian: {np.median(customer_waiting_times_multiqueue)}")
    print(f"\t3. quartile: {np.quantile(customer_waiting_times_multiqueue, q=0.75)}")
    print()


# # cashier throughput
cashier_throughput = np.array([result[3] for result in simulation_results_no_rm]).T
print("Cashier throughput:")
print(f"\tmean: {np.mean(cashier_throughput, axis=1)}")
print(f"\tstandard deviation: {np.std(cashier_throughput, axis=1, ddof=1)}")
print(f"\t1. quartile: {np.quantile(cashier_throughput, axis=1, q=0.25)}")
print(f"\tmedian: {np.median(cashier_throughput, axis=1)}")
print(f"\t3. quartile: {np.quantile(cashier_throughput, axis=1, q=0.75)}")
print()
