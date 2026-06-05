import itertools
import numpy as np
import matplotlib.pyplot as plt

import agents
import events
import timeseries_tools

def simulate(seed, simulation_end_time, service_time, interarr_time, amount_cashiers=2):
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

    return (queue_length, cashiers_busy, queue.customer_waiting_times, cashier_throughputs)


def plot_queue_length_statistics(queue_length_data:list[timeseries_tools.TimeSeriesStepFunction], simulation_end_time):
    # plotting
    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)

    for timeseries in queue_length_data:
        ax[0].step(timeseries.timepoints, timeseries.values, where='post', color=(0.8, 0.8, 0.8))
        ax[1].step(timeseries.timepoints, timeseries.values, where='post', color=(0.8, 0.8, 0.8))

    # mean plotting
    x = np.linspace(0, simulation_end_time)
    mean = timeseries_tools.time_series_mean(queue_length_data, x)
    ax[0].plot(x, mean, label="Queue length mean")
    # ax[0].step(x, mean, label="Queue length mean", where="post")

    # mean +- standard deviation
    std_dev = timeseries_tools.time_series_std_deviation(queue_length_data, x)
    ax[0].plot(x, mean - std_dev, label="mean - std deviation")
    ax[0].plot(x, mean + std_dev, label="mean + std deviation")

    # median
    mean = timeseries_tools.time_series_quantile(queue_length_data, x, 0.5)
    ax[1].plot(x, mean, label="Queue length median")

    # 1. quartile
    quartile_1 = timeseries_tools.time_series_quantile(queue_length_data, x, 0.25)
    ax[1].plot(x, quartile_1, label="1. quartile")

    # 3. quartile
    quartile_2 = timeseries_tools.time_series_quantile(queue_length_data, x, 0.75)
    ax[1].plot(x, quartile_2, label="3. quartile")

    ax[0].legend()
    ax[1].legend()


def plot_cashiers_busy(cashiers_busy_data, simulation_end_time):
    cashiers_busy_sorted_by_cashiers = [[cashiers_busy_data[j][i] for j in range(len(cashiers_busy_data))] for i in range(len(cashiers_busy_data[0]))]

    amount_cashiers = len(cashiers_busy_sorted_by_cashiers)
    fig, ax = plt.subplots(nrows=amount_cashiers)
    x = np.arange(0, simulation_end_time + 1)

    for i in range(amount_cashiers):
        multi_timeseries = cashiers_busy_sorted_by_cashiers[i]

        for series in multi_timeseries:
            ax[i].step(series.timepoints, series.values, where='post', color=(0.8, 0.8, 0.8))

        # 1. quartile
        quartile_1 = timeseries_tools.time_series_quantile(multi_timeseries, x, 0.25)
        ax[i].plot(x, quartile_1, label="1. quartile")

        # 3. quartile
        quartile_2 = timeseries_tools.time_series_quantile(multi_timeseries, x, 0.75)
        ax[i].plot(x, quartile_2, label="3. quartile")

        # median
        median = timeseries_tools.time_series_quantile(multi_timeseries, x, 0.5)
        ax[i].plot(x, median, label="Cashier busy: median")

        ax[i].legend()

if __name__=="__main__":

    simulation_end_time = 50

    # chi chi
    df1 = 2
    df2 = 4

    def service_time(customer):
        return np.random.chisquare(df2)

    def interarr_time():
        return np.random.chisquare(df1)

    # generate simulation seeds
    np.random.seed(17)
    simulation_size = 30
    seeds = np.random.randint(2**31, size=simulation_size)

    # run Monte Carlo simulation
    simulation_results = list(map(lambda seed: simulate(seed, simulation_end_time, service_time, interarr_time), seeds))

    # plot queue length
    queue_length_data = [result[0] for result in simulation_results]
    plot_queue_length_statistics(queue_length_data, simulation_end_time)

    # plot how busy the cashiers are
    cashiers_busy_data = [result[1] for result in simulation_results]
    plot_cashiers_busy(cashiers_busy_data, simulation_end_time)

    # print mean and sd of customer waiting time
    customer_waiting_times = list(itertools.chain.from_iterable([result[2] for result in simulation_results]))
    print("Customer waiting time:")
    print(f"\tmean: {np.mean(customer_waiting_times)}")
    print(f"\tstandard deviation: {np.std(customer_waiting_times, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(customer_waiting_times, q=0.25)}")
    print(f"\tmedian: {np.median(customer_waiting_times)}")
    print(f"\t3. quartile: {np.quantile(customer_waiting_times, q=0.75)}")
    print()

    # cashier throughput
    cashier_throughput = np.array([result[3] for result in simulation_results]).T
    print("Cashier throughput:")
    print(f"\tmean: {np.mean(cashier_throughput, axis=1)}")
    print(f"\tstandard deviation: {np.std(cashier_throughput, axis=1, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(cashier_throughput, axis=1, q=0.25)}")
    print(f"\tmedian: {np.median(cashier_throughput, axis=1)}")
    print(f"\t3. quartile: {np.quantile(cashier_throughput, axis=1, q=0.75)}")
    print()

    plt.show()
