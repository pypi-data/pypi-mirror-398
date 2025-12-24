from pathlib import Path
from gamengine3d import Engine, vector3d, Color, Cuboid, Light, DirectionalLight, ObjModel

# Initialize engine
engine = Engine(
    1200, 800,
    background_color=Color.light_blue,
    ambient_light=0.1,
    name="Player Movement Demo"
)

EXAMPLE_DIR = Path(__file__).parent

def add_light(pos): # function to add a light
    global engine

    engine.add_object(Cuboid(
        pos=pos,
        size=vector3d(.5, .05, .5),
        color=Color.white,
        emit=True
    ))
    engine.add_light(DirectionalLight(
        position=pos,
        color=Color.white,
        intensity=light_intensity,
        rotation=vector3d.zero
    ))

def add_bench(pos, color): # function to add a bench. You can run gamengine3d demo from_obj to see how it works.
    global engine

    engine.add_object(ObjModel(file_path=str(EXAMPLE_DIR/"objects"/"bench.obj"), scale=vector3d(.25), pos=pos, color=color))

# Room setup
room_size = vector3d(10, 1.5, 11)
half_size = room_size / 2
room_color = Color.white
light_intensity = 0.3

# Camera positioning
engine.camera.move_to(vector3d(0.0, 1.4, 2.3))

# Disable shadows
engine.renderer.shadows = False

# Floor
floor = Cuboid(
    size=vector3d(room_size.x, 1, room_size.z),
    color=Color.light_grey,
    name="Floor",
    pos=vector3d(0, 0.05 - 0.5)
)
engine.add_object(floor)

# Ceiling
ceiling = Cuboid(
    size=vector3d(room_size.x, 1, room_size.z),
    color=Color.light_grey,
    name="Ceiling",
    pos=vector3d(0, room_size.y + .5, 0)
)
engine.add_object(ceiling)

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

front_wall = Cuboid(
    pos=vector3d(0, half_size.y, half_size.z),
    size=vector3d(room_size.x, room_size.y, 0.1),
    color=room_color,
    name="Front"
)
engine.add_object(front_wall)
# Player
player = Cuboid(
    name="Player",
    color=Color.light_red,
    size=vector3d(0.2),
    pos=vector3d(0, 1)
)
player_script = EXAMPLE_DIR / "scripts" / "player_movement.py" # get the player_movement script path

player.attach(player_script, engine.context)  # attach movement script
# you can directly add a relative path like "scripts/player_movement.py"

engine.add_object(player)

# Lights
add_light(vector3d(0, room_size.y-.001, 0.0001))
add_light(vector3d(1/3 * room_size.x, room_size.y-.001, 1/3 * room_size.z))
add_light(vector3d(1/3 * room_size.x, room_size.y-.001, -1/3 * room_size.z))
add_light(vector3d(-1/3 * room_size.x, room_size.y-.001, 1/3 * room_size.z))
add_light(vector3d(-1/3 * room_size.x, room_size.y-.001, -1/3 * room_size.z))

add_light(vector3d(-1/3 * room_size.x, room_size.y-.001, 0))
add_light(vector3d(1/3 * room_size.x, room_size.y-.001, 0))
add_light(vector3d(0, room_size.y-.001, 1/3 * room_size.z))
add_light(vector3d(0, room_size.y-.001, -1/3 * room_size.z))

# Benches
add_bench(vector3d(1/3 * room_size.x, .05, 1/3 * room_size.z), Color.light_red)
add_bench(vector3d(1/3 * room_size.x, .05, -1/3 * room_size.z), Color.light_green)
add_bench(vector3d(-1/3 * room_size.x, .05, 1/3 * room_size.z), Color.light_yellow)
add_bench(vector3d(-1/3 * room_size.x, .05, -1/3 * room_size.z), Color.light_blue)

engine.run(dynamic_view=False)
