# %%

import time
import itertools

import matplotlib.pyplot as plt
import numpy as np

# matplotlib.rcParams['figure.figsize'] = [12, 12]

import agents
import events
import timeseries_tools

# %%

amount_cashiers = 4

simulation_size = 300

simulation_start_time = 8 * 60 * 60
simulation_end_time = 18 * 60 * 60

day_in_year = 160
mean_interarr_time = 254.26239964 + day_in_year * -0.35616587

max_time_to_reactivation = 2 * 60
mean_time_to_reactivation = 30

shape_no_queue = 1.000000000268730446e+03
shape_slope = 6.496680292314401760e-08
scale_no_queue = 2.337070386598759653e-01
scale_slope = 9.999998500570692062e-02

def interarr_time():
    return np.random.exponential(mean_interarr_time)

def service_duration(customer, queue):
    # needs queue length
    queue_len = len(queue.customers)
    duration = np.random.gamma(shape = shape_no_queue + queue_len * shape_slope,
                               scale = scale_no_queue + queue_len * scale_slope,
                              )

    # account for fact that call cannot go beyond 18:00
    # if customer.start_service_time + duration >= (18 * 60 * 60 - 1):
    #     # call takes until 17:59:59, for "safety"
    #     duration = 18 * 60 * 60 - customer.start_service_time - 1
    #     if duration < 0:
    #         duration = 0


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
    cashiers = [agents.Cashier(service_time=lambda: None, active=False, threshold_lo=i/2, threshold_hi=i/2 + 1, time_to_activate=time_to_activate, time=simulation_start_time) for i in range(amount_cashiers)]
    cashiers[0].set_active(True, simulation_start_time)
    # cashiers = [agents.Cashier(service_time=lambda: None) for _ in range(amount_cashiers)]
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
        ax[i].plot(x, mean, label="Queue length median")

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        # ax[1].plot(x, quartile_1, label="1. quartile")
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        # ax[1].plot(x, quartile_2, label="3. quartile")
        ax[i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.1)

        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[i].plot(x, mean, label="Queue length mean")

    plt.show()
    # ax[0].legend()
    # ax[1].legend()

# %%




# plot queue length
queue_length_data = [result[0] for result in simulation_results]
plot_multi_queue_length_statistics(queue_length_data, simulation_start_time, simulation_end_time)


# %%


# plot how busy the cashiers are
# cashiers_busy_data = [result[1] for result in simulation_results]
# plot_cashiers_busy(cashiers_busy_data, simulation_end_time)


# %%

def plot_cashier_activity(cashier_activity_data, simulation_start_time, simulation_end_time):
    # restructure by cashier
    activity_by_cashiers = [[result[i] for result in cashier_activity_data] for i in range(amount_cashiers)]

    fig, ax = plt.subplots(nrows=amount_cashiers, sharex=True, sharey=True)

    for i, timeseries in enumerate(activity_by_cashiers):
        x = np.linspace(simulation_start_time, simulation_end_time)

        # median
        mean = timeseries_tools.time_series_quantile(timeseries, x, 0.5)
        ax[i].plot(x, mean, label="Cashier activity median")

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(timeseries, x, 0.25)
        # ax[1].plot(x, quartile_1, label="1. quartile")
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        # ax[1].plot(x, quartile_2, label="3. quartile")
        ax[i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.1)

        mean = timeseries_tools.time_series_mean(timeseries, x)
        ax[i].plot(x, mean, label="Cashier activity mean")

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
        # ax[1].plot(x, quartile_1, label="1. quartile")
        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(timeseries, x, 0.75)
        # ax[1].plot(x, quartile_2, label="3. quartile")
        ax[1 + i].fill_between(x, quartile_2, quartile_1, color="blue", alpha=0.1)

    plt.show()

# plot how busy the cashiers are
# cashiers_busy_data = [result[1] for result in simulation_results]
# plot_cashiers_busy(cashiers_busy_data, simulation_start_time, simulation_end_time)



# %%


# print mean and sd of customer waiting time
customer_waiting_times = list(itertools.chain.from_iterable([result[2][0] for result in simulation_results]))
print(customer_waiting_times[0])
print("Customer waiting time:")
print(f"\tmean: {np.mean(customer_waiting_times)}")
print(f"\tstandard deviation: {np.std(customer_waiting_times, ddof=1)}")
print(f"\t1. quartile: {np.quantile(customer_waiting_times, q=0.25)}")
print(f"\tmedian: {np.median(customer_waiting_times)}")
print(f"\t3. quartile: {np.quantile(customer_waiting_times, q=0.75)}")
print()

# total inactivity time
# total_inactivity_times = []
# for cashiers_activity in [data[4] for data in simulation_results]:
#     per_sim_inactivity = 0
#     for individual_activity in cashiers_activity:
#         # check validity
#         for i in range(1, len(individual_activity.values)):
#             assert individual_activity.values[i] == (not individual_activity.values[i - 1])
#         assert individual_activity.values[0] == simulation_start_time
#         if individual_activity.values[0] == 1:
#             per_sim_inactivity += sum()
#         elif individual_activity.values[0] == 0:
#             ...?
#         else:
#             raise RuntimeError
#     total_inactivity_times.append(per_sim_inactivity)


# # cashier throughput
# cashier_throughput = np.array([result[3] for result in simulation_results]).T
# print("Cashier throughput:")
# print(f"\tmean: {np.mean(cashier_throughput, axis=1)}")
# print(f"\tstandard deviation: {np.std(cashier_throughput, axis=1, ddof=1)}")
# print(f"\t1. quartile: {np.quantile(cashier_throughput, axis=1, q=0.25)}")
# print(f"\tmedian: {np.median(cashier_throughput, axis=1)}")
# print(f"\t3. quartile: {np.quantile(cashier_throughput, axis=1, q=0.75)}")
# print()
