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

    def __init__(self, scheduled_time, interarr_time, queue, customer_properties = dict()):
        super().__init__(scheduled_time)
        self.interarr_time = interarr_time
        self.queue = queue
        self.customer_properties = customer_properties

    def execute(self, des):
        # add Customer to queue
        self.queue.add_customer(agents.Customer(arrival_in_queue=self.scheduled_time,
                                                properties=self.customer_properties
                                               ),
                                time = self.scheduled_time
                                )
        # schedule next arrival
        des.push(Arrival(self.scheduled_time+self.interarr_time(), self.interarr_time,
                         self.queue, self.customer_properties
                        ))
        # if possible, immediately go to cashier
        next_free_cashier = self.queue.find_free_cashier()
        if next_free_cashier != "busy":
            # reserve cashier until StartService
            next_free_cashier.set_busy(True, self.scheduled_time)
            # schedule StartService
            des.push(StartService(self.scheduled_time, self.queue, next_free_cashier))

    def __str__(self):
        return f"Arrival event, scheduled at t = {self.scheduled_time}, with customer properties {self.customer_properties}"


class StartService(Event):

    def __init__(self, scheduled_time, queue, cashier, customer=None):
        super().__init__(scheduled_time)
        self.queue = queue
        assert cashier in queue.cashiers
        self.cashier = cashier
        self.customer = customer

    def execute(self, des):
        # start service
        self.cashier.set_busy(True, self.scheduled_time)
        if self.customer is None:
            self.customer = self.queue.remove_customer(time = self.scheduled_time)

        # store waiting time
        self.customer.waiting_time = self.scheduled_time - self.customer.arrival_in_queue
        if self.queue.log:
            self.queue.customer_waiting_times.append(self.customer.waiting_time)

        # schedule end of service
        end_service_time = self.scheduled_time + self.cashier.service_time(self.customer)
        des.push(EndService(end_service_time, self.queue, self.cashier))

    def __str__(self):
        return f"StartService event, scheduled at t = {self.scheduled_time}"


class EndService(Event):

    def __init__(self, scheduled_time, queue, cashier):
        super().__init__(scheduled_time)
        self.cashier = cashier
        self.queue = queue

    def execute(self, des):
        # free the cashier
        self.cashier.set_busy(False, self.scheduled_time)

        # if possible, immediately serve next customer;
        # the next customer is taken out of the queue so that
        # it does not disappear until StartService
        next_customer = self.queue.remove_customer(time = self.scheduled_time)
        if next_customer != "empty":
            des.push(StartService(self.scheduled_time, self.queue, self.cashier,
                                  customer=next_customer
                                 ))

    def __str__(self):
        return f"EndService event, scheduled at t = {self.scheduled_time}"
