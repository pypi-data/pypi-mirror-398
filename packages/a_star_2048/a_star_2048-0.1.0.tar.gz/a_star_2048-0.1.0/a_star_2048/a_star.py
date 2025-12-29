from collections.abc import Generator
from dataclasses import dataclass
from heapq import heappush, heappop

from .board import move_board


possible_states = []


def most_points_heuristic(matrix: list[list[int]]):
    return sum(sum(row) for row in matrix)


def most_zero_tiles(matrix: list[list[int]]):
    return sum([row.count(0) for row in matrix])


def largest_tile_heuristic(matrix: list[list[int]]):
    """
    Heuristic that considers largest tiles to be better
    """
    return 2048 - max([max(row) for row in matrix])


class State:
    def __init__(self, matrix: list[list[int]]) -> None:
        self.matrix = matrix

    def get_transitions(self) -> Generator["Transition"]:
        for op in ["left", "right", "up", "down"]:
            new_board = move_board(self.matrix, op)  # pyright: ignore[reportArgumentType]
            yield Transition(destiny=State(new_board))


@dataclass
class Transition:
    destiny: State
    # making the cost 1 because every transition equals to one more play
    # this cost is used in the final to count how many plays were made
    cost: int = 1


@dataclass
class Node:
    parent: "Node"


def a_star(start_state, end_state, heuristic):
    queue = [start_state]

    costs = {start_state: 0}

    visited = set()

    while queue:
        current = heappop(queue)

        visited.add(current)

        if current == end_state:
            return current

        for transition in current.transitions:
            new_cost = current.cost + transition.cost
            if not current in visited or new_cost < costs.get(current, 0):
                costs[current] = new_cost
                heappush(queue, transition.state)
