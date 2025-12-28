# _espresso.pyi
from typing import List, Tuple

def minimize_old(
    cubes: List[Tuple[str, int]],
    verbosity: int = 0
) -> List[Tuple[str, int]]: ...



def minimize(
    nbinary: int,
    mvars: List[int],
    cubesf: List[List[int]],
    cubesd: List[List[int]],
    cubesr: List[List[int]],
    verbosity: int = 0
) -> List[Tuple[str, int]]: ...