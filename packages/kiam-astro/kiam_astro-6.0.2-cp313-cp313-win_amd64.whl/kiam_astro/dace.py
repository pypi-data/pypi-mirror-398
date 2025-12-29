"""
This Python module is a part of the KIAM Astrodynamics Toolbox developed in
Keldysh Institute of Applied Mathematics (KIAM), Moscow, Russia.

The provides routines for dealing with DACE state vectors.

The toolbox is licensed under the MIT License.

Install:

    `pip install kiam_astro`

Upgrade:

    `pip install kiam_astro --upgrade`

Requirements:

    windows, macos (gfortran needed), ubuntu (gfortran needed)
    python>=3.9,<=3.13
    numpy>=2.0,<3.0
    jdcal
    networkx
    scipy
    plotly
    kaleido==0.1.0.post1
    pillow

"""

import daceypy as da
import numpy as np
from kiam_astro import kiam
from typing import Callable, Iterable

# Служебные функции
def create(x0: Iterable, order: int) -> da.array:
    """
    Initializes a DACE state vector around a given point.

    Initializes the Differential Algebra environment with the specified order
    and number of variables, then creates a vector of DA variables centered at `x0`.
    Each component consists of the constant part from `x0` and an identity part
    (independent variable).

    Parameters:
    -----------
    `x0` : np.ndarray
        Nominal state vector (center point of the expansion).
        The length of this array determines the number of DA variables.

    `order` : int
        Order of the Taylor expansion (computation order).

    Returns:
    --------
    `da_state` : da.array
        Initialized DACE vector where the i-th element represents
        the variable initialized as x0[i] + delta_i.

    Examples:
    ---------
    ```
    import numpy as np

    from kiam_astro import dace

    x_nominal = np.array([1.0, 2.5, 0.0])

    da_vars = dace.create(x_nominal, order=3)

    # Returns a da.array object with 3 variables and order 3, with constant parts [1.0, 2.5, 0.0].

    print(da_vars)
    ```
    """

    da.DA.init(order, len(x0))

    # array.identity() создает вектор DA-переменных [DA(1), DA(2), ..., DA(n)]
    da_state = da.array.identity(len(x0))

    # Добавляем константные части из numpy-массива
    for i in range(len(x0)):
        da_state[i] += x0[i]

    return da_state
def dace2numpy(da_array: da.array) -> np.ndarray:
    """
    Extracts the constant part of a DACE array.

    Converts a Differential Algebra array into a standard NumPy array by taking
    only the zero-order terms (constant parts) of the expansion, effectively
    discarding the higher-order derivatives.

    Parameters:
    -----------
    `da_array` : da.array
        Input DACE array (vector of DA objects).

    Returns:
    --------

    `out` : np.ndarray
        NumPy array containing the constant values of the input DA variables.

    Examples:
    ---------
    ```
    import numpy as np

    from kiam_astro import dace

    x_nominal = np.array([1.0, 2.5])

    da_vars = dace.create(x_nominal, order=3)

    result = dace.dace2numpy(da_vars)

    print(result)

    # [1., 2.5]

    print(type(result))

    # <class 'numpy.ndarray'>
    ```
    """
    return da_array.cons()
def extract_value(da_obj: da.DA) -> float:
    """
    Extracts the constant value from a single DACE scalar object.

    Retrieves the zero-order term (constant part) of a Differential Algebra number.

    Parameters:
    -----------
    `da_obj` : da.DA
        Single DACE object (scalar).

    Returns:
    --------
    `val` : float
        The constant value of the DA object.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(1, 1)

    # Create a DA variable x = 3.14 + delta_1

    x = da.DA(1) + 3.14

    print(dace.extract_value(x))

    # 3.14
    ```
    """

    return da_obj.cons()
def extract_gradient(da_obj: da.DA) -> np.ndarray:
    """
    Extracts the gradient vector from a single DACE scalar object.

    Retrieves the first-order partial derivatives of the DA object with respect
    to the initialized independent variables.

    Parameters:
    -----------
    `da_obj` : da.DA
        Single DACE object (scalar).

    Returns:
    --------
    `grad` : np.ndarray
        NumPy array containing the gradient vector. The length corresponds
        to the number of independent variables in the DACE environment.

    Examples:
    ---------
    ```
    import daceypy as da

    import numpy as np

    from kiam_astro import dace

    # Initialize DACE: Order 1, 2 independent variables

    da.DA.init(1, 2)

    # Define independent variables: x_1 and x_2

    x1 = da.DA(1)

    x2 = da.DA(2)

    # Function f = 3x1 + 5x2 + 10

    f = 3 * x1 + 5 * x2 + 10

    print(dace.extract_gradient(f))

    # [3. 5.]
    ```
    """
    return da_obj.gradient()
def extract_hessian(da_obj: da.DA, n_vars: int) -> np.ndarray:
    """
    Extracts the Hessian matrix from a single DACE scalar object.

    Computes the matrix of second-order partial derivatives of the DA object
    with respect to the independent variables. The values correspond to the
    derivatives evaluated at the expansion point (constant parts).

    Parameters:
    -----------
    `da_obj` : da.DA
        Single DACE object (scalar).

    `n_vars` : int
        Number of independent variables in the DACE environment.
        Determines the size of the output matrix.

    Returns:
    --------

    `hessian` : np.ndarray
        A square NumPy array of shape (n_vars, n_vars) containing the
        Hessian matrix elements.

    Examples:
    ---------
    ```
    import daceypy as da

    import numpy as np

    from kiam_astro import dace

    # Initialize DACE: Order 2 (required for Hessian), 2 variables

    da.DA.init(2, 2)

    # Define variables x (id 1) and y (id 2)

    x = da.DA(1)

    y = da.DA(2)

    # Define function f = x^2 + x*y

    # Hessian should be: [[2, 1], [1, 0]]

    f = x**2 + x*y

    H = dace.extract_hessian(f, n_vars=2)

    print(H)

    # [[2. 1.]

    # [1. 0.]]
    ```
    """
    hessian = np.zeros((n_vars, n_vars))
    for i in range(n_vars):
        deriv1 = da_obj.deriv(i + 1)
        for j in range(n_vars):
            deriv2 = deriv1.deriv(j + 1)
            hessian[i, j] = deriv2.cons()
    return hessian

# Функции для работы с матрицами и векторами
def dot(v1: da.array, v2: da.array) -> da.DA:
    """
    Calculates the dot product of two DACE vectors.

    Computes the scalar product of two arrays containing Differential Algebra
    objects. The result is a single DA object representing the sum of element-wise
    products.

    Parameters:
    -----------

    `v1` : da.array
        First input vector of DA variables.

    `v2` : da.array
        Second input vector of DA variables.

    Returns:
    --------

    `result` : da.DA
        The scalar dot product of the two vectors.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    # x - a vector of variables wrt which derivatives of all functions will be computed

    x = dace.create([1.0, 2.0], 3)

    v1 = da.array([x[0], x[1]])

    v2 = da.array([x[0], x[1]])

    prod = dace.dot(v1, v2).cons()

    print(prod)

    # 5.0
    ```
    """

    if v1.shape[0] != v2.shape[0]:
        raise ValueError(f"Размеры векторов не совпадают: {v1.shape[0]} и {v2.shape[0]}")

    result = da.DA(0.0)
    for i in range(v1.shape[0]):
        result += v1[i] * v2[i]

    return result
def dotmv(matrix: da.array, vector: da.array) -> da.array:
    """
    Computes the matrix-vector product involving DACE arrays.

    Performs the multiplication of a 2D matrix by a 1D vector. The elements
    can be DA objects or constants.

    Parameters:
    -----------
    `matrix` : da.array
        A 2-dimensional DACE array of shape (m, n).

    `vector` : da.array
        A 1-dimensional DACE array of shape (n,).

    Returns:
    --------

    `result` : da.array
        A 1-dimensional DACE array of shape (m,) containing the product.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    x = dace.create([1.0, 2.0], 3)

    m = da.array([[x[0], x[1]], [x[0], x[1]]])

    v = da.array([x[0], x[1]])

    mv = dace.dotmv(m, v).cons()

    print(mv)

    # [5. 5.]
    ```
    """

    if len(matrix.shape) != 2:
        raise Exception('Матрица должна быть двумерным массивом.')

    if len(vector.shape) != 1:
        raise Exception('Вектор должен быть одномерным массивом.')

    m, n = matrix.shape

    if vector.shape[0] != n:
        raise ValueError(f"Несовместимые размерности: матрица ({m}×{n}) и вектор ({vector.shape[0]})")

    # Создаем результирующий вектор
    result = da.array.zeros(m)

    # Умножаем каждую строку матрицы на вектор
    for i in range(m):
        for j in range(n):
            result[i] += matrix[i, j] * vector[j]

    return result
def dotvm(vector: da.array, matrix: da.array) -> da.array:
    """
    Computes the vector-matrix product involving DACE arrays.

    Performs the multiplication of a 1D vector (interpreted as a row vector)
    by a 2D matrix. The elements can be DA objects or constants.

    Parameters:
    -----------
    `vector` : da.array
        A 1-dimensional DACE array of shape (m,).

    `matrix` : da.array
        A 2-dimensional DACE array of shape (m, n).

    Returns:
    --------

    `result` : da.array
        A 1-dimensional DACE array of shape (n,) containing the product.

    Examples:
    --------
    ```
    import daceypy as da

    from kiam_astro import dace

    x = dace.create([1.0, 2.0], 3)

    v = da.array([x[0], x[1]])

    m = da.array([[x[0], x[1]], [x[0], x[1]]])

    vm = dace.dotvm(v, m).cons()

    print(vm)

    # [3. 6.]
    ```
    """

    if len(matrix.shape) != 2:
        raise Exception('Матрица должна быть двумерным массивом.')

    if len(vector.shape) != 1:
        raise Exception('Вектор должен быть одномерным массивом.')

    m, n = matrix.shape

    if vector.shape[0] != m:
        raise ValueError(
            f"Несовместимые размерности: вектор ({vector.shape[0]}) "
            f"и матрица ({m}×{n})"
        )

    # Создаем результирующий вектор
    result = da.array.zeros(n)

    # Умножаем вектор на каждый столбец матрицы
    for j in range(n):
        for i in range(m):
            result[j] += vector[i] * matrix[i, j]  # ← Исправлено: result[j]

    return result
def dotmm(matrix1: da.array, matrix2: da.array) -> da.array:
    """
    Computes the matrix-matrix product of two DACE arrays.

    Performs standard linear algebraic matrix multiplication. The calculation
    combines rows of the first matrix with columns of the second matrix.

    Parameters:
    -----------

    `matrix1` : da.array
        First input matrix, a 2-dimensional DACE array of shape (m, n).

    `matrix2` : da.array
        Second input matrix, a 2-dimensional DACE array of shape (n, p).

    Returns:
    --------

    `result` : da.array
        A 2-dimensional DACE array of shape (m, p) containing the matrix product.

    Examples:
    --------
    ```
    import daceypy as da

    from kiam_astro import dace

    x = dace.create([1.0, 2.0], 3)

    m1 = da.array([[x[0], x[1]], [x[0], x[1]]])

    m2 = da.array([[x[0], x[1]], [x[0], x[1]]])

    mm = dace.dotmm(m1, m2).cons()

    print(mm)

    # [[3. 6.]

    #  [3. 6.]]
    ```

    """
    if len(matrix1.shape) != 2:
        raise Exception('Матрица 1 должна быть двумерным массивом.')

    if len(matrix2.shape) != 2:
        raise Exception('Матрица 2 должна быть двумерным массивом.')

    m1, n1 = matrix1.shape
    m2, n2 = matrix2.shape

    if n1 != m2:
        raise ValueError(
            f"Несовместимые размерности матриц: {m1}x{n1} * {m2}x{n2}"
        )

    # Создаем результирующий вектор
    result = da.array.zeros((m1, n2))

    # Умножаем вектор на каждый столбец матрицы
    for i in range(m1):
        for j in range(n2):
            for k in range(n1):
                result[i, j] += matrix1[i, k] * matrix2[k, j]

    return result
def cross(v1: da.array, v2: da.array) -> da.array:
    """
    Computes the cross product of two 3-dimensional DACE vectors.

    Calculates the vector product where the resulting vector is perpendicular
    to the plane defined by the two input vectors. This operation is strictly
    defined for vectors of length 3 containing DA objects or constants.

    Parameters:
    -----------

    `v1` : da.array
        First input vector containing 3 elements.

    `v2` : da.array
        Second input vector containing 3 elements.

    Returns:
    --------

    `result` : da.array
        A 3-element DACE array representing the cross product vector.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    x = dace.create([1.0, 2.0, 3.0], 3)

    v1 = da.array([x[0], x[1], x[2]])

    v2 = da.array([x[0] + 1.0, x[1] - 1.0, x[2]])

    w = dace.cross(v1, v2).cons()

    print(w)

    # [ 3.  3. -3.]
    ```
    """
    if v1.size != 3 or v2.size != 3:
        raise ValueError("Векторное произведение определено только для 3D векторов")

    result = da.array.zeros(3)
    result[0] = v1[1] * v2[2] - v1[2] * v2[1]
    result[1] = v1[2] * v2[0] - v1[0] * v2[2]
    result[2] = v1[0] * v2[1] - v1[1] * v2[0]

    return result
def norm(v: da.array) -> da.DA:
    """
   Computes the Euclidean norm (length) of a DACE vector.

   Calculates the square root of the sum of squares of the vector elements.
   The result is returned as a scalar Differential Algebra object.

   Parameters:
   -----------

   `v` : da.array
       Input DACE vector.

   Returns:
   --------

   `da.DA`
       Scalar DA object representing the norm of the vector.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    x = dace.create([1.0, 2.0, 3.0], 3)

    v = da.array([x[0] + 1.0, x[1] - 1.0, x[2]])

    nv = dace.norm(v).cons()

    print(nv)

    # 3.7416573867739413
    ```

   """
    return v.vnorm()
def normalize(v: da.array) -> da.array:
    """
    Computes the normalized unit vector for a given DACE vector.

    Returns a new vector with the same direction as the input vector but with
    a Euclidean norm (magnitude) of 1. Each element of the input vector is
    divided by its scalar norm.

    Parameters:
    -----------

    `v` : da.array
        Input 1-dimensional DACE vector to be normalized.

    Returns:
    --------

    `result` : da.array
        A unit vector (1-dimensional DACE array) corresponding to the input.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    x = dace.create([1.0, 2.0, 3.0], 3)

    v = da.array([x[0] + 1.0, x[1] - 1.0, x[2]])

    nv = dace.normalize(v).cons()

    print(nv)

    # [0.53452248 0.26726124 0.80178373]
    ```
    """
    if len(v.shape) != 1:
        raise ValueError('Вектор должен быть одномерным массивом.')

    # Вычисляем норму вектора
    norm = v.vnorm()

    # Создаем результирующий вектор
    n = v.shape[0]
    result = da.array.zeros(n)

    # Делим каждый элемент на норму
    for i in range(n):
        result[i] = v[i] / norm

    return result

# Тригонометрические функции
def sin(angle: da.DA) -> da.DA:
    """
    Computes the sine of a Differential Algebra object.

    Calculates the trigonometric sine function for the input DA variable.
    This operation assumes the input is in radians and performs the operation
    within the algebra of truncated power series.

    Parameters:
    -----------

    `angle` : da.DA
        The input angle in radians as a DA object.

    Returns:
    --------

    `da.DA`
        The sine of the input angle.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.sin(x).cons()

    print(y)
    ```
    """
    return angle.sin()
def cos(angle: da.DA) -> da.DA:
    """
    Computes the cosine of a Differential Algebra object.

    Calculates the trigonometric cosine function for the input DA variable.
    This operation assumes the input is in radians and performs the operation
    within the algebra of truncated power series.

    Parameters:
    -----------

    `angle` : da.DA
        The input angle in radians as a DA object.

    Returns:
    --------

    `da.DA`
        The cosine of the input angle.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.cos(x).cons()

    print(y)
    ```
    """
    return angle.cos()
def tan(angle: da.DA) -> da.DA:
    """
    Computes the tangent of a Differential Algebra object.

    Calculates the trigonometric tangent function for the input DA variable.
    This operation assumes the input is in radians and performs the operation
    within the algebra of truncated power series.

    Parameters:
    -----------

    `angle` : da.DA
        The input angle in radians as a DA object.

    Returns:
    --------

    `da.DA`
        The tangent of the input angle.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.tan(x).cons()

    print(y)
    ```
    """
    return angle.tan()
def asin(x: da.DA) -> da.DA:
    """
    Computes the arcsine of a Differential Algebra object.

    Calculates the trigonometric arcsine function for the input DA variable.

    Parameters:
    -----------

    `angle` : da.DA
        The input angle in radians as a DA object.

    Returns:
    --------

    `da.DA`
        The arcsine of the input angle.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.asin(x).cons()

    print(y)
    ```
    """
    return x.asin()
def acos(x: da.DA) -> da.DA:
    """
    Computes the arccosine of a Differential Algebra object.

    Calculates the trigonometric arccosine function for the input DA variable.

    Parameters:
    -----------

    `angle` : da.DA
        The input angle in radians as a DA object.

    Returns:
    --------

    `da.DA`
        The arccosine of the input angle.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.acos(x).cons()

    print(y)
    ```
    """
    return x.acos()
def arctan(x: da.DA) -> da.DA:
    """
    Computes the arctangent of a Differential Algebra object.

    Calculates the trigonometric arctangent function for the input DA variable.

    Parameters:
    -----------

    `angle` : da.DA
        The input angle in radians as a DA object.

    Returns:
    --------

    `da.DA`
        The arctangent of the input angle.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.arctan(x).cons()

    print(y)
    ```
    """
    return x.arctan()
def arctan2(y: da.DA, x: da.DA) -> da.DA:
    """
    Computes the element-wise arc tangent of y/x choosing the quadrant correctly.

    Calculates the principal value of the arctangent of y/x, using the signs
    of both arguments to determine the quadrant of the returned angle. The result
    is a Differential Algebra object representing the angle in radians, typically
    in the range (-pi, pi].

    Parameters:
    -----------
    `y` : da.DA
        The y-coordinate (numerator) as a DA object.

    `x` : da.DA
        The x-coordinate (denominator) as a DA object.

    Returns:
    --------
    `da.DA`
        The calculated angle in radians as a DA object.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=2)

    x, y = da.DA(1.0), da.DA(2.0)

    angle = dace.arctan2(y, x).cons()

    print(angle)
    ```

    """
    return y.arctan2(x)

# Прочие обычные функции
def sqrt(x: da.DA) -> da.DA:
    """
    Computes the square root of a Differential Algebra object.

    Calculates the principal square root of the input DA variable using
    truncated power series algebra.

    Parameters:
    -----------

    `x` : da.DA
        The input DA object (must be non-negative in the constant part for real evaluation).

    Returns:
    --------

    `da.DA`
        The square root of the input.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.sqrt(x).cons()

    print(y)
    ```
    """
    return x.sqrt()
def exp(x: da.DA) -> da.DA:
    """
    Computes the exonent function of a Differential Algebra object.

    Calculates the exponent of the input DA variable using
    truncated power series algebra.

    Parameters:
    -----------

    `x` : da.DA
        The input DA object (must be non-negative in the constant part for real evaluation).

    Returns:
    --------

    `da.DA`
        The exponent of the input.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.exp(x).cons()

    print(y)
    ```
    """
    return x.exp()
def log(x: da.DA) -> da.DA:
    """
    Computes the natural logarithm function of a Differential Algebra object.

    Calculates the natural logarithm of the input DA variable using
    truncated power series algebra.

    Parameters:
    -----------

    `x` : da.DA
        The input DA object (must be non-negative in the constant part for real evaluation).

    Returns:
    --------

    `da.DA`
        The natural logarithm of the input.

    Examples:
    ---------
    ```
    import daceypy as da

    from kiam_astro import dace

    da.DA.init(ord=3, nvar=1)

    x = da.DA(0.0)

    y = dace.log(x).cons()

    print(y)
    ```
    """
    return x.log()

# Функции преобразования
def rv2oe(rv: da.array, mu: float) -> da.array:
    """
    Converts Cartesian state vectors to classical Keplerian orbital elements.

    Transforms a state vector comprising position and velocity into the set of
    six Keplerian elements. This function operates on Differential Algebra (DA)
    objects, allowing for the computation of the transformation and its
    derivatives/expansions.

    Parameters:
    -----------
    `rv` : da.array
        A 6-element DACE array representing the state vector.
        - `rv[0:3]`: Position vector (x, y, z).
        - `rv[3:6]`: Velocity vector (vx, vy, vz).

    `mu` : float
        The standard gravitational parameter (GM) of the central body.

    Returns:
    --------

    `oe` : da.array
        A 6-element DACE array containing the orbital elements in the following order:
        1. `a`: Semi-major axis
        2. `e`: Eccentricity
        3. `i`: Inclination (radians)
        4. `Omega`: Longitude of the ascending node (radians)
        5. `omega`: Argument of periapsis (radians)
        6. `nu`: True anomaly (radians)

    Examples:
    ---------
    ```
    from kiam_astro import dace

    rv = dace.create([1.0, 0.0, 0.0, 0.1, 1.0, 0.1], 3)

    oe = dace.rv2oe(rv, 1.0)

    print(oe.cons())
    ```
    """

    # Распаковка
    rvec = rv[:3]
    vvec = rv[3:6]

    # 1. Основные величины
    r = rvec.vnorm()
    v2 = vvec.dot(vvec)

    # 2. Орбитальный момент c = r x v
    cvec = rvec.cross(vvec)
    c = cvec.vnorm()

    # 3. Вектор узлов n = k x c = [-cy, cx, 0]
    nvec = da.array([-cvec[1], cvec[0], 0.0])

    # 4. Вектор эксцентриситета e = (v x c)/mu - r/|r|
    cross_vc = vvec.cross(cvec)
    evec = cross_vc / mu - rvec / r
    e = evec.vnorm()

    # 5. Энергия и большая полуось a
    xi = v2 / 2.0 - mu / r
    a = -mu / (2.0 * xi)

    # 6. Наклонение i
    i = (cvec[2] / c).acos()

    # 7. Долгота восходящего узла Omega
    Omega = nvec[1].atan2(nvec[0])

    # 8. Аргумент перицентра omega
    cross_ne = nvec.cross(evec)
    sin_omega_scaled = cross_ne.dot(cvec) / c
    cos_omega_scaled = nvec.dot(evec)
    omega = sin_omega_scaled.atan2(cos_omega_scaled)

    # 9. Истинная аномалия nu
    cross_er = evec.cross(rvec)
    sin_nu_scaled = cross_er.dot(cvec) / c
    cos_nu_scaled = evec.dot(rvec)
    nu = sin_nu_scaled.atan2(cos_nu_scaled)

    # Формируем результирующий массив
    oe = da.array([a, e, i, Omega, omega, nu])

    return oe
def oe2rv(oe: da.array, mu: float) -> da.array:
    """
    Converts classical Keplerian orbital elements to Cartesian state vectors.

    Transforms a set of six Keplerian elements into a state vector comprising
    position and velocity coordinates. This function performs the inverse
    transformation of `rv2oe`, calculating the position and velocity in the
    inertial frame (ECI) via the perifocal frame. Supports Differential Algebra
    objects for high-order expansion.

    Parameters:
    -----------
    `oe` : da.array
        A 6-element DACE array containing the orbital elements:
        1. `a`: Semi-major axis
        2. `e`: Eccentricity
        3. `i`: Inclination (radians)
        4. `Omega`: Longitude of the ascending node (radians)
        5. `omega`: Argument of periapsis (radians)
        6. `nu`: True anomaly (radians)

    `mu` : float
        The standard gravitational parameter (GM) of the central body.

    Returns:
    --------
    `rv` : da.array
        A 6-element DACE array representing the state vector.
        - `rv[0:3]`: Position vector (x, y, z).
        - `rv[3:6]`: Velocity vector (vx, vy, vz).

    Examples:
    ---------
    ```
    from kiam_astro import dace

    oe = dace.create([1.0, 0.1, 0.1, 0.0, 0.0, 0.0], 3)

    rv = dace.oe2rv(oe, 1.0)

    print(rv.cons())
    ```
    """

    # Распаковка орбитальных элементов
    a, e, i, Omega, omega, nu = oe[0], oe[1], oe[2], oe[3], oe[4], oe[5]

    # 1. Предварительные вычисления тригонометрии
    # Используем методы DA-объектов
    c_O, s_O = Omega.cos(), Omega.sin()
    c_w, s_w = omega.cos(), omega.sin()
    c_i, s_i = i.cos(), i.sin()
    c_nu, s_nu = nu.cos(), nu.sin()

    # 2. Параметр орбиты p = a * (1 - e^2)
    p = a * (1.0 - e ** 2)

    # 3. Расстояние до центра притяжения r = p / (1 + e*cos(nu))
    r = p / (1.0 + e * c_nu)

    # 4. Координаты и скорость в перифокальной системе (PQW)
    # В этой системе ось P направлена в перицентр, Q - перпендикулярно в плоскости движения
    # r_pqw = [r * cos(nu), r * sin(nu), 0]
    # v_pqw = sqrt(mu/p) * [-sin(nu), e + cos(nu), 0]

    xp = r * c_nu
    yp = r * s_nu

    sqrt_mu_p = (mu / p).sqrt()
    vxp = sqrt_mu_p * (-s_nu)
    vyp = sqrt_mu_p * (e + c_nu)

    # 5. Единичные векторы P и Q в инерциальной системе
    # Матрица поворота R = Rz(-Omega) * Rx(-i) * Rz(-omega)

    # Вектор P (направление на перицентр)
    Px = c_O * c_w - s_O * s_w * c_i
    Py = s_O * c_w + c_O * s_w * c_i
    Pz = s_w * s_i

    # Вектор Q (направление на параметр, повернуто на 90 град от P в плоскости)
    Qx = -c_O * s_w - s_O * c_w * c_i
    Qy = -s_O * s_w + c_O * c_w * c_i
    Qz = c_w * s_i

    # 6. Трансформация в ECI
    # r_vec = xp * P + yp * Q
    # v_vec = vxp * P + vyp * Q

    x = xp * Px + yp * Qx
    y = xp * Py + yp * Qy
    z = xp * Pz + yp * Qz

    vx = vxp * Px + vyp * Qx
    vy = vxp * Py + vyp * Qy
    vz = vxp * Pz + vyp * Qz

    # Формируем результирующий массив
    rv = da.array([x, y, z, vx, vy, vz])

    return rv
def rv2ee(rv: da.array, mu: float) -> da.array:
    """
    Converts Cartesian state vectors to Equinoctial orbital elements.

    Transforms a Cartesian state vector (position and velocity) into non-singular
    Equinoctial elements. This formulation eliminates singularities associated with
    zero eccentricity and zero inclination, making it suitable for a wider range of
    orbits compared to classical Keplerian elements.

    The implementation uses an auxiliary frame defined by vectors `f` and `g` to
    project the state vector.

    Parameters:
    -----------
    `rv` : da.array
        A 6-element DACE array representing the state vector.
        - `rv[0:3]`: Position vector (x, y, z).
        - `rv[3:6]`: Velocity vector (vx, vy, vz).

    `mu` : float
        The standard gravitational parameter (GM) of the central body.

    Returns:
    --------
    `ee` : da.array
        A 6-element DACE array containing the Equinoctial elements:
        1. `h`: Square rooted semi-latus rectum divided by mu (or related parameter depending on specific formulation).
           Note: Specifically here, h = sqrt(p / mu) where p is the semi-latus rectum.
        2. `ex`: x-component of the eccentricity vector in the equinoctial frame (k).
        3. `ey`: y-component of the eccentricity vector in the equinoctial frame (h).
        4. `ix`: x-component of the inclination vector (q).
        5. `iy`: y-component of the inclination vector (p).
        6. `L`: True longitude (radians).

    Examples:
    ---------
    ```
    from kiam_astro import dace

    rv = dace.create([1.0, 0.0, 0.0, 0.1, 1.0, 0.1], 3)

    ee = dace.rv2ee(rv, 1.0)

    print(ee.cons())
    ```
    """

    # Распаковка
    rvect = rv[0:3]
    vvect = rv[3:6]

    # 1. Орбитальный момент и радиус
    cvect = rvect.cross(vvect)
    r = rvect.vnorm()
    c = cvect.vnorm()

    # 2. Вектор avect (связан с вектором эксцентриситета)
    cross_vc = vvect.cross(cvect)
    avect = cross_vc - mu * rvect / r

    # 3. Вспомогательные векторы f и g
    denom = c + cvect[2]
    fvect = da.array([
        c - cvect[0] ** 2 / denom,
        -cvect[0] * cvect[1] / denom,
        -cvect[0]
    ])
    gvect = da.array([
        -cvect[0] * cvect[1] / denom,
        c - cvect[1] ** 2 / denom,
        -cvect[1]
    ])

    # 4. Проекции L1, L2
    L1 = rvect.dot(gvect)
    L2 = rvect.dot(fvect)

    # 5. Вычисление элементов
    h = c / mu
    ex = avect.dot(fvect) / (c * mu)
    ey = avect.dot(gvect) / (c * mu)
    ix = -cvect[1] / denom
    iy = cvect[0] / denom
    L = L1.atan2(L2)

    # Формируем результирующий массив
    ee = da.array([h, ex, ey, ix, iy, L])

    return ee
def ee2rv(ee: da.array, mu: float) -> da.array:
    """
    Converts Equinoctial orbital elements to Cartesian state vectors.

    Transforms a set of non-singular Equinoctial elements into position and
    velocity vectors in the inertial frame. This is the inverse operation of
    `rv2ee`. It utilizes the equinoctial basis vectors (f, g) and the
    auxiliary parameter K to reconstruct the state vector from the provided
    elements.

    Parameters:
    -----------
    `ee` : da.array
        A 6-element DACE array containing the Equinoctial elements:
        1. `h`: Parameter related to semi-latus rectum (specifically h = sqrt(p/mu)).
        2. `ex`: x-component of the eccentricity vector.
        3. `ey`: y-component of the eccentricity vector.
        4. `ix`: x-component of the inclination vector.
        5. `iy`: y-component of the inclination vector.
        6. `L`: True longitude (radians).

    `mu` : float
        The standard gravitational parameter (GM) of the central body.

    Returns:
    --------
    `rv` : da.array
        A 6-element DACE array representing the state vector.
        - `rv[0:3]`: Position vector (x, y, z).
        - `rv[3:6]`: Velocity vector (vx, vy, vz).

    Examples:
    ---------
    ```
    from kiam_astro import dace

    ee = dace.create([1.0, 0.1, 0.1, 0.0, 0.0, 0.0], 3)

    rv = dace.ee2rv(ee, 1.0)

    print(rv.cons())
    ```

    """

    # Распаковка элементов
    h, ex, ey, ix, iy, L = ee[0], ee[1], ee[2], ee[3], ee[4], ee[5]

    # Тригонометрия
    cosL = L.cos()
    sinL = L.sin()

    # Предварительные вычисления
    ix2 = ix ** 2
    iy2 = iy ** 2
    ixiy = ix * iy

    p = h ** 2 * mu
    ksi = 1.0 + ex * cosL + ey * sinL

    K = h * mu / (1.0 + ix2 + iy2)

    # Векторы f и g
    f = da.array([
        K * (1.0 + ix2 - iy2),
        K * 2.0 * ixiy,
        -2.0 * K * iy
    ])

    g = da.array([
        2.0 * K * ixiy,
        K * (1.0 - ix2 + iy2),
        2.0 * K * ix
    ])

    # Вспомогательные коэффициенты
    t1 = (ex + cosL) / p
    t2 = (ey + sinL) / p

    # Формируем вектор состояния
    rv = da.array([
        h * (f[0] * cosL + g[0] * sinL) / ksi,
        h * (f[1] * cosL + g[1] * sinL) / ksi,
        h * (f[2] * cosL + g[2] * sinL) / ksi,
        t1 * g[0] - t2 * f[0],
        t1 * g[1] - t2 * f[1],
        t1 * g[2] - t2 * f[2]
    ])

    return rv
def scrs2mer(x: da.array, jd: float) -> da.array:
    """
    Transforms a state vector from the SCRS (Spacecraft-Centered Rotating System)
    frame to the MER (Mean Earth/Rotation) frame.

    This function applies a coordinate transformation matrix, retrieved via the
    `kiam.scrs2mer` library function at the specified Julian Date, to both the
    position and velocity components of the input state vector.

    Note: The input `x` is treated as a 6-element state vector [rx, ry, rz, vx, vy, vz].
    The rotation is applied identically to the position and velocity vectors, implying
    a coordinate rotation without accounting for the transport theorem (Coriolis/centrifugal terms),
    or that the velocity is already expressed relative to the rotating frame but resolved
    in inertial axes.

    Parameters:
    -----------
    `x` : da.array
       The input 6-element state vector in the SCRS frame.
       - `x[0:3]`: Position vector.
       - `x[3:6]`: Velocity vector.

    `jd` : float
       The Julian Date for which the transformation matrix is calculated.

    Returns:
    --------
    `da.array`
       The transformed 6-element state vector in the MER frame.

    Examples:
    ---------
    ```
    from kiam_astro import dace, kiam

    jd = kiam.juliandate(2028, 1, 1, 0, 0, 0)

    scrs = dace.create([1.0, 0.0, 0.0, 0.1, 1.0, 0.1], 3)

    mer = dace.scrs2mer(scrs, jd)

    print(mer.cons())
    ```

    """
    m_scrs2mer = kiam.scrs2mer(np.eye(3), jd*np.ones(3))
    rvect = dotmv(m_scrs2mer, x[0:3])
    vvect = dotmv(m_scrs2mer, x[3:6])
    return da.array([rvect[0], rvect[1], rvect[2], vvect[0], vvect[1], vvect[2]])
def mer2scrs(x: da.array, jd: float) -> da.array:
    """
    Transforms a state vector from the MER (Mean Earth/Rotation) frame to the
    SCRS (Spacecraft-Centered Rotating System) frame.

    This performs the inverse transformation of `scrs2mer`. It retrieves the
    rotation matrix for the specified Julian Date using `kiam.mer2scrs` and
    applies it to the position and velocity vectors.

    Parameters:
    -----------
    `x` : da.array
        The input 6-element state vector in the MER frame.
        - `x[0:3]`: Position vector.
        - `x[3:6]`: Velocity vector.

    `jd` : float
        The Julian Date for which the transformation matrix is calculated.

    Returns:
    --------
    `da.array`
        The transformed 6-element state vector in the SCRS frame.

    Examples:
    --------
    ```
    from kiam_astro import dace, kiam

    jd = kiam.juliandate(2028, 1, 1, 0, 0, 0)

    mer = dace.create([1.0, 0.0, 0.0, 0.1, 1.0, 0.1], 3)

    scrs = dace.mer2scrs(mer, jd)

    print(scrs.cons())
    ```

    """
    m_mer2scrs = kiam.mer2scrs(np.eye(3), jd*np.ones(3))
    rvect = dotmv(m_mer2scrs, x[0:3])
    vvect = dotmv(m_mer2scrs, x[3:6])
    return da.array([rvect[0], rvect[1], rvect[2], vvect[0], vvect[1], vvect[2]])

# Уравнения движения
def r2bp(t: float, x: da.array, mu: float) -> da.array:
    """
    Computes the equations of motion for the Two-Body Problem (Keplerian motion).

    Calculates the time derivative of the state vector (velocity and acceleration)
    given the current state and the gravitational parameter. This function describes
    the motion of a body under the influence of a central point mass gravity field.

    Parameters:
    -----------
    `t` : float
        Current time (not used explicitly in the autonomous 2BP, but required by
        standard ODE solver signatures).

    `x` : da.array
        The 6-element state vector.
        - `x[0:3]`: Position vector (r).
        - `x[3:6]`: Velocity vector (v).

    `mu` : float
        The standard gravitational parameter (GM) of the central body.

    Returns:
    --------
    `da.array`
        The time derivative of the state vector (dx/dt).
        - `[0:3]`: Velocity vector (v).
        - `[3:6]`: Acceleration vector (a = -mu * r / |r|^3).

    Examples:
    ---------
    ```
    from kiam_astro import dace

    t = 0.0

    x = dace.create([1.0, 0.0, 0.0, 0.0, 1.0, 0.0], 3)

    dxdt = dace.r2bp(t, x, 1.0)

    print(dxdt)
    ```

    """
    rvect: da.array = x[0:3]  # вектор положения
    vvect: da.array = x[3:6]  # вектор скорости
    r = rvect.vnorm()  # норма радиус-вектора
    acc = - mu * rvect / (r ** 3)  # ускорение
    dx = vvect.concat(acc)  # объединение скорости и ускорения
    return dx

# Интеграторы
def rk4(func: Callable, x0: da.array, t0: float, t1: float, h: float) -> da.array:
    """
    Implements the 4th-order Runge-Kutta (RK4) numerical integration method.

    Solves a system of ordinary differential equations (ODEs) defined by `func`
    over the interval [t0, t1]. This implementation dynamically adjusts the
    step size slightly to ensure the final time `t1` is reached exactly with
    an integer number of steps.

    Parameters:
    -----------
    `func` : Callable[[float, da.array], da.array]
        The system dynamics function f(t, x). It must accept time and state
        as arguments and return the derivative of the state (dx/dt).

    `x0` : da.array
        Initial state vector at time t0. Supports Differential Algebra (DA)
        objects for propagating expansions through the integration.

    `t0` : float
        Start time of the integration.

    `t1` : float
        End time of the integration.

    `h` : float
        Target step size. The actual step size used (`h_actual`) will be calculated
        as `(t1 - t0) / n_steps` to fit perfectly within the interval, where
        `n_steps` is `ceil((t1 - t0) / h)`.

    Returns:
    --------
    `da.array`
        The integrated state vector at time `t1`.

    Examples:
    ---------
    ```
    from kiam_astro import dace

    import numpy

    t_start = 0.0

    t_end = 2.0 * numpy.pi

    num_steps = 100

    step_size = (t_end - t_start) / num_steps

    x_init = dace.create([1.0, 0.0, 0.0, 0.0, 1.0, 0.0], 3)

    dynamics = lambda t, x: dace.r2bp(t, x, 1.0)

    x_final = dace.rk4(func=dynamics, x0=x_init, t0=t_start, t1=t_end, h=step_size)

    print("Final vector:", x_final)
    ```
    """

    x = x0.copy()
    t = t0

    # Количество шагов
    n_steps = int(np.ceil((t1 - t0) / h))
    h_actual = (t1 - t0) / n_steps

    for _ in range(n_steps):

        # Вычисление коэффициентов Рунге-Кутты
        k1 = func(t, x)
        k2 = func(t + h_actual / 2.0, x + h_actual * k1 / 2.0)
        k3 = func(t + h_actual / 2.0, x + h_actual * k2 / 2.0)
        k4 = func(t + h_actual, x + h_actual * k3)

        # Обновление состояния
        x = x + h_actual * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        t = t + h_actual

    return x