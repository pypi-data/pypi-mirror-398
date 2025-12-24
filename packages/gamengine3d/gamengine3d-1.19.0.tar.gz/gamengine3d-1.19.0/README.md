GamEngine3D is a Python 3D engine for creating interactive 3D scenes. This README focuses on basic usage.

Quick Start

```python
from gamengine3d import *

# 1. Initialize the engine
engine = Engine(1200, 800, background_color=Color.light_blue)

# 2. Create objects
floor = Cuboid(size=vector3d(5, 0.1, 5), color=Color.light_grey, name="Floor")
player = Cuboid(name="Player", color=Color.light_red, size=vector3d(0.2), pos=vector3d(0, 1))

# 3. Add objects to the engine
engine.add_object(floor)
engine.add_object(player)

# 4. Attach behavior to objects
player.attach("player_controller.py", engine.context)

# 5. Run the engine
engine.run(dynamic_view=True)
```

Notes

Engine: Manages rendering, lights, and the main loop.

Objects: Add cubes, spheres, or custom shapes with Cuboid(), Sphere(), etc.

Attach Scripts: Use .attach("script.py", context) to add movement, input, or custom logic.

Run: engine.run() starts the simulation; dynamic_view=True enables interactive camera movement.

Example: player_controller.py

```python
from gamengine3d import *
import math

class PlayerController:
    def __init__(self, obj, context):
        self.obj = obj
        self.context = context
        self.speed = 1
        self.context.on_key_held("up", callback=self.move_forward, dt=True)

    def update(self, dt):
        pass  # called every frame

    def move_forward(self, dt):
        # simple forward movement
        yaw = math.radians(self.obj.rotation.z)
        forward = vector3d(-math.sin(yaw), 0, math.cos(yaw))
        self.obj.pos += forward * self.speed * dt
```
This minimal PlayerController shows how to attach a script to an object and respond to input.

You can run any built-in demo with ``gamengine3d demo <demo_name>`` and see all available options using ``gamengine3d demo -h``.

The 2d version of ```gamengine3d``` is out under ``gamengine2d``

Check out the full documentation for this package here: [Package Docs](https://sites.google.com/view/samarthsprojects/python-packages/gamengine3d)
