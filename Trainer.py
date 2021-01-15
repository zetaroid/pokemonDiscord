from Pokemon import Pokemon
from datetime import datetime

class Trainer(object):

    def __init__(self, author, name, location, partyPokemon=None, boxPokemon=None, locationProgressDict=None, flags=None, itemList=None):
        self.author = author
        self.name = name
        self.date = datetime.today().date()
        self.location = location
        if itemList is None:
            self.itemList = {}
            self.itemList['money'] = 0
        else:
            self.itemList = itemList
        if flags is None:
            self.flags = []
        else:
            self.flags = flags
        if locationProgressDict is None:
            self.locationProgressDict = {}
        else:
            self.locationProgressDict = locationProgressDict
        if partyPokemon is None:
            self.partyPokemon = []
        else:
            self.partyPokemon = partyPokemon
        if boxPokemon is None:
            self.boxPokemon = []
        else:
            self.boxPokemon = boxPokemon    

    def addItem(self, item, amount):
        if (item in self.itemList):
            self.itemList[item] = self.itemList[item] + amount
        else:
            self.itemList[item] = amount

    def useItem(self, item, amount):
        if (item in self.itemList):
            self.itemList[item] = self.itemList[item] - amount
            return True
        return False

    def getItemAmount(self, item):
        if (item in self.itemList):
            return self.itemList[item]
        return 0

    def checkFlag(self, flag):
        return flag in self.flags

    def addFlag(self, flag):
        if (flag in self.flags):
            return
        self.flags.append(flag)

    def checkProgress(self, location):
        progress = 0
        if (location in self.locationProgressDict):
            progress = self.locationProgressDict[location]
        else:
            self.locationProgressDict[location] = 0
        return progress

    def progress(self, location):
        if (location in self.locationProgressDict):
            self.locationProgressDict[location] = self.locationProgressDict[location] + 1
        else:
            self.locationProgressDict[location] = 1

    def addPokemon(self, pokemon, changeOT):
        if changeOT:
            pokemon.OT = self.author
        if (len(self.partyPokemon) < 6):
            self.partyPokemon.append(pokemon)
        else:
            self.boxPokemon.append(pokemon)

    def swapPartyPokemon(self, pos):
        if (pos != 0):
            self.partyPokemon[0], self.partyPokemon[pos] = self.partyPokemon[pos], self.partyPokemon[0] 

    def movePokemonPartyToBox(self, index):
        if (len(self.partyPokemon) > 1):
            pokemon = self.partyPokemon.pop(index)
            self.boxPokemon.append(pokemon)
            return True
        else:
            return False

    def movePokemonBoxToParty(self, index):
        if (len(self.partyPokemon) < 6):
            pokemon = self.boxPokemon.pop(index)
            self.partyPokemon.append(pokemon)
            return True
        else:
            return False
        
    def swapPartyAndBoxPokemon(self, partyIndex, boxIndex):
        partyPokemon = self.partyPokemon.pop(partyIndex)
        boxPokemon = self.boxPokemon.pop(boxIndex)
        self.boxPokemon.insert(boxIndex, partyPokemon)
        self.partyPokemon.insert(partyIndex, boxPokemon)