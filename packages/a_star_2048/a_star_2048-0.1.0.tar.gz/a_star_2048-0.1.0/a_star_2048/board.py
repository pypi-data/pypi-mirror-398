from collections import defaultdict, deque

from collections.abc import Mapping
from copy import deepcopy
from random import choice, choices
from typing import Literal


SQUARE_SIZE = 4


empty_positions: list[tuple[int, int]] = []


def init_board():
    board = [[0] * SQUARE_SIZE for _ in range(SQUARE_SIZE)]
    spawn_value(board)
    return board


def spawn_value(board: list[list[int]]):
    empty_positions = [
        (i, j)
        for i in range(SQUARE_SIZE)
        for j in range(SQUARE_SIZE)
        if board[i][j] == 0
    ]
    empty_tile = choice(empty_positions)

    value = choices([2, 4], weights=[0.7, 0.3], k=1)

    board[empty_tile[0]][empty_tile[1]] = value[0]


def move_board(
    board: list[list[int]], direction: Literal["left", "right", "up", "down"]
) -> list[list[int]]:
    new_board = deepcopy(board)

    new_line: deque[int]
    new_col: deque[int]

    match direction:
        case "right":
            for row_idx in range(SQUARE_SIZE):
                new_line = deque()
                col_idx = 0
                while col_idx < SQUARE_SIZE:
                    new_element = new_board[row_idx][col_idx]
                    if new_element == 0:
                        new_line.appendleft(new_board[row_idx][col_idx])
                    else:
                        new_line.append(new_board[row_idx][col_idx])

                    while len(new_line) > 1 and new_line[-1] == new_line[-2]:
                        new_line.append(new_line.pop() + new_line.pop())
                    col_idx += 1
                while len(new_line) < SQUARE_SIZE:
                    new_line.appendleft(0)
                new_board[row_idx] = list(new_line)

        case "left":
            for row_idx in range(SQUARE_SIZE):
                new_line = deque()
                col_idx = SQUARE_SIZE - 1
                while col_idx > -1:
                    new_element = new_board[row_idx][col_idx]
                    if new_element == 0:
                        new_line.append(new_board[row_idx][col_idx])
                    else:
                        new_line.appendleft(board[row_idx][col_idx])

                    while (
                        len(new_line) > 1
                        and new_line[0] != 0
                        and new_line[0] == new_line[1]
                    ):
                        new_line.appendleft(new_line.popleft() + new_line.popleft())
                    col_idx -= 1
                while len(new_line) < SQUARE_SIZE:
                    new_line.append(0)
                new_board[row_idx] = list(new_line)

        case "up":
            for col_idx in range(SQUARE_SIZE):
                new_col = deque()
                row_idx = SQUARE_SIZE - 1
                while row_idx > -1:
                    new_element = new_board[row_idx][col_idx]
                    if new_element == 0:
                        new_col.append(new_board[row_idx][col_idx])
                    else:
                        new_col.appendleft(new_board[row_idx][col_idx])

                    while (
                        len(new_col) > 1
                        and new_col[0] != 0
                        and new_col[0] == new_col[1]
                    ):
                        new_col.appendleft(new_col.popleft() + new_col.popleft())
                    row_idx -= 1
                while len(new_col) < SQUARE_SIZE:
                    new_col.append(0)

                for i in range(SQUARE_SIZE):
                    new_board[i][col_idx] = new_col[i]

        case "down":
            for col_idx in range(SQUARE_SIZE):
                new_col = deque()
                row_idx = 0
                while row_idx < SQUARE_SIZE:
                    new_element = new_board[row_idx][col_idx]
                    if new_element == 0:
                        new_col.appendleft(new_board[row_idx][col_idx])
                    else:
                        new_col.append(new_board[row_idx][col_idx])

                    while len(new_col) > 1 and new_col[-1] == new_col[-2]:
                        new_col.append(new_col.pop() + new_col.pop())
                    row_idx += 1
                while len(new_col) < SQUARE_SIZE:
                    new_col.appendleft(0)

                for i in range(SQUARE_SIZE):
                    new_board[i][col_idx] = new_col[i]

    return new_board


def print_board(board: list[list[int]]):
    print(" ".join("#" * (len(board) + 2)))
    for row in board:
        print(f"# {' '.join([str(num) for num in row])} #")
    print(" ".join("#" * (len(board) + 2)))


def is_finished(board: list[list[int]]):
    """
    Check if there are no more movements possible in the board
    """
    no_empty_tiles = sum([row.count(0) for row in board]) == 0

    # checking horizontally
    for row in board:
        current_element = row[0]
        for el in row[1:]:
            if el == current_element:
                return False
            else:
                current_element = el

    # checking vertically
    for col_idx in range(len(board)):
        current_element = board[0][col_idx]
        for row_idx in range(1, len(board)):
            if current_element == board[row_idx][col_idx]:
                return False
            else:
                current_element = board[row_idx][col_idx]

    return no_empty_tiles
