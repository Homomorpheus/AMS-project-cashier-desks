import numpy as np


def project_to_positive(a, b, eps):
    "move a towards b until all components of a are >= eps"
    a = a.copy()
    b = b.copy()

    assert np.all(b > 0)
    # assert np.all(b >= eps)

    if np.all(a > eps):
        return a

    i = np.argmin(eps + a)
    assert (eps[i] - b[i]) / (a[i] - b[i]) < 1
    assert (eps[i] - b[i]) / (a[i] - b[i]) >= 0
    a_projected =  b + (eps[i] - b[i]) / (a[i] - b[i]) * (a - b)
    # breakpoint()
    # assert np.all(a_projected >= eps)
    return a_projected

def spsa_pos(objective_fctn, start, c, first_step_magnitude_low, amount_iterations, gradient_mean_size, eps, param_switch=None):
    """
    simultaneous perturbation stochastic approximation; minimization algorithm;
    this implementation optimizes only among component-wise positive input values
    """
    # eps is the threshold so that position values are not 0
    # assert np.all(eps > 0)
    #
    if param_switch is None:
        param_switch = amount_iterations / 3

    alpha = 0.602
    gamma = 0.101
    A = amount_iterations / 10
    a = None # chosen later
    a_k = lambda k: a / ((k + A) ** alpha)
    c_k = lambda k: c / ((k) ** gamma)
    assert c > 0

    # old_positions = [start]

    # def approx_gradient_nonneg(k, current_position):
    #     # perturbation is component-wise bernoulli +-1
    #     perturbation = np.asarray(np.random.binomial(n = 1, p = 0.5, size=len(start)), dtype=np.float64) * 2 - 1
    #     # print(current_position + c_k(k) * perturbation)
    #     #
    #     # assure that no evaluation of objective_fctn is made for negative input
    #     mask_plus_eval = current_position + c_k(k) * perturbation <= 0
    #     mask_minus_eval = current_position - c_k(k) * perturbation <= 0
    #     c_k_plus = - (current_position - eps) / perturbation
    #     c_k_minus = (current_position - eps) / perturbation
    #     dist_truncated = (np.logical_not(mask_plus_eval) * c_k(k) + mask_plus_eval * c_k_plus) + (np.logical_not(mask_minus_eval) * c_k(k) + mask_minus_eval * c_k_minus)
    #     truncated_plus_eval = np.logical_not(mask_plus_eval) * (current_position + c_k(k) * perturbation) + mask_plus_eval * (current_position + c_k_plus * perturbation)
    #     truncated_minus_eval = np.logical_not(mask_minus_eval) * (current_position - c_k(k) * perturbation) + mask_minus_eval * (current_position - c_k_minus * perturbation)
    #     # print(truncated_plus_eval - truncated_minus_eval)
    #     # print(np.logical_not(mask_plus_eval) * (current_position + c_k(k) * perturbation) + mask_plus_eval * (current_position + c_k_plus * perturbation) - (np.logical_not(mask_minus_eval) * (current_position - c_k(k) * perturbation) + mask_minus_eval * (current_position - c_k_minus * perturbation)))
    #     # print(current_position, c_k(k), truncated_plus_eval, truncated_minus_eval)
    #     # breakpoint()
    #     # assert np.isclose(np.linalg.det([truncated_plus_eval - current_position, truncated_minus_eval - current_position]), 0)
    #     assert np.allclose(dist_truncated, (truncated_plus_eval - truncated_minus_eval) / perturbation)

    #     approx = (objective_fctn(truncated_plus_eval) - objective_fctn(truncated_minus_eval)) / (dist_truncated * perturbation)
    #     return approx
    #
    def truncate(vec):
        return vec * (vec > 0) + eps * (vec <= 0)

    def approx_gradient(k, current_position):
        # perturbation is component-wise bernoulli +-1
        perturbation = np.asarray(np.random.binomial(n = 1, p = 0.5, size=len(start)), dtype=np.float64) * 2 - 1
        print(perturbation)
        eval_plus = truncate(current_position + c_k(k) * perturbation)
        eval_minus = truncate(current_position - c_k(k) * perturbation)
        delta_eval = eval_plus - eval_minus
        approx = (objective_fctn(eval_plus) - objective_fctn(eval_minus)) / (delta_eval * perturbation)
        return approx

    current_position = np.asarray(start, dtype=np.float64).copy()

    for k in range(1, amount_iterations + 1):
        last_position = current_position.copy()
        approx_gradient_mean = np.mean([approx_gradient(k, current_position) for _ in range(gradient_mean_size)], axis=0)
        if k == 1:
            # breakpoint()
            a = first_step_magnitude_low / np.min(np.abs(approx_gradient_mean / ((1 + A) ** alpha)))
        current_position = current_position - a_k(k) * approx_gradient_mean # project_to_positive(current_position - a_k(k) * approx_gradient_mean, current_position, eps=2*eps)
        current_position = truncate(current_position)

        print(f"position: {current_position} with gradient: {approx_gradient_mean}")

        if np.allclose(last_position, current_position):
            print(f"automatically terminated after {k} steps")
            break

        # old_positions.append(current_position)
        # if k == amount_iterations:
        #     ## print(np.stack(old_positions))
        #     plt.plot(list(range(amount_iterations + 1)), old_positions)
        #     plt.show()
        #     print(start)

        if k >= param_switch:
            alpha = 1
            gamma = 1 / 6

    return current_position




def spsa(objective_fctn, start, c, first_step_magnitude_low, amount_iterations, gradient_mean_size, param_switch=None):
    """
    simultaneous perturbation stochastic approximation; minimization algorithm;
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
        # perturbation is component-wise bernoulli +-1
        perturbation = np.asarray(np.random.binomial(n = 1, p = 0.5, size=len(start)), dtype=np.float64) * 2 - 1

        eval_plus = current_position + c_k(k) * perturbation
        eval_minus = current_position - c_k(k) * perturbation
        delta_eval = eval_plus - eval_minus
        approx = (objective_fctn(eval_plus) - objective_fctn(eval_minus)) / (delta_eval * perturbation)
        breakpoint()
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



if __name__=="__main__":
    np.random.seed(17)
    res = spsa(lambda x: np.linalg.norm(x - 1)**2 + np.random.normal(0, 0.1), np.array([3, 4]), 0.1, 0.4, 50, 2, 40)
    print(res)
