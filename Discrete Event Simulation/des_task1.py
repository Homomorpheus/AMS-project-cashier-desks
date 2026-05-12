# Implement a classic GGk queue, where arrival and service times can follow an arbitrary positive distribution.
# Test different distributions and parameters, and plot time-dependent statistics (e.g. mean,
# confidence intervals, etc.) for the queue length and server utilisation.
import heapq
import numpy as np
import matplotlib.pyplot as plt
from bisect import bisect_left


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

    mean_queue = np.zeros(int(T)+1)
    mean_server_utilisation = np.zeros(int(T)+1)
    mean_sq_queue = np.zeros(int(T)+1)
    mean_sq_server_utilisation = np.zeros(int(T)+1)
    var_queue = np.zeros(int(T)+1)
    var_server_utilisation = np.zeros(int(T)+1)

    for i in range(1, runs+1):

        timepoints, Q_data, S_data = run_simulation(k, arrival_time, service_time, T)
        """plt.step(timepoints, Q_data, where='post', color='red')
        plt.step(timepoints, S_data, where='post', color='blue')"""

        equidistant_Q = [Q_data[0]]
        equidistant_S = [S_data[0]]

        lo = 0
        for j in range(1, int(T)+1):
            # find last index s.t. timepoints[index] < T
            idx = bisect_left(timepoints, j, lo=lo) - 1
            equidistant_Q.append(Q_data[idx])
            equidistant_S.append(S_data[idx])
            lo = max(lo, idx) if idx >= 0 else lo
            # update means
            mean_queue[j] = (i-1)/i*mean_queue[j] + 1/i*equidistant_Q[j]
            mean_server_utilisation[j] = (i-1)/i*mean_server_utilisation[j] + 1/i*equidistant_S[j]
            mean_sq_queue[j] = (i-1)/i*mean_sq_queue[j] + 1/i*equidistant_Q[j]**2
            mean_sq_server_utilisation[j] = (i - 1) / i * mean_sq_server_utilisation[j] + 1 / i * equidistant_S[j]**2
            if i > 1:
                var_queue[j] = i/(i-1)*(mean_sq_queue[j] - mean_queue[j]**2)
                var_server_utilisation[j] = i/(i-1)*(mean_sq_server_utilisation[j] - mean_server_utilisation[j]**2)

    """plt.title('Queue length: red, Server utilisation: blue')
    plt.show()"""

    return mean_queue, mean_server_utilisation, var_queue, var_server_utilisation


np.random.seed(4627)
k = 5  # number of servers

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
df1 = 1
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
runs = 300
mean_queue, mean_servers, var_queue, var_servers = MonteCarlo(runs, k, arrival_time, service_time, T)
plt.step(range(T+1), mean_queue, where='post', color='red', label='mean queue length')
plt.step(range(T+1), mean_servers, where='post', color='blue', label='mean server utilisation')
plt.step(range(T+1), mean_queue - np.sqrt(var_queue), where='post', color='red', linestyle='dashed', linewidth=1)
plt.step(range(T+1), mean_queue + np.sqrt(var_queue), where='post', color='red', linestyle='dashed', linewidth=1)
plt.step(range(T+1), mean_servers - np.sqrt(var_servers), where='post', color='blue', linestyle='dashed', linewidth=1)
plt.step(range(T+1), mean_servers + np.sqrt(var_servers), where='post', color='blue', linestyle='dashed', linewidth=1)
plt.legend()
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
