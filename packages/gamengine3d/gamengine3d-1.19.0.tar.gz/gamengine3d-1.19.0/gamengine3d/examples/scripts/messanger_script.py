from gamengine3d import Cuboid, Context

class MessangerScript:
    def __init__(self, obj: Cuboid, context: Context):
        self.obj = obj
        self.context = context

    def update(self, dt):
        if "space" in self.context.keys_held:
            self.context.send_message("Cuboid2", "The Space Bar has been pressed!")
