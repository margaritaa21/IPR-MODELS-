import numpy as np
x_vals = np.linspace(0.0, 0.14, 100)
n_vals = 98.395 * (x_vals**2) - 13.587 * x_vals + 1.35
v_vals = 6e6 * (x_vals**6) - 3e6 * (x_vals**5) + 485849 * (x_vals**4) - 41934 * (x_vals**3) + 1804.3 * (x_vals**2) - 35.015 * x_vals + 0.3439
print("Min V:", np.min(v_vals))
print("Max V:", np.max(v_vals))
print("Min N:", np.min(n_vals))
print("Max N:", np.max(n_vals))
