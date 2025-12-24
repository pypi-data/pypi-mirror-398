import math
import moderngl
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
import importlib.resources as pkg_resources
import numpy as np
from pyrr import Matrix44
from .helper import vector3d, ShadowVolume

class Renderer:
    def __init__(self, width=800, height=600, flags=DOUBLEBUF | OPENGL):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), flags)
        self.ctx = moderngl.create_context()
        self.ctx.viewport = (0, 0, width, height)
        self.samples = 4
        self.color_tex = self.ctx.texture((width, height), 3, samples=self.samples)
        self.depth_rbo = self.ctx.depth_renderbuffer((width, height), samples=self.samples)
        self.fbo = self.ctx.framebuffer(color_attachments=[self.color_tex], depth_attachment=self.depth_rbo)
        self.lights = []
        self.width = width
        self.height = height
        self.ambient = 0.2
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.MAX_VERTICES = 500_000

        # === Main shader ===
        self.prog = self._load_shader("default.vert", "default.frag")
        self.prog["model"].write(np.eye(4, dtype="f4").tobytes())
        self.proj = Matrix44.perspective_projection(60.0, width / height, 0.1, 100.0)
        self.view = Matrix44.look_at(
            eye=(3.0, 2.0, 3.0),
            target=(0.0, 0.0, 0.0),
            up=(0.0, 1.0, 0.0)
        )
        self.mvp = self.proj * self.view
        self.prog["mvp"].write(self.mvp.astype("f4").tobytes())
        self.prog["ambient"].value = self.ambient

        self.shadow_size = 4096
        self.shadow_depth_tex = self.ctx.depth_texture((self.shadow_size, self.shadow_size))
        try:
            self.shadow_depth_tex.repeat_x = False
            self.shadow_depth_tex.repeat_y = False
        except Exception:
            pass
        self.shadow_fbo = self.ctx.framebuffer(depth_attachment=self.shadow_depth_tex)
        self.depth_prog = self._load_shader("depth.vert", "depth.frag")
        self.light_space_matrix = np.eye(4, dtype="f4")

        self.frame_vertices = []
        self.vbo = self.ctx.buffer(reserve=self.MAX_VERTICES * 4 * 9)

        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, "3f 3f 3f", "in_vert", "in_color", "in_normal")]
        )

        self.shadow_volume = ShadowVolume(minx=-50, maxx=50, miny=-50, maxy=50, minz=1, maxz=100)

    def resize(self, width, height):
        self.width = width
        self.height = height
        pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)

        # just update viewport, don’t create a new context
        self.ctx.viewport = (0, 0, width, height)

        # update projection matrix
        aspect = width / height
        self.proj = Matrix44.perspective_projection(60.0, aspect, 0.1, 100.0)
        self.mvp = self.proj * self.view
        self.prog["mvp"].write(self.mvp.astype("f4").tobytes())

        # resize textures and framebuffers
        self.color_tex.release()
        self.color_tex = self.ctx.texture((width, height), 3, samples=self.samples)

        self.depth_rbo.release()
        self.depth_rbo = self.ctx.depth_renderbuffer((width, height), samples=self.samples)

        self.fbo.release()
        self.fbo = self.ctx.framebuffer(color_attachments=[self.color_tex], depth_attachment=self.depth_rbo)

        self._send_lights()

    def add_light(self, light):
        self.lights.append(light)

    def _compute_normal(self, p1, p2, p3):
        u = p2 - p1
        v = p3 - p1
        return u.cross(v).normalized

    def compute_light_matrix(self, light):
        light_proj = Matrix44.orthogonal_projection(self.shadow_volume.minx, self.shadow_volume.maxx, self.shadow_volume.miny, self.shadow_volume.maxy, self.shadow_volume.minz, self.shadow_volume.maxz)
        light_view = Matrix44.look_at(
            eye=light.position.totuple(),
            target=(0, 0, 0),
            up=(0, 1, 0)
        )
        return light_proj * light_view

    def render_cylinder(self, center, height, radius, color, segments=32, rotation=vector3d(0, 0, 0)):
        vertices = []

        def apply_matrix(v: vector3d, m: Matrix44) -> vector3d:
            vec4 = np.array([v.x, v.y, v.z, 1.0], dtype="f4")
            transformed = m @ vec4
            return vector3d(*transformed[:3])

        def apply_matrix_normal(n: vector3d, m: Matrix44) -> vector3d:
            vec4 = np.array([n.x, n.y, n.z, 0.0], dtype="f4")  # w=0 for direction
            transformed = m @ vec4
            return vector3d(*transformed[:3]).normalized

        rot_x = Matrix44.from_x_rotation(math.radians(rotation.x))
        rot_y = Matrix44.from_y_rotation(math.radians(rotation.y))
        rot_z = Matrix44.from_z_rotation(math.radians(rotation.z))
        rot_matrix = rot_z * rot_y * rot_x

        for i in range(segments):
            theta1 = 2 * math.pi * i / segments
            theta2 = 2 * math.pi * (i + 1) / segments

            # Top/bottom circle vertices
            top1 = vector3d(radius * math.cos(theta1), height / 2, radius * math.sin(theta1))
            top2 = vector3d(radius * math.cos(theta2), height / 2, radius * math.sin(theta2))
            bottom1 = vector3d(radius * math.cos(theta1), -height / 2, radius * math.sin(theta1))
            bottom2 = vector3d(radius * math.cos(theta2), -height / 2, radius * math.sin(theta2))

            top1 = apply_matrix(top1, rot_matrix) + center
            top2 = apply_matrix(top2, rot_matrix) + center
            bottom1 = apply_matrix(bottom1, rot_matrix) + center
            bottom2 = apply_matrix(bottom2, rot_matrix) + center

            normal1 = apply_matrix_normal(vector3d(math.cos(theta1), 0, math.sin(theta1)), rot_matrix)
            normal2 = apply_matrix_normal(vector3d(math.cos(theta2), 0, math.sin(theta2)), rot_matrix)

            # Side quad
            for tri in [(top1, bottom1, bottom2), (top1, bottom2, top2)]:
                n1 = (tri[0] - center).normalized
                n2 = (tri[1] - center).normalized
                n3 = (tri[2] - center).normalized
                vertices.extend([
                    *tri[0].totuple(), *color.to_rgb(), *n1.totuple(),
                    *tri[1].totuple(), *color.to_rgb(), *n2.totuple(),
                    *tri[2].totuple(), *color.to_rgb(), *n3.totuple(),
                ])

            # Top cap
            top_center = apply_matrix(vector3d(0, height / 2, 0), rot_matrix) + center
            normal_top = apply_matrix_normal(vector3d(0, 1, 0), rot_matrix)
            vertices.extend([
                *top_center.totuple(), *color.to_rgb(), *normal_top.totuple(),
                *top2.totuple(), *color.to_rgb(), *normal_top.totuple(),
                *top1.totuple(), *color.to_rgb(), *normal_top.totuple(),
            ])

            # Bottom cap
            bottom_center = apply_matrix(vector3d(0, -height / 2, 0), rot_matrix) + center
            normal_bottom = apply_matrix_normal(vector3d(0, -1, 0), rot_matrix)
            vertices.extend([
                *bottom_center.totuple(), *color.to_rgb(), *normal_bottom.totuple(),
                *bottom1.totuple(), *color.to_rgb(), *normal_bottom.totuple(),
                *bottom2.totuple(), *color.to_rgb(), *normal_bottom.totuple(),
            ])

        self._append_vertices(vertices)

    def render_sphere(self, center, radius, color, segments=32, rings=16):
        vertices = []
        for i in range(rings):
            theta1 = math.pi * i / rings
            theta2 = math.pi * (i + 1) / rings
            for j in range(segments):
                phi1 = 2 * math.pi * j / segments
                phi2 = 2 * math.pi * (j + 1) / segments

                p1 = vector3d(radius * math.sin(theta1) * math.cos(phi1),
                              radius * math.cos(theta1),
                              radius * math.sin(theta1) * math.sin(phi1)) + center
                p2 = vector3d(radius * math.sin(theta2) * math.cos(phi1),
                              radius * math.cos(theta2),
                              radius * math.sin(theta2) * math.sin(phi1)) + center
                p3 = vector3d(radius * math.sin(theta2) * math.cos(phi2),
                              radius * math.cos(theta2),
                              radius * math.sin(theta2) * math.sin(phi2)) + center
                p4 = vector3d(radius * math.sin(theta1) * math.cos(phi2),
                              radius * math.cos(theta1),
                              radius * math.sin(theta1) * math.sin(phi2)) + center

                for tri in [(p1, p2, p3), (p1, p3, p4)]:
                    n1 = (tri[0] - center).normalized
                    n2 = (tri[1] - center).normalized
                    n3 = (tri[2] - center).normalized
                    vertices.extend([
                        *tri[0].totuple(), *color.to_rgb(), *n1.totuple(),
                        *tri[1].totuple(), *color.to_rgb(), *n2.totuple(),
                        *tri[2].totuple(), *color.to_rgb(), *n3.totuple(),
                    ])

        self._append_vertices(vertices)

    def render_shadow_pass(self, objects):
        if not self.lights:
            return
        light = self.lights[0]
        self.light_space_matrix = self.compute_light_matrix(light)

        self.shadow_fbo.clear(depth=1.0)
        self.shadow_fbo.use()
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Batch all shadow vertices for this frame
        shadow_vertices = []

        for obj in objects:
            if not hasattr(obj, "get_corners"):
                continue
            corners = obj.get_corners()
            for face in obj.faces:
                p1, p2, p3, p4 = [corners[i] for i in face]
                # Two triangles per quad
                shadow_vertices.extend([
                    *p1.totuple(), *p2.totuple(), *p3.totuple(),
                    *p1.totuple(), *p3.totuple(), *p4.totuple()
                ])

        if shadow_vertices:
            vertices = np.array(shadow_vertices, dtype="f4")
            vbo = self.ctx.buffer(vertices.tobytes())
            vao = self.ctx.vertex_array(self.depth_prog, [(vbo, "3f", "in_vert")])
            self.depth_prog["model"].write(np.eye(4, dtype="f4").tobytes())
            self.depth_prog["light_space_matrix"].write(self.light_space_matrix.astype("f4").tobytes())
            vao.render()
            vao.release()
            vbo.release()

        self.ctx.screen.use()

    def _append_vertices(self, vertices):
        self.frame_vertices.extend(vertices)

    def flush(self):
        if not self.frame_vertices:
            return
        vertices = np.array(self.frame_vertices, dtype="f4")
        # write to the preallocated VBO
        self.vbo.write(vertices.tobytes())
        # Ensure FBO is bound before rendering (defensive; prevents bind-state drift)
        self.fbo.use()
        # send lights and shadow map uniforms
        self._send_lights()
        self.prog["light_space_matrix"].write(self.light_space_matrix.astype("f4").tobytes())
        self.shadow_depth_tex.use(location=0)
        self.prog["shadow_map"].value = 0
        # FIXED: Compute #vertices (total floats / 9 floats per vert)
        num_verts = len(vertices) // 9
        # render the pre-made VAO
        self.vao.render(vertices=num_verts)
        self.frame_vertices.clear()
    # === Modified render calls to batch ===

    def render_plane(self, p1, p2, p3, color):
        normal = self._compute_normal(p1, p2, p3)
        vertices = [
            *p1.totuple(), *color.to_rgb(), *normal.totuple(),
            *p2.totuple(), *color.to_rgb(), *normal.totuple(),
            *p3.totuple(), *color.to_rgb(), *normal.totuple()
        ]
        self._append_vertices(vertices)

    def render_quad(self, p1, p2, p3, p4, color):
        normal = self._compute_normal(p1, p2, p3)
        vertices = [
            *p1.totuple(), *color.to_rgb(), *normal.totuple(),
            *p2.totuple(), *color.to_rgb(), *normal.totuple(),
            *p3.totuple(), *color.to_rgb(), *normal.totuple(),
            *p1.totuple(), *color.to_rgb(), *normal.totuple(),
            *p3.totuple(), *color.to_rgb(), *normal.totuple(),
            *p4.totuple(), *color.to_rgb(), *normal.totuple()
        ]
        self._append_vertices(vertices)

    def _send_lights(self):
        max_lights = 8
        num_lights = min(len(self.lights), max_lights)
        self.prog["num_lights"].value = num_lights
        self.prog["ambient"].value = self.ambient
        for i in range(num_lights):
            light = self.lights[i]
            self.prog[f"lights[{i}].position"].value = light.position.totuple()
            self.prog[f"lights[{i}].color"].value = tuple(c / 255 for c in light.color.to_rgb())
            self.prog[f"lights[{i}].intensity"].value = light.intensity

    def clear(self, color):
        color_f = np.array(color.to_rgb(), dtype="f4") / 255.0
        self.fbo.clear(*color_f, depth=1.0)
        self.fbo.use()
        self.frame_vertices.clear()

    def swap(self):
        self.flush()  # Render everything in one draw call
        self.ctx.copy_framebuffer(dst=self.ctx.screen, src=self.fbo)
        pygame.display.flip()

    def quit(self):
        pygame.quit()

    def _load_shader(self, vert_name, frag_name):
        vert_src = pkg_resources.read_text(f"{__package__}.shaders", vert_name)
        frag_src = pkg_resources.read_text(f"{__package__}.shaders", frag_name)
        return self.ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)

class Camera:
    def __init__(self, position=None, target=None, up=None, fov=60.0, aspect_ratio=4/3, near=0.1, far=100.0, orbiting=True):
        self.orbiting = orbiting  # New: toggle automatic look-at behavior
        self.target = target or vector3d(0, 0, 0)
        self.up = up or vector3d.up
        self.fov = fov
        self.aspect_ratio = aspect_ratio
        self.near = near
        self.far = far

        # Compute spherical coordinates from initial position
        pos = position or vector3d(3, 2, 3)
        if self.orbiting:
            self._update_spherical(pos)
        self.position = pos

        self._update_position()

    def move_to(self, new_position: vector3d):
        """
        Move the camera to a new position.
        If orbiting is enabled, updates spherical coordinates.
        If orbiting is disabled, just sets position directly.
        """
        self.position = new_position
        if self.orbiting:
            self._update_spherical(new_position)
        self._update_position()

    def set_orbiting(self, orbiting: bool):
        """Enable or disable automatic look-at behavior."""
        self.orbiting = orbiting

    def _update_spherical(self, pos):
        """Convert position to spherical coordinates relative to target."""
        dir_vec = pos - self.target
        self.radius = dir_vec.magnitude
        self.azimuth = math.atan2(dir_vec.z, dir_vec.x)  # yaw
        self.elevation = math.asin(dir_vec.y / self.radius)  # pitch

    def _update_position(self):
        if self.orbiting:
            x = self.radius * math.cos(self.elevation) * math.cos(self.azimuth)
            y = self.radius * math.sin(self.elevation)
            z = self.radius * math.cos(self.elevation) * math.sin(self.azimuth)
            self.position = self.target + vector3d(x, y, z)

        look_at = self.target if self.orbiting else self.position + getattr(self, "look_dir", vector3d(0, 0, -1))

        self.view_matrix = Matrix44.look_at(
            self.position.totuple(),
            look_at.totuple(),
            self.up.totuple()
        )

        self.near = max(self.radius * 0.001, 1e-4)
        self.far = self.radius * 10_000
        self.projection_matrix = Matrix44.perspective_projection(
            self.fov, self.aspect_ratio, self.near, self.far
        )


    def rotate_around_target(self, delta_azimuth_degrees, delta_elevation_degrees):
        if not self.orbiting:
            return  # rotation disabled in free mode

        self.azimuth += math.radians(delta_azimuth_degrees)
        self.elevation += math.radians(delta_elevation_degrees)

        # Handle elevation wrapping to allow full rotation without flipping
        while self.elevation > math.pi / 2:
            self.elevation = math.pi - self.elevation
            self.azimuth += math.pi
            self.up = -self.up  # flip up vector

        while self.elevation < -math.pi / 2:
            self.elevation = -math.pi - self.elevation
            self.azimuth += math.pi
            self.up = -self.up  # flip up vector

        self._update_position()


    def zoom(self, amount):
        """
        Dolly zoom:
        Positive amount moves forward
        Negative amount moves backward
        """

        # Forward direction
        if self.orbiting:
            forward = (self.target - self.position).normalized
        else:
            forward = getattr(self, "look_dir", vector3d(0, 0, -1)).normalized

        # Move camera
        delta = forward * amount
        self.position += delta

        if self.orbiting:
            self._update_spherical(self.position)

        self._update_position()

    def update_renderer(self, renderer: Renderer):
        renderer.view = self.view_matrix
        renderer.proj = self.projection_matrix
        renderer.mvp = renderer.proj * renderer.view
        renderer.prog["mvp"].write(renderer.mvp.astype("f4").tobytes())

    def look_at(self, point: vector3d):
        """
        Make the camera look at a specific point in space.
        - In orbiting mode, sets the target and updates spherical coordinates.
        - In free mode, sets the look direction vector.
        """
        if self.orbiting:
            self.target = point
            self._update_spherical(self.position)
        else:
            self.look_dir = (point - self.position).normalized  # direction vector in free mode

        self._update_position()
