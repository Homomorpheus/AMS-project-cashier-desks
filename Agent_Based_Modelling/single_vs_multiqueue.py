import itertools
import numpy as np
import matplotlib.pyplot as plt
import agents
import events
import timeseries_tools
import time
from pathlib import Path

start_time = time.time()


def simulate_single_queue(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=2):
    "run the actual, single simulation"

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time) for _ in range(amount_cashiers)]
    customers = []
    queue = agents.Queue(cashiers, customers)

    # create initial event
    start_event = events.Arrival(scheduled_time=0., interarr_time=interarr_time, queues=[queue])

    # run the DES
    des = events.DES(start_event)
    des.run(simulation_end_time)

    # collect data for statistics
    queue_length = timeseries_tools.TimeSeriesStepFunction(queue.timepoints_amounts_customers, queue.amounts_customers)
    cashiers_busy = [timeseries_tools.TimeSeriesStepFunction(cashier.timepoints, [int(busy) for busy in cashier.busy_at_time]) for cashier in cashiers]
    cashier_throughputs = [cashier.throughput(0, simulation_end_time) for cashier in cashiers]

    return queue_length, cashiers_busy, queue.customer_waiting_times, cashier_throughputs


# simulates multi queue scenario and returns data as timeseries_tools.TimeStepFunction
def simulate_multiqueue(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=2):
    "run the actual, single simulation"

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time) for _ in range(amount_cashiers)]
    queues = [agents.Queue([cashiers[i]], []) for i in range(amount_cashiers)]

    # create initial event
    start_event = events.Arrival(scheduled_time=0., interarr_time=interarr_time, queues=queues)

    # run the DES
    des = events.DES(start_event)
    des.run(simulation_end_time)

    # collect data for statistics
    queue_lengths = [timeseries_tools.TimeSeriesStepFunction(queue.timepoints_amounts_customers, queue.amounts_customers) for queue in queues]
    cashiers_busy = [timeseries_tools.TimeSeriesStepFunction(cashier.timepoints, [int(busy) for busy in cashier.busy_at_time]) for cashier in cashiers]
    cashier_throughputs = [cashier.throughput(0, simulation_end_time) for cashier in cashiers]
    waiting_times = [queue.customer_waiting_times for queue in queues]

    return queue_lengths, cashiers_busy, waiting_times, cashier_throughputs


def compare_queue_length_statistics(queue_length_data_single, queue_length_data_multi, simulation_end_time):

    """for timeseries in total_queue_length_data:
        ax[0].step(timeseries.timepoints, timeseries.values, where='post', color=(0.8, 0.8, 0.8))
        ax[1].step(timeseries.timepoints, timeseries.values, where='post', color=(0.8, 0.8, 0.8))"""
    fig, ax = plt.subplots(ncols=2, sharex=True, sharey=True)
    # mean and median for single queue
    x = np.linspace(0, simulation_end_time)
    mean_single = timeseries_tools.time_series_mean(queue_length_data_single, x)
    median_single = timeseries_tools.time_series_quantile(queue_length_data_single, x, 0.5)
    ax[0].plot(x, mean_single, label="Single queue length mean", color='firebrick')
    ax[0].plot(x, median_single, label="Single queue length median", color='red')

    # 1st and 3rd quartile of single queue
    quartile_1_single = timeseries_tools.time_series_quantile(queue_length_data_single, x, 0.25)
    quartile_3_single = timeseries_tools.time_series_quantile(queue_length_data_single, x, 0.75)
    ax[0].fill_between(x, quartile_1_single, quartile_3_single, color='red', alpha=0.2)

    # mean and median for multi queue
    mean_multi = timeseries_tools.time_series_mean(queue_length_data_multi, x)
    ax[1].plot(x, mean_multi, label="Total queue length mean for multiqueue", color='navy')
    median_multi = timeseries_tools.time_series_quantile(queue_length_data_multi, x, 0.5)
    ax[1].plot(x, median_multi, label="Total queue length median for multiqueue", color='blue')

    # 1. quartile
    quartile_1_multi = timeseries_tools.time_series_quantile(queue_length_data_multi, x, 0.25)
    quartile_3_multi = timeseries_tools.time_series_quantile(queue_length_data_multi, x, 0.75)
    ax[1].fill_between(x, quartile_1_multi, quartile_3_multi, color='blue', alpha=0.2)

    ax[0].legend()
    ax[1].legend()

    """# mean +- standard deviation
    std_dev_single = timeseries_tools.time_series_std_deviation(queue_length_data_single, x)
    ax[0].plot(x, mean_single - std_dev_single, color='red', linestyle='dashed', linewidth=1)
    ax[0].plot(x, mean_single + std_dev_single, color='red', linestyle='dashed', linewidth=1)
    std_dev_multi = timeseries_tools.time_series_std_deviation(queue_length_data_multi, x)
    ax[0].plot(x, mean_multi - std_dev_multi, color='blue', linestyle='dashed', linewidth=1)
    ax[0].plot(x, mean_multi + std_dev_multi, color='blue', linestyle='dashed', linewidth=1)
"""


def compare_cashiers_busy(cashiers_busy_data_single, cashiers_busy_data_multi, simulation_end_time):
    cashiers_busy_sorted_by_cashiers_single = [[cashiers_busy_data_single[j][i] for j in range(len(cashiers_busy_data_single))] for i in range(len(cashiers_busy_data_single[0]))]
    cashiers_busy_sorted_by_cashiers_multi = [[cashiers_busy_data_multi[j][i] for j in range(len(cashiers_busy_data_multi))] for i in range(len(cashiers_busy_data_multi[0]))]

    amount_cashiers = len(cashiers_busy_sorted_by_cashiers_single)
    fig, ax = plt.subplots(nrows=amount_cashiers, sharex=True, sharey=True)
    x = np.arange(0, simulation_end_time + 1)

    for i in range(amount_cashiers):
        multi_timeseries_single = cashiers_busy_sorted_by_cashiers_single[i]
        multi_timeseries_multi = cashiers_busy_sorted_by_cashiers_multi[i]

        # for series in multi_timeseries_multi:
        #     ax[i].step(series.timepoints, series.values, where='post', color=(0.8, 0.8, 0.8))

        # median and quartiles for single queue
        median_single = timeseries_tools.time_series_quantile(multi_timeseries_single, x, 0.5)
        ax[i].plot(x, median_single, label="median for single queue", color='red')
        quartile_1_single = timeseries_tools.time_series_quantile(multi_timeseries_single, x, 0.25)
        quartile_3_single = timeseries_tools.time_series_quantile(multi_timeseries_single, x, 0.75)
        ax[i].fill_between(x, quartile_1_single, quartile_3_single, color='red', alpha=0.2)

        # median and quartiles for multi queue
        median_multi = timeseries_tools.time_series_quantile(multi_timeseries_multi, x, 0.5)
        ax[i].plot(x, median_multi, label="median for multiple queues", color='blue')
        quartile_1_multi = timeseries_tools.time_series_quantile(multi_timeseries_multi, x, 0.25)
        quartile_3_multi = timeseries_tools.time_series_quantile(multi_timeseries_multi, x, 0.75)
        ax[i].fill_between(x, quartile_1_multi, quartile_3_multi, color='blue', alpha=0.2)

        ax[i].legend()


def plot_waiting_time_boxplot(simulation_results_singlequeue, simulation_results_multiqueue, filename=None):
    customer_waiting_times = list(itertools.chain.from_iterable([result[2] for result in simulation_results_singlequeue]))
    all_customer_waiting_times_multiqueue = [list(itertools.chain.from_iterable(result[2][i] for result in simulation_results_multiqueue)) for i in range(k)]

    fig = plt.figure()
    gs = fig.add_gridspec(ncols=2, wspace=0, width_ratios=[1, k])
    ax = gs.subplots(sharey=True)

    ax[0].boxplot(customer_waiting_times, showmeans=True, tick_labels=[""], whis=(0, 100))
    # ax[0].legend([bpl0["means"][0]], ["Mittelwert"])
    ax[0].set_ylabel("Wartezeit in Minuten")
    ax[0].set_xlabel("Einzelne\nSchlange")

    tick_labels = [f"Schlange {i + 1}" for i in range(k)]
    bpl1 = ax[1].boxplot(all_customer_waiting_times_multiqueue, showmeans=True, tick_labels=tick_labels, whis=(0, 100))
    ax[1].legend([bpl1["means"][0]], ["Mittelwert"])
    # ax[1].set_ylabel("Wartezeit in Minuten")
    ax[1].set_xlabel("Mehrere Schlangen")

    plt.show()
    if filename is not None:
        fig.savefig(filename)


def plot_cashier_throughput_boxplot(k, cashier_throughput_single, cashier_throughput_multi, filename=None):
    fig, ax = plt.subplots(nrows=k, sharex=True, figsize=(10, 6))
    tick_labels = ["Einzelne\nSchlange", "Mehrere\nSchlangen"]

    for i in range(k):
        bpl = ax[i].boxplot([cashier_throughput_single[i, :], cashier_throughput_multi[i, :]], showmeans=True, tick_labels=tick_labels, whis=(0, 100), vert=False)
        if i == 0:
            fig.legend([bpl["means"][0]], ["Mittelwert"], loc="outside right upper")
        ax[i].set_ylabel(f"Kassier_in {i + 1}")

    ax[-1].set_xlabel("Kunden pro Minute")

    plt.show()
    if filename is not None:
        fig.savefig(filename)


if __name__=="__main__":

    simulation_end_time = 120

    k = 5
    # chi chi
    df1 = 2
    df2 = 3

    def service_time(customer):
        return np.random.chisquare(df2)

    def interarr_time():
        return np.random.chisquare(df1)

    """# exp gamma
    scale_arr = 2  # mean of exp(scale) = scale
    shape_serv = 2
    scale_serv = 3
    filename_code = "singlevsmulti_1"

    def service_time(customer):
        return np.random.gamma(shape_serv, scale_serv)

    def interarr_time():
        return np.random.exponential(scale_arr)"""

    # generate simulation seeds
    np.random.seed(17)
    simulation_size =1000
    seeds = np.random.randint(2**31, size=simulation_size)

    # run Monte Carlo simulation
    simulation_results_multiqueue = list(map(lambda seed: simulate_multiqueue(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=k), seeds))
    simulation_results_singlequeue = list(map(lambda seed: simulate_single_queue(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=k), seeds))

    end_time = time.time()

    # plot queue length
    single_queue_length_data = [result[0] for result in simulation_results_singlequeue]
    multi_queue_length_data = [sum([result[0][i] for i in range(k)]) for result in simulation_results_multiqueue]
    compare_queue_length_statistics(single_queue_length_data, multi_queue_length_data, simulation_end_time)

    # plot how busy the cashiers are
    cahier_busy_data_singlequeue = [result[1] for result in simulation_results_singlequeue]
    cashiers_busy_data_multiqueue = [result[1] for result in simulation_results_multiqueue]
    compare_cashiers_busy(cahier_busy_data_singlequeue, cashiers_busy_data_multiqueue, simulation_end_time)
    plt.tight_layout()
    plt.show()

    # print mean and sd of customer waiting time
    customer_waiting_times = list(itertools.chain.from_iterable([result[2] for result in simulation_results_singlequeue]))
    print("Customer waiting time in single queue simulation:")
    print(f"\tmean: {np.mean(customer_waiting_times)}")
    print(f"\tstandard deviation: {np.std(customer_waiting_times, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(customer_waiting_times, q=0.25)}")
    print(f"\tmedian: {np.median(customer_waiting_times)}")
    print(f"\t3. quartile: {np.quantile(customer_waiting_times, q=0.75)}")
    print()

    print("Customer waiting time in multi queue simulation:")
    for i in range(k):
        customer_waiting_times_multiqueue = list(itertools.chain.from_iterable(result[2][i] for result in simulation_results_multiqueue))
        print(f"in Queue {i+1}:")
        print(f"\tmean: {np.mean(customer_waiting_times_multiqueue)}")
        print(f"\tstandard deviation: {np.std(customer_waiting_times_multiqueue, ddof=1)}")
        print(f"\t1. quartile: {np.quantile(customer_waiting_times_multiqueue, q=0.25)}")
        print(f"\tmedian: {np.median(customer_waiting_times_multiqueue)}")
        print(f"\t3. quartile: {np.quantile(customer_waiting_times_multiqueue, q=0.75)}")
        print()

    plot_waiting_time_boxplot(simulation_results_singlequeue, simulation_results_multiqueue, filename=Path("plots") / Path(filename_code + "_waiting_time_boxplot.pdf"))

    # cashier throughput
    cashier_throughput_single = np.array([result[3] for result in simulation_results_singlequeue]).T
    print("Cashier throughput in single queue simulation:")
    print(f"\tmean: {np.mean(cashier_throughput_single, axis=1)}")
    print(f"\tstandard deviation: {np.std(cashier_throughput_single, axis=1, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(cashier_throughput_single, axis=1, q=0.25)}")
    print(f"\tmedian: {np.median(cashier_throughput_single, axis=1)}")
    print(f"\t3. quartile: {np.quantile(cashier_throughput_single, axis=1, q=0.75)}")
    print()


    cashier_throughput_multi = np.array([result[3] for result in simulation_results_multiqueue]).T
    print("Cashier throughput in multi queue simulation:")
    print(f"\tmean: {np.mean(cashier_throughput_multi, axis=1)}")
    print(f"\tstandard deviation: {np.std(cashier_throughput_multi, axis=1, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(cashier_throughput_multi, axis=1, q=0.25)}")
    print(f"\tmedian: {np.median(cashier_throughput_multi, axis=1)}")
    print(f"\t3. quartile: {np.quantile(cashier_throughput_multi, axis=1, q=0.75)}")
    print()

    plot_cashier_throughput_boxplot(k, cashier_throughput_single, cashier_throughput_multi, filename=Path("plots") / Path(filename_code + "_throughput_boxplot.pdf"))

    print(f"Simulation time: {end_time - start_time}")

# conclusio: single queue is generally better
# reason: a new customer does not know how long it will take until the next server is free
# so when both queues are equally long, the customer might choose the one with longer waiting time
# meanwhile, the other cashier sits around and does nothing because the customer is not in their queue
# perfect example: exp(1) exp(2) k=3.
# in the single queue simulation, all three cashiers are busy most of the time
# in the multi queue model, the third cashier is not busy most of the time.
# customer waiting times: 0.9 vs 1.8, 1.6, 1.5
# also very interesting: exp(0.5) exp(4.5) k=10
# single queue length is about 2 or less, multi queue length rises to 8
# single queue waiting time: 1.5, multi queue: 3.5 - 5.3
