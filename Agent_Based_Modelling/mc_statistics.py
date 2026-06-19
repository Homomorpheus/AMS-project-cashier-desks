import itertools
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

import agents
import events
import timeseries_tools

def simulate(simulation_end_time, service_time, interarr_time, amount_cashiers=2):
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


def plot_queue_length_statistics(queue_length_data:list[timeseries_tools.TimeSeriesStepFunction], simulation_end_time, filename=None):
    # plotting

    """for timeseries in queue_length_data:
        ax[0].step(timeseries.timepoints, timeseries.values, where='post', color=(0.8, 0.8, 0.8))
        ax[1].step(timeseries.timepoints, timeseries.values, where='post', color=(0.8, 0.8, 0.8), zorder=1)
"""

    x = np.linspace(0, simulation_end_time, simulation_end_time+1)

    # median
    median = timeseries_tools.time_series_quantile(queue_length_data, x, 0.5)
    plt.plot(x, median, color='tab:blue', label="Median der Schlangen-Länge")
    # 1. quartile
    quartile_1 = timeseries_tools.time_series_quantile(queue_length_data, x, 0.25)
    # 3. quartile
    quartile_3 = timeseries_tools.time_series_quantile(queue_length_data, x, 0.75)
    plt.fill_between(x, quartile_3, quartile_1, color="tab:blue", alpha=0.3)

    # mean plotting
    mean = timeseries_tools.time_series_mean(queue_length_data, x)
    plt.plot(x, mean, color='tab:orange', label="Mittelwert der Schlangen-Länge")

    plt.legend()

    """if filename is not None:
        plt.savefig(filename)"""


def plot_cashiers_busy(cashiers_busy_data, simulation_end_time, filename=None):
    cashiers_busy_sorted_by_cashiers = [[cashiers_busy_data[j][i] for j in range(len(cashiers_busy_data))] for i in range(len(cashiers_busy_data[0]))]

    amount_cashiers = len(cashiers_busy_sorted_by_cashiers)
    x = np.linspace(0, simulation_end_time, simulation_end_time + 1)

    fig, ax = plt.subplots()
    business_tensor = np.array([[result[i].evaluate(x) for result in cashiers_busy_data] for i in range(amount_cashiers)])
    assert business_tensor.shape[0] == amount_cashiers
    assert business_tensor.shape[1] == len(cashiers_busy_data)
    assert business_tensor.shape[2] == len(x)
    cashiers_summed = np.sum(business_tensor, axis=0)

    mean = np.mean(cashiers_summed, axis=0)
    median = np.median(cashiers_summed, axis=0)
    quartile_1 = np.quantile(cashiers_summed, axis=0, q=0.25)
    quartile_3 = np.quantile(cashiers_summed, axis=0, q=0.75)

    ax.plot(x, median, label="Median", color='tab:blue')
    ax.fill_between(x, quartile_3, quartile_1, color="tab:blue", alpha=0.3)
    ax.plot(x, mean, label="Mean", color='tab:orange')
    plt.title('Overall cashier business')
    ax.set_ylim(bottom=0)
    ax.legend()
    plt.show()

    fig, ax = plt.subplots(nrows=amount_cashiers, sharex=True, sharey=True)

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

    # if filename is not None:
    #    plt.savefig(filename)


def plot_waiting_time_boxplot(customer_waiting_times, filename=None):
    fig, ax = plt.subplots()
    bpl = ax.boxplot(customer_waiting_times, showmeans=True, tick_labels=[""], whis=(0, 100))
    ax.legend([bpl["means"][0]], ["Mittelwert"])
    ax.set_ylabel("Wartezeit in Minuten")

    fig.show()
    if filename is not None:
        fig.savefig(filename)

def plot_cashier_throughput_boxplot(cashier_throughput, filename=None):
    fig, ax = plt.subplots()
    tick_labels = [f"Kassier_in {i}" for i in range(cashier_throughput.shape[0])]
    bpl = ax.boxplot(cashier_throughput.T, showmeans=True, tick_labels=tick_labels, whis=(0, 100))
    ax.legend([bpl["means"][0]], ["Mittelwert"])
    ax.set_ylabel("Durchsatz in Kund_innen pro Minute")

    fig.show()
    if filename is not None:
        fig.savefig(filename)

if __name__=="__main__":

    simulation_end_time = 240
    k = 4

    # chi chi
    df1 = 2
    df2 = 3
    filename_code = f"abm_chi{df1}chi{df2}k={k}"

    """def service_time(customer):
        return np.random.chisquare(df2)

    def interarr_time():
        return np.random.chisquare(df1)
        """

    """# exp chi
    scale_arr = 2
    df2 = 4
    filename_code = f"abm_e{scale_arr}chi{df2}k={k}"

    def service_time(customer):
        return np.random.chisquare(df2)

    def interarr_time():
        return np.random.exponential(scale_arr)"""

    # exp gamma
    scale_arr = 2
    shape_serv = 2
    scale_serv = 3
    filename_code = f"abm_e{scale_arr}gamma{shape_serv}_{scale_serv}k={k}"

    def interarr_time():
        return np.random.exponential(scale_arr)

    def service_time(customer):
        return np.random.gamma(shape_serv, scale_serv)

    # generate simulation seeds
    np.random.seed(4627)  # 17
    simulation_size = 5000
    seeds = np.random.randint(2**31, size=simulation_size)

    # run Monte Carlo simulation
    simulation_results = [simulate(simulation_end_time, service_time, interarr_time, k) for _ in range(simulation_size)]

    # plot queue length
    queue_length_data = [result[0] for result in simulation_results]
    plot_queue_length_statistics(queue_length_data, simulation_end_time, filename=Path("plots") / Path(f"{filename_code}_queue_length.pdf"))

    # plot how busy the cashiers are
    cashiers_busy_data = [result[1] for result in simulation_results]
    plot_cashiers_busy(cashiers_busy_data, simulation_end_time, filename=Path("plots") / Path(f"{filename_code}_cashiers_busy.pdf"))

    # print mean and sd of customer waiting time
    customer_waiting_times = list(itertools.chain.from_iterable([result[2] for result in simulation_results]))
    print("Customer waiting time:")
    print(f"\tmean: {np.mean(customer_waiting_times)}")
    print(f"\tstandard deviation: {np.std(customer_waiting_times, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(customer_waiting_times, q=0.25)}")
    print(f"\tmedian: {np.median(customer_waiting_times)}")
    print(f"\t3. quartile: {np.quantile(customer_waiting_times, q=0.75)}")
    print()
    plot_waiting_time_boxplot(customer_waiting_times, filename=Path("plots") / Path(f"{filename_code}_waiting_time_boxplot.pdf"))

    # cashier throughput
    cashier_throughput = np.array([result[3] for result in simulation_results]).T
    print("Cashier throughput:")
    print(f"\tmean: {np.mean(cashier_throughput, axis=1)}")
    print(f"\tstandard deviation: {np.std(cashier_throughput, axis=1, ddof=1)}")
    print(f"\t1. quartile: {np.quantile(cashier_throughput, axis=1, q=0.25)}")
    print(f"\tmedian: {np.median(cashier_throughput, axis=1)}")
    print(f"\t3. quartile: {np.quantile(cashier_throughput, axis=1, q=0.75)}")
    print()
    plot_cashier_throughput_boxplot(cashier_throughput, filename=Path("plots") / Path(f"{filename_code}_cashier_throughput_boxplot.pdf"))

    plt.show()
