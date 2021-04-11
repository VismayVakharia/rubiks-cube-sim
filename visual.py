#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import numpy as np
import pyglet
import pyglet.gl as gl
import quaternion
from typing import Tuple, Iterable

import cube as cb

Quaternion = quaternion.quaternion

Colors = {
    (0, 1): (233, 68, 48),
    (0, -1): (241, 148, 47),
    (1, 1): (244, 234, 43),
    (1, -1): (255, 255, 255),
    (2, 1): (1, 118, 206),
    (2, -1): (118, 227, 11),
}


def distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def scale_tuple(array: Iterable, scale: float = 1):
    result = ()
    for element in array:
        result += (element * scale,)
    return result


class Cubie(object):
    def __init__(self, piece: cb.Piece, sticker_factor: float = 0.9,
                 batch: pyglet.graphics.Batch = None):
        self.piece = piece
        self.sticker_factor = sticker_factor
        self.batch = pyglet.graphics.Batch() if (batch is None) else batch
        if piece.type == cb.PieceType.CORNER:
            num_faces = piece.type.value + 6
        elif piece.type == cb.PieceType.EDGE:
            num_faces = piece.type.value + 4
        elif piece.type == cb.PieceType.CENTER:
            num_faces = piece.type.value + 5
        else:
            num_faces = piece.type.value + 6
        self.vertex_list = self.batch.add(num_faces * 4, gl.GL_QUADS, None, "v3f", "c3B")
        self.relative_vectors = []

        ix = 0
        for index, (axis, sign) in enumerate(Colors):
            if self.piece.colors[index]:
                self.add_face(axis, sign, ix)
                ix += 1
                self.add_face(axis, sign, ix, sticker=True)
                ix += 1
            else:
                if self.piece.type == cb.PieceType.CORNER:
                    self.add_face(axis, sign, ix)
                    ix += 1
                elif self.piece.type == cb.PieceType.EDGE:
                    position = self.piece.position.as_list()
                    temp_axis_position = min(map(lambda x: abs(x), position))
                    if temp_axis_position in position:
                        temp_axis = position.index(temp_axis_position)
                    else:
                        temp_axis = position.index(-temp_axis_position)
                    if axis == temp_axis:
                        self.add_face(axis, sign, ix)
                        ix += 1
                elif self.piece.type == cb.PieceType.CENTER:
                    temp_axis = (self.piece.colors.index(True) // 2) % 3
                    if axis != temp_axis:
                        self.add_face(axis, sign, ix)
                        ix += 1
        self.update()

    def add_face(self, axis, sign, vl_index: int, sticker: bool = False):
        corners = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        sticker_factor = 1 if not sticker else self.sticker_factor
        colors = ()

        for c1, c2 in corners:
            vertex = [0, 0, 0]
            vertex[axis] = sign * (1 if not sticker else 1.01)
            vertex[(axis + sign*2) % 3] = c1 * sticker_factor
            vertex[(axis + sign*1) % 3] = c2 * sticker_factor
            vertex_vec = cb.Vector.from_list(vertex)
            vertex_vec *= 0.5
            self.relative_vectors.append(vertex_vec)
            colors += (0, 0, 0) if not sticker else Colors[axis, sign]
        self.vertex_list.colors[12 * vl_index: 12 * vl_index + 12] = colors

    def update(self):
        for index, vector in enumerate(self.relative_vectors):
            vertex_vec = cb.Vector.rotate(vector, self.piece.orientation)
            vertex_vec += self.piece.position
            self.vertex_list.vertices[3*index: 3*index + 3] = vertex_vec.as_list()


class Window(pyglet.window.Window):
    def __init__(self, width: int, height: int, cube_size: int = 3,
                 paused: bool = False, record: bool = False):
        config = pyglet.gl.Config(sample_buffers=1, samples=4, depth_size=1)
        super(Window, self).__init__(width, height, config=config)
        gl.glClearColor(0.5, 0.5, 0.5, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

        self.position = [0, 0, -10]
        self.rotation = [30.0, -45.0, 0]

        self.cube = cb.Cube(cube_size)

        self.faces = pyglet.graphics.Batch()
        self.cubies = []
        for piece in self.cube.pieces:
            self.cubies.append(Cubie(piece, batch=self.faces))

        self.angle_step = np.pi/20
        self.commands = []
        self.current_command = [None, 0]
        self.current_state = 0.0
        self.is_paused = paused

        self.record = record
        self.frame_count = 0

    def on_resize(self, width, height):
        gl.glViewport(0, 0, width, height)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect_ratio = width / height
        gl.gluPerspective(35, aspect_ratio, 1, 100)
        # gl.glOrtho(-3, 3, -3, 3, -3, 3)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        # gl.gluLookAt(0.0, -1.0, 0.0,
        #              0.0, 0.0, 0.0,
        #              0.0, 0.0, 1.0)

    def on_draw(self):
        self.clear()
        gl.glPushMatrix()
        gl.glTranslatef(*self.position)
        gl.glRotatef(self.rotation[0], 1, 0, 0)
        gl.glRotatef(self.rotation[1], 0, 1, 0)
        gl.glRotatef(self.rotation[2], 0, 0, 1)

        for cubie in self.cubies:
            cubie.update()

        self.faces.draw()
        gl.glPopMatrix()

        if self.record:
            pyglet.image.get_buffer_manager().get_color_buffer().save("./frames/" + str(self.frame_count) + '.png')
            self.frame_count += 1

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            self.is_paused = not self.is_paused
        elif symbol == pyglet.window.key.BACKSPACE:
            self.position = [0, 0, -10]
            self.rotation = [30.0, -45.0, 0]
        elif 97 <= symbol <= 122:
            if bool(modifiers & pyglet.window.key.MOD_SHIFT) ^ bool(modifiers & pyglet.window.key.MOD_CAPSLOCK):
                key = chr(symbol).upper()
            else:
                key = chr(symbol).upper() + "'"
            if key[0].upper() in "RLUDFBMESXYZ":
                self.commands.append(key)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.rotation[0] -= dy
            if self.rotation[0] > 90:
                self.rotation[0] = 90
            elif self.rotation[0] < -90:
                self.rotation[0] = -90
            else:
                pass
            self.rotation[1] += dx

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.position[2] += scroll_y
        if self.position[2] < -50:
            self.position[2] = -50
        elif self.position[2] > -5:
            self.position[2] = -5

    def update(self, dt):
        if not self.is_paused:
            if self.current_command[0] is None:
                if self.commands:
                    self.current_command = self.commands.pop(0), np.pi/2
            else:
                move, angle = self.current_command
                if abs(self.current_state - angle) >= self.angle_step:
                    self.cube.rotate3x3(move, self.angle_step)
                    self.current_state += self.angle_step
                else:
                    self.current_command = [None, 0]
                    self.current_state = 0

    def main(self):
        pyglet.clock.schedule_interval(self.update, 1 / 50)
        pyglet.app.run()
