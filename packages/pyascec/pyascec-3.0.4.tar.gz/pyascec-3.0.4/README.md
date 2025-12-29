# PyASCEC

<p style="text-align: justify"> 
PyASCEC is a Python-based program designed to perform Markov chain simulations of atomic and molecular cluster conformations using a modified Metropolis algorithm. The acceptance criterion is based on the electronic energy of the system. During the simulation, the fragments evolve within a box centered on the center of mass of the input cluster.</p>

<p style="text-align: justify">
For the PyASCEC program to work, you will need to have the Gaussian 09/16 (Default: g09), Dalton, or Dirac program installed. 
Furthermore, the PyASCEC code can likely be modified to interface with other programs.
</p>

Flux diagram for the algorithm is sketched in the following figure[[2]](#2)

<img src="ascec.svg">

If you use this code please cite: 

<p style="text-align: justify"><a id="1">[1]</a>> Pérez, J. F.; Restrepo, A. ASCEC V-01: Annealing Simulado Con Energı́a Cuántica. Property, Development and Implementation; Grupo de Quı́mica-Fı́sica Teórica, Instituto de Quı́mica, Universidad de Antioquia, AA 1226 Medellı́n, Colombia.</p>
> <p style="text-align: justify"><a id="2">[2]</a> Pérez, J. F.; Hadad, C. Z., Restrepo, A. Structural Studies of Water Tetramer. Int. J. Quantum Chem. 2008, 108, 1653.</p>

### Install
To install execute the following command  

```
pip install pyascec
```

### Example 

Motion and rotate each one fragment of cluster

```
from cluster import Cluster
from ascec import *

geometry = [
        ["O", 0.000000,  0.000000,  0.118997,
         "H", 0.000000,  0.753010, -0.475986,
         "H", 0.000000, -0.753010, -0.475986,
        ],
        ["O", 0.000000,  0.000000,  0.118997,
         "H", 0.000000,  0.753010, -0.475986,
         "H", 0.000000, -0.753010, -0.475986,
        ],
    ]

cluster = Cluster(geometry)

# ASCEC object
obj_ascec = ASCEC(system=cluster)

# Move each
with open("move_dimer_water.xyz", "w") as f:
    for ig in range(10):
        f.write(f" {cluster.natoms} \n")
        f.write(f" Structure {ig}\n")
        seed, motion_cluster = obj_ascec.cluster.move_cluster(
            obj_ascec.cluster,
            obj_ascec.center_cube
            )
        for ifrag in motion_cluster:
            nats = len(ifrag) // 4
            for ia in range(nats):
                ia0 = ia * 4
                f.write(
                    f"{ifrag[ia0]}   {ifrag[ia0+1]}  {ifrag[ia0+2]}  {ifrag[ia0+3]}\n"
                )
```

Exploration of Potential Energy Surface with Gaussian 

```
from cluster impore Cluster
from ascec import *

geometry = [
        ["O", 0.000000,  0.000000,  0.118997,
         "H", 0.000000,  0.753010, -0.475986,
         "H", 0.000000, -0.753010, -0.475986,
        ],
        ["O", 0.000000,  0.000000,  0.118997,
         "H", 0.000000,  0.753010, -0.475986,
         "H", 0.000000, -0.753010, -0.475986,
        ],
    ]

cluster = Cluster(
    geometry=geometry,
    ic=1,  # (1:Gaussain,2:Dalton,3:Dirac)
    alias="g09",  # alias or PATH
)

# Minimum parameters required to run ASCEC and Gaussian.
# The default methodology is HF, and the default basis set is sto-3g.
obj_ascec = ascec(cluster)

# More parameters
cluster = Cluster(
                geometry=geometry,
                ic=1,  # (1:Gaussain,2:Dalton,3:Dirac)
                alias="g09",  # alias or PATH
                meth="DFTB3LYP",
                bas="6-311G",
                nproc=2,
                mem=4.0, # Memory in GB
                )

obj_ascec = ascec(
                route=2, "1:lineal,2:geometric"
                i_temp=200, 
                n_temp=5, 
                d_temp=10, 
                max_cycles=200, 
                length=4.0,
		        seed=141423122025 # Default: minsec#day
                )

    print(" *** ASCEC Results (Gaussian) ***")
    
    # * Start exploration #####################
    energies, geoms = obj_ascec.pes_exp()
    # * End exploration   #######################

    ngeoms = len(energies)
    print(f"Total the geometries accepted: {ngeoms}")
    cc = obj_ascec.center_cube

    # * Save geometries in .xyz ##########################
    with open("dimer_water.xyz", "w") as f:
        for ic, en in enumerate(energies):
            f.write(f" {cluster.natoms} \n")
            f.write(f" Structure {ic} Energy {en} a.u.\n")
            for ifrag in geoms[ic]:
                nats = len(ifrag) // 4
                for ia in range(nats):
                    ia0 = ia * 4
                    f.write(
                        f"{ifrag[ia0]}   {ifrag[ia0+1]}  {ifrag[ia0+2]}  {ifrag[ia0+3]}\n"
                    )
            f.write(f"X     {cc[0] + 2.0}  {cc[0] + 2.0}  {cc[0] + 2.0}\n")
            f.write(f"X     {cc[0] + 2.0}  {cc[0] + 2.0}  {cc[0] - 2.0}\n")
            f.write(f"X     {cc[0] + 2.0}  {cc[0] - 2.0}  {cc[0] + 2.0}\n")
            f.write(f"X     {cc[0] + 2.0}  {cc[0] - 2.0}  {cc[0] - 2.0}\n")
            f.write(f"X     {cc[0] - 2.0}  {cc[0] + 2.0}  {cc[0] + 2.0}\n")
            f.write(f"X     {cc[0] - 2.0}  {cc[0] + 2.0}  {cc[0] - 2.0}\n")
            f.write(f"X     {cc[0] - 2.0}  {cc[0] - 2.0}  {cc[0] + 2.0}\n")
            f.write(f"X     {cc[0] - 2.0}  {cc[0] - 2.0}  {cc[0] - 2.0}\n")
    # * End  #########################################
```

Exploration of Potential Energy Surface with Dalton or Dirac

```
from cluster impore Cluster
from ascec import *

geometry = [
        ["O", 0.000000,  0.000000,  0.118997,
         "H", 0.000000,  0.753010, -0.475986,
         "H", 0.000000, -0.753010, -0.475986,
        ],
        ["O", 0.000000,  0.000000,  0.118997,
         "H", 0.000000,  0.753010, -0.475986,
         "H", 0.000000, -0.753010, -0.475986,
        ],
    ]


print(" *** ASCEC Results (Dalton) ***")
cluster = Cluster(
                    geometry=geometry,
                    ic=2,  # or (1:Gaussain,2:Dalton,3:Dirac)
                    alias="PATH/dalton",  # alias or PATH of Dalton
                    scratch="Path/scratch",  # Path of scratch
                    meth="DFTB3LYP",
                    bas="STO-3G",
                    nproc=2,
                    mem=4.0 # Memory in GB
                )

obj_ascec = ASCEC(
                    cluster,
                    i_temp=200,
                    n_temp=4,
                    d_temp=10,
                    max_cycles=50,
                    length=4.0,
                )

# * Start exploration #####################
energies, geoms = obj_ascec.pes_exp()
# * End exploration   #######################

ngeoms = len(energies)
print(f"Total the geometries accepted: {ngeoms}")
cc = obj_ascec.center_cube

# * Save geometries in .xyz ##########################
with open("dimer_water.xyz", "w") as f:
    for ic, en in enumerate(energies):
        f.write(f" {cluster.natoms} \n")
        f.write(f" Structure {ic} Energy {en} a.u.\n")
        for ifrag in geoms[ic]:
            nats = len(ifrag) // 4
            for ia in range(nats):
                ia0 = ia * 4
                f.write(
                    f"{ifrag[ia0]}   {ifrag[ia0+1]}  {ifrag[ia0+2]}  {ifrag[ia0+3]}\n"
                )
        f.write(f"X     {cc[0] + 2.0}  {cc[0] + 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] + 2.0}  {cc[0] + 2.0}  {cc[0] - 2.0}\n")
        f.write(f"X     {cc[0] + 2.0}  {cc[0] - 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] + 2.0}  {cc[0] - 2.0}  {cc[0] - 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] + 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] + 2.0}  {cc[0] - 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] - 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] - 2.0}  {cc[0] - 2.0}\n")
# * End  #########################################

print(" *** ASCEC Results (Dirac) ***")

cluster = Cluster(
                    geometry=geometry,
                    ic=2,  # or (1:Gaussain,2:Dalton,3:Dirac)
                    alias="PATH/pam",  # alias or PATH of Dirac
                    scratch="Path/scratch",  # Path of scratch
                    meth="DFTB3LYP",
                    bas="STO-3G",
                    nproc=2,
                    mem=4.0 # Memory in GB
                )

obj_ascec = ASCEC(
                    cluster,
                    i_temp=200,
                    n_temp=4,
                    d_temp=10,
                    max_cycles=50,
                    length=4.0,
                )


# * Start exploration #####################
energies, geoms = obj_ascec.pes_exp()
# * End exploration   #######################

ngeoms = len(energies)
print(f"Total the geometries accepted: {ngeoms}")
cc = obj_ascec.center_cube

# * Save geometries in .xyz ##########################
with open("dimer_water.xyz", "w") as f:
    for ic, en in enumerate(energies):
        f.write(f" {cluster.natoms} \n")
        f.write(f" Structure {ic} Energy {en} a.u.\n")
        for ifrag in geoms[ic]:
            nats = len(ifrag) // 4
            for ia in range(nats):
                ia0 = ia * 4
                f.write(
                    f"{ifrag[ia0]}   {ifrag[ia0+1]}  {ifrag[ia0+2]}  {ifrag[ia0+3]}\n"
                )
        f.write(f"X     {cc[0] + 2.0}  {cc[0] + 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] + 2.0}  {cc[0] + 2.0}  {cc[0] - 2.0}\n")
        f.write(f"X     {cc[0] + 2.0}  {cc[0] - 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] + 2.0}  {cc[0] - 2.0}  {cc[0] - 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] + 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] + 2.0}  {cc[0] - 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] - 2.0}  {cc[0] + 2.0}\n")
        f.write(f"X     {cc[0] - 2.0}  {cc[0] - 2.0}  {cc[0] - 2.0}\n")
# * End  #########################################    
```
