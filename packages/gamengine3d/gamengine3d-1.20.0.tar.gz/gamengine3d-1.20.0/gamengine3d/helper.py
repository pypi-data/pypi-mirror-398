import sys
import importlib.util
import math
import moderngl
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
import importlib.resources as pkg_resources
import numpy as np
from pyrr import Matrix44
import os
import time

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget(owner)

class vector3d:
    def __init__(self, x, y=None, z=None):
        self.x = x
        self.y = y
        self.z = z

        if y is None and z is None:
            self.y = self.x
            self.z = self.x
        elif z is None:
            self.z = 0.0

    @property
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    @property
    def sqr_magnitude(self):
        return self.x**2 + self.y**2 + self.z**2

    def normalize(self):
        magnitude = self.magnitude
        if magnitude != 0:
            self.x /= magnitude
            self.y /= magnitude
            self.z /= magnitude

    @property
    def normalized(self):
        magnitude = self.magnitude
        if magnitude == 0:
            return vector3d(0, 0, 0)
        return vector3d(self.x / magnitude, self.y / magnitude, self.z / magnitude)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return vector3d(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
            )

    def __add__(self, other):
        if isinstance(other, vector3d):
            return vector3d(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            return vector3d(self.x + other, self.y + other, self.z + other)

    def __sub__(self, other):
        if isinstance(other, vector3d):
            return vector3d(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            return vector3d(self.x - other, self.y - other, self.z - other)

    def __mul__(self, other):
        if isinstance(other, vector3d):
            return vector3d(self.x * other.x, self.y * other.y, self.z * other.z)
        else:
            return vector3d(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        if isinstance(other, vector3d):
            return vector3d(self.x / other.x, self.y / other.y, self.z / other.z)
        else:
            return vector3d(self.x / other, self.y / other, self.z / other)

    def totuple(self):
        return (self.x, self.y, self.z)

    def __radd__(self, other):
        return vector3d(self.x + other, self.y + other, self.z + other)

    def __rsub__(self, other):
        return vector3d(self.x - other, self.y - other, self.z - other)

    def __rtruediv__(self, other):
        return vector3d(self.x / other, self.y / other, self.z / other)

    def __rmul__(self, other):
        return vector3d(self.x * other, self.y * other, self.z * other)

    @classmethod
    def fromtuple(cls, tuple):
        return cls(*tuple)

    def __repr__(self):
        return f"vector3d({self.x}, {self.y}, {self.z})"

    def copy(self):
        return vector3d(self.x, self.y, self.z)

    def __neg__(self):
        return vector3d(-self.x, -self.y, -self.z)

    @classproperty
    def up(cls):
        return cls(0, 1, 0)

    @classproperty
    def down(cls):
        return cls(0, -1, 0)

    @classproperty
    def right(cls):
        return cls(1, 0, 0)

    @classproperty
    def left(cls):
        return cls(-1, 0, 0)

    @classproperty
    def forward(cls):
        return cls(0, 0, 1)

    @classproperty
    def back(cls):
        return cls(0, 0, -1)

    @classproperty
    def one(cls):
        return cls(1, 1, 1)

    @classproperty
    def zero(cls):
        return cls(0, 0, 0)

class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def RGB(r, g, b): return Color(r, g, b)

    @staticmethod
    def hex(hex_string):
        if not hex_string.startswith("#"): raise Exception("String must start with #")
        if not len(hex_string) == 7: raise Exception("String must contain 7 characters")
        r = int(hex_string[1:3], 16)
        g = int(hex_string[3:5], 16)
        b = int(hex_string[5:7], 16)
        return Color(r, g, b)

    def __eq__(self, other):
        if self.r == other.r and self.g == other.g and self.b == other.b:
            return True
        return False

    def to_hex(self):
        if not all(0 <= x <= 255 for x in (self.r, self.g, self.b)):
            raise ValueError("RGB values must be in the range 0-255")
        return "#{:02X}{:02X}{:02X}".format(self.r, self.g, self.b)

    def to_rgb(self):
        return self.r, self.g, self.b

    @classproperty
    def black(cls):
        return cls(0, 0, 0)

    @classproperty
    def white(cls):
        return cls(255, 255, 255)

    @classproperty
    def red(cls): return cls(255, 0, 0)

    @classproperty
    def green(cls): return cls(0, 255, 0)

    @classproperty
    def blue(cls): return cls(0, 0, 255)

    @classproperty
    def yellow(cls): return cls(255, 255, 0)

    @classproperty
    def cyan(cls): return cls(0, 255, 255)

    @classproperty
    def magenta(cls): return cls(255, 0, 255)

    @classproperty
    def grey(cls): return cls(33, 33, 33)

    @classproperty
    def light_grey(cls): return cls(80, 80, 80)

    @classproperty
    def light_red(cls): return cls(253, 89, 111)

    @classproperty
    def light_green(cls): return cls(0, 190, 160)

    @classproperty
    def light_yellow(cls): return cls(254, 208, 95)

    @classproperty
    def orange(cls): return cls(254, 166, 93)

    @classproperty
    def light_blue(cls): return cls(109, 154, 218)

class Light:
    def __init__(self, position: vector3d, color: Color, intensity: float = 1.0, show=False, name="Light"):
        self.position = position
        self.color = color
        self.intensity = intensity
        self.show = show
        self.name = name

    def serialize(self):
        return {
            "position": self.position.totuple(),
            "color": self.color.to_rgb(),
            "intensity": self.intensity,
            "show": self.show,
            "name": self.name,
        }

    @staticmethod
    def deserialize(data):
        position = data["position"]
        color = data["color"]
        intensity = data["intensity"]
        show = data["show"]
        name = data["name"]

        return Light(position=vector3d.fromtuple(position), color=Color.RGB(*color), intensity=intensity, show=show, name=name)

class DirectionalLight:
    def __init__(
            self,
            rotation: vector3d,       # rotation defines direction
            color: Color,
            intensity: float = 1.0,
            position: vector3d = vector3d.zero,   # directional lights can have a position
            show: bool = False,
            name: str = "DirectionalLight"
    ):
        self.rotation = rotation
        self.position = position
        self.color = color
        self.intensity = intensity
        self.show = show
        self.name = name

        # compute forward direction from rotation
        self.direction = self._compute_direction()

    def _compute_direction(self):
        """Turn rotation (Euler angles in degrees) into a normalized direction vector."""

        # Convert to radians
        rx = math.radians(self.rotation.x)
        ry = math.radians(self.rotation.y)
        rz = math.radians(self.rotation.z)

        # Rotation matrices in ZYX order (standard for camera/light)
        cz, sz = math.cos(rz), math.sin(rz)
        cy, sy = math.cos(ry), math.sin(ry)
        cx, sx = math.cos(rx), math.sin(rx)

        # Forward vector through rotation matrix
        # This matches right-handed forward = +Z convention
        m00 = cy * cz
        m01 = cz * sx * sy - cx * sz
        m02 = sx * sz + cx * cz * sy

        # Forward direction = (m02, m12, m22) depending on convention
        # You use Z-forward, so:
        forward = vector3d(m02, -(sx * cy), cy * cx)

        return forward.normalized

    # ---------------------- Serialization -------------------------

    def serialize(self):
        return {
            "rotation": self.rotation.totuple(),
            "position": self.position.totuple(),
            "color": self.color.to_rgb(),
            "intensity": self.intensity,
            "show": self.show,
            "name": self.name,
        }

    @staticmethod
    def deserialize(data):
        rotation = vector3d.fromtuple(data["rotation"])
        position = vector3d.fromtuple(data["position"])
        color = Color.RGB(*data["color"])
        intensity = data["intensity"]
        show = data["show"]
        name = data["name"]

        return DirectionalLight(
            rotation=rotation,
            position=position,
            color=color,
            intensity=intensity,
            show=show,
            name=name
        )

class Script:
    def __init__(self, obj, script_path, context):
        self.obj = obj
        self.context = context
        self.script_path = script_path
        self.module = None
        self.cls = None
        self.instance = None
        self.load(script_path)

    def load(self, path):
        if not os.path.exists(path):
            print(f"[Script] File not found: {path}")
            return
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[Script] Error loading module {path}: {e}")
            return
        self.module = module

        # Class is PascalCase version of file name
        class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        if hasattr(module, class_name):
            self.cls = getattr(module, class_name)
        else:
            print(f"[Script] No class '{class_name}' found in {path}")

    def init_instance(self):
        if self.cls is None or self.instance is not None:
            return
        try:
            self.instance = self.cls(self.obj, self.context)
        except Exception as e:
            print(f"[Script] Failed to instantiate script for {self.obj.name if hasattr(self.obj, "name") else "Engine"}: {e}")
            self.instance = None

        if self.instance and hasattr(self.instance, "start"):
            try:
                self.instance.start()
            except Exception:
                pass

    def update(self, dt):
        if self.instance is None:
            return
        self.instance.update(dt)

    def run(self, func_name):
        if self.instance is None:
            return

        if hasattr(self.instance, func_name):
            func = getattr(self.instance, func_name)
            func()

class EngineError(Exception):
    pass

class Message:
    def __init__(self, message, sender):
        self.message = message
        self.sender = sender
        self.time = time.time()

    def __repr__(self):
        return f"Message({self.message=}, {self.sender=}, {self.time=})"

class RigidBody:
    def __init__(self, mass=1.0, bounce=0.3, gravity=True):
        self.mass = mass
        self.bounce = bounce
        self.gravity = gravity

        self.velocity = vector3d.zero
        self.forces = vector3d.zero

    def add_force(self, f):
        self.forces += f

class ShadowVolume:
    def __init__(self, minx, maxx, miny, maxy, minz, maxz):
        self.minx = minx
        self.maxx = maxx
        self.miny = miny
        self.maxy = maxy
        self.minz = minz
        self.maxz = maxz

def get_forward(rotation):
    yaw = math.radians(rotation.z)
    fx = -math.sin(yaw)
    fy = 0
    fz = math.cos(yaw)
    return vector3d(fx, fy, fz)

class AreaLight:
    def __init__(self, shape: str, params: dict, color: Color, intensity: float = 1.0, samples: int = 4, name: str = "AreaLight"):
        self.shape = shape
        self.params = params
        self.color = color
        self.intensity = intensity
        self.samples = max(1, int(samples))
        self.name = name
        self.is_area = True

    @staticmethod
    def _lerp(a: vector3d, b: vector3d, t: float) -> vector3d:
        return a * (1.0 - t) + b * t

    def sample_points(self):
        """Return a list of vector3d sample positions on the surface."""
        if self.shape == 'plane':
            corners = self.params.get('corners')
            if not corners or len(corners) < 4:
                raise ValueError("AreaLight plane requires 'corners' list of 4 vector3d")
            p1, p2, p3, p4 = corners
            n = int(math.sqrt(self.samples))
            if n * n < self.samples:
                n += 1
            points = []
            count = 0
            for i in range(n):
                for j in range(n):
                    if count >= self.samples:
                        break
                    u = (i + 0.5) / n
                    v = (j + 0.5) / n
                    a = self._lerp(p1, p2, u)
                    b = self._lerp(p4, p3, u)
                    pos = self._lerp(a, b, v)
                    points.append(pos)
                    count += 1
                if count >= self.samples:
                    break
            return points

        elif self.shape == 'sphere':
            center = self.params.get('center')
            radius = self.params.get('radius')
            if center is None or radius is None:
                raise ValueError("AreaLight sphere requires 'center' and 'radius'")
            pts = []
            n = self.samples
            for i in range(n):
                z = 1.0 - 2.0 * (i + 0.5) / n
                r = math.sqrt(max(0.0, 1.0 - z * z))
                phi = 2.0 * math.pi * ((i * 0.618033988749895) % 1.0)
                x = r * math.cos(phi)
                y = r * math.sin(phi)
                pos = vector3d(center.x + radius * x, center.y + radius * z, center.z + radius * y)
                pts.append(pos)
            return pts

        elif self.shape == 'cylinder':
            center = self.params.get('center')
            height = self.params.get('height')
            radius = self.params.get('radius')
            rotation = self.params.get('rotation', vector3d.zero)
            if center is None or height is None or radius is None:
                raise ValueError("AreaLight cylinder requires 'center', 'height', and 'radius'")
            pts = []
            n_axial = max(1, int(math.sqrt(self.samples)))
            n_angular = max(1, int(math.ceil(self.samples / n_axial)))
            count = 0
            for i in range(n_axial):
                y = -height / 2.0 + (i + 0.5) * (height / n_axial)
                for j in range(n_angular):
                    if count >= self.samples:
                        break
                    theta = 2.0 * math.pi * (j + 0.5) / n_angular
                    x = radius * math.cos(theta)
                    z = radius * math.sin(theta)
                    local = vector3d(x, y, z)
                    # apply rotation (Euler degrees) if provided
                    rx, ry, rz = math.radians(rotation.x), math.radians(rotation.y), math.radians(rotation.z)
                    cx, sx = math.cos(rx), math.sin(rx)
                    cy, sy = math.cos(ry), math.sin(ry)
                    cz, sz = math.cos(rz), math.sin(rz)
                    Rx = [[1,0,0],[0,cx,-sx],[0,sx,cx]]
                    Ry = [[cy,0,sy],[0,1,0],[-sy,0,cy]]
                    Rz = [[cz,-sz,0],[sz,cz,0],[0,0,1]]
                    def mat_mult(A, B):
                        return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
                    R = mat_mult(mat_mult(Rz, Ry), Rx)
                    lx = R[0][0]*local.x + R[0][1]*local.y + R[0][2]*local.z
                    ly = R[1][0]*local.x + R[1][1]*local.y + R[1][2]*local.z
                    lz = R[2][0]*local.x + R[2][1]*local.y + R[2][2]*local.z
                    pos = vector3d(center.x + lx, center.y + ly, center.z + lz)
                    pts.append(pos)
                    count += 1
                if count >= self.samples:
                    break
            return pts

        else:
            raise ValueError(f"Unsupported area light shape: {self.shape}")
