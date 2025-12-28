import math

# ==========================================
# SECTION 1: ADVANCED ALGEBRA & NUMBER THEORY
# ==========================================

def quadratic_roots(a, b, c):
    """
    Returns roots for ax^2 + bx + c = 0.
    Handles complex roots (e.g., 2 + 3j).
    """
    if a == 0: raise ValueError("Coefficient 'a' cannot be 0 in quadratic.")
    delta = b**2 - 4*a*c
    sqrt_delta = math.isqrt(delta) if delta >= 0 else math.sqrt(abs(delta)) * 1j
    
    r1 = (-b + sqrt_delta) / (2*a)
    r2 = (-b - sqrt_delta) / (2*a)
    return (r1, r2)

def prime_factors(n):
    """Returns a list of prime factors of n."""
    factors = []
    d = 2
    temp = n
    while d * d <= temp:
        while temp % d == 0:
            factors.append(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.append(temp)
    return factors

def sigmoid(x):
    """Sigmoid activation function (used in AI/ML)."""
    return 1 / (1 + math.exp(-x))

# ==========================================
# SECTION 2: LINEAR ALGEBRA (MATRICES)
# ==========================================
# Matrices are represented as list of lists: [[1, 2], [3, 4]]

def matrix_shape(matrix):
    """Returns (rows, cols) of a matrix."""
    return len(matrix), len(matrix[0])

def matrix_add(A, B):
    """Adds two matrices of same dimensions."""
    rows, cols = matrix_shape(A)
    if (rows, cols) != matrix_shape(B):
        raise ValueError("Matrices must have same dimensions to add.")
    return [[A[i][j] + B[i][j] for j in range(cols)] for i in range(rows)]

def matrix_multiply(A, B):
    """Multiplies Matrix A (mxn) by Matrix B (nxp)."""
    rows_A, cols_A = matrix_shape(A)
    rows_B, cols_B = matrix_shape(B)
    
    if cols_A != rows_B:
        raise ValueError(f"Cannot multiply {rows_A}x{cols_A} and {rows_B}x{cols_B}")
    
    # Create result matrix filled with zeros
    result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]
    
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]
    return result

def matrix_transpose(matrix):
    """Swaps rows and columns."""
    rows, cols = matrix_shape(matrix)
    return [[matrix[i][j] for i in range(rows)] for j in range(cols)]

def determinant_2x2(matrix):
    """Calculates determinant of a 2x2 matrix."""
    if matrix_shape(matrix) != (2, 2): raise ValueError("Not a 2x2 matrix")
    return (matrix[0][0] * matrix[1][1]) - (matrix[0][1] * matrix[1][0])

# ==========================================
# SECTION 3: VECTORS (PHYSICS & ENGINEERING)
# ==========================================
# Vectors are lists: [x, y, z]

def vector_dot(v1, v2):
    """Dot Product: a . b = ax*bx + ay*by + az*bz"""
    if len(v1) != len(v2): raise ValueError("Vectors must be same length")
    return sum(x * y for x, y in zip(v1, v2))

def vector_cross_3d(a, b):
    """Cross Product of two 3D vectors."""
    if len(a) != 3 or len(b) != 3: raise ValueError("Must be 3D vectors")
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    ]

def vector_magnitude(v):
    """Returns the length (magnitude) of a vector."""
    return math.sqrt(sum(x**2 for x in v))

def vector_angle(v1, v2):
    """Returns angle between two vectors in degrees."""
    dot = vector_dot(v1, v2)
    mag = vector_magnitude(v1) * vector_magnitude(v2)
    if mag == 0: return 0
    # Clamp value to avoid domain errors due to float precision
    cos_theta = max(min(dot / mag, 1), -1) 
    return math.degrees(math.acos(cos_theta))

# ==========================================
# SECTION 4: NUMERICAL CALCULUS
# ==========================================

def derivative(func, x, h=1e-5):
    """
    Approximates derivative of function f at point x.
    Uses central difference formula: (f(x+h) - f(x-h)) / 2h
    """
    return (func(x + h) - func(x - h)) / (2 * h)

def definite_integral(func, a, b, n=1000):
    """
    Approximates integral of f from a to b using Trapezoidal Rule.
    n = number of trapezoids (precision).
    """
    h = (b - a) / n
    total = 0.5 * (func(a) + func(b))
    for i in range(1, n):
        total += func(a + i * h)
    return total * h

# ==========================================
# SECTION 5: ADVANCED GEOMETRY & TRIG
# ==========================================

def law_of_cosines_side(a, b, angle_gamma_degrees):
    """Calculates side c given sides a, b and angle gamma between them."""
    rad = math.radians(angle_gamma_degrees)
    return math.sqrt(a**2 + b**2 - 2*a*b*math.cos(rad))

def spherical_coordinates(x, y, z):
    """Converts (x, y, z) to spherical (radius, theta, phi)."""
    r = math.sqrt(x**2 + y**2 + z**2)
    theta = math.degrees(math.acos(z / r)) if r != 0 else 0
    phi = math.degrees(math.atan2(y, x))
    return (r, theta, phi)

# ==========================================
# SECTION 6: NUMERICAL ANALYSIS (ROOT FINDING)
# ==========================================

def newton_raphson(func, x0, tol=1e-6, max_iter=100):
    """
    Finds root of f(x) = 0 using Newton-Raphson method.
    x0: Initial guess
    tol: Tolerance (how precise the result should be)
    """
    x = x0
    for _ in range(max_iter):
        y = func(x)
        y_prime = derivative(func, x) # Uses your existing derivative function
        
        if abs(y_prime) < 1e-10: 
            break # Avoid division by zero
            
        x_new = x - (y / y_prime)
        
        if abs(x_new - x) < tol:
            return x_new
        x = x_new
    return x # Return best guess if max_iter reached

def bisection_method(func, a, b, tol=1e-6):
    """
    Finds root between [a, b] where func(a) and func(b) have opposite signs.
    Reliable but slower than Newton-Raphson.
    """
    if func(a) * func(b) >= 0:
        raise ValueError("Function must have opposite signs at a and b")
        
    mid = a
    while (b - a) / 2 > tol:
        mid = (a + b) / 2
        if func(mid) == 0:
            return mid
        elif func(a) * func(mid) < 0:
            b = mid
        else:
            a = mid
    return mid


# ==========================================
# SECTION 7: ADVANCED MATRIX OPERATIONS
# ==========================================

def identity_matrix(n):
    """Generates an n x n Identity matrix (1s on diagonal, 0s elsewhere)."""
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]

def matrix_trace(matrix):
    """Sum of diagonal elements."""
    rows, cols = matrix_shape(matrix)
    if rows != cols:
        raise ValueError("Matrix must be square to calculate trace")
    return sum(matrix[i][i] for i in range(rows))

def determinant_3x3(m):
    """Calculates determinant of a 3x3 matrix using rule of expansion."""
    if matrix_shape(m) != (3, 3):
        raise ValueError("Matrix must be 3x3")
    
    # a(ei − fh) − b(di − fg) + c(dh − eg)
    det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
           m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
           m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    return det

# ==========================================
# SECTION 8: PROBABILITY DISTRIBUTIONS
# ==========================================

def combinations(n, k):
    """nCr calculation."""
    return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))

def binomial_probability(n, k, p):
    """
    Probability of exactly k successes in n trials.
    p = probability of success in one trial.
    """
    return combinations(n, k) * (p**k) * ((1 - p)**(n - k))

def poisson_probability(lam, k):
    """
    Probability of k events occurring in a fixed interval.
    lam (lambda) = average rate of occurrence.
    """
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def entropy(probabilities):
    """
    Calculates Shannon Entropy (Information Theory).
    probabilities: list of probs summing to 1.
    """
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


# ==========================================
# SECTION 9: POLYNOMIALS & SIGNALS
# ==========================================

def evaluate_polynomial(coeffs, x):
    """
    Evaluates a polynomial at x using Horner's Method (Efficient).
    coeffs: List of coefficients [an, ..., a1, a0] for an*x^n + ...
    Example: [2, -3, 1] represents 2x^2 - 3x + 1
    """
    result = 0
    for c in coeffs:
        result = result * x + c
    return result

def moving_average(data, window_size):
    """
    Smooths a data list (Signal Processing).
    Returns a new list with the moving averages.
    """
    if window_size > len(data):
        raise ValueError("Window size larger than data length")
        
    averages = []
    for i in range(len(data) - window_size + 1):
        window = data[i : i + window_size]
        avg = sum(window) / window_size
        averages.append(avg)
    return averages


# ==========================================
# SECTION 10: STATISTICS & DATA ANALYSIS
# ==========================================

def mean(data):
    """Calculates the arithmetic mean."""
    if not data: return 0
    return sum(data) / len(data)

def median(data):
    """Finds the middle value."""
    if not data: return 0
    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2
    
    if n % 2 == 1:
        return sorted_data[mid]
    else:
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2

def variance(data, population=True):
    """
    Calculates Variance (spread of data).
    population=True for Population Variance (div by N).
    population=False for Sample Variance (div by N-1).
    """
    if len(data) < 2: return 0
    mu = mean(data)
    sq_diffs = sum((x - mu) ** 2 for x in data)
    n = len(data)
    return sq_diffs / n if population else sq_diffs / (n - 1)

def std_deviation(data, population=True):
    """Standard Deviation (square root of variance)."""
    return math.sqrt(variance(data, population))

def covariance(data_x, data_y):
    """
    Measures how two variables change together.
    Returns positive value if they increase together.
    """
    if len(data_x) != len(data_y):
        raise ValueError("Datasets must have equal length")
    n = len(data_x)
    if n < 2: return 0
    
    mu_x = mean(data_x)
    mu_y = mean(data_y)
    
    numerator = sum((data_x[i] - mu_x) * (data_y[i] - mu_y) for i in range(n))
    return numerator / (n - 1) # Sample covariance

def correlation_coefficient(data_x, data_y):
    """
    Pearson Correlation (r).
    Returns value between -1 and 1.
    1 = Perfect positive correlation.
    -1 = Perfect negative correlation.
    """
    cov = covariance(data_x, data_y)
    std_x = std_deviation(data_x, population=False)
    std_y = std_deviation(data_y, population=False)
    
    if std_x == 0 or std_y == 0: return 0
    return cov / (std_x * std_y)





# ==========================================
# SECTION 11: SEQUENCES & SERIES
# ==========================================

def arithmetic_sequence_nth(a, d, n):
    """
    Finds n-th term of arithmetic sequence.
    a = first term, d = difference, n = term number
    """
    return a + (n - 1) * d

def arithmetic_series_sum(a, d, n):
    """Sum of first n terms of arithmetic sequence."""
    return (n / 2) * (2 * a + (n - 1) * d)

def geometric_sequence_nth(a, r, n):
    """
    Finds n-th term of geometric sequence.
    a = first term, r = ratio, n = term number
    """
    return a * (r ** (n - 1))

def geometric_series_sum(a, r, n):
    """Sum of first n terms of geometric sequence."""
    if r == 1: return a * n
    return a * (1 - r**n) / (1 - r)

def infinite_geometric_sum(a, r):
    """Sum of infinite geometric series (only if -1 < r < 1)."""
    if abs(r) >= 1:
        raise ValueError("Series does not converge (abs(r) must be < 1)")
    return a / (1 - r)