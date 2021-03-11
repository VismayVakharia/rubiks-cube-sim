# rubiks-cube-sim

Rubik's Cube Simulator using just python

Rotation Notations:
[website](https://www.randelshofer.ch/rubik/vcube6/doc/supersetENG_6x6.html)

### Dependencies:
 - numpy
 - quaternion
 - pyglet

Use pip to install these packages (`python3 -m pip install <package_name>`)

### Control:

#### Mouse Control:
Click and Drag to change the orientation of the cube

Scroll to zoom in/out 

Use `space` to toggle **Pause**, `backspace` to reset the cube to default orientation

#### Keyboard Control (3x3):
 - Face: **F R U B L D**
 - Slice: **M E S**
 - Whole: **X Y Z**

Uppercase letters rotate clockwise and lowercase do counter-clockwise.