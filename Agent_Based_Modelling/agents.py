"""ABM Agent classes for the queuing system"""

class Customer:
    "Customer agent class"

    def __init__(self, arrival_in_queue:float, properties:dict = dict()):
        self.arrival_in_queue = arrival_in_queue
        self.properties = properties
        self.waiting_time = None

    def __str__(self):
        return f"Customer arrived at t = {self.arrival_in_queue}, with properties {self.properties}"

class Cashier:
    "Cashier agent class"

    # whether to keep track of changes in how many cashiers are busy
    log = True

    def __init__(self, service_time, properties:dict = dict(), busy = False, time = 0.):
        self.service_time = service_time
        self.properties = properties
        self._busy = busy

        if self.log:
            self.timepoints = [time]
            self.busy_at_time = [self._busy]
            self.end_service_timepoints = []

    def get_busy(self):
        "is the cashier busy?"
        return self._busy

    def set_busy(self, boolean, time):
        """register whether the cashier is busy or not;
        takes timestamp for recording"""
        if boolean != self._busy and self.log:
            self.timepoints.append(time)
            self.busy_at_time.append(boolean)
            # genuine switches to False mean the end of a service,
            # which is also recorded:
            if boolean != True:
                self.end_service_timepoints.append(time)

        self._busy = boolean

    def throughput(self, start_time, end_time):
        """cashier throughput in time interval [start_time, end_time];
        the throughput shall be defined as the amount of served customers divided
        by the length of the time interval"""
        assert start_time < end_time
        assert all(self.end_service_timepoints[i] <= self.end_service_timepoints[i+1] for i in range(len(self.end_service_timepoints) - 1))

        # which service end time happened in the specified interval?
        restricted_service_end_times = [service_end_time for service_end_time in self.end_service_timepoints
                                        if start_time <= service_end_time <= end_time]
        # "velocity"
        customer_throughput = len(restricted_service_end_times) / (end_time - start_time)
        return customer_throughput

    def __str__(self):
        return f"Cashier which is {'not ' if not self._busy else '' }busy, with properties {self.properties}"

class Queue:
    """
    queue of customers, and the cashiers responsible for the queue

    Arguments:
        cashiers
        customers
        time -- simulation time at which queue object comes to life (default 0.)
        active -- whether the queue is occupied by its cashiers
        threshold_lo -- if there are less customers in the queue than threshold_lo,
                        deactivate it
        threshold_hi -- if there are more customers in the queue than threshold_hi,
                        try to activate another queue
        time_to_activate -- function to sample randomly from the time it takes for
                            the cashiers to come back to the queue
    """

    # whether to keep track of changes in the queue of customers
    log = True

    def __init__(self, cashiers: list[Cashier]=[], customers: list[Customer]=[],
                 time = 0., active=True, threshold_lo=float("-inf"),
                 threshold_hi=float("inf"), time_to_activate=lambda: 0):
        for cashier in cashiers:
            assert isinstance(cashier, Cashier)
        for customer in customers:
            assert isinstance(customer, Customer)

        self.cashiers = cashiers
        self.customers = customers
        self._active = active
        self.threshold_lo = threshold_lo
        self.threshold_hi = threshold_hi
        assert threshold_lo < threshold_hi
        self.time_to_activate = time_to_activate

        if self.log:
            self.timepoints_amounts_customers = [time]
            self.amounts_customers = [len(self.customers)]
            self.customer_waiting_times = []
            self.timepoints_activity_states = [time]
            self.activity_states = [active]

    def find_free_cashier(self):
        """find a cashier that is not busy;
        return 'busy' if such a cashier does not exist"""
        for cashier in self.cashiers:
            if not cashier.get_busy():
                return cashier
        else:
            return "busy"

    def add_customer(self, customer: Customer, time = None):
        "add customer to queue"
        assert isinstance(customer, Customer)
        # assert customer.arrival_in_queue == time
        self.customers.append(customer)

        # keep track of chain length
        if self.log:
            assert time is not None
            self.timepoints_amounts_customers.append(time)
            self.amounts_customers.append(self.amounts_customers[-1] + 1)

    def remove_customer(self, time = None, index = 0):
        """remove first customer from queue,
        returns 'empty' if there are no customers in the queue"""
        if len(self.customers) == 0:
            return "empty"
        else:
            # keep track of queue length
            if self.log:
                assert time is not None
                self.timepoints_amounts_customers.append(time)
                self.amounts_customers.append(self.amounts_customers[-1] - 1)

            # remove customer from queue
            return self.customers.pop(index)

    def get_active(self):
        return self._active

    def set_active(self, boolean, time):
        if self._active != boolean:
            self._active = boolean
            if self.log:
                self.timepoints_activity_states.append(time)
                self.activity_states.append(boolean)


    def __str__(self):
        string = "Queue, with cashiers:"

        for cashier in self.cashiers:
            string += "\n\t" + str(cashier)

        string += "and customers:"

        for customer in self.customers:
            string += "\n\t" + str(customer)

        string += "\n"

        return string
