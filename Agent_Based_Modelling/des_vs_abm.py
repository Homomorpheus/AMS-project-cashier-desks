# compare des and abm
# they should do the same

import heapq
import numpy as np
import matplotlib.pyplot as plt
import itertools

import agents
import events
import timeseries_tools
import sys
if sys.platform == "win32":
    sys.path.append(r"..\Discrete Event Simulation")
elif sys.platform == "linux":
    sys.path.append(r"../Discrete Event Simulation")
import des_task1
import mc_statistics


np.random.seed(4627)
k = 4  # number of servers

# gamma gamma. expectation = shape*scale. if shape=1: gives exp(scale)
shape1 = 1
scale1 = 2
shape2 = 2
scale2 = 3
arrival_time = lambda : np.random.gamma(shape1, scale1)
service_time = lambda : np.random.gamma(shape2, scale2)
T = 240
runs = 100
q_des, s_des = des_task1.MonteCarlo(runs, k, arrival_time, service_time, T)
des_task1.plot_statistics(q_des, s_des, T)
plt.show()

seeds = np.random.randint(2**31, size=runs)
abm_simulation_results = list(map(lambda seed: mc_statistics.simulate(seed, T, service_time, arrival_time, k), seeds))
# plot queue length
queue_length_data = [result[0] for result in abm_simulation_results]
mc_statistics.plot_queue_length_statistics(queue_length_data, T)

# plot how busy the cashiers are
cashiers_busy_data = [result[1] for result in abm_simulation_results]
mc_statistics.plot_cashiers_busy(cashiers_busy_data, T)

plt.show()