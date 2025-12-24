from gamengine3d import *

class Cylinder:
    def __init__(self, obj: Cylinder, context: Context):
        self.obj = obj
        self.context = context
        self.color_idx = 0
        self.obj.color = self.context.runtime_vars.cylinder_colors[0]
        self.context.add_scheduled_caller(n_times=-1, delay=1, callback=self.switch_color)

    def update(self, dt):
        if "w" in self.context.keys_held:
            self.context.functions.draw_cylinder(vector3d(4, 3, 5), 2, 1, Color.light_green, 32)

        if "e" in self.context.keys_pressed:
            self.context.functions.draw_sphere(vector3d(1, 5, 6), radius=1, color=Color.blue)

        if "r" in self.context.keys_released:
            self.context.functions.draw_cube(pos=vector3d(5, 1, 4), size=vector3d(.2, 1, .5), color=Color.orange)

    def switch_color(self):
        self.color_idx += 1
        self.obj.color = self.context.runtime_vars.cylinder_colors[self.color_idx % self.context.runtime_vars.num_cylinder_colors]
