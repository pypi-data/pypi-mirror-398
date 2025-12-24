from gamengine3d import *
from pathlib import Path

engine = Engine(1200, 800, name="Solar System Simulation", background_color=Color.black, ambient_light=.6)

EXAMPLES_DIR = Path(__file__).parent

engine.attach(EXAMPLES_DIR / "scripts" / "solar_system.py")
engine.camera.move_to(vector3d(0, 100, 190))

engine.run(60)
