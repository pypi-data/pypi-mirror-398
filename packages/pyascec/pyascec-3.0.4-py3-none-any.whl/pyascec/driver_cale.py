"""
Andy Zapata
21/12/2025
"""

import subprocess

from pyascec.atomic_charge import acharge

wavedirac = """#
**DIRAC
.TITLE
 WV
.WAVE FUNCTION
**INTEGRALS
.NUCMOD
 1
**WAVE FUNCTIONS
"""

wavedal = """**DALTON INPUT
.RUN WAVE
*MOLBAS
.UNCONT
**WAVE FUNCTIONS
"""


def write_atoms(f, geometry) -> None:
    """
    Write atoms in input file
    """
    for frag in geometry:
        natoms = len(frag) // 4
        for ia in range(natoms):
            ia0 = ia * 4
            f.write(f" {frag[ia0]} {frag[ia0+1]} {frag[ia0+2]} {frag[ia0+3]}\n")


def en_gaussian(
    geometry, alias, meth, bas, charge, mult, nproc, mem
) -> tuple[int, float]:
    """
    Gaussian inputs and electronic energy calculation
    """
    # * .com file
    if "DFT" in meth.upper():
        meth.replace("DFT", "")
    with open("en_gauss.com", "w") as f:
        if mem > 0.0:
            f.write(f"%mem={mem*nproc}GB\n")
        f.write(f"%nproc={nproc}\n")
        f.write(f"# {meth}/{bas}\n\n")
        f.write("Single Point Calculation with Gaussian\n\n")
        f.write(f"{charge} {mult}\n")
        write_atoms(f, geometry)
        f.write("\n")
    # * End com

    # * Execution of gaussian ######
    subprocess.run(
        f"{alias} en_gauss.com", shell=True, executable="/bin/tcsh", check=False
    )
    # * End calculation ############

    # * Read energy from .log ######
    value = subprocess.run(
        "grep termination en_gauss.log | sed s/termination.*//",
        shell=True,
        capture_output=True,
        check=False,
    ).stdout.decode("utf-8")
    value = value.replace(" ", "").replace("\n", "")
    # * End read ##################

    if value != "Normal":
        done = 0
        energy = 0.0
    else:
        done = 1
        # * Read energy
        energy = float(
            subprocess.run(
                "grep Done: en_gauss.log | sed s/.*=// | sed s/A.U.*//",
                shell=True,
                capture_output=True,
                check=False,
            ).stdout
        )
        # * End
    return done, energy


def moldal(geometry, bas, charge) -> None:
    """
    Made .mol file for Dalton program

    Parameter
    ---------
    geometry: (list[list[str, float, float, float, ...], ...])
            list with symbol and coordinates
    bas: (str)
         basis for all the molecule
    charge: int
        molecular charge
    """
    natoms = 0
    for frag in geometry:
        natoms += len(frag) // 4

    with open("mol_dalton.mol", "w") as f:
        f.write("ATOMBASIS\n")
        f.write("ASCEC\n\n")

        f.write(f"Angstrom Atomtypes={natoms} Generators=0 Charge={charge}\n")
        for frag in geometry:
            natoms = len(frag) // 4
            for ia in range(natoms):
                ia0 = ia * 4
                z = list(acharge.keys())[list(acharge.values()).index(frag[ia0])]
                f.write(f"Charge={z} Atoms=1 Basis={bas}\n")
                f.write(f"{frag[ia0]} {frag[ia0+1]} {frag[ia0+2]} {frag[ia0+3]}\n")
        f.write("FINISH")


def en_dalton(
    geometry, alias, meth, bas, charge, scratch, nproc, mem
) -> tuple[int, float]:
    """
    Dalton input and electronic energy calculation
    """
    # * .dal file
    with open("en_dalton.dal", "w") as f:
        f.write(wavedal)
        # * Wave function methodology
        if "DFT" in meth.upper():
            meth.replace("DFT", "")
            f.write(".DFT\n")
            f.write(f"{meth}\n")
        else:
            f.write(f".{meth.upper()}\n")
        # * End methodology
        f.write("**END OF INPUT")
    # * End .inp

    # * .mol file
    moldal(geometry, bas, charge)
    # * End .mol

    # * Execution of dalton
    command = f"{alias} -noarch -t {scratch}"
    if mem != 0.0:
        command += f" -mem {mem}"
    if nproc > 1:
        command += f" -mpi {nproc}"
    command += " en_dalton.dal mol_dalton.mol"
    subprocess.run(command, shell=True, check=False)
    # * End calculation

    # * does calculation done?
    value = subprocess.run(
        "grep 'Converged SCF energy' en_dalton_mol_dalton.out | awk '{print $2}'",
        shell=True,
        capture_output=True,
        check=False,
    ).stdout.decode("utf-8")
    value = value.replace(" ", "").replace("\n", "")
    # * End done

    if value.upper() != "CONVERGED":
        done = 0
        energy = 0.0
    else:
        done = 1
        # * Read energy
        energy = float(
            subprocess.run(
                "grep 'Electronic energy:' en_dalton_mol_dalton.out | awk '{print $4}'",
                shell=True,
                capture_output=True,
                check=False,
            ).stdout
        )
        # * End
    return done, energy


def en_dirac(
    geometry, alias, meth, bas, charge, scratch, nproc, mem
) -> tuple[int, float]:
    """
    Dirac input and electronic energy calculation
    """
    # * .inp file
    with open("en_dirac.inp", "w") as f:
        f.write(wavedirac)
        # * Wave function methodology
        if "DFT" not in meth.upper():
            if "HF" or "DHF" in meth.upper():
                f.write(".SCF\n")
            else:
                f.write(f".{meth}\n")
        f.write("*SCF\n.INTFLG\n 1 1 0\n.MAXITR\n 50\n")
        if "DFT" in meth.upper():
            meth.replace("DFT", "")
            f.write("**HAMILTONIAN\n")
            f.write(f".DFT\n{meth}\n")
        # * End WF
        # * Molecule specifications
        f.write(f"**MOLECULE\n*CHARGE\n.CHARGE\n {charge}\n")
        f.write("*SYMMETRY\n.NOSYM\n")
        f.write(f"*BASIS\n.DEFAULT\n {bas}\n")
        f.write("*COORDINATES\n.UNITS\n AU\n")
        f.write("*END OF\n")
        # * End Molecule
    # * End .inp

    natoms = 0
    for frag in geometry:
        natoms += len(frag) // 4
    # * .mol file
    with open("mol_dirac.xyz", "w") as fmol:
        fmol.write(f" {natoms}\n\n")
        write_atoms(fmol, geometry)
    # * End mol

    # * Execution of dirac
    command = f"{alias} --noarch --scratch={scratch}"
    if mem != 0.0:
        command += f" --mem={mem}"
    if nproc > 1:
        command += f" --mpi={nproc}"
    command += " --inp=en_dirac.inp --mol=mol_dirac.xyz"
    subprocess.run(command, shell=True, check=False)
    # * End calculation

    # * does calculation done?
    value = subprocess.run(
        "grep 'Convergence after' en_dirac_mol_dirac.out | awk '{print $2}'",
        shell=True,
        capture_output=True,
        check=False,
    ).stdout.decode("utf-8")
    value = value.replace(" ", "").replace("\n", "")
    # * End read

    if value.upper() != "CONVERGENCE":
        done = 0
        energy = 0.0
    else:
        done = 1
        # * Read energy
        energy = float(
            subprocess.run(
                "grep 'Total energy' en_dirac_mol_dirac.out | awk '{print $4}'",
                shell=True,
                capture_output=True,
                check=False,
            ).stdout
        )
        # * End
    return done, energy


def cale(
    geometry,
    idprogram=1,
    alias="g09",
    scratch="",
    meth="HF",
    bas="sto-3g",
    charge=0,
    mult=1,
    nproc=1,
    mem=0.0,
) -> tuple[int, float]:
    """
    Driver the electronic energy calculation

    Parameters
    ----------
    geometry: (list[list[str,float,float,float,str,...],...])
            #! Please, respect the format.
            System under study. Each sublist represents a fragment that
            can interact with others through intermolecular interactions
            without undergoing a reaction.
    ic: (int)
        Selection the program which calculates the electronic energy (1:Gaussian,
        2:Dalton, and 3:Dirac).
        The default value is 1.
    alias: (str)
        Code alias of the program.
        The default value is g09.
    scratch: (str)
            scratch path
    meth: (str)
           Methodology to calculate the energy.
           The default value is HF (Hartree-Fock).
    bas: (str)
            Basis set.
            The default value is sto-3g.
    charge: (int)
            Molecular charge.
            The default value is 0.
    mult: (int)
            Spin multiplicity.
            The default value is 1.
    nproc: (int)
            Number of processors
            The default value is 1.
    mem: (float)
            Quantity of ram memory in GB by processor.
            The default value of the program.
    """
    done = 0
    energy = 0.0

    if idprogram == 1:
        # * Gaussain
        done, energy = en_gaussian(geometry, alias, meth, bas, charge, mult, nproc, mem)
    if idprogram == 2:
        # * Dalton
        done, energy = en_dalton(
            geometry, alias, meth, bas, charge, scratch, nproc, mem
        )
    if idprogram == 3:
        # * Dirac
        done, energy = en_dirac(geometry, alias, meth, bas, charge, scratch, nproc, mem)

    return done, energy
