

def rosenbrock(x, a=1.0, b=100.0):
    # Optimal value: (a, a^2)
    return (a - x[0])**2 + b * (x[1] - x[0]**2)**2


