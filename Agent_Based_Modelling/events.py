import heapq

import agents

class DES:
    """discrete event simulation class;
    manages the event list, runs everything"""
    def __init__(self, start_event):
        # event_list has to be accessed using heapq!
        self.event_list = [start_event]

    def push(self, event):
        "push to event list"
        heapq.heappush(self.event_list, event)

    def pop(self):
        "pop from event list, returns event"
        return heapq.heappop(self.event_list)

    def run(self, end_time):
        "run the DES"
        time = float("-inf")
        while True:
            current_event = self.pop()
            # if self.event_list[0].scheduled_time < current_event.scheduled_time:
            #     breakpoint()
            if current_event.scheduled_time < time:
                # breakpoint()
                raise RuntimeError("event list not sorted")
            time = current_event.scheduled_time
            if time > end_time:
                break
            current_event.execute(self)
            # print(list(map(lambda event: event.scheduled_time, filter(lambda event: isinstance(event, Arrival), self.event_list))))

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

    def shortest_active_queue_index(self):
        "returns the index of the shortest active queue in self.queues"

        # what if there are no active queues
        if not any((queue.get_active() for queue in self.queues)):
            return "no queue active"

        shortest_index = 0
        for i in range(len(self.queues)):
            if self.queues[i].get_active() and len(self.queues[i].customers) < len(self.queues[shortest_index].customers):
                shortest_index = i

        return shortest_index


    def activate_other_queue(self, des, chosen_queue):
        "activate another queue, for the case that there is already an active one"
        # find inactive queue
        for new_queue_index, new_queue in enumerate(self.queues):
            if not new_queue.get_active():
                # activate
                new_queue.set_active(True, time=self.scheduled_time)

                # if the queue has already emptied after last active period,
                # schedule arrival of cashier
                if len(new_queue.customers) == 0 and not any(cashier.get_busy() for cashier in new_queue.cashiers):
                    cashier_arrival_time = self.scheduled_time + new_queue.time_to_activate()
                    des.push(CashierArrival(cashier_arrival_time, self.queues, new_queue_index))

                # move customers from overly long queue to the reactivated queue
                # if the threshold of the other queue is lower, move fewer customers
                # if there are still customers in the other queue, move fewer customers
                # uses weighted average
                # the new queue shall have a portion of the customers in both queues, the portion is relative to the threshold_hi's:
                target_amount_customers_new_queue = int(new_queue.threshold_hi / (new_queue.threshold_hi + chosen_queue.threshold_hi) * (len(new_queue.customers) + len(chosen_queue.customers)))
                amount_customers_to_change_queue = target_amount_customers_new_queue - len(new_queue.customers)
                # add customers to new queue, keeping their order
                for i in range(amount_customers_to_change_queue):
                    # remove customer from old queue
                    customer = chosen_queue.remove_customer(time = self.scheduled_time, index = -amount_customers_to_change_queue + i)
                    assert customer != "empty"
                    # add customer to new queue
                    new_queue.add_customer(customer, time = self.scheduled_time)
                break

    def activate_first_queue(self, des):
        "activate queue, for the case that there is no active queue"
        new_queue = self.queues[0]
        new_queue_index = 0

        # activate
        new_queue.set_active(True, time=self.scheduled_time)

        # if the queue has already emptied after last active period,
        # schedule arrival of cashier
        if len(new_queue.customers) == 0 and not any(cashier.get_busy() for cashier in new_queue.cashiers):
            cashier_arrival_time = self.scheduled_time + new_queue.time_to_activate()
            des.push(CashierArrival(cashier_arrival_time, self.queues, new_queue_index))


    def execute(self, des):
        # add Customer to shortest queue
        # h, tm = divmod(self.scheduled_time, 60*60)
        # m, s = divmod(tm, 60)
        # print(h, m, s)
        """print('Customer arriving')
        print('Current queue lengths:')
        for queue in self.queues:
            print(str(queue))"""
        shortest_queue_index = self.shortest_active_queue_index()

        # handle the case that there is no active queue
        if shortest_queue_index == "no queue active":
            shortest_queue_index = 0
            self.activate_first_queue(des)

        chosen_queue = self.queues[shortest_queue_index]
        chosen_queue.add_customer(agents.Customer(arrival_in_queue=self.scheduled_time,
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
        next_free_cashier = chosen_queue.find_free_cashier()
        if next_free_cashier != "busy":
            # reserve cashier until StartService
            next_free_cashier.set_busy(True, self.scheduled_time)
            # schedule StartService
            des.push(StartService(self.scheduled_time, self.queues, next_free_cashier, shortest_queue_index))

        # if necessary, activate another queue
        if len(chosen_queue.customers) >= chosen_queue.threshold_hi:
            self.activate_other_queue(des, chosen_queue)


    def __str__(self):
        return f"Arrival event, scheduled at t = {self.scheduled_time}, with customer properties {self.customer_properties}"


class StartService(Event):

    def __init__(self, scheduled_time, queues, cashier, chosen_queue_index=0, customer=None):
        super().__init__(scheduled_time)
        self.queues = queues
        self.chosen_queue_index = chosen_queue_index
        self.chosen_queue = queues[chosen_queue_index]
        assert cashier in queues[chosen_queue_index].cashiers
        self.cashier = cashier
        self.customer = customer

    def execute(self, des):
        # start service
        self.cashier.set_busy(True, self.scheduled_time)
        if self.customer is None:
            self.customer = self.chosen_queue.remove_customer(time = self.scheduled_time)
            if self.customer == "empty":
                breakpoint()
            assert self.customer != "empty"

        # store waiting time
        self.customer.waiting_time = self.scheduled_time - self.customer.arrival_in_queue
        self.customer.start_service_time = self.scheduled_time
        if self.chosen_queue.log:
            self.chosen_queue.customer_waiting_times.append(self.customer.waiting_time)

        # schedule end of service
        service_duration = self.cashier.service_time(self.customer)
        end_service_time = self.scheduled_time + service_duration
        if end_service_time > 18*60*60:
            breakpoint()
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
                                  chosen_queue_index=self.chosen_queue_index,
                                  customer=next_customer
                                  ))

        if len(self.queues[self.chosen_queue_index].customers) <= self.queues[self.chosen_queue_index].threshold_lo:
            self.queues[self.chosen_queue_index].set_active(False, time=self.scheduled_time)

    def __str__(self):
        return f"EndService event in Queue {self.chosen_queue_index}, scheduled at t = {self.scheduled_time}"


class CashierArrival(Event):
    """
    event for the arrival of the cashier at the cash desk (after inactivity)

    without this event, an Arrival event could trigger a StartService before the
        cashier has arrived
    """

    def __init__(self, scheduled_time, queues, queue_index):
        self.scheduled_time = scheduled_time
        self.queues = queues
        # index of queue on which to simulate the arrival of a cashier
        self.queue_index = queue_index
        # queue to that index:
        self.queue = queues[queue_index]

        # remove cashiers from queue so that they do not start to work
        # before their arrival
        self.cashiers = self.queue.cashiers
        self.queue.cashiers = []

    def execute(self, des):
        # add cashiers back in
        # (they were removed in __init__ so that an Arrival event cannot
        # trigger a premature StartService)
        self.queue.cashiers = self.cashiers

        # start service if there are customers waiting
        if len(self.queue.customers) > 0:
            des.push(StartService(self.scheduled_time,
                        self.queues, self.queue.cashiers[0], self.queue_index))

    def __str__(self):
        return f"CashierArrival event in Queue {self.chosen_queue_index}, scheduled at t = {self.scheduled_time}"
