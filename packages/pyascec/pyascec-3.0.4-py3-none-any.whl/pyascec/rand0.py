"""
Andy Zapata
21/12/2025
"""


def rand0(seed: int) -> tuple[float, int]:
    """
    Reset seed based in ASCEC algorithm
    """
    # * PARAMETERS #########
    IA = 16807
    IM = 2147483647
    AM = 1.0 / IM
    IQ = 127773
    IR = 2836
    MASK = 123459876
    # * End PARAMETERS #####
    seed = seed ^ MASK
    k = seed // IQ
    seed = IA * (seed - k * IQ) - IR * k
    if seed < 0:
        seed = seed + IM
    random0 = AM * seed
    seed = seed ^ MASK
    return random0, seed
