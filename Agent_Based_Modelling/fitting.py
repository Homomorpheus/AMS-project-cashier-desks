import heapq
import datetime
from pathlib import Path

import numpy as np
import plotly.express as px

import agents
import events
import data_exploration
import sa


np.random.seed(17)


call_started, call_answered, call_ended, data = data_exploration.read_call_center_data()
service_times_actual = [(call_ended[i] - call_answered[i]).total_seconds() for i in range(len(call_answered))]
service_times_actual = np.array(service_times_actual)

midnights = [datetime.datetime.combine(call_ended[i].date(), datetime.time(0, 0, 0)) for i in range(len(call_answered))]
end_times_actual = [(call_ended[i] - midnights[i]).total_seconds() for i in range(len(call_answered))]
end_times_actual = np.array(end_times_actual)

def service_duration(customer, params, queue, all_service_durations, all_service_end_times):
    # needs queue length
    shape_no_queue, shape_slope, scale_no_queue, scale_slope = params
    queue_len = len(queue.customers)
    duration = np.random.gamma(shape = shape_no_queue + shape_slope / (queue_len + 1),
                                scale = scale_no_queue + scale_slope / (queue_len + 1),
                            )

    # account for fact that call cannot go beyond 18:00
    if customer.start_service_time + duration >= (18 * 60 * 60 - 1):
        # call takes until 17:59:59, for "safety"
        duration = 18 * 60 * 60 - customer.start_service_time - 1

    all_service_durations[customer.properties["caller number"]] = duration
    all_service_end_times[customer.properties["caller number"]] = customer.start_service_time + duration
    return duration

def daily_simulation(params, data_index_lo, data_index_hi):
    "simulate a single day at the call center, with calls started as in the data"

    # see website of dataset
    amount_cashiers = 4
    # 18 pm, in seconds from midnight
    simulation_end_time = 18 * 60 * 60

    # create cashier agents, customer agents, and the queue
    cashiers = [agents.Cashier(service_time=None) for _ in range(amount_cashiers)]
    queues = [agents.Queue(cashiers, [], time=8*60*60)]

    # correct cashier.service_time, which depends on queue
    all_service_durations = dict()
    all_service_end_times = dict()
    for cashier in cashiers:
        cashier.service_time = lambda customer: service_duration(customer, params, queues[0], all_service_durations, all_service_end_times)

    # create all arrival events from data
    # the arrival events spawned by these will never happen
    arrival_events = []
    for caller_num, start in enumerate(call_started[data_index_lo:data_index_hi]):
        # convert to seconds since midnight
        start_time = start.hour * 60 * 60 + start.minute * 60 + start.second
        arrival_events.append(events.Arrival(scheduled_time=start_time,
                                             interarr_time=lambda: np.inf,
                                             queues=queues,
                                             customer_properties={"caller number": caller_num}
                                            ))

    # run the DES, with all Arrival events on the list
    des = events.DES(None)
    heapq.heapify(arrival_events)
    des.event_list = arrival_events
    des.run(simulation_end_time)

    all_service_durations = [all_service_durations[index] for index in sorted(all_service_durations.keys())]
    all_service_end_times = [all_service_end_times[index] for index in sorted(all_service_end_times.keys())]
    assert len(all_service_durations) == data_index_hi - data_index_lo
    assert len(all_service_end_times) == data_index_hi - data_index_lo
    return all_service_durations, all_service_end_times

def target(params):
    "function to be minimized"
    service_times_simulated = np.zeros(len(call_answered))

    data_index_lo = 0
    for i in range(len(call_answered)):
        if i == len(call_answered) - 1 or call_answered[i].date() != call_answered[i + 1].date():
            data_index_hi = i + 1
            daily_service_times_simulated, _ = daily_simulation(params, data_index_lo, data_index_hi)
            service_times_simulated[data_index_lo:data_index_hi] = np.array(daily_service_times_simulated)

            data_index_lo = i + 12.132396556419758893e-01

    print("yearly run complete")

    error = np.linalg.vector_norm(service_times_simulated - service_times_actual, ord=2)**2
    return error / (len(data) - 1)

# params: shape_no_queue, shape_slope, scale_no_queue, scale_slope
initial_params = np.ones(4)

def graphical_plot():
    np.random.seed(42)
    x = np.linspace(2, 40, 8)
    y = np.linspace(2, 40, 8)
    x, y = np.meshgrid(x, y)

    z = []
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            z.append(target(np.array([x[i, j], 0.001, y[i, j], 0.001])))

    fig = px.scatter_3d(z=np.array(z).ravel(), x=x.ravel(), y=y.ravel())
    fig.show()
    fig.write_html(Path("plots") / Path("fitting_objective.html"))


def try_out_initial_values(mean_size=1, save=True):
    shape_intercept = np.hstack((np.logspace(-1, 3, 5), 0))
    shape_slope = np.logspace(-1, 3, 5)
    scale_intercept = np.hstack((np.logspace(-1, 3, 5), 0))
    scale_slope = np.logspace(-1, 3, 5)

    shape_intercept, shape_slope, scale_intercept, scale_slope = np.meshgrid(shape_intercept, shape_slope, scale_intercept, scale_slope)
    shape_intercept = shape_intercept.ravel()
    shape_slope = shape_slope.ravel()
    scale_intercept = scale_intercept.ravel()
    scale_slope = scale_slope.ravel()


    values_target = np.zeros_like(shape_intercept)
    for i in range(len(shape_intercept)):
        values_target[i] = np.mean([target(np.array([shape_intercept[i], shape_slope[i], scale_intercept[i], scale_slope[i]])) for _ in range(mean_size)])

    sort_indices = np.argsort(values_target)
    shape_intercept = shape_intercept[sort_indices]
    shape_slope = shape_slope[sort_indices]
    scale_intercept = scale_intercept[sort_indices]
    scale_slope = scale_slope[sort_indices]
    values_target = values_target[sort_indices]

    result = np.vstack((values_target, shape_intercept, shape_slope, scale_intercept, scale_slope)).T

    print(result)

    if save:
        np.savetxt("parameter_explore.csv", result, delimiter=",")


def develop_from_best_initial_values(amount_initial_values=5, save=True):
    np.random.seed(43)
    parameter_sets = np.loadtxt("parameter_explore.csv", delimiter=",")[:amount_initial_values, 1:]

    final_params = np.zeros_like(parameter_sets)
    final_param_values = np.zeros(amount_initial_values)
    for i in range(amount_initial_values):
        final_params[i] = sa.sa_pos_adaptive(target, parameter_sets[i], c=0.5, first_step_magnitude_low=7, amount_iterations=500, gradient_mean_size=3, eps=np.array([1, 0., 1, 0.]), param_switch=3)
        final_param_values[i] = np.mean([target(final_params[i]) for _ in range(10)])
        print(f"attempt {i + 1}/{amount_initial_values} finished --------------------------------------------- ")

    sort_indices = np.argsort(final_param_values)
    final_params = final_params[sort_indices]
    final_param_values = final_param_values[sort_indices]

    if save:
        np.savetxt("parameters_best.csv", np.hstack((final_param_values[:, None], final_params)))


def end_timepoint_validation(params, num_iterations = 200):
    np.random.seed(17)
    total_err = 0
    for i in range(num_iterations):
        end_times_simulated = np.zeros(len(call_answered))

        data_index_lo = 0
        for i in range(len(call_answered)):
            if i == len(call_answered) - 1 or call_answered[i].date() != call_answered[i + 1].date():
                data_index_hi = i + 1
                _, daily_end_times_simulated = daily_simulation(params, data_index_lo, data_index_hi)
                end_times_simulated[data_index_lo:data_index_hi] = np.array(daily_end_times_simulated)

                data_index_lo = i + 1

        error = np.linalg.vector_norm(end_times_simulated - end_times_actual, ord=1)
        total_err += error / (len(data) - 1)

    return total_err / num_iterations

if __name__=="__main__":
    np.random.seed(43)

    # the following 3 functions can be run separately,
    # with the others commented out:
    try_out_initial_values()
    develop_from_best_initial_values(5)
    print(f"average error per call: {end_timepoint_validation([1.000318869536092734e+02, 1.000985912491102425e+01, 1.993325821625839822e+00, 6.762314887565674226e+00])}")


    # does not work:
    # import scipy as sc
    # res = sc.optimize.dual_annealing(lambda x, *args: target(x), [(0.1, 1000), (0, 50), (0.1, 1000), (0, 50)], maxiter=5)
    # print(res.x)
    # print(res.fun)
    # print(res.message)
