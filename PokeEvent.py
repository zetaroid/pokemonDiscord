class PokeEvent(object):

    def __init__(self, name, item, image, desc):
        self.name = name
        self.item = item
        self.image = "data/sprites/events/" + image
        self.desc = desc
