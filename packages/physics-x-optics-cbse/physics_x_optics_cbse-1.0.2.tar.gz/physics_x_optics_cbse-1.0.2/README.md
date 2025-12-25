physics_x_optics_cbse

A simple and educational Python library for Class 10 CBSE Optics.
Created for students, teachers, and beginners to easily solve numerical problems using Python.

This library covers:

- Reflection of Light (Mirrors)
- Refraction of Light (Snell’s Law, Critical Angle, Apparent Depth)
- Refraction Through Lenses (Lens Formula, Magnification, Power)


INSTALLATION
-------------
After publishing on PyPI:

pip install physics_x_optics_cbse

For local install:

pip install .


IMPORT
-------
from physics_x_optics_cbse import *
or
from physics_x_optics_cbse import lens_formula, mirror_formula


EXAMPLES
--------
Mirror Formula:
f = mirror_formula(u=-20, v=-30)

Lens Formula:
f = lens_formula(u=-20, v=40)

Power of Lens:
P = power_of_lens(f_cm=25)

Snell’s Law:
r = snells_law_find_r(1.0, 30, 1.5)

Critical Angle:
C = critical_angle(1.5)

Apparent Depth:
d = apparent_depth(12, 4/3)


TARGET USERS
------------
- Class 10 CBSE Students
- Physics Teachers
- Python Beginners
- Educational App Developers


AUTHOR
------
Name : Dinesh_Pandiyan_B
Email: rajadineshp@gmail.com


LICENSE
-------
This project is free for educational and learning purposes.


FUTURE PLANS
------------
- Ray diagram plotting
- Menu-driven optics calculator
- Full Class 10 Physics library
- GUI-based Physics calculator