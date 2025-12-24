from pathlib import Path
from gamengine3d import Engine, vector3d, Color, Cuboid, Light, DirectionalLight

# Initialize engine
engine = Engine(
    1200, 800,
    background_color=Color.light_blue,
    ambient_light=0.3,
    name="Player Movement Demo"
)

# Room setup
room_size = vector3d(5, 1.5, 2.5)
half_size = room_size / 2
room_color = Color.white
light_intensity = 0.3

# Camera positioning
engine.camera.move_to(vector3d(0.0, 1.4, 2.3))

# Floor
floor = Cuboid(
    size=vector3d(room_size.x, 1, room_size.z),
    color=Color.light_grey,
    name="Floor",
    pos=vector3d(0, 0.05 - 0.5)
)
engine.add_object(floor)

# Walls
left_wall = Cuboid(
    pos=vector3d(-half_size.x, half_size.y, 0),
    size=vector3d(0.1, room_size.y, room_size.z),
    color=room_color,
    name="Left"
)
engine.add_object(left_wall)

right_wall = Cuboid(
    pos=vector3d(half_size.x, half_size.y, 0),
    size=vector3d(0.1, room_size.y, room_size.z),
    color=room_color,
    name="Right"
)
engine.add_object(right_wall)

back_wall = Cuboid(
    pos=vector3d(0, half_size.y, -half_size.z),
    size=vector3d(room_size.x, room_size.y, 0.1),
    color=room_color,
    name="Back"
)
engine.add_object(back_wall)

# Player
player = Cuboid(
    name="Player",
    color=Color.light_red,
    size=vector3d(0.2),
    pos=vector3d(0, 1)
)
EXAMPLE_DIR = Path(__file__).parent
player_script = EXAMPLE_DIR / "scripts" / "player_movement.py" # get the player_movement script path

player.attach(player_script, engine.context)  # attach movement script
# you can directly add a relative path like "scripts/player_movement.py"

engine.add_object(player)

# Lights
engine.add_light(DirectionalLight(
    position=vector3d(1/3 * room_size.x, room_size.y, 1),
    color=Color.white,
    intensity=light_intensity,
    rotation=vector3d.zero
))
engine.add_light(DirectionalLight(
    position=vector3d(-1/3 * room_size.x, room_size.y, 1),
    color=Color.white,
    intensity=light_intensity,
    rotation=vector3d.zero
))

engine.run(dynamic_view=True)
