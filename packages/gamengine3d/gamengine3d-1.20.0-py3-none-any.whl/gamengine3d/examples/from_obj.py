from gamengine3d import Engine, Color, vector3d, Light, ObjModel
from pathlib import Path

EXAMPLE_DIR = Path(__file__).parent

engine = Engine(1200, 800, background_color=Color.light_grey, ambient_light=.5, name="Loading an OBJ File")

obj = ObjModel(name="Icosahedron", pos=vector3d(4, 2, 1), color=Color.blue, file_path=str(EXAMPLE_DIR / "objects" / "icosahedron.obj"), scale=vector3d(1, 2, 4))

engine.add_object(obj)

engine.add_light(Light(vector3d(20, 20, 20), Color.white, 0.8))

engine.run()
