"""
Andy Zapata
26/12/2026

This version:
    *) Used the same bases set for all fragments/atoms
    *) Respect formate of basis set for DIRAC and DALTON, for example,
        sto-3g is STO-3G
        dyall.cv2z is dyall.cv2z
    *) Dalton and Dirac work only with closed shell systems
"""

from datetime import datetime

from pyascec.fungeom import *
from pyascec.driver_cale import *


def empty_list(lista: list, message: str) -> None:
    """
    Check if a list is empty
    """
    if len(lista) == 0:
        raise ValueError(message)


class Cluster:
    """
    System of studio

    Parameters
    ----------
    cluster: (list[list[str,float,float,float,str,...],...])
            #! Please, respect the format.
            System under study. Each sublist represents a fragment that
            can interact with others through intermolecular interactions
            without undergoing a reaction.
    charge: (int)
            Molecular charge.
            The default value is 0.
    mult: (int)
            Spin multiplicity.
            The default value is 1.
    # ! Wave function
    meth: (str)
           Methodology to calculate the energy.
           The default value is HF (Hartree-Fock).
           For DFT methodology please used the following nomenclature:
                            DFTFunctional
    bas: (str)
            Basis set.
            The default value is sto-3g.
    # ! Electronic Structure Program
    ic: (int)
            Selection the program which calculates the electronic energy (1:Gaussian,
            2:Dalton, and 3:Dirac).
            The default value is 1.
    alias: (str)
            Code alias of the program.
            The default value is g09.
    scratch: (str)
            Scratch path
    nproc: (int)
            Number of processors
            The default value is 1.
    mem: (float)
            Quantity of ram memory by processor.
            The default value of the program.
    """

    def __init__(
        self,
        geometry: list[list[str, float, float, float]] = [],
        charge: int = 0,
        mult: int = 1,
        # Electronic structure program configuration
        ic: int = 1,
        alias: str = "g09",
        scratch: str = "",
        nproc: int = 1,
        mem: float = 0.0,
        meth: str = "HF",
        bas: str = "STO-3G",
        # End Configuration ########################
    ) -> None:
        empty_list(geometry, "*** Please input the geometry under study.")
        if not isinstance(geometry, list):
            raise TypeError(
                "*** The geometry variable might be a list[list['str',float,float, float, 'str', ...], ....]"
            )
        self.geometry = geometry
        self.charge = charge
        self.mult = mult
        self.natoms = 0
        for ifrag in geometry:
            self.natoms += len(ifrag) // 4
        ##############* Electronic Energy Calc. Configurations *################
        self.ic = ic
        self.alias = alias
        self.scratch = scratch
        self.nproc = nproc
        self.mem = mem
        self.meth = meth
        if "DFT" in meth.upper():
            print("Nomenclature for DFT methodologies:\nDFTFunctional (DFTB3LYP)")
        self.bas = bas
        #####################*    End Configuration    *#######################
        label = []
        xyz = []
        for frag in geometry:
            natoms = len(frag) // 4
            for ia in range(natoms):
                ia0 = ia * 4
                label.append(frag[ia0])
                xyz += frag[ia0 + 1 : ia0 + 4]
        self.label = label
        self.xyz = xyz
        self.mass_center = cm(self.label, self.xyz)

    # *#########################################################################
    # *                         METHODS
    # *#########################################################################
    def move_cluster(
        self,
        geometry: list[list[str, float, float, float]] = [],
        center_cube: list[float, float, float] = [],
        length: float = 4.0,
        max_r: float = 1.0,
        max_a: float = 1.0,
        seed: int = int(datetime.now().strftime("%M%S%d")),
    ) -> tuple[int, list[list[str, float, float, float]]]:
        """
        Move the geometry of each fragment within the cube

        Parameters
        ----------
        geometry: (list[list[str,float,float,float,str,...],...])
                        #! Please, respect the format.
                    Geometry under study.
        center_cube: ([float,float,float])
                    Center of cube where system evolutions
        length: (float)
                    Cubic edge that encloses the cluster under study.
                    By default, the program adds 4 Å to the highest coordinate.
        max_r: (float)
                    Maximum displacement in Å.
                    The default value is 1.0 Å.
        max_a: (float)
                    Maximum rotation angle. The default value is 1. radians.
        seed: (int)
                    seed to make random number
                    The default value is minutes:second:#day.
        """
        empty_list(geometry, "*** Please input the cluster geometry.")
        empty_list(geometry, "*** Please input the cubic center.")
        seed, new_geometry = move_geom_cluster(
            geometry, center_cube, length, max_r, max_a, seed
        )
        return seed, new_geometry

    def single_point(
        self, geometry: list[list[str, float, float, float]] = []
    ) -> tuple[int, float]:
        """
        Get electronic energy
        """
        done, energy = cale(
            geometry,
            self.ic,
            self.alias,
            self.scratch,
            self.meth,
            self.bas,
            self.charge,
            self.mult,
            self.nproc,
            self.mem,
        )
        return done, energy
