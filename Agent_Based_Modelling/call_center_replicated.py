# %%

import time
import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import agents
import events
import timeseries_tools

# %%

amount_cashiers = 3

simulation_size = 300

simulation_start_time = 8 * 60 * 60
simulation_end_time = 18 * 60 * 60

day_in_year = 160
mean_interarr_time = 254.26239964 + day_in_year * -0.35616587

max_time_to_reactivation = 2 * 60
mean_time_to_reactivation = 30

shape_no_queue = 9.938980708228197614e+01
shape_slope = 9.983734779789273261e+01
scale_no_queue = 1.287301472175391037e+00
scale_slope = 2.132396556419758893e-01

def interarr_time():
    return np.random.exponential(mean_interarr_time)

def service_duration(customer, queue):
    # needs queue length
    queue_len = len(queue.customers)
    duration = np.random.gamma(shape = shape_no_queue + shape_slope / (queue_len + 1),
                                scale = scale_no_queue + scale_slope / (queue_len + 1),
                            )

    # account for fact that call cannot go beyond 18:00
    if customer.start_service_time + duration >= (18 * 60 * 60 - 1):
        # call takes until 17:59:59, for "safety"
        duration = 18 * 60 * 60 - customer.start_service_time - 1
        if duration < 0:
            duration = 0


    return duration

def time_to_activate():
    unbounded = np.random.exponential(mean_time_to_reactivation)
    if unbounded <= max_time_to_reactivation:
        return unbounded
    else:
        return max_time_to_reactivation


# %%

def simulate(simulation_end_time, interarr_time, amount_cashiers):
    "run the actual, single simulation"

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time=lambda: None) for _ in range(amount_cashiers)]
    queues = [agents.Queue(cashiers, [])]

    for cashier in cashiers:
        cashier.service_time = lambda customer: service_duration(customer, queues[0])

    # create initial event
    start_event = events.Arrival(scheduled_time=simulation_start_time, interarr_time=interarr_time, queues=queues)

    # run the DES
    des = events.DES(start_event)
    des.run(simulation_end_time)

    # collect data for statistics
    queue_lengths = [timeseries_tools.TimeSeriesStepFunction(queue.timepoints_amounts_customers, queue.amounts_customers) for queue in queues]
    cashier_activity = [timeseries_tools.TimeSeriesStepFunction(cashier.timepoints_activity_states, [int(state) for state in cashier.activity_states]) for cashier in cashiers]
    cashiers_busy = [timeseries_tools.TimeSeriesStepFunction(cashier.timepoints, [int(busy) for busy in cashier.busy_at_time]) for cashier in cashiers]
    cashier_throughputs = [cashier.throughput(simulation_start_time, simulation_end_time) for cashier in cashiers]
    waiting_times = [queue.customer_waiting_times for queue in queues]


    return queue_lengths, cashiers_busy, waiting_times, cashier_throughputs, cashier_activity


# %%

# generate simulation seeds
np.random.seed(17)
seeds = np.random.randint(2**31, size=simulation_size)
start_time = time.time()

# run Monte Carlo simulation
simulation_results = list(map(lambda seed: simulate(simulation_end_time, interarr_time, amount_cashiers), seeds))

print(f"simulation run took {(time.time()-start_time):.2f} seconds")

# %%

def plot_multi_queue_length_statistics(queue_length_data, simulation_start_time, simulation_end_time):

    # restructure by queue
    amount_queues = len(queue_length_data[0])
    length_by_queues = [[result[i] for result in queue_length_data] for i in range(amount_queues)]

    fig, ax = plt.subplots(nrows=amount_queues, sharex=True, sharey=True)
    if amount_queues ==  1:
        ax = [ax]

    for i, timeseries in enumerate(length_by_queues):
        x = np.linspace(simulation_start_time, simulation_end_time)

        # median
        mean = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[i].plot(x, mean, label="Median der Schlangenlänge")

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        # ax[1].plot(x, quartile_1, label="1. quartile")
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        # ax[1].plot(x, quartile_2, label="3. quartile")
        ax[i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.1)

        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[i].plot(x, mean, label="Mittelwert der Schlangenlänge")

        ax[i].legend()
        ax[i].set_xticks([8 * 60 * 60, 18 * 60 * 60], ["8:00", "18:00"])

    ax[-1].set_xlabel("Tageszeit")

    plt.show()

    # fig.savefig(Path("plots") / Path("replicated_queue_length.pdf"))
    ax[0].legend()
    ax[1].legend()

# %%




# plot queue length
queue_length_data = [result[0] for result in simulation_results]
plot_multi_queue_length_statistics(queue_length_data, simulation_start_time, simulation_end_time)


# %%

def plot_cashier_activity(cashier_activity_data, simulation_start_time, simulation_end_time):
    # restructure by cashier
    activity_by_cashiers = [[result[i] for result in cashier_activity_data] for i in range(amount_cashiers)]

    fig, ax = plt.subplots(nrows=1 + amount_cashiers, sharex=True, sharey=True)

    for i, timeseries in enumerate(activity_by_cashiers):
        x = np.linspace(simulation_start_time, simulation_end_time)
        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[0].plot(x, mean, label="Cashier activity mean")

        # median
        mean = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[1 + i].plot(x, mean, label="Cashier activity median")

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        ax[1 + i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.1)

    plt.show()

# plot cashier activity
cashier_activity_data = [result[4] for result in simulation_results]
plot_cashier_activity(cashier_activity_data, simulation_start_time, simulation_end_time)


def plot_cashiers_busy(cashier_business_data, simulation_start_time, simulation_end_time):
    # restructure by cashier
    business_by_cashiers = [[result[i] for result in cashier_business_data] for i in range(amount_cashiers)]

    fig, ax = plt.subplots(nrows=1 + amount_cashiers, sharex=True, sharey=True)

    for i, timeseries in enumerate(business_by_cashiers):
        x = np.linspace(simulation_start_time, simulation_end_time)
        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[0].plot(x, mean, label="Cashier business mean")

        # median
        mean = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[1 + i].plot(x, mean, label="Cashier business median")

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        ax[1 + i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.1)

    plt.show()

# plot how busy the cashiers are
cashiers_busy_data = [result[1] for result in simulation_results]
plot_cashiers_busy(cashiers_busy_data, simulation_start_time, simulation_end_time)



# %%


# print mean and sd of customer waiting time
customer_waiting_times = list(itertools.chain.from_iterable([result[2][0] for result in simulation_results]))
print("Customer waiting time:")
print(f"\tmean: {np.mean(customer_waiting_times)}")
print(f"\tstandard deviation: {np.std(customer_waiting_times, ddof=1)}")
print(f"\t1. quartile: {np.quantile(customer_waiting_times, q=0.25)}")
print(f"\tmedian: {np.median(customer_waiting_times)}")
print(f"\t3. quartile: {np.quantile(customer_waiting_times, q=0.75)}")
print()
