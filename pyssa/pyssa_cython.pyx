"""
    Naive implementation of the Gillespie algorithm (direct method) in Cython
"""

from cpython cimport bool

import cython
import numpy as np
cimport numpy as np


Na = 6.023e23  # Avogadro's constant


@cython.boundscheck(False)
@cython.wraparound(False)
cdef (int, int) cy_roulette_selection(np.ndarray[np.float_t, ndim=1] prop_list, np.ndarray[np.int_t, ndim=1] Xt):
    """Perform roulette selection on the list of propensities"""
    cdef double prop0 = prop_list.sum()  # Sum of propensities
    cdef int status
    if prop0 == 0:
        if Xt.sum() == 0:
            status = 3
            return -1, status
        else:
            status = -2
            return -1, status
    cdef np.ndarray[np.float_t, ndim=1] prop = prop_list / prop0  # Normalize propensities to be < 1
    # Concatenate 0 to list of probabilities
    cdef np.ndarray[np.float_t, ndim=1] probs = prop.cumsum()
    cdef float r1 = np.random.random() # Roll the wheel
    # Identify where it lands and update that reaction
    cdef int ind1
    for ind1 in range(len(probs)):
        if r1 <= probs[ind1]:
            return ind1, 0


@cython.boundscheck(False)
@cython.wraparound(False)
cdef np.ndarray[np.float_t, ndim=1] cy_get_kstoc(
        np.ndarray[np.float_t, ndim=1] k_det,
        np.ndarray[np.int_t, ndim=2] V_r,
        float volume = 1.0,
        bool chem_flag = False
):
    """Compute k_stoc from k_det"""
    cdef double Na = 6.023e23  # Avogadro's constant
    cdef int nr = V_r.shape[0]  # Number of reactions
    cdef np.ndarray[np.int_t, ndim=1] orders = np.sum(V_r, 1)  # Order of rxn = number of reactants
    cdef np.ndarray[np.float_t, ndim=1] k_stoc = np.zeros_like(k_det, dtype=np.float)
    cdef double factor
    if chem_flag:
        factor = Na
    else:
        factor = 1.0
    cdef int ind
    for ind in range(nr):
        # If highest order is 3
        if V_r[ind, :].max() == 3:
            k_stoc[ind] = k_det[ind] * 6 / np.power(factor * volume, 2)
        elif V_r[ind, :].max() == 2:  # Highest order is 2
            k_stoc[ind] = k_det[ind] * 2 / np.power(factor * volume, orders[ind] - 1)
        else:
            k_stoc[ind] = k_det[ind] / np.power(factor * volume, orders[ind] - 1)
    return k_stoc


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef cy_direct_naive(
    np.ndarray[np.int_t, ndim=2] V_r,
    np.ndarray[np.int_t, ndim=2] V_p,
    np.ndarray[np.int_t, ndim=1] X0,
    np.ndarray[np.float_t, ndim=1] k_det,
    float max_t = 1.0,
    long max_iter = 100,
    float volume = 1.0,
    bool chem_flag = False,
    int seed = 0
):
    """Naive implementation of the Direct method"""
    cdef int ite = 1  # Iteration counter
    cdef double t = 0.0  # Time in seconds
    cdef int nr = V_r.shape[0]  # Number of reactions
    cdef int ns = V_r.shape[1]  # Number of species

    if (nr != V_p.shape[0]) or (ns != V_p.shape[1]):
        raise ValueError('V_r and V_p should be the same shape.')

    if (nr != k_det.shape[0]):
        raise ValueError('Number of elements in k_det must equal\
         number of rows in V_r.')

    if np.any(V_r < 0):
        raise ValueError('V_r cannot have negative elements.')

    if np.any(V_p < 0):
        raise ValueError('V_p cannot have negative elements.')

    if np.any(X0 < 0):
        raise ValueError('Initial numbers in X0 can\'t be negative.')

    if np.any(k_det < 0):
        neg_indices = np.where(k_det < 0)[0]
        raise ValueError('Rate constant(s) at position(s) ' + str(neg_indices) + ' are negative.')

    V = V_p - V_r  # nr x ns
    cdef np.ndarray[np.int_t, ndim=1] Xt = X0.copy()  # Number of species at time t
    cdef np.ndarray[np.int_t, ndim=1] Xtemp = np.zeros(nr, dtype=int)  # Temporary X for updating
    cdef np.ndarray[np.float_t, ndim=1] kstoc = np.zeros(nr)  # Stochastic rate constants
    cdef np.ndarray[np.int_t, ndim=1] orders = np.sum(V_r, 1)  # Order of rxn = number of reactants
    cdef int status = 0
    np.random.seed(seed=seed)  # Set the seed

    if orders.max() > 3:
        raise ValueError('Order greater than 3 detected.')

    # Determine kstoc from kdet and the highest order or reactions
    kstoc = cy_get_kstoc(k_det, V_r, volume, chem_flag)
    prop = kstoc.copy()  # Vector of propensities

    while ite < max_iter:
        # Calculate propensities
        for ind1 in range(nr):
            for ind2 in range(ns):
                # prop = kstoc * product of (number raised to order)
                prop[ind1] *= np.power(Xt[ind2], V_r[ind1, ind2])
        # Roulette wheel
        choice, status = cy_roulette_selection(prop, Xt)
        if status == 0:
            Xtemp = Xt + V[choice, :]
        else:
            return t, Xt, status

        # If negative species produced, reject step
        if Xtemp.min() < 0:
            continue
        # Update Xt and t
        else:
            Xt = Xtemp
            r2 = np.random.rand()
            t += 1 / prop.sum() * np.log(1 / r2)
            if t > max_t:
                status = 2
                print("Reached maximum time (t = )", t)
                return t, Xt, status
        prop = kstoc.copy()
        ite += 1
    status = 1
    return t, Xt, status