class Secret_Base_Item(object):

    def __init__(self, name, idName, sprite, categoryObj):
        self.name = name
        self.idName = idName
        self.sprite = "data/sprites/base/base_items/" + sprite
        self.categoryObj = categoryObj

    def getCategory(self):
        return self.categoryObj.category

    def getHeight(self):
        return self.categoryObj.height

    def getWidth(self):
        return self.categoryObj.width

    def canItemsBePlacedOn(self):
        return self.categoryObj.canItemsBePlacedOn

    def canPlaceOnSameLayer(self):
        return self.categoryObj.canPlaceOnSameLayer

    def getLayer(self):
        return self.categoryObj.layer

    def isWallItem(self):
        return self.categoryObj.wallItem

    def getOccupyingSpaces(self, column, row):
        occupyingSpaces = []
        for x in range(0, self.getWidth()):
            for y in range(0, self.getHeight()):
                occupyingSpaces.append((column + x, row + y))
        return occupyingSpaces

class Secret_Base_Item_Type(object):

    def __init__(self, category, height, width, canItemsBePlacedOn, canPlaceOnSameLayer, layer, wallItem):
        self.category = category
        self.height = height
        self.width = width
        self.canItemsBePlacedOn = canItemsBePlacedOn
        self.canPlaceOnSameLayer = canPlaceOnSameLayer
        self.layer = layer
        self.wallItem = wallItem
