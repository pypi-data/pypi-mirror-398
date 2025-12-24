from gamengine3d import Engine, Cuboid, vector3d, Light, Color # import all the classes

engine = Engine(500, 500, resizable=True, name="Basics Demo", background_color=Color.light_blue, ambient_light=0.4) # define the Engine object.

floor = Cuboid(pos=vector3d.zero, size=vector3d(10, .5, 10), color=Color.light_grey) # create the floor

engine.add_light(Light(position=vector3d(0, 4, .1), color=Color.white)) # create and add a light (x or z values of 0 don't create the light in this case, fixes are being made

engine.add_object(floor) # add the floor object

engine.run() # run the game
