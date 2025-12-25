# File: transport_solver.pyi
from typing import List, Tuple

def solve_nwcr(
    supply: List[int],
    demand: List[int],
    costs: List[List[int]]
) -> Tuple[int, List[List[int]]]: ...

def solve_least_cost(
    supply: List[int],
    demand: List[int],
    costs: List[List[int]]
) -> Tuple[int, List[List[int]]]: ...

def solve_vam(
    supply: List[int],
    demand: List[int],
    costs: List[List[int]]
) -> Tuple[int, List[List[int]]]: ...

def optimize_modi(
    supply: List[int],
    demand: List[int],
    costs: List[List[int]],
    allocation: List[List[int]]
) -> Tuple[int, List[List[int]]]: ...