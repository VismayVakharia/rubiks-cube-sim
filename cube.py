#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import enum
from typing import Union, List, Tuple
import itertools
import numpy as np
import quaternion

Quaternion = quaternion.quaternion


class Vector(object):

    @classmethod
    def from_list(cls, list_: Union[List, Tuple]):
        if len(list_) == 3:
            x = list_[0]
            y = list_[1]
            z = list_[2]
            return cls(x, y, z)
        else:
            return cls(0, 0, 0)

    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __add__(self, other: 'Vector') -> 'Vector':
        x = self.x + other.x
        y = self.y + other.y
        z = self.z + other.z
        return Vector(x, y, z)

    def __mul__(self, other: Union[float, int]) -> 'Vector':
        return Vector(self.x * other, self.y * other, self.z * other)

    def __sub__(self, other) -> 'Vector':
        return self + other * (-1)

    def __eq__(self, other: 'Vector') -> bool:
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __ne__(self, other: 'Vector') -> bool:
        return (self.x, self.y, self.z) != (other.x, other.y, other.z)

    def __str__(self) -> str:
        # return "Point:({x}, {y}, {z})".format(**self.__dict__)
        return "<{0.x}, {0.y}, {0.z}>".format(self)

    def __repr__(self):
        return "<{0.x}, {0.y}, {0.z}>".format(self)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def norm(self) -> float:
        return np.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        norm = self.norm()
        self.x = self.x / norm
        self.y = self.y / norm
        self.z = self.z / norm

    def midpoint(self, other: 'Vector') -> 'Vector':
        return Vector.from_list([ix / 2 for ix in self + other])

    def as_array(self):
        return np.array([self.x, self.y, self.z])

    def as_list(self) -> List:
        return [self.x, self.y, self.z]

    @classmethod
    def rotate(cls, vector: 'Vector', rotation_quaternion: Quaternion) -> 'Vector':
        return cls.from_list(quaternion.rotate_vectors(rotation_quaternion, vector.as_list()))

    def dot(self, other: 'Vector') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z


class PieceType(enum.Enum):
    CENTER = 1
    EDGE = 2
    CORNER = 3
    CUBIE = 6

    def __str__(self):
        return self.name


Color = bool
Colors = Tuple[
    Color,  # Red (+X)
    Color,  # Orange (-X)
    Color,  # Yellow (+Y)
    Color,  # White (-Y)
    Color,  # Blue (+Z)
    Color,  # Green (-Z)
]


class Piece(object):
    def __init__(self, type_: PieceType, position: Vector, orientation: Quaternion):
        self.type = type_
        self.colors: Colors = self.calculate_colors(position)
        self.position = position
        self.orientation = orientation

    def __repr__(self):
        return "{type} piece at {position} with {orientation}".format(**self.__dict__)

    @staticmethod
    def calculate_colors(solved_position: Vector) -> Colors:
        dist = max(max(solved_position), -min(solved_position))
        color = [False, False, False, False, False, False]
        for axis, value in enumerate(solved_position):
            if value == dist:
                color[axis * 2] = True
            if value == -dist:
                color[axis * 2 + 1] = True
        return tuple(color)


class Cube(object):
    face_turns = {"R": Vector(1, 0, 0),
                  "U": Vector(0, 1, 0),
                  "F": Vector(0, 0, 1),
                  "L": Vector(-1, 0, 0),
                  "D": Vector(0, -1, 0),
                  "B": Vector(0, 0, -1)}
    notation_map3x3 = {"M": "NL", "E": "ND", "S": "NF",
                       "X": "CR", "Y": "CU", "Z": "CF"}
    notation_map2x2 = {"X": "CR", "Y": "CU", "Z": "CF"}

    def __init__(self, size):
        self.size = size

        orient_vec = lambda: Quaternion(1, 0, 0, 0)
        all_stickers = (True, True, True, True, True, True,)

        if size == 1:
            self.pieces = [Piece(PieceType.CUBIE, Vector(0, 0, 0), orient_vec())]
        else:
            # corners
            dist = (size - 1) / 2.
            _corners = list(itertools.product([-dist, dist], repeat=3))
            self.corners = []
            for corner in _corners:
                position_vec = Vector(*corner)
                self.corners.append(Piece(PieceType.CORNER, position_vec, orient_vec()))

            # edges
            # for each axis, there are 4 sets of edges -> 3 groups
            _edge_groups = list(itertools.product([-dist, dist], repeat=2))
            _edges = []

            edge_offsets = np.linspace((3-size)/2, (size-3)/2, size-2)
            for c1, c2 in _edge_groups:
                _edges.extend((edge_offset, c1, c2) for edge_offset in edge_offsets)
                _edges.extend((c1, edge_offset, c2) for edge_offset in edge_offsets)
                _edges.extend((c1, c2, edge_offset) for edge_offset in edge_offsets)

            self.edges = []
            for edge in _edges:
                position_vec = Vector(*edge)
                self.edges.append(Piece(PieceType.EDGE, position_vec, orient_vec()))

            # centers
            _center_groups = [-dist, dist]
            _centers = []

            center_offsets_x, center_offsets_y = np.meshgrid(edge_offsets, edge_offsets)
            center_offsets = list(zip(center_offsets_x.flatten(), center_offsets_y.flatten()))

            for c in _center_groups:
                _centers.extend((c, center_offset[0], center_offset[1]) for center_offset in center_offsets)
                _centers.extend((center_offset[0], c, center_offset[1]) for center_offset in center_offsets)
                _centers.extend((center_offset[0], center_offset[1], c) for center_offset in center_offsets)

            self.centers = []
            for center in _centers:
                position_vec = Vector(*center)
                self.centers.append(Piece(PieceType.CENTER, position_vec, orient_vec()))

            self.pieces = self.centers + self.corners + self.edges

    def rotate_layer(self, axis: Vector, layer_index: int, angle: float):
        axis.normalize()
        rotation_quaternion = quaternion.from_rotation_vector(axis.as_array() * angle)

        dist = (self.size - 1) / 2
        assert (0 < layer_index < self.size + 1), "Invalid layer index"

        for piece in self.pieces:
            if abs((dist - piece.position.dot(axis) + 1) - layer_index) < 1e-6:
                piece.orientation = rotation_quaternion * piece.orientation
                piece.position = Vector(*quaternion.rotate_vectors(rotation_quaternion, piece.position.as_array()))

    def rotate(self, move: str, angle: float = np.pi/2):
        # move direction and/or amount
        if move[-1] == "'":
            multiplier = 1
            move = move[: -1]
        elif move[-1] == "2":
            multiplier = 2
            move = move[: -1]
        else:
            multiplier = -1

        # move axis
        axis = Cube.face_turns[move[-1]]
        move = move[: -1]

        # layers to be rotated
        layers = []
        if len(move) == 0:
            # face rotation only
            layers.append(1)
        elif move[0] == "C":
            # cube rotation
            layers.extend(range(1, self.size + 1))
        elif move[0] == "T":
            # tier rotation
            layers.append(1)
            move = move[1:]
            if len(move) == 0:
                layers.append(2)
            else:
                layers.extend(range(2, int(move) + 1))
        elif move[0] == "N":
            # numbered rotations
            move = move[1:]
            if len(move) == 0:
                layers.append(2)
            elif "-" not in move:
                layers.append(int(move))
            else:
                a, b = move.split("-")
                layers.extend(range(int(a), int(b) + 1))
        else:
            assert "Incorrect rotation input"

        for layer in layers:
            self.rotate_layer(axis, layer, angle * multiplier)

    def rotateNxN(self, move: str, angle: float = np.pi/2):
        if move[0] in Cube.notation_map2x2:
            mapped_move = Cube.notation_map2x2[move[0]] + move[1:]
        else:
            mapped_move = move
        self.rotate(mapped_move, angle)

    def rotate3x3(self, move: str, angle: float = np.pi/2):
        if move[0] in Cube.face_turns:
            mapped_move = move
        elif move[0].upper() in Cube.face_turns:
            mapped_move = "T" + move[0].upper() + move[1:]
        elif move[0] in Cube.notation_map3x3:
            mapped_move = Cube.notation_map3x3[move[0]] + move[1:]
        else:
            raise Exception("Incorrect rotation input")
        self.rotate(mapped_move, angle)

    def rotate2x2(self, move: str, angle: float = np.pi/2):
        if move[0] in Cube.face_turns:
            mapped_move = move
        elif move[0] in Cube.notation_map2x2:
            mapped_move = Cube.notation_map2x2[move[0]] + move[1:]
        else:
            raise Exception("Incorrect rotation input")
        self.rotate(mapped_move, angle)

    def rotate1x1(self, move: str, angle: float = np.pi/2):
        if move[0] in Cube.notation_map2x2:
            mapped_move = Cube.notation_map2x2[move[0]] + move[1:]
        else:
            raise Exception("Incorrect rotation input")
        self.rotate(mapped_move, angle)
