# Implement a classic GGk queue, where arrival and service times can follow an arbitrary positive distribution.
# Test different distributions and parameters, and plot time-dependent statistics (e.g. mean,
# confidence intervals, etc.) for the queue length and server utilisation.
import heapq
import numpy as np
import matplotlib.pyplot as plt


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
            print(f"Start. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(S)

        if current_event.type == "arrival":
            Q += 1
            if S > 0:
                heapq.heappush(event_list, Event("start_service", sim_time))
            new_arrival = sim_time + arrival_time()
            heapq.heappush(event_list, Event("arrival", new_arrival))
            print(f"Arrival. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(S)

        if current_event.type == "start_service":
            S -= 1
            Q -= 1
            if S < 0 or Q < 0:
                print(f"ERROR S = {S}, Q = {Q}")
            end_time = sim_time + service_time()
            heapq.heappush(event_list, Event("end_service", end_time))
            print(f"Started Service. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(S)

        if current_event.type == "end_service":
            S += 1
            print(f"Ended Service. Q = {Q}, S = {S}, time = {sim_time}")
            timepoints.append(sim_time)
            Q_data.append(Q)
            S_data.append(S)
            if Q > 0:  # i do not even put SS on the event list, but do it immediately
                S -= 1
                Q -= 1
                if S < 0 or Q < 0:
                    print(f"ERROR S = {S}, Q = {Q}")
                end_time = sim_time + service_time()
                heapq.heappush(event_list, Event("end_service", end_time))
                print(f"Started Service. Q = {Q}, S = {S}, time = {sim_time}")
                timepoints.append(sim_time)
                Q_data.append(Q)
                S_data.append(S)

    return timepoints, Q_data, S_data


np.random.seed(4627)
k = 2  # number of servers

"""# exp exp
scale_arr = 0.5
scale_serv = 4  # mean of exp(scale) = scale
arrival_time = lambda : np.random.exponential(scale_arr)
service_time = lambda : np.random.exponential(scale_serv)
"""

"""# gamma gamma
shape1 = 2
scale1 = 1
shape2 = 2
scale2 = 2
arrival_time = lambda : np.random.gamma(shape1, scale1)
service_time = lambda : np.random.gamma(shape2, scale2)
"""

# chi chi
df1 = 3
df2 = 6
arrival_time = lambda : np.random.chisquare(df1)
service_time = lambda : np.random.chisquare(df2)

T = 50
timepoints, Q_data, S_data = run_simulation(k, arrival_time, service_time, T)
plt.step(timepoints, Q_data, where='post', label='Queue length')
plt.step(timepoints, S_data, where='post', label='Servers available')
plt.legend()
plt.show()
