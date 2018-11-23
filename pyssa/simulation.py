"""
    Naive implementation of the Gillespie algorithm (direct method) in Numba
"""

from typing import List, Optional
from warnings import warn

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from .direct_naive import direct_naive
from .results import Results


class Simulation:
    """
        A main class for running simulations

        Parameters
        ---------
        react_stoic : (nr, ns) ndarray
            A 2D array of the stoichiometric coefficients of the reactants.
            Reactions are rows and species are columns.
        prod_stoic : (nr, ns) ndarray
            A 2D array of the stoichiometric coefficients of the products.
            Reactions are rows and species are columns.
        init_state : (ns,) ndarray
            A 1D array representing the initial state of the system.
        k_det : (nr,) ndarray
            A 1D array representing the deterministic rate constants of the
            system.
        volume : float, optional
            The volume of the reactor vessel which is important for second
            and higher order reactions. Defaults to 1 arbitrary units.
        chem_flag : bool, optional
            If True, divide by Na while calculating stochastic rate constants.
            Defaults to False.

        Attributes
        ---------
        results : Results
            The results instance

        Raises
        ------
        ValueError
            If supplied with order > 3.

        References
        ----------
        1. Gillespie, D.T., 1976. A general method for numerically
        simulating the stochastic time evolution of coupled chemical
        reactions. J. Comput. Phys. 22, 403–434.
        doi:10.1016/0021-9991(76)90041-3.
        2. Cao, Y., Gillespie, D.T., Petzold, L.R., 2006.
        Efficient step size selection for the tau-leaping simulation
        method. J. Chem. Phys. 124, 044109. doi:10.1063/1.2159468
        3. Gupta, A., 2013. Parameter estimation in deterministic
        and stochastic models of biological systems. University of
        Wisconsin-Madison.

        Examples
        --------
        >>> V_r = np.array([[1,0,0],[0,1,0]])
        >>> V_p = np.array([[0,1,0],[0,0,1]])
        >>> X0 = np.array([10,0,0])
        >>> k = np.array([1,1])
        >>> [_, _, status] = direct_naive(V_r, V_p, X0, k, max_t = 1, max_iter = 100)
    """

    _results: Optional[Results] = None

    def __init__(
        self,
        react_stoic: np.ndarray,
        prod_stoic: np.ndarray,
        init_state: np.ndarray,
        k_det: np.ndarray,
        chem_flag: bool = False,
        volume: float = 1.0,
    ) -> None:
        self._react_stoic = react_stoic
        self._prod_stoic = prod_stoic
        self._init_state = init_state
        self._k_det = k_det
        self._chem_flag = chem_flag
        self._nr = self._react_stoic.shape[0]
        self._ns = self._react_stoic.shape[1]
        self._volume = volume
        self._orders = np.sum(
            self._react_stoic, 1
        )  # Order of rxn = number of reactants
        self._check_consistency()

    def _check_consistency(self):
        if (self._nr != self._prod_stoic.shape[0]) or (
            self._ns != self._prod_stoic.shape[1]
        ):
            raise ValueError("react_stoic and prod_stoic should be the same shape.")
        if np.any(self._react_stoic < 0):
            raise ValueError("react_stoic cannot have negative elements.")
        if np.any(self._prod_stoic < 0):
            raise ValueError("V_p cannot have negative elements.")
        if np.any(self._init_state < 0):
            raise ValueError("Initial numbers in X0 can't be negative.")
        if np.any(self._k_det < 0):
            raise ValueError("Rate constant(s) can't be negative.")
        if self._k_det.shape[0] != self._nr:
            raise ValueError("Number of rate constants must equal number of reactions")
        if self._chem_flag not in (True, False):
            raise ValueError("chem_flag must be a boolean True or False.")
        if np.max(self._orders) > 3:
            raise ValueError("Order greater than 3 not suppported.")

    @property
    def results(self) -> Optional[Results]:
        """
            The ``Results`` instance of the simulation

            Returns
            -------
            Optional[Results]
        """
        if self._results is None:
            warn("Run `Simulation.simulate` before requesting the results object")
            return self._results
        else:
            return self._results

    def simulate(
        self,
        max_t: float = 10.0,
        max_iter: int = 1000,
        volume: float = 1.0,
        seed: Optional[List[int]] = None,
        n_rep: int = 1,
        algorithm: str = "direct_naive",
        **kwargs,
    ):
        """
        Run the simulation

        Parameters
        ----------
        max_t : float, optional
            The end time of the simulation
            The default is 10.0
        max_iter : int, optional
            The maximum number of iterations of the simulation loop. The
            The default is 1000 iterations.
        volume : float, optional
            The volume of the system
            The default value is 1.0
        seed : List[int], optional
            The list of seeds for the simulations
            The length of this list should be equal to `n_rep`
            The default value is None
        n_rep : int, optional
            The number of repetitions of the simulation required
            The default value is 1
        algorithm : str, optional
            The algorithm to be used to run the simulation
            The default value is "direct_naive"

        Returns
        -------
        t : float
            End time of the simulation.
        Xt : ndarray
            System state at time `t` and initial.
        status : int
            Indicates the status of the simulation at exit.
            1 : Succesful completion, terminated when `max_iter` iterations reached.
            2 : Succesful completion, terminated when `max_t` crossed.
            3 : Succesful completion, terminated when all species went extinct.
            -1 : Failure, order greater than 3 detected.
            -2 : Failure, propensity zero without extinction.
        """
        tlist = []
        xlist = []
        status_list = []

        if seed is not None:
            if n_rep != len(seed):
                raise ValueError("Seed should be as long as n_rep")
        else:
            seed = [index for index in range(n_rep)]

        if algorithm == "direct_naive":
            for index in range(n_rep):
                t, X, status = direct_naive(
                    self._react_stoic,
                    self._prod_stoic,
                    self._init_state,
                    self._k_det,
                    max_t,
                    max_iter,
                    volume,
                    seed[index],
                    self._chem_flag,
                )
                tlist.append(t)
                xlist.append(X)
                status_list.append(status)
            self._results = Results(tlist, xlist, status_list, algorithm, seed)
        else:
            raise ValueError("Requested algorithm not supported")

    def plot(self, disp: bool = True):
        if self._results is None:
            raise ValueError("Simulate not run.")
        else:
            # colmap = cm.get_cmap("Pastel1")
            # print(colmap)
            # cols = plt.cm.Pastel1
            prop_cycle = plt.rcParams['axes.prop_cycle']
            colors = prop_cycle.by_key()['color']
            print(colors)

            res = self._results
            for ind in range(len(res.status_list)):
                for index2 in range(self._ns):
                    plt.plot(res.t_list[ind], res.x_list[ind][:, index2], color=colors[index2])
            if disp:
                plt.show()
