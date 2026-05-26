import heapq

import agents

class DES:
    """discrete event simulation class;
    manages the event list, runs everything"""
    def __init__(self, start_event):
        self.event_list = [start_event]

    def push(self, event):
        "push to event list"
        heapq.heappush(self.event_list, event)

    def pop(self):
        "pop from event list, returns event"
        return heapq.heappop(self.event_list)

    def run(self, end_time):
        "run the DES"
        while True:
            current_event = self.pop()
            time = current_event.scheduled_time
            if time > end_time:
                break
            current_event.execute(self)

    def __str__(self):
        return f"Discrete event simulation, with {len(self.event_list)} events in queue"

class Event:

    def __init__(self, scheduled_time=0.0):
        self.scheduled_time = scheduled_time

    def __lt__(self, other):
        return self.scheduled_time < other.scheduled_time

    def execute(self, des):
        raise NotImplementedError("define execute in subclass")


class Arrival(Event):

    def __init__(self, scheduled_time, interarr_time, queues, customer_properties = dict()):
        super().__init__(scheduled_time)
        self.interarr_time = interarr_time
        self.queues = queues
        self.customer_properties = customer_properties

    def execute(self, des):
        # add Customer to shortest queue
        """print('Customer arriving')
        print('Current queue lengths:')
        for queue in self.queues:
            print(str(queue))"""
        queue_lengths = [len(queue.customers) for queue in self.queues]
        shortest_queue_index = queue_lengths.index(min(queue_lengths))
        # print('Chosen queue:', shortest_queue_index)
        self.queues[shortest_queue_index].add_customer(agents.Customer(arrival_in_queue=self.scheduled_time,
                                                properties=self.customer_properties
                                               ),
                                time = self.scheduled_time
                                )
        """print('Customer chose queue')
        print('Current queue lengths:')
        for queue in self.queues:
            print(str(queue))"""
        # schedule next arrival
        des.push(Arrival(self.scheduled_time+self.interarr_time(), self.interarr_time,
                         self.queues, self.customer_properties
                        ))
        # if possible, immediately go to cashier
        next_free_cashier = self.queues[shortest_queue_index].find_free_cashier()
        if next_free_cashier != "busy":
            # reserve cashier until StartService
            next_free_cashier.set_busy(True, self.scheduled_time)
            # schedule StartService
            des.push(StartService(self.scheduled_time, self.queues, next_free_cashier, shortest_queue_index))

    def __str__(self):
        return f"Arrival event, scheduled at t = {self.scheduled_time}, with customer properties {self.customer_properties}"


class StartService(Event):

    def __init__(self, scheduled_time, queues, cashier, shortest_queue_index=0, customer=None):
        super().__init__(scheduled_time)
        self.queues = queues
        self.chosen_queue_index = shortest_queue_index
        self.chosen_queue = queues[shortest_queue_index]
        assert cashier in queues[shortest_queue_index].cashiers
        self.cashier = cashier
        self.customer = customer

    def execute(self, des):
        # start service
        self.cashier.set_busy(True, self.scheduled_time)
        if self.customer is None:
            self.customer = self.chosen_queue.remove_customer(time = self.scheduled_time)

        # store waiting time
        self.customer.waiting_time = self.scheduled_time - self.customer.arrival_in_queue
        if self.chosen_queue.log:
            self.chosen_queue.customer_waiting_times.append(self.customer.waiting_time)

        # schedule end of service
        end_service_time = self.scheduled_time + self.cashier.service_time(self.customer)
        des.push(EndService(end_service_time, self.queues, self.cashier, self.chosen_queue_index))

    def __str__(self):
        return f"StartService event in Queue {self.chosen_queue_index}, scheduled at t = {self.scheduled_time}"


class EndService(Event):

    def __init__(self, scheduled_time, queues, cashier, chosen_queue_index=0):
        super().__init__(scheduled_time)
        self.cashier = cashier
        self.queues = queues
        self.chosen_queue_index = chosen_queue_index

    def execute(self, des):
        # free the cashier
        self.cashier.set_busy(False, self.scheduled_time)

        # if possible, immediately serve next customer;
        # the next customer is taken out of the queue so that
        # it does not disappear until StartService
        next_customer = self.queues[self.chosen_queue_index].remove_customer(time = self.scheduled_time)
        if next_customer != "empty":
            des.push(StartService(self.scheduled_time, self.queues, self.cashier,
                                  shortest_queue_index=self.chosen_queue_index,
                                  customer=next_customer
                                  ))

    def __str__(self):
        return f"EndService event in Queue {self.chosen_queue_index}, scheduled at t = {self.scheduled_time}"
