import numpy as np


def sa(objective_fctn, start, c, first_step_magnitude_low, amount_iterations, gradient_mean_size, param_switch=None):
    """
    stochastic approximation; minimization algorithm;
    this implementation optimizes only among component-wise positive input values
    """

    if param_switch is None:
        param_switch = amount_iterations / 3

    alpha = 0.602
    gamma = 0.101
    A = amount_iterations / 10
    a = None # chosen later
    a_k = lambda k: a / ((k + A) ** alpha)
    c_k = lambda k: c / ((k) ** gamma)
    assert c > 0


    def approx_gradient(k, current_position):

        approx = np.zeros_like(current_position)
        for i in range(len(approx)):
            e_i = np.zeros_like(current_position)
            e_i[i] = 1
            eval_plus = current_position + c_k(k) * e_i
            eval_minus = current_position - c_k(k) * e_i
            approx[i] = (objective_fctn(eval_plus) - objective_fctn(eval_minus)) / (2 * c_k(k))
        return approx

    current_position = np.asarray(start, dtype=np.float64).copy()

    for k in range(1, amount_iterations + 1):
        last_position = current_position.copy()
        approx_gradient_mean = np.mean([approx_gradient(k, current_position) for _ in range(gradient_mean_size)], axis=0)

        if k == 1:
            a = first_step_magnitude_low / np.min(np.abs(approx_gradient_mean / ((1 + A) ** alpha)))

        current_position = current_position - a_k(k) * approx_gradient_mean

        print(f"position: {last_position} with gradient: {approx_gradient_mean}")
        print(f"current position: {current_position}")

        if np.allclose(last_position, current_position):
            print(f"automatically terminated after {k} steps")
            break

        if k >= param_switch:
            alpha = 1
            gamma = 1 / 6

    return current_position


def sa_pos(objective_fctn, start, c, first_step_magnitude_low, amount_iterations, gradient_mean_size, eps, param_switch=None):
    """
    stochastic approximation; minimization algorithm;
    this implementation optimizes only among values that are >= eps (component-wise)
    """

    if param_switch is None:
        param_switch = amount_iterations / 3

    alpha = 0.602
    gamma = 0.101
    A = amount_iterations / 10
    a = None # chosen later
    a_k = lambda k: a / ((k + A) ** alpha)
    c_k = lambda k: c / ((k) ** gamma)
    assert c > 0

    def truncate(vec):
        return vec * (vec > 0) + eps * (vec <= 0)

    def approx_gradient(k, current_position):
        "approximate gradient of the objective_fctn, using central difference quotients"
        approx = np.zeros_like(current_position)
        for i in range(len(approx)):
            e_i = np.zeros_like(current_position)
            e_i[i] = 1
            eval_plus = truncate(current_position + c_k(k) * e_i)
            eval_minus = truncate(current_position - c_k(k) * e_i)
            approx[i] = (objective_fctn(eval_plus) - objective_fctn(eval_minus)) / np.linalg.norm(eval_plus - eval_minus)
        return approx

    current_position = np.asarray(start, dtype=np.float64).copy()

    for k in range(1, amount_iterations + 1):
        last_position = current_position.copy()
        #
        approx_gradient_mean = np.mean([approx_gradient(k, current_position) for _ in range(gradient_mean_size)], axis=0)
        if k == 1:
            a = first_step_magnitude_low / np.min(np.abs(approx_gradient_mean / ((1 + A) ** alpha)))
        current_position = current_position - a_k(k) * approx_gradient_mean
        current_position = truncate(current_position)

        print(f"position: {current_position} with gradient: {approx_gradient_mean}")

        if np.allclose(last_position, current_position):
            print(f"automatically terminated after {k} steps")
            break

        if k >= param_switch:
            alpha = 1
            gamma = 1 / 6

    return current_position


def sa_pos_adaptive(objective_fctn, start, c, first_step_magnitude_low, amount_iterations, gradient_mean_size, eps, param_switch=None):
    """
    stochastic approximation; minimization algorithm;
    this implementation optimizes only among values that are >= eps (component-wise)
    """

    if param_switch is None:
        param_switch = amount_iterations / 3

    alpha = 0.602
    gamma = 0.101
    A = amount_iterations / 10
    a = None # chosen later
    a_k = lambda k: a / ((k + A) ** alpha)
    c_k = lambda k: c / ((k) ** gamma)
    assert c > 0

    def truncate(vec):
        return vec * (vec > 0) + eps * (vec <= 0)

    def approx_gradient(k, current_position):
        "approximate gradient of the objective_fctn, using central difference quotients"
        approx = np.zeros_like(current_position)
        for i in range(len(approx)):
            e_i = np.zeros_like(current_position)
            e_i[i] = 1
            eval_plus = truncate(current_position + c_k(k) * e_i)
            eval_minus = truncate(current_position - c_k(k) * e_i)
            approx[i] = (objective_fctn(eval_plus) - objective_fctn(eval_minus)) / np.linalg.norm(eval_plus - eval_minus)
        return approx

    current_position = np.asarray(start, dtype=np.float64).copy()
    last_value_sample = [objective_fctn(current_position) for _ in range(2)]

    for k in range(1, amount_iterations + 1):
        last_position = current_position.copy()

        approx_gradient_mean = np.mean([approx_gradient(k, current_position) for _ in range(gradient_mean_size)], axis=0)
        if k == 1:
            a = first_step_magnitude_low / np.min(np.abs(approx_gradient_mean / ((1 + A) ** alpha)))
        current_position = current_position - a_k(k) * approx_gradient_mean
        current_position = truncate(current_position)

        # adaptive part, bisection
        while True:
            value_sample = [objective_fctn(current_position) for _ in range(2)]
            if np.mean(value_sample) > np.mean(last_value_sample):
                print(f"step back from {current_position} to {(current_position + last_position) / 2} as {np.mean(value_sample)} > {np.mean(last_value_sample)}")
                current_position = (current_position + last_position) / 2
            else:
                last_value_sample = value_sample
                print(f"accept {current_position} with value {np.mean(value_sample)}")
                break

        print(f"position: {current_position} with gradient: {approx_gradient_mean}")

        if np.allclose(last_position, current_position):
            print(f"automatically terminated after {k} steps")
            break

        if k >= param_switch:
            alpha = 1
            gamma = 1 / 6

    return current_position

if __name__=="__main__":
    np.random.seed(17)
    res = sa_pos(lambda x: np.linalg.norm(x + np.array([-5, 1]))**2 + np.random.normal(0, 0.1), np.array([3, 4]), 0.1, 0.4, 500, 2, 40)
    print(res)
