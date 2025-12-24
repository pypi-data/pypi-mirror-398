from gamengine3d import *

class Planet:
    def __init__(self, context: Context, color, radius, pos, mass, name, initial_vel):
        self.context = context
        self.color = color
        self.radius = radius
        self.pos = pos
        self.velocity = initial_vel
        self.mass = mass
        self.name = name

    def draw(self):
        self.context.functions.draw_sphere(pos=self.pos, radius=self.radius, color=self.color)

    def update(self, dt, planets):
        for planet in planets:
            if planet.name != self.name:
                sqr_dst = (self.pos - planet.pos).sqr_magnitude
                force_dir = (planet.pos - self.pos).normalized
                force = force_dir * planet.mass * self.mass / sqr_dst
                acceleration = force / self.mass
                self.velocity += acceleration * dt

        self.pos += self.velocity * dt

class SolarSystem:
    def __init__(self, obj: Engine, context: Context):
        self.engine = obj
        mercury_distance = 30
        mercury_mass = .001
        mercury_orbital_speed = 20
        self.context = context
        self.planets = [Planet(self.context, Color.light_yellow, 25, vector3d.zero, mercury_mass * 10e6, "Sun", vector3d.zero),
                        Planet(self.context, Color.light_red, .6, vector3d(mercury_distance, 0), mercury_mass, "Mercury", vector3d(0, 0, mercury_orbital_speed)),
                        Planet(self.context, Color.orange, .9, vector3d(mercury_distance * 1.86, 0), mercury_mass * 14.8, "Venus", vector3d(0, 0, mercury_orbital_speed * .74)),
                        Planet(self.context, Color.blue, 1.4, vector3d(mercury_distance * 2.58, 0), mercury_mass * 18.1, "Earth", vector3d(0, 0, mercury_orbital_speed * .63)),
                        Planet(self.context, Color.red, 1.4, vector3d(mercury_distance * 3.93, 0), mercury_mass * 1.94, "Mars", vector3d(0, 0, mercury_orbital_speed * .51)),
                        Planet(self.context, Color.orange, 15, vector3d(mercury_distance * 13.4, 0), mercury_mass * 5770, "Jupiter", vector3d(0, 0, mercury_orbital_speed * .28)),
                        ]


    def update(self, dt):
        for planet in self.planets:
            planet.update(dt, self.planets)
            planet.draw()
