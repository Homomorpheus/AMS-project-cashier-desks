"""
Statistical inference on the arrival of customers in the queue.
It is assumed that the distribution of the interarrival time
does not depend on the cash desk and its queue.
"""

import csv
import datetime

import numpy as np
import matplotlib.pyplot as plt
import scipy as sc


def read_call_center_data():

    data = []
    with open("../data/simulated_call_centre.csv", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)

    # transform data into python objects
    call_started = []
    call_answered = []
    call_ended = []
    for row in data[1:]:
        call_started.append(datetime.datetime.strptime(f"{row[1]} {row[3]}", "%Y-%m-%d %I:%M:%S %p"))
        call_answered.append(datetime.datetime.strptime(f"{row[1]} {row[4]}", "%Y-%m-%d %I:%M:%S %p"))
        call_ended.append(datetime.datetime.strptime(f"{row[1]} {row[5]}", "%Y-%m-%d %I:%M:%S %p"))

        row[0] = int(row[0])
        row[1] = datetime.date(*([int(entry) for entry in row[1].split("-")]))
        row[2] = int(row[2])
        row[3] = datetime.datetime.strptime(row[3], "%I:%M:%S %p").time()
        row[4] = datetime.datetime.strptime(row[4], "%I:%M:%S %p").time()
        row[5] = datetime.datetime.strptime(row[5], "%I:%M:%S %p").time()
        row[6] = int(row[6])
        row[7] = int(row[7])
        row[8] = bool(row[8])

    return call_started, call_answered, call_ended, data

def verify_first_come_first_serve(call_started, call_answered):
    sort_indices_start = np.argsort(call_started)
    sort_indices_answer = np.argsort(call_answered)

    print(np.sum(sort_indices_start != sort_indices_answer))


def start_time_inference(call_started, data):
    "inference on the time between new calls"

    daily_mean_interarrival = []
    current_day_arrival_times = []
    for i in range(len(call_started)):
        current_day_arrival_times.append(call_started[i])
        if i == len(call_started) - 1 or data[i + 2][1] != data[i + 1][1]: # date mismatch
            current_day_interarr_times = [(current_day_arrival_times[i + 1] - current_day_arrival_times[i]).total_seconds() for i in range(len(current_day_arrival_times) - 1)]
            daily_mean_interarrival.append(np.mean(current_day_interarr_times))
            current_day_arrival_times = []


    date_indices = list(range(len(daily_mean_interarrival)))

    # perform linear regression on daily_mean_interarrival
    F = np.vstack((np.ones(len(daily_mean_interarrival)), date_indices)).T

    coeffs = sc.linalg.solve(F.T @ F, F.T @ daily_mean_interarrival)

    print(f"result of linear regression: y = {coeffs[0]} + x * {coeffs[1]}")
    # result of linear regression: y = 253.90623376949912 + x * -0.4986322147377886

    fig, ax = plt.subplots()
    ax.plot(date_indices, daily_mean_interarrival, label="Mittlere Zeit zwischen Ankünften am Tag")
    ax.plot(date_indices, coeffs[0] + coeffs[1] * np.array(date_indices), label="Least-squares-fit")
    ax.set_xlabel("Arbeitstag")
    ax.legend()
    plt.show()
    fig.savefig("plots/arrival_data_yeartime.pdf")

    # rescale to day indices 1,...,365
    A = np.array([[1., 1.],
                [1., 365.],
                ])
    b = np.array([[coeffs[0], coeffs[0] + coeffs[1] * 260]]).T
    coeffs_365 = sc.linalg.solve(A, b)
    print(f"result of linear regression, scaled to days x=1,...,365: y = {coeffs_365[0][0]} + x * {coeffs_365[1][0]}")
    # result of linear regression, scaled to days x=1,...,365: y = 254.26239964 + x * -0.35616587

def processing_time_data_exploration_throughout_year(call_answered, call_ended):
    processing_times = []
    days = []
    current_day_processing_times = []
    for i in range(len(call_answered)):
        current_day_processing_times.append((call_ended[i] - call_answered[i]).total_seconds())
        if i == len(call_answered) - 1 or call_answered[i+1].date() != call_answered[i].date():
            processing_times.append(np.mean(current_day_processing_times))
            current_day_processing_times = []
            days.append(call_answered[i].date())
            print(f"day {call_answered[i].date()}")

    # reveals independence
    fig, ax = plt.subplots()
    ax.plot(days, processing_times)
    fig.show()
    fig.savefig("plots/processing_time_year.pdf")


def processing_time_data_exploration_throughout_day(call_answered, call_ended, data):
    processing_times = []
    day_times = []
    for i in range(len(call_answered)):
        processing_times.append((call_ended[i] - call_answered[i]).total_seconds())
        day_times.append(call_answered[i].time())

    sort_indices = np.argsort(day_times)
    processing_times = [processing_times[i] for i in sort_indices]
    day_times = [day_times[i] for i in sort_indices]

    # merge data so that matplotlib has less to plot
    per_minute_processing_times = []
    minute_times = []
    current_processing_times = []
    for i in range(len(day_times)):
        current_processing_times.append(processing_times[i])
        if i == len(day_times) - 1 or day_times[i].hour != day_times[i + 1].hour or day_times[i].minute != day_times[i + 1].minute:
            per_minute_processing_times.append(np.mean(current_processing_times))
            current_processing_times = []
            minute_times.append(day_times[i].hour*60 + day_times[i].minute)
            print(f"time {day_times[i]}")


    # reveals drop at end of day
    fig, ax = plt.subplots()
    ax.plot(minute_times, per_minute_processing_times)
    ax.set_xlabel("Minute des Tages")
    ax.set_ylabel("Mittlere Bearbeitungsdauer,\ninnerhalb einer Minute des Tages")
    plt.show()
    fig.savefig("plots/processing_time_day.pdf")
    print(np.max(minute_times)/ 24)

def interarrival_data_exploration_throughout_day(call_started):
    interarrival_times = []
    day_times = []
    for i in range(1, len(call_started)):
        interarrival_times.append((call_started[i] - call_started[i - 1]).total_seconds())
        day_times.append(call_started[i].time())

    sort_indices = np.argsort(day_times)
    interarrival_times = [interarrival_times[i] for i in sort_indices]
    day_times = [day_times[i] for i in sort_indices]

    # merge data so that matplotlib has less to plot
    per_minute_interarr_times = []
    minute_times = []
    current_interarr_times = []
    for i in range(len(day_times)):
        current_interarr_times.append(interarrival_times[i])
        if i == len(day_times) - 1 or day_times[i].hour != day_times[i + 1].hour or day_times[i].minute != day_times[i + 1].minute:
            per_minute_interarr_times.append(np.mean(current_interarr_times))
            current_interarr_times = []
            minute_times.append(day_times[i].hour*60 + day_times[i].minute)
            print(f"time {day_times[i]}")

    fig, ax = plt.subplots()
    print(per_minute_interarr_times)
    ax.semilogy(minute_times, per_minute_interarr_times)
    ax.set_xlabel("Minute des Tages")
    ax.set_ylabel("Mittlere Dauer zwischen Starts von Anrufen,\ninnerhalb einer Minute des Tages")
    fig.savefig("plots/arrival_data_daytime.pdf")
    plt.show()


if __name__=="__main__":
    call_started, call_answered, call_ended, data = read_call_center_data()
    interarrival_data_exploration_throughout_day(call_started)
    verify_first_come_first_serve(call_started, call_answered)
    start_time_inference(call_started, data)
    processing_time_data_exploration_throughout_year(call_answered, call_ended)
    processing_time_data_exploration_throughout_day(call_started, call_ended, data)
