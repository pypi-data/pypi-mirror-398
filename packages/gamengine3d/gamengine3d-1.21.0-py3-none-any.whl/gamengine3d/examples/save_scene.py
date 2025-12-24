"""
The recreates the everything demo, and then saves the scene into a JSON file called "the_everything_demo.json".
"""

from gamengine3d import *
import random
from pathlib import Path

engine = Engine(1000, 800, name="The Everything DEMO", background_color=Color.grey)
engine.context.runtime_vars.from_settings("gamengine3d.examples.scripts.settings") # set the runtime vars from a module

positions = [
    vector3d(0, 4, 0.5),
    vector3d(-3, 2, 2),
    vector3d(3, 3, -2),
    vector3d(-2, 5, -3),
    vector3d(4, 6, 4),
    vector3d(1, 6, 7),
    vector3d(-4, 3, 5),
    vector3d(5, 5, 9),
    vector3d(0, 7, -4),
    vector3d(-5, 4, 3),
    vector3d(2, 8, 2),
    vector3d(3, 5, -5),
    vector3d(-3, 6, 6),
    vector3d(6, 3, 3)
]

for pos in positions:
    intensity = random.uniform(0.4, .8)
    engine.add_light(Light(position=pos, color=Color.white, intensity=intensity))

EXAMPLE_DIR = Path(__file__).parent
scripts_dir = EXAMPLE_DIR / "scripts"

cylinder = Cylinder(vector3d.zero, 2, .5, Color.light_green, 64, vector3d(40, 60, 100), "Cylinder")
cylinder.attach(scripts_dir/"cylinder.py", engine.context)
engine.add_object(cylinder)

cuboid = Cuboid(vector3d(3, 2, 5), color=Color.orange, size=vector3d(2, 1, 3))
engine.add_object(cuboid)

sphere = Sphere(vector3d(0, 5, 2), color=Color.light_blue, radius=1, rings=32, segments=64)
engine.add_object(sphere)

obj = ObjModel(name="Icosahedron", pos=vector3d(10, 5, -5), color=Color.light_green, file_path=str(EXAMPLE_DIR / "objects" / "icosahedron.obj"), scale=vector3d(1, 1, 3))
engine.add_object(obj)

text = Text(text="01", spacing=-.05, rotation=vector3d(90, 0, 0), pos=vector3d(-5, 8, 0), color=Color.white, scale=vector3d(1, 1, 3))
engine.add_object(text)

engine.save_scene("the_everything_demo.json") # Save the current scene to a JSON file

