# %%

import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# matplotlib.rcParams['figure.figsize'] = [12, 12]

import agents
import events
import timeseries_tools
import itertools

# %%


simulation_end_time = 120

# chi chi
df1 = 1
df2 = 4
df3 = 2

def service_time(customer):
    return np.random.chisquare(df2)

def interarr_time():
    return np.random.chisquare(df1)

def time_to_activate():
    return np.random.chisquare(df3)

amount_cashiers = 5

simulation_size = 1000


# %%

def simulate(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=2):
    "run the actual, single simulation"

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time) for _ in range(amount_cashiers)]
    queues = [agents.Queue([cashier], [], threshold_lo=9, threshold_hi=14, time_to_activate=time_to_activate, active=False) for cashier in cashiers]

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


# %%

# generate simulation seeds
np.random.seed(17)
seeds = np.random.randint(2**31, size=simulation_size)
start_time = time.time()

# run Monte Carlo simulation
simulation_results = list(map(lambda seed: simulate(seed, simulation_end_time, service_time, interarr_time, amount_cashiers), seeds))

print(f"simulation run took {(time.time()-start_time):.2f} seconds")

# %%

def plot_multi_queue_length_statistics(queue_length_data, simulation_end_time):

    # restructure by queue
    amount_queues = len(queue_length_data[0])
    length_by_queues = [[result[i] for result in queue_length_data] for i in range(amount_queues)]
    sum_queue_lengths = [sum([result[k] for k in range(amount_queues)]) for result in queue_length_data]

    # plot overall queue length statistics
    x = np.linspace(0, simulation_end_time, simulation_end_time + 1)
    mean_sum = timeseries_tools.time_series_mean(sum_queue_lengths, x)
    median_sum = timeseries_tools.time_series_quantile(sum_queue_lengths, x, 0.5)
    quartile_1_sum = timeseries_tools.time_series_quantile(sum_queue_lengths, x, 0.25)
    quartile_3_sum = timeseries_tools.time_series_quantile(sum_queue_lengths, x, 0.75)

    plt.plot(x, median_sum, label='Overall queue length median')
    plt.fill_between(x, quartile_1_sum, quartile_3_sum, alpha=0.2)
    plt.plot(x, mean_sum, label='Overall queue length mean')

    plt.legend()
    plt.show()

    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)

    for i, timeseries in enumerate(length_by_queues):
        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[0].plot(x, mean, label=f'Queue {i+1} length mean')

        # median
        median = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[1].plot(x, median, label=f"Queue {i+1} length median")

        # quartiles
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        quartile_3 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        ax[1].fill_between(x, quartile_3, quartile_1, alpha=0.2)

    ax[0].legend()
    ax[1].legend()
    plt.show()

# %%


# plot queue length
queue_length_data = [result[0] for result in simulation_results]
plot_multi_queue_length_statistics(queue_length_data, simulation_end_time)


# %%


# plot how busy the cashiers are
# cashiers_busy_data = [result[1] for result in simulation_results]
# plot_cashiers_busy(cashiers_busy_data, simulation_end_time)


# %%

def plot_queue_activity(queue_activity_data, simulation_end_time):
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


# plot queue activity
queue_activity_data = [result[4] for result in simulation_results]
plot_queue_activity(queue_activity_data, simulation_end_time)


# %%


# print mean and sd of customer waiting time
customer_waiting_times = list(itertools.chain.from_iterable([result[2] for result in simulation_results]))
print("Customer waiting time:")
print(f"\tmean: {np.mean(customer_waiting_times)}")
print(f"\tstandard deviation: {np.std(customer_waiting_times, ddof=1)}")
print(f"\t1. quartile: {np.quantile(customer_waiting_times, q=0.25)}")
print(f"\tmedian: {np.median(customer_waiting_times)}")
print(f"\t3. quartile: {np.quantile(customer_waiting_times, q=0.75)}")
print()

# # cashier throughput
cashier_throughput = np.array([result[3] for result in simulation_results]).T
print("Cashier throughput:")
print(f"\tmean: {np.mean(cashier_throughput, axis=1)}")
print(f"\tstandard deviation: {np.std(cashier_throughput, axis=1, ddof=1)}")
print(f"\t1. quartile: {np.quantile(cashier_throughput, axis=1, q=0.25)}")
print(f"\tmedian: {np.median(cashier_throughput, axis=1)}")
print(f"\t3. quartile: {np.quantile(cashier_throughput, axis=1, q=0.75)}")
print()
