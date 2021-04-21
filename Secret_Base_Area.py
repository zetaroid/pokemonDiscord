class Secret_Base_Area(object):

    def __init__(self, baseType, defaultName, sprite, validTilesJson, validWallTilesJson):
        self.baseType = baseType
        self.defaultName = defaultName
        self.sprite = "data/sprites/base/base_areas/area_" + sprite
        self.validTiles = {}
        self.createValidTilesDict(validTilesJson)
        self.validWallTiles = {}
        self.createValidWallTilesDict(validWallTilesJson)

    def createValidTilesDict(self, validTilesJson):
        for validTileObj in validTilesJson:
            column = ord(validTileObj['column'].lower()) - 96
            rowList = validTileObj['rows']
            self.validTiles[column] = validTile(column, rowList)

    def createValidWallTilesDict(self, validWallTilesJson):
        for validWallTileObj in validWallTilesJson:
            column = ord(validWallTileObj['column'].lower()) - 96
            rowList = validWallTileObj['rows']
            self.validWallTiles[column] = validTile(column, rowList, True)

    def isValidSelection(self, column, row, isWallItem=False):
        if isWallItem:
            # print('column = ',column)
            # print('self.validWallTiles.keys() = ', self.validWallTiles.keys())
            if column in self.validWallTiles.keys():
                return self.validWallTiles[column].isValidSelection(row)
        else:
            # print('column = ',column)
            # print('self.validTiles.keys() = ', self.validTiles.keys())
            if column in self.validTiles.keys():
                return self.validTiles[column].isValidSelection(row)
        return False

class validTile(object):

    def __init__(self, column, validRows, isWall=False):
        self.column = column
        self.validRows = validRows
        self.isWall = isWall

    def isValidSelection(self, row):
        # print('row = ', row)
        # print('isWall = ', self.isWall)
        # print('self.validRows = ', self.validRows)
        if row in self.validRows:
            return True
        return False
