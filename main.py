#!/usr/share/env python3.8

from visual import Window

WIN_W = 640
WIN_H = 640
CUBE_SIZE = 3

COMMANDS = []
PAUSED = False
RECORDING = False


if __name__ == "__main__":
    sim = Window(WIN_W, WIN_H, CUBE_SIZE, PAUSED, RECORDING)
    sim.commands.extend(COMMANDS)
    sim.main()
