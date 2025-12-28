# _espresso.pyi
from typing import List

def minimize(
    nbinary: int,
    mvars: List[int],
    cubesf: List[List[int]],
    cubesd: List[List[int]],
    verbosity: int = 0,
) -> List[str]: ...
