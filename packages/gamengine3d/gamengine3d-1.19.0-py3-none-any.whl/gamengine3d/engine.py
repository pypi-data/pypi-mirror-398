import json
from itertools import product
from pyrr import Matrix44
from .context import Context
import pygame
from .game_objects import Cuboid, GameObject, Sphere, Cylinder, ObjModel, Text
from .helper import vector3d, Color, Light, EngineError, Script
from .renderer import Renderer, Camera
import math

class Engine:
    def __init__(self, width=500, height=500, resizable=True, name="GamEngine3d", background_color=Color.light_grey, ambient_light=.2):
        self.width = width
        self.height = height
        self.resizable = resizable
        self.window_name = name
        self.background_color = background_color
        self.scripts = []
        self.script_paths = []

        flags = pygame.DOUBLEBUF | pygame.OPENGL
        if self.resizable:
            flags |= pygame.RESIZABLE

        pygame.display.set_caption(self.window_name)
        self.renderer = Renderer(width, height, flags=flags)
        self.renderer.ambient = ambient_light
        self.clock = pygame.time.Clock()

        self.camera = Camera(position=vector3d(0, 1.5, 3),
                             target=vector3d(0, 0, 0),
                             aspect_ratio=self.width / self.height)

        self.last_mouse_pos = None
        self.mouse_sensitivity = 0.3
        self.pan_sensitivity = 0.005
        self.active_button = None

        self.gameobjects = []

        self.context = Context()

        self.context.functions.draw_cube = self.draw_cuboid
        self.context.functions.draw_sphere = self.draw_sphere
        self.context.functions.add_light = self.add_light
        self.context.functions.add_object = self.add_object
        self.context.functions.draw_cylinder = self.draw_cylinder
        self.context.functions.get_game_object = self.get_object
        self.context.functions.is_colliding = self.is_colliding
        self.context.functions.remove_light = self.remove_light
        self.context.functions.remove_object = self.remove_object
        self.context.functions.is_colliding_pos = self.is_colliding_pos
        self.context.functions.save_scene = self.save_scene
        self.context.functions.load_scene = self.load_scene

        self.context.game_objects = self.gameobjects
        self.context.engine = self
        self.context.camera = self.camera
        self.context.renderer = self.renderer
        self.context.clock = self.clock

        self.context.lights = self.renderer.lights
        self.context.ambient_light = ambient_light

    def run(self, fps=60, dynamic_view=True):
        running = True
        self.context.fps = fps
        keys_held = []
        self.context.keys_held = keys_held
        self.init_scripts()

        for script in self.scripts:
            script.run("on_start")

        while running:
            keys_pressed = []
            keys_released = []
            dt = self.clock.get_time() / 1000
            self.mouse_sensitivity = self.context.mouse_sensitivity
            self.pan_sensitivity = self.context.pan_sensitivity
            self.context.fps = self.clock.get_fps()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.resizable and event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.renderer.resize(self.width, self.height)

                    self.camera.aspect_ratio = self.width / self.height

                    old_pos = self.camera.position.copy()
                    self.camera.move_to(vector3d.one)
                    self.camera.move_to(old_pos)

                if dynamic_view:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button in (1, 3):  # Left or right
                            self.last_mouse_pos = pygame.mouse.get_pos()
                            self.active_button = event.button
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button in (1, 3):
                            self.last_mouse_pos = None
                            self.active_button = None

                    elif event.type == pygame.MOUSEMOTION:
                        if self.last_mouse_pos is not None:
                            x, y = pygame.mouse.get_pos()
                            dx = x - self.last_mouse_pos[0]
                            dy = y - self.last_mouse_pos[1]
                            self.last_mouse_pos = (x, y)

                            if self.active_button == 3:
                                self.camera.rotate_around_target(-dx * self.mouse_sensitivity, dy * self.mouse_sensitivity)

                            elif self.active_button == 1:
                                self._pan_camera(dx, dy)

                    elif event.type == pygame.MOUSEWHEEL:
                        self.camera.zoom(event.y * 0.5)

                if event.type == pygame.KEYDOWN:
                    key_name = pygame.key.name(event.key)
                    keys_pressed.append(key_name)
                    keys_held.append(key_name)

                elif event.type == pygame.KEYUP:
                    key_name = pygame.key.name(event.key)
                    keys_held.remove(key_name)
                    keys_released.append(key_name)

            self.context.keys_pressed = keys_pressed
            self.context.keys_released = keys_released
            self.context.update(dt)

            self.renderer.render_shadow_pass(self.gameobjects)
            self.renderer.clear(self.background_color)
            self.camera.update_renderer(self.renderer)

            self.renderer.ambient = self.context.ambient_light

            for script in self.scripts:
                script.update(dt)

            for obj in self.gameobjects:
                self.context.push_caller(obj)
                obj.update(dt)
                obj.draw(self.renderer)

            if self.context.exit:
                running = False

            self.renderer.flush()
            self.renderer.swap()
            self.clock.tick(fps)

        for script in self.scripts:
            script.run("on_exit")
        self.renderer.quit()

    def _pan_camera(self, dx, dy):
        forward = (self.camera.target - self.camera.position).normalized
        right = forward.cross(self.camera.up).normalized
        up = self.camera.up.normalized

        pan = (right * -dx + up * dy) * self.pan_sensitivity * self.camera.radius
        self.camera.target += pan
        self.camera.position += pan
        self.camera._update_position()

    def add_light(self, light):
        self.renderer.add_light(light)
        if light.show:
            self.add_object(Sphere(pos=light.position, color=light.color, radius=.1))

    def add_object(self, obj: GameObject):
        self.gameobjects.append(obj)

    def remove_object(self, name):
        obj = self.get_object(name)
        self.gameobjects.remove(obj)

    def remove_light(self, name):
        for light in self.renderer.lights:
            if light.name == name:
                self.renderer.lights.remove(light)
                return

        raise EngineError(f"No Light Object Named {name}")

    def get_object(self, name):
        for obj in self.gameobjects:
            if obj.name == name:
                return obj

        raise EngineError(f"Game Object with name {name} not found")

    def is_colliding(self, name1, name2):
        obj1 = self.get_object(name1)
        obj2 = self.get_object(name2)

        if not (isinstance(obj1, Cuboid) and isinstance(obj2, Cuboid)):
            raise NotImplementedError(f"Cylinder And Sphere Collision Not Implemented")

        corners = obj1.get_corners()
        for corner in corners:
            if obj2.is_point_in(corner):
                return True

        return False

    def is_colliding_pos(self, name, pos):
        obj = self.get_object(name)
        if not isinstance(obj, Cuboid):
            raise NotImplementedError(f"Cylinder And Sphere Collision Not Implemented")

        return obj.is_point_in(pos)

    def draw_cuboid(self, pos: vector3d=vector3d.zero, size: vector3d=vector3d(2), rotation: vector3d=vector3d.zero, color: Color = Color.light_blue):
        faces = [
            [0, 1, 3, 2],
            [4, 6, 7, 5],
            [0, 4, 5, 1],
            [2, 3, 7, 6],
            [0, 2, 6, 4],
            [1, 5, 7, 3],
        ]

        half_size = size / 2

        rot_matrix = Matrix44.from_eulers((
            math.radians(rotation.x),
            math.radians(rotation.y),
            math.radians(rotation.z)
        ))

        corners = []
        for dx, dy, dz in product([-1, 1], repeat=3):
            local = vector3d(dx * half_size.x, dy * half_size.y, dz * half_size.z)

            rotated = vector3d(
                *(rot_matrix @ [local.x, local.y, local.z, 1.0])[:3]
            )

            world = pos + rotated
            corners.append(world)

        for face_idx in faces:
            self.renderer.render_quad(
                corners[face_idx[0]],
                corners[face_idx[1]],
                corners[face_idx[2]],
                corners[face_idx[3]],
                color=color
            )

    def draw_sphere(self, pos: vector3d=vector3d.zero, radius: int=2, color: Color=Color.light_red, segments=32, rings=16):
        self.renderer.render_sphere(center=pos, radius=radius, color=color, segments=segments, rings=rings)

    def draw_cylinder(self, pos: vector3d=vector3d.zero, length: int=2, radius: int=.5, color: Color=Color.light_yellow, segments: int=32, rotation: vector3d=vector3d.zero):
        self.renderer.render_cylinder(center=pos, height=length, radius=radius, color=color, segments=segments, rotation=rotation)

    def attach(self, path):
        script = Script(self, path, self.context)
        script.init_instance()
        self.script_paths.append(path)
        self.scripts.append(script)

    def attach_scripts(self, scripts):
        for path in scripts:
            self.attach(path)

    def init_scripts(self):
        for script in self.scripts:
            script.init_instance()

    def physics_update(self, dt):
        for obj in self.gameobjects:
            if isinstance(obj, Cuboid):
                cube = obj
                rb = cube.rigid_body
                if rb is not None:
                    if rb.gravity:
                        rb.velocity += vector3d.down * 9.8 * dt

                    # integrate forces
                    rb.velocity += (rb.forces / rb.mass) * dt
                    rb.forces = vector3d.zero

                    # integrate movement
                    cube.pos += rb.velocity * dt

    def resolve_collision(self, name1, name2):
        obj1 = self.get_object(name1)
        obj2 = self.get_object(name2)

        if not (isinstance(obj1, Cuboid) and isinstance(obj2, Cuboid)):
            raise NotImplementedError("Cylinder And Sphere Collision Not Implemented")

        # If they do not overlap, exit
        if not self.is_colliding(name1, name2):
            return

        rb = obj1.rigid_body  # the moving object
        # obj2 may or may not have rigid body — we treat it as static for now

        # Determine correction direction by checking corners
        corners = obj1.get_corners()

        min_penetration = float("inf")
        best_axis = None

        for corner in corners:
            if obj2.is_point_in(corner):
                # penetration vector = from obj2 center to corner
                penetration_vec = corner - obj2.pos
                # absolute magnitude along each axis
                px = abs(penetration_vec.x)
                py = abs(penetration_vec.y)
                pz = abs(penetration_vec.z)

                # pick smallest axis penetration
                axis_val = min(px, py, pz)
                if axis_val < min_penetration:
                    min_penetration = axis_val
                    if axis_val == px:
                        best_axis = vector3d.right if penetration_vec.x > 0 else vector3d.left
                    elif axis_val == py:
                        best_axis = vector3d.up if penetration_vec.y > 0 else vector3d.down
                    else:
                        best_axis = vector3d.forward if penetration_vec.z > 0 else vector3d.back

        if best_axis is None:
            return

        correction = best_axis * min_penetration
        obj1.pos += correction

        normal = best_axis.normalized()
        vel_along_normal = rb.velocity.dot(normal)

        if vel_along_normal < 0:
            rb.velocity -= (1 + rb.bounce) * vel_along_normal * normal

    def save_scene(self, filename):
        all_gameobjects = []
        for obj in self.gameobjects:
            all_gameobjects.append(obj.serialize())

        all_lights = []
        for light in self.renderer.lights:
            all_lights.append(light.serialize())

        context_attrs = self.context.serialize()

        with open(filename, "w") as f:
            json.dump({"game-objects": all_gameobjects, "lights": all_lights, "engine": self.serialize(), "context": context_attrs}, f, indent=4)

    def load_scene(self, filename):
        with open(filename, "r") as f:
            data = json.load(f)

        self.context.deserialize(data["context"])

        lights = data["lights"]
        for light in lights:
            self.renderer.add_light(Light.deserialize(light))

        gameobjects = data["game-objects"]
        for gameobject in gameobjects:
            if gameobject["type"] == "cuboid":
                obj = Cuboid.deserialize(gameobject, self.context)
                self.add_object(obj)

            elif gameobject["type"] == "sphere":
                obj = Sphere.deserialize(gameobject, self.context)
                self.add_object(obj)

            elif gameobject["type"] == "cylinder":
                obj = Cylinder.deserialize(gameobject, self.context)
                self.add_object(obj)

            elif gameobject["type"] == "obj-model":
                obj = ObjModel.deserialize(gameobject, self.context)
                self.add_object(obj)

            elif gameobject["type"] == "text":
                obj = Text.deserialize(gameobject, self.context)
                self.add_object(obj)

        engine = data["engine"]
        self.deserialize(engine)

    def serialize(self):
        return {
            "ambient_light": self.renderer.ambient,
            "background_color": self.background_color.to_rgb(),
            "scripts": self.script_paths,
        }

    def deserialize(self, data):
        ambient_light = data["ambient_light"]
        background_color = data["background_color"]
        scripts = data["scripts"]

        self.renderer.ambient = ambient_light
        self.background_color = Color.RGB(*background_color)
        self.attach_scripts(scripts)
