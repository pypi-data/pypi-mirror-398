"""
Author: Andy Zapata
Date:   21/10/25

This version:
    *) Gaussian runs on tcsh shell
    *) Dirac and Dalton runs on bash shell
    *) Dalton and Dirac work only with closed shell systems
"""

from datetime import datetime
from math import exp

from pyascec.cluster import Cluster


def maxv(lista: list[list[str, float, float, float, ...], ...]) -> float:
    """
    Get maximum value from a list which has float and string values
    """
    maxt = 0
    for mol in lista:
        for x in mol:
            if isinstance(x, str):
                continue
            if abs(x) > abs(maxt):
                maxt = x
    return maxt


class ASCEC:
    """
    Driver of the ASCEC calculation

    Paramters
    ---------
    system: (object)
            Object of the class cluster
    length: (float)
            Cubic edge that encloses the cluster under study.
            By default, the program adds 4 Å to the highest coordinate.
    route: (int)
            Quenching rout 1: linear, 2: geometrical.
            The default value is 2.
    i_temp: (float)
            Initial temperature.
            The default value is 500 K.
    n_temp: (int)
            Number of the temperatures.
            The default value is 200.
    d_temp: (float)
            Step between temperatures.
            The default value is 2%.
    max_cycles: (int)
            Maximum number of cycles of the interactions of the ASCEC
            algorithm by temperature.
            The default value is 2500.
    max_r: (float)
            Maximum displacement in Å.
            The default value is 1.0 Å.
    max_a: (float)
            Maximum rotation angle. The default value is 1. radians.
    seed: (int)
           seed to make random number.
           The default value is minutes:second:#day.
    """

    def __init__(
        self,
        # System configuration
        system: Cluster | None = None,
        # End Configuration ########################
        # ASCEC Configuration
        length: float = -1.0,
        route: int = 2,
        i_temp: float = 500.0,
        n_temp: int = 200,
        d_temp: float = 2,
        max_cycles: int = 2500,
        max_r: float = 1.0,
        max_a: float = 1.0,
        seed: int = int(datetime.now().strftime("%M%S%d")),
        # End Configuration ##########################
    ) -> None:
        if system is None:
            raise ValueError("*** Please input the cluster under study.")
        if not isinstance(system, Cluster):
            raise TypeError("*** The cluster variable might be a cluster object")
        self.cluster = system
        #####################*  ASCEC Configuration  *#########################
        self.length = length
        if self.length == -1.0:
            self.length = 4.0
        self.route = route
        self.i_temp = i_temp
        self.n_temp = n_temp
        self.d_temp = d_temp
        self.max_cycles = max_cycles
        self.max_r = max_r
        self.max_a = max_a
        self.seed = seed
        #####################*   End Configuration *###########################
        self.center_cube = system.mass_center

    def move_energy(
        self, geometry, cycle, max_cycles
    ) -> tuple[int, float, list[list[str, float, float, float]]]:
        """
        Move the cluster until get any electronic energy value

        Parameters
        ----------
        geometry: (list[list[str,float,float,float,str,...],...])
                        #! Please, respect the format.
                    Geometry under study.
        cycle: (int)
                    Number of cycle
        """
        # * Energy evaluation until a normal termination
        done = 0
        while done == 0 and cycle < max_cycles:
            done, energy = self.cluster.single_point(geometry)
            if done == 0:
                self.seed, geometry = self.cluster.move_cluster(
                    geometry,
                    self.center_cube,
                    self.length,
                    self.max_r,
                    self.max_a,
                    self.seed,
                )
            cycle += 1
        # * End energy evaluation
        return cycle, energy, geometry

    def pes_exp(self) -> tuple[[float], [[[str, float, float, float]]]]:
        """
        Start potential energy surface exploration using ascec algorithm
        """
        kb = 3.1668e-6
        cluster_accept = []
        energy_accept = []
        icluster = self.cluster.geometry

        # * Initial energy and cluster
        cycle, energy, icluster = self.move_energy(icluster, 0, 500)
        print(f"Energy of structure inital {energy} a.u. (#cycles: {cycle})")
        cluster_accept.append(icluster)
        energy_accept.append(energy)
        # * end
        energy = 0.0
        temp_i = self.i_temp
        iT = 0
        ######################### ! Core ASCEC ! #############################
        while iT < self.n_temp:
            cycle = 0
            while cycle < self.max_cycles:
                # * Energy evaluation until a normal termination
                self.seed, new_geometry = self.cluster.move_cluster(
                    cluster_accept[-1],
                    self.center_cube,
                    self.length,
                    self.max_r,
                    self.max_a,
                    self.seed,
                )
                cycle, energy, icluster = self.move_energy(
                    new_geometry,
                    cycle,
                    self.max_cycles,
                )
                # * End energy evaluation
                deltaE = energy - energy_accept[-1]
                # * Accept and exit of MaxCycles
                if deltaE < 0.0:
                    energy_accept.append(energy)
                    cluster_accept.append(icluster)
                    print(f"*** Structure Accepted\nE={energy}a.u. (DE<0)")
                    print(f"*** Temperature {temp_i}K and #Cycle {cycle}")
                    cycle = self.max_cycles
                # * End
                # * Accept structure according modified metropolis and pass
                # * to another cycle
                if deltaE > 0.0 and exp(-deltaE / (kb * temp_i)) > deltaE / energy:
                    energy_accept.append(energy)
                    cluster_accept.append(icluster)
                    print(f"*** Structure Accepted\nE={energy}a.u. (DE>0)")
                    print(f"*** Temperature {temp_i}K and #Cycle {cycle}")
                # * End
            # * Next Temperature
            iT += 1
            if self.route == 1:
                # * lineal route
                temp_i -= self.d_temp * iT
            else:
                # * Geometrical route
                temp_i -= self.d_temp * temp_i / 100
            # * End
        ####################### ! End Core ASCEC ! ############################
        return energy_accept, cluster_accept


# if __name__ == "__main__":
