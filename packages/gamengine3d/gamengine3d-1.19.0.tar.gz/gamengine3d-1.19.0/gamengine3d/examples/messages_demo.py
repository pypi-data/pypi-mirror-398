from gamengine3d import Engine, Cuboid, vector3d, Light, Color
from pathlib import Path

EXAMPLE_DIR = Path(__file__).parent
messanger_script = EXAMPLE_DIR / "scripts" / "messanger_script.py"
receiver_script = EXAMPLE_DIR / "scripts" / "message_receiver.py"

engine = Engine(1200, 800, name="Messages Demo")

cuboid = Cuboid(name="Cuboid1")
cuboid.attach(messanger_script, engine.context)


cuboid2 = Cuboid(name="Cuboid2", pos=vector3d(6, 3, 6), color=Color.light_blue)
cuboid2.attach(receiver_script, engine.context)
engine.add_object(cuboid2)

engine.add_light(Light(position=vector3d(0, 5, .0001), color=Color.white))

engine.add_object(cuboid)

engine.run()
