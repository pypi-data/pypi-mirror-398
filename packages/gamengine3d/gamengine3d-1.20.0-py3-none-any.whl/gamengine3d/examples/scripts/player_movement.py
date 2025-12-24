from gamengine3d import vector3d, Context, Cuboid
from gamengine3d.helper import get_forward

class PlayerMovement:  # Class name must match file name in PascalCase
    def __init__(self, obj: Cuboid, context: Context):
        self.obj = obj
        self.context = context

        self.speed = 1                  # units per second
        self.rotate_speed = 100         # degrees per second
        self.gravity = vector3d(0, -4.8, 0)
        self.velocity = vector3d.zero
        self.obj.visible = False

        # Movement bindings
        self.context.on_key_held("w", callback=self.handle_controls, dt=True, args=["forward"])
        self.context.on_key_held("s", callback=self.handle_controls, dt=True, args=["backward"])
        self.context.on_key_held("a", callback=self.handle_controls, dt=True, args=["left"])
        self.context.on_key_held("d", callback=self.handle_controls, dt=True, args=["right"])
        self.context.on_key_held("space", callback=self.handle_controls, dt=True, args=["up"])

        self.obj.rotation = vector3d(0)  # start facing forward
        self.context.camera.set_orbiting(False)


    def update(self, dt):
        # Gravity runs every frame
        self.handle_gravity(dt)
        self.handle_camera()


    def handle_controls(self, dt, direction):
        forward = get_forward(self.obj.rotation)  # forward relative to facing direction

        if direction == "forward":
            delta_pos = forward * self.speed * dt
            self.obj.pos += delta_pos

            # undo if hitting walls
            if any([
                self.context.functions.is_colliding(self.obj.name, "Left"),
                self.context.functions.is_colliding(self.obj.name, "Right"),
                self.context.functions.is_colliding(self.obj.name, "Back"),
            ]):
                self.obj.pos -= delta_pos

        elif direction == "backward":
            delta_pos = forward * self.speed * dt
            self.obj.pos -= delta_pos

            # undo if hitting walls
            if any([
                self.context.functions.is_colliding(self.obj.name, "Left"),
                self.context.functions.is_colliding(self.obj.name, "Right"),
                self.context.functions.is_colliding(self.obj.name, "Back"),
            ]):
                self.obj.pos += delta_pos

        elif direction == "left":
            self.obj.rotation.z -= self.rotate_speed * dt  # turn left

        elif direction == "right":
            self.obj.rotation.z += self.rotate_speed * dt  # turn right

        elif direction == "up":
            # jump only if grounded
            if self.context.functions.is_colliding(self.obj.name, "Floor"):
                self.velocity.y = 3
                self.obj.pos.y += 0.1  # small lift to ensure gravity applies next frame


    def handle_gravity(self, dt):
        grounded = self.context.functions.is_colliding(self.obj.name, "Floor")

        if not grounded:
            self.velocity += self.gravity * dt  # accelerate downward
        else:
            floor = self.context.functions.get_game_object("Floor")
            self.obj.pos.y = floor.pos.y + floor.size.y/2 + self.obj.size.y/2  # snap to surface
            self.velocity = vector3d.zero

        # check predicted collision next frame
        if self.context.functions.is_colliding_pos("Floor", self.obj.pos + self.velocity * dt):
            floor = self.context.functions.get_game_object("Floor")
            self.obj.pos.y = floor.pos.y + floor.size.y/2 + self.obj.size.y/2
        else:
            self.obj.pos += self.velocity * dt  # apply gravity motion



    def handle_camera(self):
        forward = get_forward(self.obj.rotation).normalized  # ensure no zero vector issues
        eye_height = self.obj.size.y * 0.9  # adjust for player height
        cam_pos = self.obj.pos + vector3d(0, eye_height, 0)  # camera at eye level
        look_target = cam_pos + forward  # look straight ahead
        self.context.camera.move_to(cam_pos)
        self.context.camera.look_at(look_target)
