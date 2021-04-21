from Secret_Base_Item import Secret_Base_Item
import uuid

class Secret_Base(object):

    def __init__(self, data, baseType, name, location):
        self.data = data
        self.baseType = baseType
        self.name = name
        self.baseObj = None
        self.location = location
        self.getBaseObject(self.baseType)
        self.placedItems = {}
        temp_uuid = uuid.uuid4()
        self.filename = "data/temp/secret_base_" + str(temp_uuid) + ".png"
        self.gridOn = False

    def toggleGrid(self):
        self.gridOn = not self.gridOn

    def getBaseObject(self, baseType):
        if baseType in self.data.secretBaseAreaDict.keys():
            self.baseObj = self.data.secretBaseAreaDict[baseType]

    def placeItem(self, column, row, item):
        valid, errorMessage = self.isValidPlacement(column, row, item)
        if valid:
            if (column, row) not in self.placedItems.keys():
                self.placedItems[(column, row)] = []
            self.placedItems[(column, row)].append(item)
        return valid, errorMessage

    def placeItemByLetter(self, column, row, item):
        column = ord(column.lower()) - 96
        return self.placeItem(column, row, item)

    def removeItem(self, column, row):
        if (column, row) in self.placedItems.keys():
            if len(self.placedItems[(column, row)]) > 0:
                item = self.placedItems[(column, row)].pop()
                if len(self.placedItems[(column, row)]) == 0:
                    del self.placedItems[(column, row)]
                return True, item.name
        return False, ''

    def removeItemByLetter(self, column, row):
        column = ord(column.lower()) - 96
        return self.removeItem(column, row)

    def isValidPlacement(self, column, row, item):
        occupyingSpaces = item.getOccupyingSpaces(column, row)
        errorMessage = ''
        # print('occupyingSpaces = ', occupyingSpaces)
        for (occupiedColumn, occupiedRow) in occupyingSpaces:
            if not self.baseObj.isValidSelection(occupiedColumn, occupiedRow, item.isWallItem()):
                # print('tile said not valid')
                errorMessage = 'Invalid location in base for item.'
                return False, errorMessage
        for (tempColumn, tempRow), tempItemList in self.placedItems.items():
            for tempItem in tempItemList:
                itemUnderneath = False
                confirmedCoords = []
                tempOccupyingSpaces = tempItem.getOccupyingSpaces(tempColumn, tempRow)
                # print(tempOccupyingSpaces)
                # print(occupyingSpaces)
                for (tempOccupiedColumn, tempOccupiedRow) in tempOccupyingSpaces:
                    for (occupiedColumn, occupiedRow) in occupyingSpaces:
                        if occupiedColumn == tempOccupiedColumn and occupiedRow == tempOccupiedRow and tempItem.getLayer() >= item.getLayer():
                            # print("1: ", (occupiedColumn, occupiedRow), (tempOccupiedColumn, tempOccupiedRow))
                            itemUnderneath = True
                            confirmedCoords.append((occupiedColumn, occupiedRow))
                            if not tempItem.canItemsBePlacedOn():
                                # print('cannot be placed on other item')
                                errorMessage = 'Cannot place this item on top of the item at that location.'
                                return False, errorMessage
                            continue
                        elif itemUnderneath and tempItem.getLayer() == item.getLayer() and (occupiedColumn, occupiedRow) not in confirmedCoords:
                            # print("2: ", (occupiedColumn, occupiedRow), (tempOccupiedColumn, tempOccupiedRow))
                            # print('hanging off edge')
                            errorMessage = 'Cannot place this item here, it will be hanging off an edge.'
                            return False, errorMessage
        return True, errorMessage





