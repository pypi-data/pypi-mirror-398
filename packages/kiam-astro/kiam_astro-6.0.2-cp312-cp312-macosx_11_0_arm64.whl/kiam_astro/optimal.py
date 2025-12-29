"""
This Python module is a part of the KIAM Astrodynamics Toolbox developed in
Keldysh Institute of Applied Mathematics (KIAM), Moscow, Russia.

The module provides routines to solve optimal control problems.

The toolbox is licensed under the MIT License.

For more information see GitHub page of the project:
https://github.com/shmaxg/KIAMToolbox

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

from kiam_astro import kiam
from scipy.optimize import minimize, least_squares
from numpy.linalg import norm
import numpy
from numpy import sqrt
from typing import Callable, Any

def sigmoid(x, center, width):
    EPSILON = 1.0e-6
    if abs(width) < EPSILON:
        return numpy.where(x >= center, 1.0, 0.0)
    else:
        return 1.0 / (1.0 + numpy.exp(-(x - center) / width))

# r2bp_pontr_energy_irm_u_rv problem
def solve_r2bp_pontr_energy_irm_u_rv(x0: numpy.ndarray, x1: numpy.ndarray, tof: float, nrevs: int, disp_iter: bool = True, atol_in: float = 1e-12, rtol_in: float = 1e-12, atol_ex: float = 1e-10, rtol_ex: float = 1e-10):
    """
    Solve standard energy-optimal control problem by Pontryagin principle in two-body problem,
    position-velocity variables in ideally-regulated engine model, using control acceleration as control variable.

    Parameters:
    -----------

    `x0` : numpy.ndarray, shape (6,)

    Initial phase state. Stucture: [x, y, z, vx, vy, vz]. Dimensionless, mu = 1.0.

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz]. Dimensionless, mu = 1.0.

    `tof` : float

    The time of flight.

    `nrevs` : int

    The number of revolutions.

    `disp_iter` : bool

    Whether to display iterations of the differential continuation method. Default: True.

    `atol_in` : float

    Absolute tolerance when integrating the internal equations (equations of motion). Default is 1e-12.

    `rtol_in` : float

    Relative tolerance when integrating the internal equations (equations of motion). Default is 1e-12.

    `atol_ex` : float

    Absolute tolerance when integrating the external equations (equations of differential continuation). Default is 1e-10.

    `rtol_ex` : float

    Relative tolerance when integrating the internal equations (equations of differential continuation). Default is 1e-10.

    Returns:
    --------

    `zopt` : numpy.ndarray, shape (6,)

    The optimized vector of initial conjugate variables. Structure: [lamx, lamy, lamz, lamvx, lamvy, lamvz].
    The optimization is done by using a Newton method with adaptive step.

    `zend` : numpy.ndarray, shape (6,)

    The non-optimized vector of initial conjugate variables obtained by differential correction procedure. Structure: [lamx, lamy, lamz, lamvx, lamvy, lamvz].

    `res` : numpy.ndarray, shape (6,)

    The residue between the target position and velocity and obtained by using `zopt` conjugate variables.

    `jac` : numpy.ndarray, shape (6, 6)

    The Jacobian of the residue function at `zopt`.

    Examples:
    ---------
    ```
    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    tof = 3 * numpy.pi

    nrevs = 1

    zopt, zend, res, jac = optimal.solve_r2bp_pontr_energy_irm_u_rv(x0, x1, tof, nrevs)
    ```
    """
    kiam.FKIAMToolbox.optimalcontrol.atol_in = atol_in
    kiam.FKIAMToolbox.optimalcontrol.rtol_in = rtol_in
    kiam.FKIAMToolbox.optimalcontrol.atol_ex = atol_ex
    kiam.FKIAMToolbox.optimalcontrol.rtol_ex = rtol_ex
    kiam.FKIAMToolbox.optimalcontrol.display_iterations = disp_iter
    zopt, zend, res, jac = kiam.FKIAMToolbox.optimalcontrol.solve_energy_optimal_problem(x0, x1, tof, nrevs)
    return zopt, zend, res, jac
def propagate_r2bp_pontr_energy_irm_u_rv(tspan: numpy.ndarray,  y0: numpy.ndarray, mu: float = 1.0, mu0: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Propagate extended by conjugate variables equations of motion.
    Two-body problem, energy-optimal control, ideally-regulated engine model, thrust acceleration as control function, position and velocity as variables.

    Parameters:
    -----------

    `tspan` : numpy.ndarray, shape (n,)

    The times at which the solution should be obtained.

    `y0` : numpy.ndarray, shape (12,), (156,), (168,)

    The initial state.

    Structure options:

    1. [rvect, vvect, lamr, lamv]

    2. [rvect, vvect, lamr, lamv, stm]

    3. [rvect, vvect, lamr, lamv, stm, dxdtau]

    where stm is the state transition matrix and dxdtau is derivative of [rvect, vvect, lamr, lamv] with respect to continuation parameter tau (gravitational parameter mu = mu0 + (1 - mu0) * tau).

    `mu` : float

    Gravitational parameter of the central body. Default is 1.0.

    `mu0` : float

    Initial value of the gravitational parameter in differential continuation process.
    This parameter is required only if dxdtau is among the dependent variables (len(y0) == 168).
    Otherwise the value is ignored.

    `atol` : float

    Absolute tolerance when integrating the equations. Default is 1e-12.

    `rtol` : float

    Relative tolerance when integrating the equations. Default is 1e-12.

    Returns:
    --------

    `T` : numpy.ndarray, shape (n,)

    The times at which the solution is obtained. Equals to tspan.

    `Y` : numpy.ndarray, shape (m, n)

    The integrated solutions. Each column correspond to a vector y at the correspondent time t in T.

    Examples:
    ---------
    ```
    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    z0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    tof = 3 * numpy.pi

    T, Y = optimal.propagate_r2bp_pontr_energy_irm_u_rv(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, z0)))
    ```
    """

    neq = len(y0)

    if neq == 12:
        stmreq, gradmureq = False, False
    elif neq == 156:
        stmreq = True
        gradmureq = False
    elif neq == 168:
        stmreq = True
        gradmureq = False
    else:
        raise Exception('Wrong number of dependent variables.')

    T, Y = kiam.FKIAMToolbox.propagationmodule.propagate_r2bp_pontr_eopt_irm_u_rv(tspan, y0, neq, atol, rtol, mu, mu0, stmreq, gradmureq)

    return T, Y

# r2bp_pontr_time_bnd_f_rv problem
def solve_r2bp_pontr_time_bnd_f_rv(x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, mass0: float, z0: numpy.ndarray, mu: float = 1.0, method: str = 'trust-constr', atol: float = 1e-12, rtol: float = 1e-12):
    """
    Solve time-optimal control problem by Pontryagin principle in two-body problem,
    position-velocity variables for thrust-bounded engine model with fixed exhaust velocity, using thrust force as control variable

    Parameters:
    -----------

    `x0` : numpy.ndarray, shape (6,)

    Initial phase state. Stucture: [x, y, z, vx, vy, vz].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `mass0` : float

    The initial mass of spacecraft.

    `z0` : numpy.ndarray, shape(7,)

    The initial guess for the optimization variables. Structure: [px, py, pz, pvx, pvy, pvz, tof], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    tof -- time of flight.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `method` : str

    Optimization method. Options: `'trust-constr'` (default), `'nelder-mead'`.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `zopt` : numpy.ndarray, shape (7,)

    The optimal optimization variables. Sturcture: [px, py, pz, pvx, pvy, pvz, tof], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    tof -- time of flight.

    `res` : numpy.ndarray, shape (7,)

    The optimal residue. Structure: [r(tend) - r1, v(tend) - v1, H(tend) - 0], where tend -- final time,
    r(tend) -- the final integrated position, v(tend) -- the final integrated velocity,
    r1 -- the target position, v1 -- the target velocity, H(tend) -- the Hamiltonian at final time.

    `jac` : numpy.ndarray, shape (7, 7)

    The Jacobian of res, i.e. the derivative matrix of res wrt optimization variables.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    mass0 = 80

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([-5.0, -2.0, 0.0])

    z0[3:6] = numpy.array([-2.0, -7.0, 0.0])

    z0[6] = optimal.estimate_tof(x0, x1, fmax / mass0, 1.0)

    zopt, res, jac = optimal.solve_r2bp_pontr_time_bnd_f_rv(x0, x1, fmax, vex, mass0, z0, 1.0, method='trust-constr', atol=1e-10, rtol=1e-10)

    T, Y = optimal.propagate_r2bp_pontr_time_bnd_f_rv(numpy.linspace(0.0, zopt[6], 10000), numpy.concatenate((x0, zopt[0:6])), fmax, vex, mass0)

    fig = kiam.plot(Y[0, :], Y[1, :], None, 'x', 'y', axis_equal=True)

    fig.show()

    mass = mass0 - fmax / vex * zopt[-1]

    print(f'Начальное приближение для времени полета: {z0[-1] * units["TimeUnit"]:.2f} дней')

    print(f'Оптимальное время полета: {zopt[-1] * units["TimeUnit"]:.2f} дней')

    print(f'Масса: {mass0:.2f} ---> {mass:.2f}, затрачивается {(1 - mass / mass0) * 100:.2f}%')

    print(f'Начальное ускорение: {fmax / mass0 * units["AccUnit"] * 1000} мм/с2')
    ```
    """

    if method == 'nelder-mead':

        options = {
            'disp': True,
            'maxiter': 10000,
            'return_all': False,
            'xatol': 1e-10,
            'fatol': 1e-10,
        }

        def objective(z):
            residue_norm, _ = objective_r2bp_pontr_time_bnd_f_rv(z, x0, x1, fmax, vex, mass0, mu, atol, rtol)
            return norm(residue_norm)

        result = minimize(objective,
                          z0,
                          method='Nelder-Mead',
                          options=options,
                          callback=callback_nelder_mead)

        f, jac = residue_r2bp_pontr_time_bnd_f_rv(result.x, x0, x1, fmax, vex, mass0, mu, atol, rtol)

        return result.x, f, jac

    if method == 'trust-constr':

        options = {
            'disp': True,
            'maxiter': 10000,
            'gtol': 1e-10,
            'xtol': 1e-10,
        }

        def objective(z):
            residue_norm, jacobian = objective_r2bp_pontr_time_bnd_f_rv(z, x0, x1, fmax, vex, mass0, mu, atol, rtol)
            return norm(residue_norm), jacobian

        result = minimize(objective,
                          z0,
                          jac=True,
                          method='trust-constr',
                          options=options,
                          callback=callback_trust_constr)

        f, jac = residue_r2bp_pontr_time_bnd_f_rv(result.x, x0, x1, fmax, vex, mass0, mu, atol, rtol)

        return result.x, f, jac
def propagate_r2bp_pontr_time_bnd_f_rv(tspan: numpy.ndarray, y0: numpy.ndarray, fmax: float, vex: float, mass0: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Propagate extended by conjugate variables equations of motion.
    Two-body problem, position-velocity variables, thrust-bounded engine model with fixed exhaust velocity, thrust force as control variable.

    Parameters:
    -----------

    `tspan` : numpy.ndarray, shape (n,)

    The times at which the solution should be obtained.

    `y0` : numpy.ndarray, shape (12,), (156,)

    The initial state.

    Structure options:

    1. [rvect, vvect, lamr, lamv]

    2. [rvect, vvect, lamr, lamv, stm]

    where stm is the state transition matrix.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `mass0` : float

    The initial mass of spacecraft.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `T` : numpy.ndarray, shape (n,)

    The times at which the solution is obtained. Equals to tspan.

    `Y` : numpy.ndarray, shape (m, n)

    The integrated solutions. Each column correspond to a vector y at the correspondent time t in T.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    mass0 = 80

    z0 = numpy.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 2 * numpy.pi])

    T, Y = optimal.propagate_r2bp_pontr_time_bnd_f_rv(numpy.linspace(0.0, z0[6], 10000), numpy.concatenate((x0, z0[0:6])), fmax, vex, mass0)

    fig = kiam.plot(Y[9, :], Y[10, :], None, 'px', 'py', axis_equal=True)

    fig.show()
    ```
    """
    neq = len(y0)
    if neq == 12:
        stmreq = False
    elif neq == 156:
        stmreq = True
    else:
        raise Exception('Wrong number of dependent variables.')
    T, Y = kiam.FKIAMToolbox.propagationmodule.propagate_r2bp_pontr_topt_bnd_f_rv(tspan, y0, neq, atol, rtol, mu, fmax, vex, mass0, stmreq)
    return T, Y
def residue_r2bp_pontr_time_bnd_f_rv(z: numpy.ndarray, x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, mass0: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Residue vector in boundary value problem derived for the time-optimal control problem.
    Two-body problem, bounded thrust force and fixed exhaust velocity, thrust force as control variable, position-velocity variables.

    Parameters:
    -----------

    `z` : numpy.ndarray, shape (7,)

    Optimization variables. Structure: [px, py, pz, pvx, pvy, pvz, tof], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    tof -- time of flight.

    `x0` : numpy.ndarray, shape (6,)

    Initial phase state. Stucture: [x, y, z, vx, vy, vz].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `mass0` : float

    The initial mass of spacecraft.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `res` : numpy.ndarray, shape (7,)

    The residue. Structure: [r(tend) - r1, v(tend) - v1, H(tend) - 0], where tend -- final time,
    r(tend) -- the final integrated position, v(tend) -- the final integrated velocity,
    r1 -- the target position, v1 -- the target velocity, H(tend) -- the Hamiltonian at final time.

    `jac` : numpy.ndarray, shape (7, 7)

    The Jacobian of res, i.e. the derivative matrix of res wrt optimization variables.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1/numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    mass0 = 80

    z = numpy.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 2 * numpy.pi])

    res, jac = optimal.residue_r2bp_pontr_time_bnd_f_rv(z, x0, x1, fmax, vex, mass0)

    print(res, jac)
    ```
    """

    kiam.FKIAMToolbox.optimalcontrol.atol_in = atol
    kiam.FKIAMToolbox.optimalcontrol.rtol_in = rtol

    kiam.FKIAMToolbox.optimalcontrol.ext_r0 = x0[0:3]
    kiam.FKIAMToolbox.optimalcontrol.ext_v0 = x0[3:6]
    kiam.FKIAMToolbox.optimalcontrol.ext_r1 = x1[0:3]
    kiam.FKIAMToolbox.optimalcontrol.ext_v1 = x1[3:6]

    kiam.FKIAMToolbox.optimalcontrol.ext_topt_fmax = fmax
    kiam.FKIAMToolbox.optimalcontrol.ext_topt_mu = mu
    kiam.FKIAMToolbox.optimalcontrol.ext_topt_vex = vex
    kiam.FKIAMToolbox.optimalcontrol.ext_topt_mass0 = mass0

    kiam.FKIAMToolbox.equationsmodule.mu_kr2bp_pontr_topt_bnd_f_rv = mu
    kiam.FKIAMToolbox.equationsmodule.fmax_kr2bp_pontr_topt_bnd_f_rv = fmax
    kiam.FKIAMToolbox.equationsmodule.vex_kr2bp_pontr_topt_bnd_f_rv = vex
    kiam.FKIAMToolbox.equationsmodule.mass0_kr2bp_pontr_topt_bnd_f_rv = mass0
    kiam.FKIAMToolbox.equationsmodule.t0_kr2bp_pontr_topt_bnd_f_rv = 0.0

    f, jac = kiam.FKIAMToolbox.optimalcontrol.residue_topt(z, 7, 7)

    return f, jac
def objective_r2bp_pontr_time_bnd_f_rv(z: numpy.ndarray, x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, mass0: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Scalar objective in boundary value problem derived for the time-optimal control problem.
    Two-body problem, bounded thrust force and fixed exhaust velocity, thrust force as control variable, position-velocity variables.

    Parameters:
    -----------

    `z` : numpy.ndarray, shape (7,)

    Optimization variables. Structure: [px, py, pz, pvx, pvy, pvz, tof], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    tof -- time of flight.

    `x0` : numpy.ndarray, shape (6,)

    Initial phase state. Stucture: [x, y, z, vx, vy, vz].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `mass0` : float

    The initial mass of spacecraft.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `obj` : float

    The squared norm of residue.

    `grad` : numpy.ndarray, shape (7,)

    The gradient of obj, i.e. the derivative of obj wrt optimization variables.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1/numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    mass0 = 80

    z = numpy.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 2 * numpy.pi])

    obj, grad = optimal.objective_r2bp_pontr_time_bnd_f_rv(z, x0, x1, fmax, vex, mass0)

    print(obj, grad)
    ```
    """
    f, jac = residue_r2bp_pontr_time_bnd_f_rv(z, x0, x1, fmax, vex, mass0, mu, atol, rtol)
    return norm(f)**2, jac.T @ f

# r2bp_pontr_mass_bnd_f_rv problem
def solve_r2bp_pontr_mass_bnd_f_rv(x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, tof: float, switch_width: float, z0: numpy.ndarray, mu: float = 1.0, method: str = 'trust-constr', atol: float = 1e-12, rtol: float = 1e-12):
    """
    Solve mass-optimal control problem by Pontryagin principle in two-body problem,
    position-velocity variables for thrust-bounded engine model with fixed exhaust velocity, using thrust force as control variable

    Parameters:
    -----------

    `x0` : numpy.ndarray, shape (7,)

    Initial phase state, including mass. Stucture: [x, y, z, vx, vy, vz, m].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `tof` : float

    The time of flight.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `z0` : numpy.ndarray, shape(7,)

    The initial guess for the optimization variables. Structure: [px, py, pz, pvx, pvy, pvz, pm], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    pm -- confugate to mass.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `method` : str

    Optimization method. Options: `'trust-constr'` (default), `'nelder-mead'`, `'least-squares'`.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `zopt` : numpy.ndarray, shape (7,)

    The optimal optimization variables. Sturcture: [px, py, pz, pvx, pvy, pvz, pm], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    pm -- conjugate to mass.

    `res` : numpy.ndarray, shape (7,)

    The optimal residue. Structure: [r(tend) - r1, v(tend) - v1, pm(tend) - 1], where tend -- final time,
    r(tend) -- the final integrated position, v(tend) -- the final integrated velocity,
    r1 -- the target position, v1 -- the target velocity, pm(tend) -- conjugate to mass variable at final time.

    `jac` : numpy.ndarray, shape (7, 7)

    The Jacobian of res, i.e. the derivative matrix of res wrt optimization variables.
    It is returned if the trust-constr method is used and None returned otherwise.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])

    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02,  2.47113618e-23])

    z0[6] = 5.55630093e-01

    switch_width = 2.5e-04

    zopt, res = optimal.solve_r2bp_pontr_mass_bnd_f_rv(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_rv(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    fig = kiam.plot(Y[0, :], Y[1, :], None, 'x', 'y', axis_equal=True)

    fig.show()

    force_value, force_vector = optimal.control_r2bp_pontr_mass_bnd_f_rv(Y, fmax, vex, switch_width)

    fig = kiam.plot(T, force_value, None, 't', 'f')

    fig.show()

    h = optimal.hamiltonian_r2bp_pontr_mass_bnd_f_rv(Y, fmax, vex, switch_width, 1.0)

    fig = kiam.plot(T, h, None, 't', 'f')

    fig.show()

    print(f'Масса: {Y[6, 0]:.2f} ---> {Y[6, -1]:.2f}, затрачивается {(1 - Y[6, -1] / Y[6, 0]) * 100:.2f}%')

    ```
    """

    if method == 'nelder-mead':

        options = {
            'disp': True,
            'maxiter': 10000,
            'return_all': False,
            'xatol': 1e-10,
            'fatol': 1e-10,
        }

        def objective(z):
            return objective_r2bp_pontr_mass_bnd_f_rv(z, x0, x1, fmax, vex, tof, switch_width, False, mu, atol, rtol)

        result = minimize(objective,
                          z0,
                          method='Nelder-Mead',
                          options=options,
                          callback=lambda x: callback_nelder_mead(x, objective))

        f = residue_r2bp_pontr_mass_bnd_f_rv(result.x, x0, x1, fmax, vex, tof, switch_width, False, mu, atol, rtol)

        return result.x, f, None

    if method == 'trust-constr':

        options = {
            'disp': True,
            'maxiter': 10000,
            'gtol': 1e-10,
            'xtol': 1e-10,
        }

        def objective(z):
            return objective_r2bp_pontr_mass_bnd_f_rv(z, x0, x1, fmax, vex, tof, switch_width, True, mu, atol, rtol)

        result = minimize(objective,
                          z0,
                          jac=True,
                          method='trust-constr',
                          options=options,
                          callback=callback_trust_constr)

        f, jac = residue_r2bp_pontr_mass_bnd_f_rv(result.x, x0, x1, fmax, vex, tof, switch_width, True, mu, atol, rtol)

        return result.x, f, jac

    if method == 'least-squares':

        def residue(z):
            return residue_r2bp_pontr_mass_bnd_f_rv(z, x0, x1, fmax, vex, tof, switch_width, False, mu, atol, rtol)

        sol = least_squares(residue,
                            z0,
                            jac='3-point',
                            method='trf',
                            ftol=1e-10,
                            xtol=1e-10,
                            gtol=1e-10,
                            verbose=2
                            )

        f = residue_r2bp_pontr_mass_bnd_f_rv(sol.x, x0, x1, fmax, vex, tof, switch_width, False, mu, atol, rtol)

        return sol.x, f, None

    raise ValueError(f'unknown method: {method}')
def propagate_r2bp_pontr_mass_bnd_f_rv(tspan: numpy.ndarray, y0: numpy.ndarray, fmax: float, vex: float, switch_width: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Propagate extended by conjugate variables equations of motion.
    Two-body problem, position-velocity variables, thrust-bounded engine model with fixed exhaust velocity, thrust force as control variable.

    Parameters:
    -----------

    `tspan` : numpy.ndarray, shape (n,)

    The times at which the solution should be obtained.

    `y0` : numpy.ndarray, shape (14,), (210,)

    The initial state.

    Structure options:

    1. [rvect, vvect, mass, lamr, lamv, lamm]

    2. [rvect, vvect, mass, lamr, lamv, lamm, stm]

    where stm is the state transition matrix.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `T` : numpy.ndarray, shape (n,)

    The times at which the solution is obtained. Equals to tspan.

    `Y` : numpy.ndarray, shape (m, n)

    The integrated solutions. Each column correspond to a vector y at the correspondent time t in T.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])

    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02,  2.47113618e-23])

    z0[6] = 5.55630093e-01

    switch_width = 2.5e-04

    zopt, res = optimal.solve_r2bp_pontr_mass_bnd_f_rv(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_rv(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    fig = kiam.plot(Y[0, :], Y[1, :], None, 'x', 'y', axis_equal=True)

    fig.show()

    ```
    """
    neq = len(y0)
    if neq == 14:
        stmreq = False
    elif neq == 210:
        stmreq = True
    else:
        raise Exception('Wrong number of dependent variables.')
    T, Y = kiam.FKIAMToolbox.propagationmodule.propagate_r2bp_pontr_mopt_bnd_f_rv(tspan, y0, neq, atol, rtol, mu, fmax, vex, switch_width, stmreq)
    return T, Y
def r2bp_pontr_mopt_bnd_f_rv(t: float, y: numpy.ndarray, stmreq: bool, fmax: float, vex: float, switch_width: float, mu: float = 1.0):
    """
    Extended equations of motion:
    Two-body problem, position-velocity variables, bounded thrust force, mass-optimal problem.

    Parameters
    -----------

    `t` : float

    Time.

    `y` : numpy.ndarray, shape (14,) or (210,)

    Vector of variables.
    Structure: [x, y, z, vx, vy, vz, m, px, py, pz, pvx, pvy, pvz, pm] or
    [x, y, z, vx, vy, vz, m, px, py, pz, pvx, pvy, pvz, pm, stm].

    `stmreq` : bool

    Whever to include station transition matrix computation.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    Returns
    -----------

    `dydt` : numpy.ndarray, shape (14,) or (210,)

    The time derivative of y.

    Examples
    ---------
    ```
    units = kiam.units('sun')

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    y = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0])

    dydt = r2bp_pontr_mopt_bnd_f_rv(0.0, y, False, fmax, vex, 0.0)

    print(dydt)
    ```
    """
    kiam.FKIAMToolbox.equationsmodule.mu_kr2bp_pontr_mopt_bnd_f = mu
    kiam.FKIAMToolbox.equationsmodule.fmax_kr2bp_pontr_mopt_bnd_f = fmax
    kiam.FKIAMToolbox.equationsmodule.vex_kr2bp_pontr_mopt_bnd_f = vex
    kiam.FKIAMToolbox.equationsmodule.switch_rate_kr2bp_pontr_mopt_bnd_f = switch_width
    kiam.FKIAMToolbox.equationsmodule.stm_required = stmreq
    return kiam.FKIAMToolbox.equationsmodule.kr2bp_pontr_mopt_bnd_f_rv(t, y)
def residue_r2bp_pontr_mass_bnd_f_rv(z: numpy.ndarray, x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, tof: float, switch_width: float, stmreq: bool, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Residue vector in boundary value problem derived for the mass-optimal control problem.
    Two-body problem, bounded thrust force and fixed exhaust velocity, thrust force as control variable, position-velocity variables.

    Parameters:
    -----------

    `z` : numpy.ndarray, shape (7,)

    Optimization variables. Structure: [px, py, pz, pvx, pvy, pvz, pm], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    pm -- confugate to mass.

    `x0` : numpy.ndarray, shape (7,)

    Initial phase state including mass. Stucture: [x, y, z, vx, vy, vz, mass].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `tof` : float

    The time of flight.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `stmreq` : bool

    True if integration of equations in variation is required. False otherwise.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `res` : numpy.ndarray, shape (7,)

    The residue. Structure: [r(tend) - r1, v(tend) - v1, pm(tend) - 1], where tend -- final time,
    r(tend) -- the final integrated position, v(tend) -- the final integrated velocity,
    r1 -- the target position, v1 -- the target velocity, pm(tend) -- conjugate to mass variable at final time.

    `jac` : numpy.ndarray, shape (7, 7)

    The Jacobian of res, i.e. the derivative matrix of res wrt optimization variables.
    Return if stmreq is True. Not returned otherwise.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])

    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02,  2.47113618e-23])

    z0[6] = 5.55630093e-01

    switch_width = 2.5e-04

    res = residue_r2bp_pontr_mass_bnd_f_rv(z0, x0, x1, fmax, vex, tof, switch_width, False)

    print(res)
    ```
    """

    T, Y = propagate_r2bp_pontr_mass_bnd_f_rv(
        tspan=numpy.array([0.0, tof]),
        y0=numpy.concatenate((x0, z, kiam.eye2vec(14))) if stmreq else numpy.concatenate((x0, z)),
        fmax=fmax,
        vex=vex,
        switch_width=switch_width,
        mu=mu,
        atol=atol,
        rtol=rtol
    )

    residue = numpy.concatenate((
        Y[0:6, -1] - x1,
        [Y[13, -1] - 1.0]
    ))

    if stmreq:
        phi = numpy.reshape(Y[14:, -1], (14, 14), order='F')
        jac = numpy.concatenate((phi[0:6, 7:14], phi[13:14, 7:14]), axis=0)
        return residue, jac
    else:
        return residue
def objective_r2bp_pontr_mass_bnd_f_rv(z: numpy.ndarray, x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, tof: float, switch_width: float, stmreq: bool, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Residue vector squared in boundary value problem derived for the mass-optimal control problem.
    Two-body problem, bounded thrust force and fixed exhaust velocity, thrust force as control variable, position-velocity variables.

    Parameters:
    -----------

    `z` : numpy.ndarray, shape (7,)

    Optimization variables. Structure: [px, py, pz, pvx, pvy, pvz, pm], where
    px, py, pz -- conjugate to x, y, z variables, pvx, pvy, pvz -- conjugate to vx, vy, vz variables,
    pm -- confugate to mass.

    `x0` : numpy.ndarray, shape (7,)

    Initial phase state including mass. Stucture: [x, y, z, vx, vy, vz, mass].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `tof` : float

    The time of flight.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `stmreq` : bool

    True if integration of equations in variation is required. False otherwise.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `obj` : numpy.ndarray, shape (7,)

    The objective = squared residue. Structure: [r(tend) - r1, v(tend) - v1, pm(tend) - 1], where tend -- final time,
    r(tend) -- the final integrated position, v(tend) -- the final integrated velocity,
    r1 -- the target position, v1 -- the target velocity, pm(tend) -- conjugate to mass variable at final time.

    `grad` : numpy.ndarray, shape (7,)

    The gradient of obj wrt optimization variables.
    Return if stmreq is True. Not returned otherwise.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])

    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02,  2.47113618e-23])

    z0[6] = 5.55630093e-01

    switch_width = 2.5e-04

    obj = objective_r2bp_pontr_mass_bnd_f_rv(z0, x0, x1, fmax, vex, tof, switch_width, False)

    print(obj)
    ```
    """

    if stmreq:
        f, jac = residue_r2bp_pontr_mass_bnd_f_rv(z, x0, x1, fmax, vex, tof, switch_width, stmreq, mu, atol, rtol)
        return norm(f)**2, jac.T @ f
    else:
        f = residue_r2bp_pontr_mass_bnd_f_rv(z, x0, x1, fmax, vex, tof, switch_width, stmreq, mu, atol, rtol)
        return norm(f)**2
def control_r2bp_pontr_mass_bnd_f_rv(y: numpy.ndarray, fmax: float, vex: float, switch_width: float):
    """
    Force vector corresponding to the solution of the extended equations of motion.

    Parameters:
    -----------

    `y` : numpy.ndarray, shape (14, N) or (210, N)

    Solution of the extended equations of motion.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    Returns:
    --------

    `force_value` : numpy.ndarray, shape (N,)

    The force absolute values.

    `force_vector` : numpy.ndarray, shape (3, N)

    The force vectors.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])

    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02,  2.47113618e-23])

    z0[6] = 5.55630093e-01

    switch_width = 2.5e-04

    zopt, res = optimal.solve_r2bp_pontr_mass_bnd_f_rv(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_rv(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    force_value, force_vector = optimal.control_r2bp_pontr_mass_bnd_f_rv(Y, fmax, vex, switch_width)

    fig = kiam.plot(T, force_value, None, 't', 'f')

    fig.show()

    ```

    """

    mass = y[6, :]
    lamv = y[10:13, :]
    lamm = y[13, :]

    lamvnorm = norm(lamv, axis=0)
    ef = lamv / lamvnorm

    switch_function = lamvnorm / mass - lamm / vex

    sigma = sigmoid(switch_function, 0.0, switch_width)

    force_value = fmax * sigma
    force_vector = ef * force_value

    return force_value, force_vector
def hamiltonian_r2bp_pontr_mass_bnd_f_rv(y: numpy.ndarray, fmax: float, vex: float, switch_width: float, mu: float):
    """
    Hamiltonian corresponding to the solution of the extended equations of motion.

    Parameters:
    -----------

    `y` : numpy.ndarray, shape (14, N) or (210, N)

    Solution of the extended equations of motion.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    Returns:
    --------

    `hamiltonian` : numpy.ndarray, shape (N,)

    The hamiltonian values.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])

    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02,  2.47113618e-23])

    z0[6] = 5.55630093e-01

    switch_width = 2.5e-04

    zopt, res = optimal.solve_r2bp_pontr_mass_bnd_f_rv(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_rv(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    h = optimal.hamiltonian_r2bp_pontr_mass_bnd_f_rv(Y, fmax, vex, switch_width, 1.0)

    fig = kiam.plot(T, h, None, 't', 'f')

    fig.show()
    ```
    """

    rvect = y[0:3, :]
    vvect = y[3:6, :]
    mass = y[6, :]

    lamr = y[7:10, :]
    lamv = y[10:13, :]
    lamm = y[13, :]

    lamvnorm = norm(lamv, axis=0)
    r = norm(rvect, axis=0)

    switch_function = lamvnorm / mass - lamm / vex
    sigma = sigmoid(switch_function, 0.0, switch_width)
    force_opt = fmax * sigma

    h = (lamr * vvect).sum(axis=0) - (mu / r ** 3) * (lamv * rvect).sum(axis=0) + force_opt * switch_function

    return h

# r2bp_pontr_mass_bnd_f_ee problem
def solve_r2bp_pontr_mass_bnd_f_ee(x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, tof: float, switch_width: float, z0: numpy.ndarray, mu: float = 1.0, method: str = 'trust-constr', atol: float = 1e-12, rtol: float = 1e-12):
    """
    Solve mass-optimal control problem by Pontryagin principle in two-body problem,
    modified equinoctical elements for thrust-bounded engine model with fixed exhaust velocity, using thrust force as control variable

    Parameters:
    -----------

    `x0` : numpy.ndarray, shape (7,)

    Initial phase state, including mass. Stucture: [h, ex, ey, ix, iy, L, m].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [h, ex, ey, ix, iy, L].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `tof` : float

    The time of flight.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `z0` : numpy.ndarray, shape(7,)

    The initial guess for the optimization variables. Structure: [ph, pex, pey, pix, piy, pL, pm].

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `method` : str

    Optimization method. Options: `'trust-constr'` (default), `'nelder-mead'`, `'least-squares'`.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `zopt` : numpy.ndarray, shape (7,)

    The optimal optimization variables. Sturcture: [ph, pex, pey, pix, piy, pL, pm].

    `res` : numpy.ndarray, shape (8,)

    The optimal residue. Structure:
    [
    h(tend) - h1,
    ex(tend) - ex1,
    ey(tend) - ey1,
    ix(tend) - ix1,
    iy(tend) - iy1,
    sin(L(tend)-L1),
    cos(L(tend)-L1) - 1,
    pm(tend) - 1.0
    ]

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)

    x1 = kiam.rv2ee(x1, 1.0, False)

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])

    z0[5] = 8.25721397e-10

    z0[6] = 5.55628531e-01

    switch_width = 1.25e-04

    zopt, res = optimal.solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_ee(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    RV = kiam.ee2rv(Y[0:6, :], 1.0, False)

    fig = kiam.plot(RV[0, :], RV[1, :], None, 'x', 'y', axis_equal=True)

    fig.show()

    force_value, force_vector = optimal.control_r2bp_pontr_mass_bnd_f_ee(Y, fmax, vex, switch_width)

    fig = kiam.plot(T, force_value, None, 't', 'f')

    fig.show()

    h = optimal.hamiltonian_r2bp_pontr_mass_bnd_f_ee(Y, fmax, vex, switch_width, 1.0)

    fig = kiam.plot(T, h, None, 't', 'f')

    fig.show()

    print(f'Масса: {Y[6, 0]:.2f} ---> {Y[6, -1]:.2f}, затрачивается {(1 - Y[6, -1] / Y[6, 0]) * 100:.2f}%')

    ```
    """

    if method == 'nelder-mead':

        options = {
            'disp': True,
            'maxiter': 10000,
            'return_all': False,
            'xatol': 1e-10,
            'fatol': 1e-10,
        }

        def objective(z):
            return objective_r2bp_pontr_mass_bnd_f_ee(z, x0, x1, fmax, vex, tof, switch_width, mu, atol, rtol)

        result = minimize(objective,
                          z0,
                          method='Nelder-Mead',
                          options=options,
                          callback=lambda x: callback_nelder_mead(x, objective))

        f = residue_r2bp_pontr_mass_bnd_f_ee(result.x, x0, x1, fmax, vex, tof, switch_width, mu, atol, rtol)

        return result.x, f

    if method == 'trust-constr':

        options = {
            'disp': True,
            'maxiter': 10000,
            'gtol': 1e-10,
            'xtol': 1e-10,
        }

        def objective(z):
            return objective_r2bp_pontr_mass_bnd_f_ee(z, x0, x1, fmax, vex, tof, switch_width, mu, atol, rtol)

        result = minimize(objective,
                          z0,
                          jac='3-point',
                          method='trust-constr',
                          options=options,
                          callback=callback_trust_constr)

        f = residue_r2bp_pontr_mass_bnd_f_ee(result.x, x0, x1, fmax, vex, tof, switch_width, mu, atol, rtol)

        return result.x, f

    if method == 'least-squares':

        def residue(z):
            return residue_r2bp_pontr_mass_bnd_f_ee(z, x0, x1, fmax, vex, tof, switch_width, mu, atol, rtol)

        sol = least_squares(residue,
                            z0,
                            jac='3-point',
                            method='trf',
                            ftol=1e-10,
                            xtol=1e-10,
                            gtol=1e-10,
                            verbose=2,
                            max_nfev=2000
                            )

        f = residue_r2bp_pontr_mass_bnd_f_ee(sol.x, x0, x1, fmax, vex, tof, switch_width, mu, atol, rtol)

        return sol.x, f

    raise ValueError(f'unknown method: {method}')
def propagate_r2bp_pontr_mass_bnd_f_ee(tspan: numpy.ndarray, y0: numpy.ndarray, fmax: float, vex: float, switch_width: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Propagate extended by conjugate variables equations of motion.
    Two-body problem, modified equinoctical elements, thrust-bounded engine model with fixed exhaust velocity, thrust force as control variable.

    Parameters:
    -----------

    `tspan` : numpy.ndarray, shape (n,)

    The times at which the solution should be obtained.

    `y0` : numpy.ndarray, shape (14,)

    The initial state.

    Structure: [h, ex, ey, ix, iy, L, m, ph, pex, pey, pix, piy, pL, pm].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `T` : numpy.ndarray, shape (n,)

    The times at which the solution is obtained. Equals to tspan.

    `Y` : numpy.ndarray, shape (14, n)

    The integrated solutions. Each column correspond to a vector y at the correspondent time t in T.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)

    x1 = kiam.rv2ee(x1, 1.0, False)

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])

    z0[5] = 8.25721397e-10

    z0[6] = 5.55628531e-01

    switch_width = 1.25e-04

    zopt, res, _ = optimal.solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_ee(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    RV = kiam.ee2rv(Y[0:6, :], 1.0, False)

    fig = kiam.plot(RV[0, :], RV[1, :], None, 'x', 'y', axis_equal=True)

    fig.show()

    ```
    """
    neq = len(y0)
    if neq == 14:
        stmreq = False
    elif neq == 210:
        raise Exception('State transition matrix computing is not suported at the moment.')
    else:
        raise Exception('Wrong number of dependent variables.')
    T, Y = kiam.FKIAMToolbox.propagationmodule.propagate_r2bp_pontr_mopt_bnd_f_ee(tspan, y0, neq, atol, rtol, mu, fmax, vex, switch_width, False)
    return T, Y
def r2bp_pontr_mopt_bnd_f_ee(t: float, y: numpy.ndarray, fmax: float, vex: float, switch_width: float, mu: float = 1.0):
    """
    Extended equations of motion:
    Two-body problem, modified equnoctical elements, bounded thrust force, mass-optimal problem.

    Parameters
    -----------

    `t` : float

    Time.

    `y` : numpy.ndarray, shape (14,)

    Vector of variables. Structure: [h, ex, ey, ix, iy, L, m, ph, pex, pey, pix, piy, pL, pm].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    Returns
    -----------

    `dydt` : numpy.ndarray, shape (14,)

    The time derivative of y.

    Examples
    ---------
    ```
    units = kiam.units('sun')

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    y = numpy.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 80.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0])

    dydt = r2bp_pontr_mopt_bnd_f_ee(0.0, y, False, fmax, vex, 0.0)

    print(dydt)
    ```
    """
    kiam.FKIAMToolbox.equationsmodule.mu_kr2bp_pontr_mopt_bnd_f = mu
    kiam.FKIAMToolbox.equationsmodule.fmax_kr2bp_pontr_mopt_bnd_f = fmax
    kiam.FKIAMToolbox.equationsmodule.vex_kr2bp_pontr_mopt_bnd_f = vex
    kiam.FKIAMToolbox.equationsmodule.switch_rate_kr2bp_pontr_mopt_bnd_f = switch_width
    kiam.FKIAMToolbox.equationsmodule.stm_required = False
    return kiam.FKIAMToolbox.equationsmodule.kr2bp_pontr_mopt_bnd_f_ee(t, y)
def residue_r2bp_pontr_mass_bnd_f_ee(z: numpy.ndarray, x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, tof: float, switch_width: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Residue vector in boundary value problem derived for the mass-optimal control problem.
    Two-body problem, bounded thrust force and fixed exhaust velocity, thrust force as control variable, modified equinoctical elements.

    Parameters:
    -----------

    `z` : numpy.ndarray, shape (7,)

    Optimization variables. Structure: [ph, pex, pey, pix, piy, pL, pm].

    `x0` : numpy.ndarray, shape (7,)

    Initial phase state including mass. Stucture: [h, ex, ey, ix, iy, L, m].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [h, ex, ey, ix, iy, L].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `tof` : float

    The time of flight.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `res` : numpy.ndarray, shape (7,)

    The residue. Structure:
    [
    h(tend) - h1,
    ex(tend) - ex1,
    ey(tend) - ey1,
    ix(tend) - ix1,
    iy(tend) - iy1,
    sin(L(tend)-L1),
    cos(L(tend)-L1) - 1,
    pm(tend) - 1.0
    ]

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)

    x1 = kiam.rv2ee(x1, 1.0, False)

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])

    z0[5] = 8.25721397e-10

    z0[6] = 5.55628531e-01

    switch_width = 1.25e-04

    zopt, res, _ = optimal.solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    residue = residue_r2bp_pontr_mass_bnd_f_ee(zopt, x0, x1, fmax, vex, tof, switch_width)

    print(f'Вектор невязок: {residue}')
    ```
    """

    T, Y = propagate_r2bp_pontr_mass_bnd_f_ee(
        tspan=numpy.array([0.0, tof]),
        y0=numpy.concatenate((x0, z)),
        fmax=fmax,
        vex=vex,
        switch_width=switch_width,
        mu=mu,
        atol=atol,
        rtol=rtol
    )

    residue = numpy.concatenate((
        Y[0:5, -1] - x1[0:5],
        [numpy.sin(Y[5, -1] - x1[5])],
        [numpy.cos(Y[5, -1] - x1[5]) - 1.0],
        [Y[13, -1] - 1.0]
    ))

    return residue
def objective_r2bp_pontr_mass_bnd_f_ee(z: numpy.ndarray, x0: numpy.ndarray, x1: numpy.ndarray, fmax: float, vex: float, tof: float, switch_width: float, mu: float = 1.0, atol: float = 1e-12, rtol: float = 1e-12):
    """
    Objective in boundary value problem derived for the mass-optimal control problem.
    Two-body problem, bounded thrust force and fixed exhaust velocity, thrust force as control variable, modified equinoctical elements.

    Parameters:
    -----------

    `z` : numpy.ndarray, shape (7,)

    Optimization variables. Structure: [ph, pex, pey, pix, piy, pL, pm].

    `x0` : numpy.ndarray, shape (7,)

    Initial phase state including mass. Stucture: [h, ex, ey, ix, iy, L, m].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [h, ex, ey, ix, iy, L].

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `tof` : float

    The time of flight.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    `atol` : float

    The absolute integration tolerance. Default: 1e-12.

    `rtol` : float

    The relative integration tolerance. Default: 1e-12.

    Returns:
    --------

    `obj` : float

    This vector squared:
    [
    h(tend) - h1,
    ex(tend) - ex1,
    ey(tend) - ey1,
    ix(tend) - ix1,
    iy(tend) - iy1,
    sin(L(tend)-L1),
    cos(L(tend)-L1) - 1,
    pm(tend) - 1.0
    ]

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)

    x1 = kiam.rv2ee(x1, 1.0, False)

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])

    z0[5] = 8.25721397e-10

    z0[6] = 5.55628531e-01

    switch_width = 1.25e-04

    zopt, res, _ = optimal.solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    obj = objective_r2bp_pontr_mass_bnd_f_ee(zopt, x0, x1, fmax, vex, tof, switch_width)

    print(f'Значение целевой функции: {obj}')
    ```
    """

    f = residue_r2bp_pontr_mass_bnd_f_ee(z, x0, x1, fmax, vex, tof, switch_width, stmreq, mu, atol, rtol)
    return norm(f)**2
def control_r2bp_pontr_mass_bnd_f_ee(y: numpy.ndarray, fmax: float, vex: float, switch_width: float):
    """
    Force vector corresponding to the solution of the extended equations of motion.

    Parameters:
    -----------

    `y` : numpy.ndarray, shape (14, N)

    Solution of the extended equations of motion.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    Returns:
    --------

    `force_value` : numpy.ndarray, shape (N,)

    The force absolute values.

    `force_vector` : numpy.ndarray, shape (3, N)

    The force vectors.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)

    x1 = kiam.rv2ee(x1, 1.0, False)

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])

    z0[5] = 8.25721397e-10

    z0[6] = 5.55628531e-01

    switch_width = 1.25e-04

    zopt, res = optimal.solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = optimal.propagate_r2bp_pontr_mass_bnd_f_ee(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    force_value, force_vector = optimal.control_r2bp_pontr_mass_bnd_f_ee(Y, fmax, vex, switch_width)

    fig = kiam.plot(T, force_value, None, 't', 'f')

    ```

    """

    npoints = y.shape[1]
    h, ex, ey, ix, iy, L, m = y[0, :], y[1, :], y[2, :], y[3, :], y[4, :], y[5, :], y[6, :]
    lamee, lamL, lamm = y[7:12, :], y[12, :], y[13, :]
    sinL = numpy.sin(L)
    cosL = numpy.cos(L)
    xi = 1 + ex * cosL + ey * sinL
    eta = ix * sinL - iy * cosL
    phi = (1 + ix ** 2 + iy ** 2) / 2
    hdxi = h / xi

    amat = numpy.zeros((5, 3, npoints))
    amat[0, 1, :] = h ** 2 / xi
    amat[1, 0, :] = h * sinL
    amat[1, 1, :] = ((xi + 1) * cosL + ex) * hdxi
    amat[1, 2, :] = - ey * eta * hdxi
    amat[2, 0, :] = - h * cosL
    amat[2, 1, :] = ((xi + 1) * sinL + ey) * hdxi
    amat[2, 2, :] = ex * eta * hdxi
    amat[3, 2, :] = phi * cosL * hdxi
    amat[4, 2, :] = phi * sinL * hdxi

    eprime = numpy.einsum('jki,ji->ki', amat, lamee)
    eprime[2, :] += h * eta / xi * lamL
    eprimenorm = norm(eprime, axis=0)
    ef = eprime / eprimenorm
    switch_function = eprimenorm / m - lamm / vex
    sigma = sigmoid(switch_function, 0.0, switch_width)
    # sigma = (switch_function > 0).astype(int)
    force_value = fmax * sigma
    force_vector = ef * force_value

    return force_value, force_vector
def hamiltonian_r2bp_pontr_mass_bnd_f_ee(y: numpy.ndarray, fmax: float, vex: float, switch_width: float, mu: float):
    """
    Hamiltonian corresponding to the solution of the extended equations of motion.

    Parameters:
    -----------

    `y` : numpy.ndarray, shape (14, N)

    Solution of the extended equations of motion.

    `fmax` : float

    The maximal thrust force of the engine.

    `vex` : float

    The exhaust velocity.

    `switch_width` : float

    The scale parameter in sigma(x) = 1/(1 + exp(-x/scale)) used for smoothing the switch function,
    scale = 0 means indicator function

    `mu` : float

    Gravitational parameter. Default: 1.0.

    Returns:
    --------

    `hamiltonian` : numpy.ndarray, shape (N,)

    The hamiltonian values.

    Examples:
    ---------
    ```
    units = kiam.units('sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)

    x1 = kiam.rv2ee(x1, 1.0, False)

    fmax = 14.8e-03 / units['AccUnit']

    vex = 9.3 / units['VelUnit']

    tof = 2.8 * numpy.pi

    z0 = numpy.zeros(7, )

    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])

    z0[5] = 8.25721397e-10

    z0[6] = 5.55628531e-01

    switch_width = 1.25e-04

    zopt, res = solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)

    print(f'Оптимальный вектор сопряженных переменных: {zopt}')

    T, Y = propagate_r2bp_pontr_mass_bnd_f_ee(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)

    h = hamiltonian_r2bp_pontr_mass_bnd_f_ee(Y, fmax, vex, switch_width, 1.0)

    fig = kiam.plot(T, h, None, 't', 'f')
    ```
    """

    npoints = y.shape[1]
    h, ex, ey, ix, iy, L, m = y[0, :], y[1, :], y[2, :], y[3, :], y[4, :], y[5, :], y[6, :]
    lamee, lamL, lamm = y[7:12, :], y[12, :], y[13, :]
    sinL = numpy.sin(L)
    cosL = numpy.cos(L)
    xi = 1 + ex * cosL + ey * sinL
    eta = ix * sinL - iy * cosL
    phi = (1 + ix ** 2 + iy ** 2) / 2
    hdxi = h / xi
    b = xi**2  / h**3 / mu

    amat = numpy.zeros((5, 3, npoints))
    amat[0, 1, :] = h ** 2 / xi
    amat[1, 0, :] = h * sinL
    amat[1, 1, :] = ((xi + 1) * cosL + ex) * hdxi
    amat[1, 2, :] = - ey * eta * hdxi
    amat[2, 0, :] = - h * cosL
    amat[2, 1, :] = ((xi + 1) * sinL + ey) * hdxi
    amat[2, 2, :] = ex * eta * hdxi
    amat[3, 2, :] = phi * cosL * hdxi
    amat[4, 2, :] = phi * sinL * hdxi

    eprime = numpy.einsum('jki,ji->ki', amat, lamee)
    eprime[2, :] += h * eta / xi * lamL
    eprimenorm = norm(eprime, axis=0)
    switch_function = eprimenorm / m - lamm / vex
    sigma = sigmoid(switch_function, 0.0, switch_width)
    # sigma = (switch_function > 0).astype(int)
    force_value = fmax * sigma

    h = force_value * switch_function + lamL * b

    return h

# Auxiliary functions
def callback_nelder_mead(x: numpy.ndarray, objective: Callable):
    """
    Auxiliary callback function for the scipy's Nelder-Mead routine.

    `x` : numpy.ndarray, shape (n,)

    Vector of optimization variables.

    `objective` : Callable

    Objective function.

    Returns:
    --------

    Prints the value of the objective funtion at x.

    """
    residue_norm = objective(x)
    print(f'{residue_norm}')
def callback_trust_constr(x: numpy.ndarray, state: Any):
    """
    Auxiliary callback function for the scipy's 'trust-constr' method.

    `x` : numpy.ndarray, shape (n,)

    Vector of optimization variables.

    `state` : Any

    Object that contains information about the current state of the optimization procedure.

    Returns:
    --------

    Prints the iteration number, objective value, constraints violation, and optimality value.

    """
    print('{0:4d}   {1: 3.6e}   {2: 3.6e}   {3: 3.6e}'.format(state.nit, state.fun, state.constr_violation, state.optimality))
def estimate_tof(x0: numpy.ndarray, x1: numpy.ndarray, umax: float, mu: float = 1.0):
    """
    Estimate the time of flight in the low-thrust control problem.

    `x0` : numpy.ndarray, shape (6,)

    Initial phase state. Stucture: [x, y, z, vx, vy, vz].

    `x1` : numpy.ndarray, shape (6,)

    Target phase state. Stucture: [x, y, z, vx, vy, vz].

    `umax` : float

    Maximal thrust control acceleration.

    `mu` : float

    Gravitational parameter. Default: 1.0.

    Returns:
    --------

    `tof` : float

    The estimated time of flight.

    Examples:
    ---------
    ```
    units = kiam.units('Sun')

    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])

    fmax = 14.8e-03 / units['AccUnit']

    mass0 = 80

    tof = optimal.estimate_tof(x0, x1, fmax / mass0)
    ```
    """
    oe0 = kiam.rv2oe(x0, mu, False)
    oe1 = kiam.rv2oe(x1, mu, False)
    p0 = oe0[0] * (1 - oe0[1] ** 2)
    p1 = oe1[0] * (1 - oe1[1] ** 2)
    tof = (sqrt(mu / p0) - sqrt(mu / p1)) / umax
    return tof

def test_rv():
    units = kiam.units('sun')
    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])
    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])
    fmax = 14.8e-03 / units['AccUnit']
    vex = 9.3 / units['VelUnit']
    tof = 2.8 * numpy.pi
    z0 = numpy.zeros(7, )
    z0[0:3] = numpy.array([1.41454267e+02, -1.69272674e+00, -4.26704189e-23])
    z0[3:6] = numpy.array([-1.69272675e+00, 1.41378451e+02, 2.47113618e-23])
    z0[6] = 5.55630093e-01
    switch_width = 2.5e-04
    zopt, res, _ = solve_r2bp_pontr_mass_bnd_f_rv(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)
    print(f'Оптимальный вектор сопряженных переменных: {zopt}')
    T, Y = propagate_r2bp_pontr_mass_bnd_f_rv(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)
    fig = kiam.plot(Y[0, :], Y[1, :], None, 'x', 'y', axis_equal=True)
    fig.show()
    force_value, force_vector = control_r2bp_pontr_mass_bnd_f_rv(Y, fmax, vex, switch_width)
    fig = kiam.plot(T, force_value, None, 't', 'f')
    fig.show()
    h = hamiltonian_r2bp_pontr_mass_bnd_f_rv(Y, fmax, vex, switch_width, 1.0)
    fig = kiam.plot(T, h, None, 't', 'f')
    fig.show()
    print(f'Масса: {Y[6, 0]:.2f} ---> {Y[6, -1]:.2f}, затрачивается {(1 - Y[6, -1] / Y[6, 0]) * 100:.2f}%')
def test_ee():
    units = kiam.units('sun')
    x0 = numpy.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 80.0])
    x1 = numpy.array([1.5, 0.0, 0.0, 0.0, 1 / numpy.sqrt(1.5), 0.0])
    x0[0:6] = kiam.rv2ee(x0[0:6], 1.0, False)
    x1 = kiam.rv2ee(x1, 1.0, False)
    fmax = 14.8e-03 / units['AccUnit']
    vex = 9.3 / units['VelUnit']
    tof = 2.8 * numpy.pi
    z0 = numpy.zeros(7, )
    z0[0:3] = numpy.array([1.41530246e+02, -7.69020160e-02,  1.69380406e+00])
    z0[5] = 8.25721397e-10
    z0[6] = 5.55628531e-01
    switch_width = 0.0
    zopt, res = solve_r2bp_pontr_mass_bnd_f_ee(x0, x1, fmax, vex, tof, switch_width, z0, 1.0, method='least-squares', atol=1e-10, rtol=1e-10)
    print(f'Оптимальный вектор сопряженных переменных: {zopt}')
    T, Y = propagate_r2bp_pontr_mass_bnd_f_ee(numpy.linspace(0.0, tof, 10000), numpy.concatenate((x0, zopt)), fmax, vex, switch_width)
    RV = kiam.ee2rv(Y[0:6, :], 1.0, False)
    fig = kiam.plot(RV[0, :], RV[1, :], None, 'x', 'y', axis_equal=True)
    fig.show()
    force_value, force_vector = control_r2bp_pontr_mass_bnd_f_ee(Y, fmax, vex, switch_width)
    fig = kiam.plot(T, force_value, None, 't', 'f')
    fig.show()
    h = hamiltonian_r2bp_pontr_mass_bnd_f_ee(Y, fmax, vex, switch_width, 1.0)
    fig = kiam.plot(T, h, None, 't', 'f')
    fig.show()
    print(f'Масса: {Y[6, 0]:.2f} ---> {Y[6, -1]:.2f}, затрачивается {(1 - Y[6, -1] / Y[6, 0]) * 100:.2f}%')

test_ee()