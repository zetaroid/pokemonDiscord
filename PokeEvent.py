class PokeEvent(object):

    def __init__(self, name, item, image, desc, footer=None):
        self.name = name
        self.item = item
        self.image = "data/sprites/events/" + image
        self.desc = desc
        self.footer = ''
        if footer:
            self.footer = footer
