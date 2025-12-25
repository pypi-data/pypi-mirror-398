"""
Optimization Benchmark Functions

This module implements classical benchmark functions for testing optimization algorithms.
All implementations are original Python code based on mathematical formulations from
academic literature.

Mathematical formulations are based on:

References:
-----------
[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C for
    Unconstrained Global Optimization. University of the Philippines Diliman.

[2] Surjanovic, S. & Bingham, D. (2013). Virtual Library of Simulation Experiments:
    Test Functions and Datasets. Simon Fraser University.
    Retrieved from: https://www.sfu.ca/~ssurjano/

[3] Jamil, M., & Yang, X. S. (2013). A literature survey of benchmark functions for
    global optimization problems. International Journal of Mathematical Modelling
    and Numerical Optimisation, 4(2), 150-194.

[4] Moré, J. J., Garbow, B. S., & Hillstrom, K. E. (1981). Testing Unconstrained
    Optimization Software. ACM Transactions on Mathematical Software, 7(1), 17-41.

Notes:
------
- Mathematical formulas are not subject to copyright as they represent established
  mathematical knowledge from academic literature.
- All Python implementations in this module are original code written for this package.
- Each function includes domain constraints and global minimum information in its docstring.

License: MIT
"""

import numpy as np


def ackley(x: np.ndarray) -> float:
    """
    Ackley function.
    Domain: |x_i| ≤ 30.
    Dimension: n (arbitrary).
    Global minimum: f(0) = 0 at x = 0:contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    sum_sq = np.sum(x**2)
    sum_cos = np.sum(np.cos(2 * np.pi * x))
    return -20.0 * np.exp(-0.2 * np.sqrt(sum_sq / n)) - np.exp(sum_cos / n) + 20 + np.e


def beale(x: np.ndarray) -> float:
    """
    Beale function.
    Domain: -4.5 ≤ x_i ≤ 4.5.
    Dimension: 2.
    Global minimum: f(3,0.5) = 0 at x = (3, 0.5):contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    term1 = 1.5 - x0 + x0 * x1
    term2 = 2.25 - x0 + x0 * x1**2
    term3 = 2.625 - x0 + x0 * x1**3
    return term1**2 + term2**2 + term3**2


def bohachevsky1(x: np.ndarray) -> float:
    """
    Bohachevsky function #1.
    Domain: |x_i| ≤ 50.
    Dimension: 2.
    Global minimum: f(0,0) = 0 at x = (0, 0):contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    return x0**2 + 2 * x1**2 - 0.3 * np.cos(3 * np.pi * x0) - 0.4 * np.cos(4 * np.pi * x1) + 0.7


def bohachevsky2(x: np.ndarray) -> float:
    """
    Bohachevsky function #2.
    Domain: |x_i| ≤ 50.
    Dimension: 2.
    Global minimum: f(0,0) = 0 at x = (0, 0):contentReference[oaicite:6]{index=6}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    return x0**2 + 2 * x1**2 - 0.3 * np.cos(3 * np.pi * x0) * np.cos(4 * np.pi * x1) + 0.3


def booth(x: np.ndarray) -> float:
    """
    Booth function.
    Domain: -10 ≤ x_i ≤ 10.
    Dimension: 2.
    Global minimum: f(1,3) = 0 at x = (1, 3):contentReference[oaicite:7]{index=7}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    return (x0 + 2 * x1 - 7) ** 2 + (2 * x0 + x1 - 5) ** 2


def box_betts(x: np.ndarray) -> float:
    """
    Box-Betts exponential quadratic sum function.
    Domain: x0 ∈ [0.9,1.2], x1 ∈ [9,11.2], x2 ∈ [0.9,1.2].
    Dimension: 3.
    Global minimum: f(1,10,1) = 0 at x = (1, 10, 1):contentReference[oaicite:8]{index=8}:contentReference[oaicite:9]{index=9}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1, x2 = x
    total = 0.0
    for i in range(1, 11):
        g = (
            np.exp(-0.1 * i * x0)
            - np.exp(-0.1 * i * x1)
            - ((np.exp(-0.1 * i) - np.exp(-1.0 * i)) * x2)
        )
        total += g**2
    return total


def branin(x: np.ndarray) -> float:
    """
    Branin function.
    Domain: x0 ∈ [-5, 10], x1 ∈ [0, 15].
    Dimension: 2.
    Global minima: f ≈ 0.3979 at x ≈ (-3.142,12.275), (3.142,2.275), (9.425,2.425):contentReference[oaicite:10]{index=10}:contentReference[oaicite:11]{index=11}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    a = 1.0
    b = 5.1 / (4 * np.pi**2)
    c = 5 / np.pi
    return (a * x1 - b * x0**2 + c * x0 - 6) ** 2 + 10 * (1 - 1 / (8 * np.pi)) * np.cos(x0) + 10


def branin2(x: np.ndarray) -> float:
    """
    Modified Branin (Test function 2).
    Domain: |x_i| ≤ 10.
    Dimension: 2.
    Global minimum: f(0.402357,0.287408) = 0 at x ≈ (0.402357, 0.287408):contentReference[oaicite:12]{index=12}.
    """
    x = np.asarray(x, dtype=float)
    return (1.0 - 2.0 * x[1] + np.sin(4.0 * np.pi * x[1]) / 20.0 - x[0]) ** 2 + (
        x[1] - np.sin(2.0 * np.pi * x[0]) / 2.0
    ) ** 2


def camel3(x: np.ndarray) -> float:
    """
    Three-hump camel function.
    Domain: |x_i| ≤ 5.
    Dimension: 2.
    Global minimum: f(0,0) = 0 at x = (0, 0):contentReference[oaicite:13]{index=13}:contentReference[oaicite:14]{index=14}.
    """
    x = np.asarray(x, dtype=float)
    x0 = x[0]
    term = 2 * x0**2 - 1.05 * x0**4 + x0**6 / 6.0 + x0 * x[1] ** 3
    return term


def camel6(x: np.ndarray) -> float:
    """
    Six-hump camel function.
    Domain: |x_i| < 5.
    Dimension: 2.
    Global minimum: f ≈ -1.0316 at x ≈ (0.08983,-0.7126) and (-0.08983,0.7126):contentReference[oaicite:15]{index=15}:contentReference[oaicite:16]{index=16}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    return (4 - 2.1 * x0**2 + (x0**4) / 3) * x0**2 + x0 * x1 + (-4 + 4 * x1**2) * x1**2


def chichinadze(x: np.ndarray) -> float:
    """
    Chichinadze function.
    Domain: x0 ∈ [-30, 30], x1 ∈ [-10, 10].
    Dimension: 2.
    Global minimum: f ≈ -43.3159 at x ≈ (5.90133, 0.5):contentReference[oaicite:17]{index=17}:contentReference[oaicite:18]{index=18}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    return (
        x0**2
        - 12 * x0
        + 11
        + 10 * np.cos((np.pi / 2) * x0)
        + 8 * np.sin(5 * np.pi * x0)
        - np.exp(-((x1 - 0.5) ** 2) / 5.0)
    )


def colville(x: np.ndarray) -> float:
    """
    Colville function.
    Domain: -10 ≤ x_i ≤ 10.
    Dimension: 4.
    Global minimum: f(1,1,1,1) = 0 at x = (1, 1, 1, 1):contentReference[oaicite:19]{index=19}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1, x2, x3 = x
    return (
        100 * (x0 - x2**2) ** 2
        + (1 - x0) ** 2
        + 90 * (x3 - x2**2) ** 2
        + (1 - x2) ** 2
        + 10.1 * ((x1 - 1) ** 2 + (x3 - 1) ** 2)
        + 19.8 * (x1 - 1) * (x3 - 1)
    )


def corana(x: np.ndarray) -> float:
    """
    Corana function.
    Domain: |x_i| ≤ 100.
    Dimension: 4.
    Global minimum: f = 0 at x = (0,0,0,0):contentReference[oaicite:20]{index=20}.
    """
    x = np.asarray(x, dtype=float)
    d = np.array([1.0, 1000.0, 10.0, 100.0])
    total = 0.0
    for i in range(4):
        zi = np.floor(abs(x[i] / 0.2) + 0.49999) * np.sign(x[i]) * 0.2
        if abs(x[i] - zi) < 0.05:
            term = 0.15 * (zi - 0.05 * np.sign(zi)) ** 2 * d[i]
        else:
            term = (x[i] - zi) ** 2 * d[i]
        total += term
    return total


def easom(x: np.ndarray) -> float:
    """
    Easom function.
    Domain: |x_i| ≤ 100.
    Dimension: 2.
    Global minimum: f(π,π) = -1 at x = (π, π):contentReference[oaicite:21]{index=21}.
    """
    x = np.asarray(x, dtype=float)
    return -np.cos(x[0]) * np.cos(x[1]) * np.exp(-((x[0] - np.pi) ** 2 + (x[1] - np.pi) ** 2))


def eggholder(x: np.ndarray) -> float:
    """
    Egg holder function.
    Domain: |x_i| < 512.
    Dimension: n (usually 2).
    """
    x = np.asarray(x, dtype=float)
    total = 0.0
    for i in range(x.size - 1):
        total += -(x[i + 1] + 47) * np.sin(np.sqrt(abs(x[i + 1] + x[i] / 2 + 47))) - x[i] * np.sin(
            np.sqrt(abs(x[i] - (x[i + 1] + 47)))
        )
    return total


def exp2(x: np.ndarray) -> float:
    """
    Exp2 function.
    Domain: 0 ≤ x_i ≤ 20.
    Dimension: 2.
    Global minimum: f(1,10) = 0 at x = (1, 10):contentReference[oaicite:22]{index=22}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    total = 0.0
    for i in range(10):
        total += (
            np.exp(-i * x0 / 10) - 5 * np.exp(-i * x1 / 10) - np.exp(-i / 10) + 5 * np.exp(-i)
        ) ** 2
    return total


def fraudenstein_roth(x: np.ndarray) -> float:
    """
    Freudenstein-Roth function.
    Domain: (typically -10 ≤ x_i ≤ 10).
    Dimension: 2.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    f1 = -13 + x0 + ((5 - x1) * x1 - 2) * x1
    f2 = -29 + x0 + ((x1 + 1) * x1 - 14) * x1
    return f1**2 + f2**2


def gear(x: np.ndarray) -> float:
    """
    Gear train function.
    Domain: 12 ≤ x0,x1,x2,x3 ≤ 60.
    Dimension: 4.
    Global minimum: ≈2.7e-12 at permutations of (16, 19, 43, 49):contentReference[oaicite:23]{index=23}.
    """
    x = np.asarray(x, dtype=float)
    t = 1.0 / 6.931 - np.floor(x[0]) * np.floor(x[1]) / (np.floor(x[2]) * np.floor(x[3]))
    return t**2


def goldstein_price(x: np.ndarray) -> float:
    """
    Goldstein-Price function.
    Domain: |x_i| ≤ 2.
    Dimension: 2.
    Global minimum: f(0,-1) = 3 at x = (0, -1):contentReference[oaicite:24]{index=24}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    term1 = 1 + (x0 + x1 + 1) ** 2 * (19 - 14 * x0 + 3 * x0**2 - 14 * x1 + 6 * x0 * x1 + 3 * x1**2)
    term2 = 30 + (2 * x0 - 3 * x1) ** 2 * (
        18 - 32 * x0 + 12 * x0**2 + 48 * x1 - 36 * x0 * x1 + 27 * x1**2
    )
    return term1 * term2


def griewank(x: np.ndarray) -> float:
    """
    Griewank function.
    Domain: |x_i| ≤ 600.
    Dimension: n.
    Global minimum: f(0) = 0 at x = 0:contentReference[oaicite:25]{index=25}.
    """
    x = np.asarray(x, dtype=float)
    sum_sq = np.sum(x**2) / 4000.0
    prod_cos = np.prod(np.cos(x / np.sqrt(np.arange(1, x.size + 1))))
    return sum_sq - prod_cos + 1


def himmelblau(x: np.ndarray) -> float:
    """
    Himmelblau function.
    Domain: -6 ≤ x_i ≤ 6.
    Dimension: 2.
    Global minimum: f(3,2) = 0 at x = (3, 2):contentReference[oaicite:26]{index=26}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1 = x
    return (x0**2 + x1 - 11) ** 2 + (x0 + x1**2 - 7) ** 2


def hyperellipsoid(x: np.ndarray) -> float:
    """
    Hyperellipsoid (Weighted sphere) function.
    Domain: |x_i| ≤ 10 (often).
    Dimension: n.
    Global minimum: f(0) = 0 at x = 0:contentReference[oaicite:27]{index=27}.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    return np.sum((np.arange(1, n + 1) * x**2))


def kowalik(x: np.ndarray) -> float:
    """
    Kowalik function.
    Domain: |x_i| < 5.
    Dimension: 4.
    Global minimum: ≈0.000307 at x ≈ (0.1928,0.1908,0.1231,0.1358):contentReference[oaicite:28]{index=28}.
    """
    x = np.asarray(x, dtype=float)
    a = np.array(
        [0.1957, 0.1947, 0.1735, 0.1600, 0.0844, 0.0627, 0.0456, 0.0342, 0.0323, 0.0235, 0.0246]
    )
    b = np.array([4.0, 2.0, 1.0, 0.5, 0.25, 1 / 6, 1 / 8, 0.1, 1 / 12, 1 / 14, 1 / 16])
    sum_val = 0.0
    for i in range(11):
        numerator = x[0] * (b[i] ** 2 + b[i] * x[1])
        denominator = b[i] ** 2 + b[i] * x[2] + x[3]
        yi = numerator / denominator
        sum_val += (a[i] - yi) ** 2
    return sum_val


def holzman1(x: np.ndarray) -> float:
    """
    Holzman function #1.
    Domain: 0.1 ≤ x0 ≤ 100, 0 ≤ x1 ≤ 25.6, 0 ≤ x2 ≤ 5.
    Dimension: 3.
    Global minimum: f(50,25,1.5) = 0 at x = (50, 25, 1.5):contentReference[oaicite:29]{index=29}.
    """
    x = np.asarray(x, dtype=float)
    x0, x1, x2 = x
    total = 0.0
    for i in range(100):
        ui = 25 + pow(-50.0 * np.log(0.01 * (i + 1)), 2.0 / 3.0)
        total += -0.1 * (i + 1) + np.exp((ui - x1) ** x2 / x0)
    return total


def holzman2(x: np.ndarray) -> float:
    """
    Holzman function #2.
    Domain: |x_i| ≤ 10.
    Dimension: n.
    Global minimum: f(0) = 0 at x = 0:contentReference[oaicite:30]{index=30}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum((np.arange(x.size, dtype=float) * x**4))


def hosaki(x: np.ndarray) -> float:
    """
    Hosaki function.
    Domain: x0 ≥ 0, x1 ≥ 0 (often in [0,5]×[0,6]).
    Dimension: 2.
    Global minimum: ≈ -2.3458 at x = (4, 2):contentReference[oaicite:31]{index=31}:contentReference[oaicite:32]{index=32}.
    """
    x = np.asarray(x, dtype=float)
    return (
        (1 - 8 * x[0] + 7 * x[0] ** 2 - (7 / 3) * x[0] ** 3 + 0.25 * x[0] ** 4)
        * x[1] ** 2
        * np.exp(-x[1])
    )


def katsuura(x: np.ndarray) -> float:
    """
    Katsuura function.
    Domain: |x_i| ≤ 1000.
    Dimension: n.
    Global minimum: f(0) = 1 at x = 0:contentReference[oaicite:33]{index=33}.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    prod = 1.0
    for i in range(n):
        sum_k = 0.0
        for k in range(1, 33):
            sum_k += abs(2**k * x[i] - np.round(2**k * x[i])) / (2**k)
        prod *= (1 + (i + 1) * sum_k) ** (10.0 / (n**1.2))
    return prod


def langerman(x: np.ndarray) -> float:
    """
    Langerman function.
    Domain: 0 ≤ x_i ≤ 10.
    Dimension: n.
    Global minimum: f ≈ -1.4:contentReference[oaicite:34]{index=34}.
    """
    x = np.asarray(x, dtype=float)
    # Coefficients c and points A defined for m=5 in MVF.
    afox = np.array(
        [
            [9.681, 0.667, 4.783, 9.095, 3.517, 9.325, 6.544, 0.211, 5.122, 2.020],
            [9.400, 2.041, 3.788, 7.931, 2.882, 2.672, 3.568, 1.284, 7.033, 7.374],
            [8.025, 9.152, 5.114, 7.621, 4.564, 4.711, 2.996, 6.126, 0.734, 4.982],
            [2.196, 0.415, 5.649, 6.979, 9.510, 9.166, 6.304, 6.054, 9.377, 1.426],
            [8.074, 8.777, 3.467, 1.863, 6.708, 6.349, 4.534, 0.276, 7.633, 1.567],
        ]
    )
    c = np.array([0.806, 0.517, 0.100, 0.908, 0.965])
    total = 0.0
    for i in range(5):
        dist = np.sum((x - afox[i]) ** 2)
        total -= c[i] * np.exp(-dist / np.pi) * np.cos(np.pi * dist)
    return total


def lennard_jones(x: np.ndarray) -> float:
    """
    Lennard-Jones potential function.
    Domain: (coordinates of n/3 atoms).
    Dimension: n = 3N.
    """
    x = np.asarray(x, dtype=float)
    N = x.size // 3
    energy = 0.0
    for i in range(N - 1):
        for j in range(i + 1, N):
            dist2 = np.sum((x[3 * i : 3 * i + 3] - x[3 * j : 3 * j + 3]) ** 2)
            inv6 = 1.0 / dist2**3
            energy += inv6 * (inv6 - 2.0)
    return energy


def leon(x: np.ndarray) -> float:
    """
    Leon function.
    Domain: |x_i| ≤ 10.
    Dimension: 2.
    Global minimum: f(1,1) = 0 at x = (1, 1):contentReference[oaicite:35]{index=35}.
    """
    x = np.asarray(x, dtype=float)
    return 100.0 * (x[1] - x[0] ** 3) ** 2 + (1.0 - x[0]) ** 2


def levy(x: np.ndarray) -> float:
    """
    Levy function (n-dimensional).
    Domain: |x_i| ≤ 10.
    Dimension: n.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    w = 1 + (x - 1) / 4.0
    term1 = np.sin(np.pi * w[0]) ** 2
    term3 = (w[-1] - 1) ** 2 * (1 + np.sin(2 * np.pi * w[-1]) ** 2)
    term2 = 0.0
    for i in range(n - 1):
        wi = w[i]
        term2 += (wi - 1) ** 2 * (1 + 10 * np.sin(np.pi * w[i + 1]) ** 2)
    return term1 + term2 + term3


def matyas(x: np.ndarray) -> float:
    """
    Matyas function.
    Domain: |x_i| ≤ 10.
    Dimension: 2.
    Global minimum: f(0,0) = 0 at x = (0, 0):contentReference[oaicite:36]{index=36}.
    """
    x = np.asarray(x, dtype=float)
    return 0.26 * (x[0] ** 2 + x[1] ** 2) - 0.48 * x[0] * x[1]


def maxmod(x: np.ndarray) -> float:
    """
    Maxmod function.
    Domain: |x_i| ≤ 10.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:37]{index=37}.
    """
    x = np.asarray(x, dtype=float)
    return np.max(np.abs(x))


def mccormick(x: np.ndarray) -> float:
    """
    McCormick function.
    Domain: -1.5 ≤ x0 ≤ 4, -3 ≤ x1 ≤ 4.
    Dimension: 2.
    Global minimum: f(-0.54719,-1.54719) ≈ -1.9133:contentReference[oaicite:38]{index=38}.
    """
    x = np.asarray(x, dtype=float)
    return np.sin(x[0] + x[1]) + (x[0] - x[1]) ** 2 - 1.5 * x[0] + 2.5 * x[1] + 1.0


def michalewicz(x: np.ndarray) -> float:
    """
    Michalewicz function.
    Domain: 0 ≤ x_i ≤ π.
    Dimension: n.
    """
    x = np.asarray(x, dtype=float)
    i = np.arange(1, x.size + 1)
    return -np.sum(np.sin(x) * (np.sin(i * x**2 / np.pi)) ** 20)


def multimod(x: np.ndarray) -> float:
    """
    Multimodal function.
    Domain: |x_i| ≤ 10.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:39]{index=39}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum(np.abs(x)) * np.prod(np.abs(x))


def rastrigin(x: np.ndarray) -> float:
    """
    Rastrigin function.
    Domain: |x_i| ≤ 5.12.
    Dimension: n.
    Global minimum: f = 0 at x = 0.
    """
    x = np.asarray(x, dtype=float)
    return np.sum(x**2 - 10 * np.cos(2 * np.pi * x) + 10)


def rastrigin2(x: np.ndarray) -> float:
    """
    A variant of the Rastrigin function (2D).
    Domain: |x_i| ≤ 5.12.
    Dimension: 2.
    Global minimum: f = 0 at x = 0.
    """
    x = np.asarray(x, dtype=float)
    return x[0] ** 2 + x[1] ** 2 - np.cos(12 * x[0]) - np.cos(18 * x[1])


def rosenbrock(x: np.ndarray) -> float:
    """
    Rosenbrock function (classic).
    Domain: |x_i| ≤ 10.
    Dimension: n.
    Global minimum: f = 0 at x = 1 (all xi = 1).
    """
    x = np.asarray(x, dtype=float)
    return np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)


def rosenbrock_ext1(x: np.ndarray) -> float:
    """
    Extended Rosenbrock function #1.
    Domain: |x_i| ≤ 10.
    Dimension: n (n even).
    Global minimum: f = 0 at x = 1 (all xi = 1).
    """
    x = np.asarray(x, dtype=float)
    total = 0.0
    for i in range(0, x.size, 2):
        total += 100.0 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
    return total


def rosenbrock_ext2(x: np.ndarray) -> float:
    """
    Extended Rosenbrock function #2.
    Domain: |x_i| ≤ 10.
    Dimension: n.
    Global minimum: f = 0 at x = 1 (all xi = 1).
    """
    x = np.asarray(x, dtype=float)
    return np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)


def schaffer1(x: np.ndarray) -> float:
    """
    Schaffer function #1.
    Domain: |x_i| ≤ 100.
    Dimension: 2.
    Global minimum: f(0,0) = 0 at x = (0, 0):contentReference[oaicite:44]{index=44}.
    """
    x = np.asarray(x, dtype=float)
    s = x[0] ** 2 + x[1] ** 2
    return 0.5 + (np.sin(np.sqrt(s)) ** 2 - 0.5) / (1 + 0.001 * s) ** 2


def schaffer2(x: np.ndarray) -> float:
    """
    Schaffer function #2.
    Domain: |x_i| ≤ 100.
    Dimension: 2.
    Global minimum: f(0,0) = 0 at x = (0, 0):contentReference[oaicite:45]{index=45}.
    """
    x = np.asarray(x, dtype=float)
    s = x[0] ** 2 + x[1] ** 2
    return (s**0.25) * ((50 * s**0.1) + 1)


def schwefel1_2(x: np.ndarray) -> float:
    """
    Schwefel function 1.2.
    Domain: |x_i| < 10.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:46]{index=46}.
    """
    x = np.asarray(x, dtype=float)
    total = 0.0
    for i in range(x.size):
        total += np.sum(x[: i + 1]) ** 2
    return total


def schwefel2_21(x: np.ndarray) -> float:
    """
    Schwefel function 2.21.
    Domain: |x_i| < 10.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:47]{index=47}.
    """
    x = np.asarray(x, dtype=float)
    return np.max(np.abs(x))


def schwefel2_22(x: np.ndarray) -> float:
    """
    Schwefel function 2.22.
    Domain: |x_i| < 10.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:48]{index=48}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum(np.abs(x)) + np.prod(np.abs(x))


def schwefel2_26(x: np.ndarray) -> float:
    """
    Schwefel function 2.26.
    Domain: |x_i| < 500.
    Dimension: n.
    Global minimum: ≈ -12569.5 at x ≈ 420.9687 (for n=3):contentReference[oaicite:49]{index=49}.
    """
    x = np.asarray(x, dtype=float)
    return -np.sum(x * np.sin(np.sqrt(np.abs(x))))


def schwefel3_2(x: np.ndarray) -> float:
    """
    Schwefel (variant) function 3.2.
    Domain: |x_i| < 10.
    Dimension: n.
    Global minimum: f = 0 at x = (1,1,...,1):contentReference[oaicite:50]{index=50}.
    """
    x = np.asarray(x, dtype=float)
    return (x[0] - x[1]) ** 2 + (1 - x[1]) ** 2


def sphere(x: np.ndarray) -> float:
    """
    Sphere (Harmonic) function.
    Domain: |x_i| ≤ 100.
    Dimension: n.
    Global minimum: f(0) = 0 at x = 0:contentReference[oaicite:51]{index=51}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum(x**2)


def sphere2(x: np.ndarray) -> float:
    """
    Sphere function (cumulative sum variant).
    Domain: |x_i| ≤ 100.
    Dimension: n.
    Global minimum: f(0) = 0 at x = 0:contentReference[oaicite:52]{index=52}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum(np.cumsum(x) ** 2)


def step(x: np.ndarray) -> float:
    """
    Step function.
    Domain: |x_i| ≤ 100.
    Dimension: n.
    Global minimum: f = 0 at x_i = 0.5:contentReference[oaicite:53]{index=53}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum((np.floor(x) + 0.5) ** 2)


def step2(x: np.ndarray) -> float:
    """
    Step function #2.
    Domain: |x_i| ≤ 5.12.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:54]{index=54}.
    """
    x = np.asarray(x, dtype=float)
    return 6 * x.size + np.sum(np.floor(x))


def stretched_v(x: np.ndarray) -> float:
    """
    Stretched V function.
    Domain: |x_i| ≤ 10.
    Dimension: n.
    """
    x = np.asarray(x, dtype=float)
    total = 0.0
    for i in range(x.size - 1):
        t = x[i] ** 2 + x[i + 1] ** 2
        total += (t**0.25) * (np.sin(50 * t**0.1) ** 2 + 1)
    return total


def sum_squares(x: np.ndarray) -> float:
    """
    Sum of Squares function.
    Domain: -10 ≤ x_i ≤ 10.
    Dimension: n.
    Global minimum: f = 0 at x = 0:contentReference[oaicite:55]{index=55}.
    """
    x = np.asarray(x, dtype=float)
    return np.sum((np.arange(1, x.size + 1) * x**2))


def trecanni(x: np.ndarray) -> float:
    """
    Trecanni function.
    Domain: -5 ≤ x_i ≤ 5.
    Dimension: 2.
    Global minima: f(0,0) = 0 and f(-2,0) = 0:contentReference[oaicite:56]{index=56}.
    """
    x = np.asarray(x, dtype=float)
    return x[0] ** 4 + 4 * x[0] ** 3 + 4 * x[0] ** 2 + x[1] ** 2


def trefethen4(x: np.ndarray) -> float:
    """
    Trefethen function #4.
    Domain: x0 ∈ (-6.5,6.5), x1 ∈ (-4.5,4.5).
    Dimension: 2.
    Global minimum: ≈ -3.30686865 at x ≈ (-0.0244031, 0.2106124):contentReference[oaicite:57]{index=57}.
    """
    x = np.asarray(x, dtype=float)
    return (
        np.exp(np.sin(50.0 * x[0]))
        + np.sin(60.0 * np.exp(x[1]))
        + np.sin(70.0 * np.sin(x[0]))
        + np.sin(np.sin(80.0 * x[1]))
        - np.sin(10.0 * (x[0] + x[1]))
        + 0.25 * (x[0] ** 2 + x[1] ** 2)
    )


def watson(x: np.ndarray) -> float:
    """
    Watson function.
    Domain: |x_i| ≤ 10.
    Dimension: 6.
    """
    x = np.asarray(x, dtype=float)
    a = np.arange(0, 29) / 29.0
    f = 0.0
    for i in range(1, 30):
        sum1 = 0.0
        sum2 = 0.0
        for j in range(6):
            sum1 += (j - 1) * a[j] * x[j + 1]
            sum2 += a[j] * x[j + 1]
        f += (sum1 - sum2) ** 2
    return f + x[0] ** 2


def xor(x: np.ndarray) -> float:
    """
    Xor function.
    Domain: (No specific domain given).
    Dimension: 9.
    """
    x = np.asarray(x, dtype=float)

    def sigma(z):
        return 1 / (1 + np.exp(-z))

    num = (
        1 / (1 + np.exp(-x[6] / (1 + np.exp(-x[0] - x[1] - x[4]))))
        - 1 / (1 + np.exp(-x[7] / (1 + np.exp(-x[2] - x[3] - x[5]))))
        - x[8]
    )
    return (1 / (1 + np.exp(-num))) ** 2


def zettl(x: np.ndarray) -> float:
    """
    Zettl function.
    Domain: |x_i| ≤ 10.
    Dimension: 2.
    Global minimum: f ≈ -0.00379 at x ≈ (-0.02990, 0):contentReference[oaicite:58]{index=58}.
    """
    x = np.asarray(x, dtype=float)
    return (x[0] ** 2 + x[1] ** 2 - 2 * x[0]) ** 2 + 0.25 * x[0]


def zimmerman(x: np.ndarray) -> float:
    """
    Zimmerman function.
    Domain: 0 ≤ x_i ≤ 100.
    Dimension: 2.
    """
    x = np.asarray(x, dtype=float)
    zh1 = 9 - x[0] - x[1]
    zh2 = (x[0] - 3) ** 2 + (x[1] - 2) ** 2 - 16
    zh3 = x[0] * x[1] - 14
    zp = lambda t: 100 * (1 + t)
    f_vals = [
        zh1,
        zp(zh2) * np.sign(zh2),
        zp(zh3) * np.sign(zh3),
        zp(-x[0]) * np.sign(x[0]),
        zp(-x[1]) * np.sign(x[1]),
    ]
    return np.max(f_vals)
