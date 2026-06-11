from mc_statistics import *
import numpy as np

if __name__=="__main__":

    simulation_end_time = 120

    # chi chi
    df1 = 1
    df2 = 0.2

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
    plot_queue_length_statistics(queue_length_data, simulation_end_time, filename="plots/mc_statistics_queue_length_short_service.pdf")

    # plot how busy the cashiers are
    cashiers_busy_data = [result[1] for result in simulation_results]
    plot_cashiers_busy(cashiers_busy_data, simulation_end_time, filename="plots/mc_statistics_cashiers_busy_short_service.pdf")

    df1 = 1
    df2 = 20

    # run Monte Carlo simulation
    simulation_results = list(map(lambda seed: simulate(seed, simulation_end_time, service_time, interarr_time), seeds))

    # plot queue length
    queue_length_data = [result[0] for result in simulation_results]
    plot_queue_length_statistics(queue_length_data, simulation_end_time, filename="plots/mc_statistics_queue_length_long_service.pdf")

    # plot how busy the cashiers are
    cashiers_busy_data = [result[1] for result in simulation_results]
    plot_cashiers_busy(cashiers_busy_data, simulation_end_time, filename="plots/mc_statistics_cashiers_busy_long_service.pdf")



    # plt.show()
