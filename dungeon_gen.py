import random
from dataclasses import dataclass
from typing import List, Tuple

from core import index_to_pos, Board, Actor

M_SIZE = 4
MAX_ROOM_SIZE = 8
SIDE = M_SIZE * MAX_ROOM_SIZE

MPath = Tuple[int, int]
Matrix = List[MPath]
Size = Tuple[int, int]
Position = Tuple[int, int]
Room = Tuple[Size, Position]


# 1TRBL
WALLS = {
    1: (8, 8),
    10000: (24, 16),
    10001: (40, 0),
    10010: (24, 8),
    10011: (16, 0),
    10100: (24, 0),
    10101: (32, 0),
    10110: (0, 0),
    10111: (8, 0),
    11000: (40, 8),
    11001: (16, 16),
    11010: (32, 8),
    11011: (16, 8),
    11100: (0, 16),
    11101: (8, 16),
    11110: (0, 8),
    11111: (8, 8),
}


@dataclass
class Level:
    matrix: Matrix
    rooms: List[Room]


def matrix_neighbours(index: int) -> List[int]:
    col, row = index_to_pos(index, M_SIZE)

    return [
        r * M_SIZE + c
        for r, c in [
            (row, col + 1),
            (row + 1, col),
            (row, col - 1),
            (row - 1, col),
        ]
        if r < M_SIZE and c < M_SIZE and r >= 0 and c >= 0
    ]


def count_neighbours(matrix: Matrix, index: int) -> int:
    return sum(1 for a, b in matrix if a == index or b == index)


def dig_matrix(start) -> Matrix:
    matrix: Matrix = []
    visited = {start}
    to_explore = set(matrix_neighbours(start))
    while to_explore:
        start = random.choice(list(to_explore))
        old = next(n for n in visited if n in matrix_neighbours(start))
        matrix.append((old, start))
        visited.add(start)
        to_explore.remove(start)
        to_explore |= set(
            n for n in matrix_neighbours(start) if n not in visited
        )

    return matrix


def add_loops(matrix: Matrix) -> Matrix:
    extras = random.randrange(int(M_SIZE / 2), M_SIZE)
    goal = extras + len(matrix)
    while len(matrix) < goal:
        a = random.randrange(M_SIZE * M_SIZE)
        try:
            b = next(
                b
                for b in matrix_neighbours(a)
                if (a, b) not in matrix and (b, a) not in matrix
            )
        except StopIteration:
            continue
        else:
            matrix.append((a, b))

    return matrix


def random_room(matrix: Matrix, room_index: int) -> Room:
    n_neigh = count_neighbours(matrix, room_index)
    threshold = 4
    min_size = 3 if n_neigh > 1 else threshold

    max_size = MAX_ROOM_SIZE - 0
    w, h = (
        random.randint(min_size, max_size),
        random.randint(min_size, max_size),
    )

    if w < threshold or h < threshold:
        return (1, 1), (0, 0)

    return (w, h), (0, 0)


def create_matrix() -> Matrix:
    start = random.randrange(M_SIZE * M_SIZE)
    return add_loops(dig_matrix(start))


def carve_room(board: Board, room: Room, pos: Position) -> Board:
    (w, h), offset = room
    x, y = pos
    for i in range(h):
        for j in range(w):
            _x = j + x
            _y = i + y
            board.set(_x, _y, 0)
    return board


def carve_path(board: Board, level: Level, path: MPath) -> Board:
    a, b = path
    r1, r2 = level.rooms[a][0], level.rooms[b][0]
    p1, p2 = list(room_anchor(a)), list(room_anchor(b))
    other = 0 if p1[0] == p2[0] else 1
    max_off = min(r1[other], r2[other])
    off = random.randrange(max_off)

    p1[other] += off
    p2[other] += off

    coord = 1 if p1[0] == p2[0] else 0
    step = 1 if p1[coord] < p2[coord] else -1
    p = p1

    if step > 0:
        p[coord] += r1[coord]
        p2[coord] -= 1
    else:
        p[coord] -= 1
        p2[coord] += r2[coord]

    cpt = 0
    last_i = None
    while p[coord] != p2[coord]:
        x, y = p

        if board.get(x, y) == 0:
            return board

        top = board.get(x, y - 1)
        val = 2 if last_i is None else 0

        if r1 == (1, 1):
            val = 0

        board.set(x, y, val)
        p[coord] += step
        cpt += 1
        last_i = x, y

    x, y = p2
    top = board.get(x, y - 1)
    val = 0 if r2 == (1, 1) else 2
    if last_i is not None and cpt < 2:
        board.set(*last_i, 0)

    board.set(x, y, val)

    return board


def room_anchor(index: int) -> Position:
    x = (index * MAX_ROOM_SIZE) % SIDE
    y = int((index * MAX_ROOM_SIZE) / SIDE) * MAX_ROOM_SIZE
    return x, y


def board_neigh(index):
    x, y = index_to_pos(index, SIDE)

    return [
        y_ * SIDE + x_
        for x_, y_ in [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
        if 0 <= x_ < SIDE and 0 <= y_ < SIDE
    ]


def encode_wall(board: Board, index: int) -> int:
    val = 0b10000

    x, y = index_to_pos(index, board.side)
    neighs = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]

    for i, (x_, y_) in enumerate(neighs):
        if board.outside(x_, y_) or is_wall(board.get(x_, y_)):
            val = val | (1 << i)

    return int("{0:b}".format(val))


def encode_floor(board: Board, index: int) -> int:
    x, y = index_to_pos(index, board.side)
    top = x, y - 1

    top_val = board.get(*top)

    if board.outside(*top):
        return 32

    elif is_wall(top_val):
        bin_str = str(top_val)
        if bin_str[4] == "0" and bin_str[2] == "1":
            return 31
        elif bin_str[4] == "1" and bin_str[2] == "1":
            return 32
        elif bin_str[4] == "1" and bin_str[2] == "0":
            return 33
        elif bin_str[4] == "0" and bin_str[2] == "0":
            return 34

    elif top_val == 20:  # front door
        return 35

    return 30


def encode_door(board: Board, index: int) -> int:
    x, y = index_to_pos(index, board.side)
    top = x, y - 1

    top_val = board.get(*top)

    if board.outside(*top):
        return 22

    elif is_wall(top_val):
        bin_str = str(top_val)
        if bin_str[4] == "0" and bin_str[2] == "1":
            return 21
        elif bin_str[4] == "1" and bin_str[2] == "1":
            return 22
        elif bin_str[2] == "0":
            return 23

    return 20


def is_wall(val: int) -> bool:
    return val in WALLS or val == 1


def is_door(val: int) -> bool:
    return val == 2 or 20 <= val < 30


def is_empty(val: int) -> bool:
    return val == 0 or 30 <= val < 40


def clean_board(board: Board) -> Board:

    for i in range(len(board)):
        val = board[i]
        if val == 1:
            board[i] = encode_wall(board, i)
        elif val == 2:
            # must happen after walls (top down)
            n_neigh = sum(1 for k in board_neigh(i) if is_empty(board[k]))
            if n_neigh > 2:
                board[i] = 0  # remove door
            else:
                board[i] = encode_door(board, i)
        elif val == 0:
            # Must happen after walls and doors
            board[i] = encode_floor(board, i)

    return board


def create_board(level: Level):
    # fully walls (+ border)
    board = Board(cells=(SIDE * SIDE) * [1], side=SIDE,)
    for i, room in enumerate(level.rooms):
        board = carve_room(board, room, room_anchor(i))

    for path in level.matrix:
        board = carve_path(board, level, path)

    return clean_board(board)


def generate_level(matrix: Matrix) -> Level:
    return Level(
        matrix=matrix,
        rooms=[random_room(matrix, i) for i in range(M_SIZE * M_SIZE)],
    )


def populate_enemies(level: Level, board: Board):
    enemies = []
    for i in range(len(board)):
        if not is_empty(board[i]):
            continue

        r = random.randint(0, 100)

        if r > 98:
            e = Actor(index_to_pos(i, board.side))
            e.pv = 4
            enemies.append(e)

    return enemies
