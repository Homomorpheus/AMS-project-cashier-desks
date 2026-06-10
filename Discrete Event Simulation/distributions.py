# just to visualize densities of certain distributions

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gamma, chi2, expon

"""# Parameter
a = 1      # shape (k)
scale = 0.25  # scale (θ = 1/rate)

x = np.linspace(0, 15, 300)
plt.plot(x, gamma.pdf(x, a=a, scale=scale))
plt.title(f"Gamma-Verteilung (a={a}, scale={scale})")
plt.xlabel("x")
plt.ylabel("Dichte")
plt.grid(True)
plt.show()
mean = gamma.mean(a=a, scale=scale)
print(mean)
"""
# Parameter
df = 4  # mean = df

x = np.linspace(0, 1000, 500)
plt.plot(x, chi2.pdf(x, df=df), label='Chi2')
plt.plot(x, expon.pdf(x, scale=df), label='exp')
plt.plot(x, gamma.pdf(x, 20, scale=20), label='gamma')
plt.title(f"Chi squared distribution with {df} degrees of freedom")
plt.legend()
plt.show()
