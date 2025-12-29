"""
Andy Zapata
21/12/2025
"""

from math import cos, sin

from pyascec.rand0 import rand0
from pyascec.atomic_mass import MA


def split_lab_xyz(fragment) -> tuple[list[str], list[float, float, float]]:
    """
    Fragment list is splited in two array, one list has atomic
    label while another list has the coordinates.
    """
    natoms = len(fragment) // 4
    mxyz = []
    mlabel = []
    for i in range(natoms):
        i0 = i * 4
        mxyz += fragment[i0 + 1 : i0 + 4]
        mlabel.append(fragment[i0])
    return mlabel, mxyz


def join_lab_xyz(
    mlabel: list[str], mxyz: list[float, float, float]
) -> list[str, float, float, float]:
    """
    Join atomic label and coordinate in one list
    """
    fragment = []
    for ia, label in enumerate(mlabel):
        fragment += [label, *mxyz[ia * 3 : (ia + 1) * 3]]
    return fragment


def cm(mlabel: list[str], mxyz: list[float, float, float]) -> list[float, float, float]:
    """
    Calculate the mass center

    Parameters
    ----------
    lelement: (list[str])
        Array with atomic labels
    mxyz: (list[list[float,float,float]])
        Array with coordinates
    """
    xcm, ycm, zcm = 0.0, 0.0, 0.0
    ma = [MA[e] for e in mlabel]
    mm = sum(ma)
    natoms = len(mxyz) // 3
    for ie in range(natoms):
        ie0 = ie * 3
        xcm += ma[ie] * mxyz[ie0]
        ycm += ma[ie] * mxyz[ie0 + 1]
        zcm += ma[ie] * mxyz[ie0 + 2]
    return [xcm / mm, ycm / mm, zcm / mm]


def randtrans(seed: int, maxr: float) -> tuple[int, float]:
    """
    Random translation
    """
    js = 1.0
    z, seed = rand0(seed)
    if z < 0.5:
        js = -1.0
    z, seed = rand0(seed)
    return seed, js * z * maxr


def trans(
    seed: int,
    maxr: float,
    mlabel: list[str],
    length: float,
    center_cube: list[float, float, float],
    mrcm: list[float, float, float],
    mxyz: list[float, float, float],
) -> tuple[int, list[float, float, float], list[float, float, float]]:
    """
    Random Molecular Translation and Its Mass Center
    """
    natoms = len(mxyz) // 3
    nmrcm = []
    for i in range(3):
        # * Move mass center
        seed, s = randtrans(seed, maxr)
        nmrcm.append(mrcm[i] + s)
        # ! Verify: is the cm into the box? ! ##
        if abs(nmrcm[i]) > (abs(center_cube[i]) + (0.425 * length)):
            # * Move mass center
            nmrcm[i] = center_cube[i] + s
        # ! End verification #########################
        for ia in range(natoms):
            ia0 = ia * 3
            # * Distance between each atom and cubic center
            dri = mxyz[ia0 + i] - mrcm[i]
            # * End
            # * Moving each coordinate of all atoms
            mxyz[ia0 + i] = nmrcm[i] + dri
            # * End
    return seed, nmrcm, mxyz


def rot(
    seed: int,
    maxa: float,
    mrcm: list[list[float, float, float]],
    mxyz: list[float, float, float],
) -> tuple[int, list[float, float, float]]:
    """
    Random Molecular Rotation
    """
    rax, ray, raz = 1, 1, 1
    z, seed = rand0(seed)
    if z >= 0.5:
        rax = -1
    z, seed = rand0(seed)
    if z >= 0.5:
        ray = -1
    z, seed = rand0(seed)
    if z >= 0.5:
        raz = -1
    z, seed = rand0(seed)
    xa = rax * z * maxa
    z, seed = rand0(seed)
    ya = ray * z * maxa
    z, seed = rand0(seed)
    za = raz * z * maxa

    natoms = len(mxyz) // 3
    rel = []
    for ia in range(natoms):
        ia0 = ia * 3
        dx = mxyz[ia0] - mrcm[0]
        dy = mxyz[ia0 + 1] - mrcm[1]
        dz = mxyz[ia0 + 2] - mrcm[2]
        rel.append(
            dx * (cos(za) * cos(ya))
            + dy * (-cos(za) * sin(ya) * sin(xa) + sin(za) * cos(xa))
            + dz * (cos(za) * sin(ya) * cos(xa) + sin(za) * sin(xa))
        )
        rel.append(
            dx * (-sin(za) * cos(ya))
            + dy * (sin(za) * sin(ya) * sin(xa) + cos(za) * cos(xa))
            + dz * (-sin(za) * sin(ya) * cos(xa) + cos(za) * sin(xa))
        )
        rel.append(
            dx * (-sin(ya)) + dy * (-cos(ya) * sin(xa)) + dz * (cos(ya) * cos(xa))
        )
        for i in range(3):
            mxyz[ia0 + i] = rel[ia0 + i] + mrcm[i]
    return seed, mxyz


def move_geom_cluster(
    geometry: list[list[str, float, float, float]],
    center_cube: list[float, float, float],
    length: float,
    maxr: float,
    maxa: float,
    seed: int,
) -> tuple[int, list[list[str, float, float, float]]]:
    """
    Translate and/or rotate the geometry of each fragment:atom/molecule
    """
    newgeometry = []
    for fragment in geometry:
        mlabel, mxyz = split_lab_xyz(fragment)
        mrcm = cm(mlabel, mxyz)
        # * Translation fragment #########################
        seed, nmrcm, nmxyz = trans(seed, maxr, mlabel, length, center_cube, mrcm, mxyz)
        # * End translation ##############################
        # * Rotation fragment with two or more atoms #####
        if len(mlabel) > 1:
            seed, nmxyz = rot(seed, maxa, nmrcm, nmxyz)
        # * End rotation #################################
        newgeometry.append(join_lab_xyz(mlabel, nmxyz))

    return seed, newgeometry
