# Implement a classic GGk queue, where arrival and service times can follow an arbitrary positive distribution.
# Test different distributions and parameters, and plot time-dependent statistics (e.g. mean,
# confidence intervals, etc.) for the queue length and server utilisation.
import numpy as np
import matplotlib.pyplot as plt

import agents
import events

np.random.seed(4627)

# all agents are objects created in __main__
# same for all queues

# chi chi
df1 = 2
df2 = 4

# create cashier agents, customer agents, and the queue
def service_time(customer):
    return np.random.chisquare(df2)
cashiers = [agents.Cashier(service_time) for _ in range(2)]
customers = []
queue = agents.Queue(cashiers, customers)

# create initial event
def interarr_time():
    return np.random.chisquare(df1)
start_event = events.Arrival(scheduled_time=0., interarr_time=interarr_time, queues=[queue])

# run it!
des = events.DES(start_event)
des.run(120)

print(queue.timepoints_amounts_customers)
print(queue.amounts_customers)

plt.step(queue.timepoints, queue.amounts_customers, where='post', label='Queue length')
plt.legend()
plt.show()
