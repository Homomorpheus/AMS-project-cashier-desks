# task 3:
# Implement different queuing strategies whilst maintaining the same level of resource availability (i.e.
# the number of servers). In particular, compare whether it is better to use multiple queues for multiple
# single-server setups or a single queue for a multi-server setup.

import numpy as np
import matplotlib.pyplot as plt
import agents
import events
import heapq
import timeseries_tools

np.random.seed(4627)

# all agents are objects created in __main__
# same for all queues

# chi chi
df1 = 2
df2 = 4


# create cashier agents, customer agents, and the queue
def service_time(customer):
    return np.random.chisquare(df2)


def interarr_time():
    return np.random.chisquare(df1)


"""# exp exp
scale1 = 2
scale2 = 4


def service_time(customer):
    return np.random.exponential(scale2)


def interarr_time():
    return np.random.exponential(scale1)
"""

k = 2
cashiers = [agents.Cashier(service_time) for _ in range(k)]
customers = []
queues = [agents.Queue([cashiers[i]], []) for i in range(k)]

# create initial event
start_event = events.Arrival(scheduled_time=0., interarr_time=interarr_time, queues=queues)

# run it!
des = events.DES(start_event)
des.run(120)

for i in range(k):
    print(queues[i].timepoints)
    print(queues[i].amounts_customers)
    plt.step(queues[i].timepoints, queues[i].amounts_customers, where='post', label=f'Queue {i+1}')

plt.legend()
plt.show()

merged_timepoints = list(heapq.merge(*[queue.timepoints_amounts_customers for queue in queues]))
queue1_length = timeseries_tools.TimeSeriesStepFunction(queues[0].timepoints, queues[0].amounts_customers)
queue2_length = timeseries_tools.TimeSeriesStepFunction(queues[1].timepoints, queues[1].amounts_customers)
added_queue_length = [queue1_length.evaluate(t) + queue2_length.evaluate(t) for t in merged_timepoints]
plt.step(merged_timepoints, added_queue_length, where='post', label='added Queue length')
plt.legend()
plt.show()
