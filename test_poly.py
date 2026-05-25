import numpy as np
import matplotlib.pyplot as plt

x = np.array([0.00, 0.005, 0.01, 0.015, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14])
y = np.array([0.38, 0.28, 0.18, 0.14, 0.15, 0.11, 0.12, 0.16, 0.14, 0.25, 0.45])

z = np.polyfit(x, y, 6)
p = np.poly1d(z)

x_lin = np.linspace(0, 0.14, 100)
y_lin = p(x_lin)

print("Coefficients:", z)
print("Min Y:", np.min(y_lin))

# Original eq
y_orig = 6e6 * (x_lin**6) - 3e6 * (x_lin**5) + 485849 * (x_lin**4) - 41934 * (x_lin**3) + 1804.3 * (x_lin**2) - 35.015 * x_lin + 0.3439
print("Min orig:", np.min(y_orig))
