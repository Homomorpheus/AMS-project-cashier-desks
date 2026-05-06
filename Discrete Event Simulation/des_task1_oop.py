# Implement a classic GGk queue, where arrival and service times can follow an arbitrary positive distribution.
# Test different distributions and parameters, and plot time-dependent statistics (e.g. mean,
# confidence intervals, etc.) for the queue length and server utilisation.
import heapq
import numpy as np


class Event:
    event_list = []

    def __init__(self, scheduled_time=0.0):
        self.scheduled_time = scheduled_time

    def __lt__(self, other):
        return self.scheduled_time < other.scheduled_time

    def execute(self):
        raise NotImplementedError("define execute in subclass")


class Start(Event):

    def __init__(self, scheduled_time=0.0, interarr_time=1):
        super().__init__(scheduled_time)
        self.interarr_time = interarr_time

    def execute(self):
        heapq.heappush(self.__class__.event_list, Arrival(self.scheduled_time+self.interarr_time, self.interarr_time))


class Arrival(Event):

    def __init__(self, scheduled_time, interarr_time, Q, S):
        super().__init__(scheduled_time)
        self.interarr_time = interarr_time
        self.Q = Q
        self.S = S

    def execute(self):
        heapq.heappush(self.__class__.event_list, Arrival(self.scheduled_time+self.interarr_time, self.interarr_time, self.Q, self.S))
        if self.S > 0:
            heapq.heappush(self.__class__.event_list, StartService(self.scheduled_time, ))


class StartService(Event):

    def __init__(self, scheduled_time, service_time, Q, S):
        super().__init__(scheduled_time)
        self.service_time = service_time
        self.Q = Q
        self.S = S

    def execute(self):
        self.S -= 1
        self.Q -= 1
        heapq.heappush(self.__class__.event_list, EndService(...))