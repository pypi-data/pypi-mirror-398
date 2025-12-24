from gamengine3d import Cuboid, Context

class MessageReceiver:
    def __init__(self, obj: Cuboid, context: Context):
        self.obj = obj
        self.context = context

    def update(self, dt):
        if self.obj.received_message:
            print("Message Received!")
            print(self.obj.messages[-1])
            print("-"*10)
