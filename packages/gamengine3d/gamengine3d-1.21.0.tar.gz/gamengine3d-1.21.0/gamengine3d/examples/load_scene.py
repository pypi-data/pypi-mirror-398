"""
This demo will load the saved scene from a JSON file.
 If you haven't run the save_scene demo yet, please do so first to generate the scene file.
"""

from gamengine3d import Engine

engine = Engine(1200, 800)

engine.load_scene("the_everything_demo.json")

engine.run()
