from Pokemon import Pokemon
from datetime import datetime

class Trainer(object):

    def __init__(self, author, name, location, partyPokemon=None, boxPokemon=None, locationProgressDict=None, flags=None, itemList=None, lastCenter=None, dailyProgress=None):
        self.author = author
        self.name = name
        self.date = datetime.today().date()
        self.location = location
        self.rewards = {}
        self.rewardFlags = []
        self.sprite = "ash.png"
        self.beforeBattleText = ""
        if (dailyProgress is None):
            self.dailyProgress = 10
        else:
            self.dailyProgress = dailyProgress
        if (lastCenter is None):
            self.lastCenter = "Littleroot Town"
        else:
            self.lastCenter = lastCenter
        if itemList is None:
            self.itemList = {}
            self.itemList['money'] = 1000
            self.itemList['Pokeball'] = 5
            self.itemList['Potion'] = 5
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

    def setBeforeBattleText(self, text):
        self.beforeBattleText = text

    def setSprite(self, sprite):
        self.sprite = sprite

    def setRewards(self, rewards):
        self.rewards = rewards

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

    def removeProgress(self, location):
        if (location in self.locationProgressDict):
            if (self.locationProgressDict[location] > 0):
                self.locationProgressDict[location] = self.locationProgressDict[location] - 1

    def addPokemon(self, pokemon, changeOT):
        if changeOT:
            pokemon.OT = self.author
        pokemon.setCaughtAt(self.location)
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

    def pokemonCenterHeal(self):
        for pokemon in self.partyPokemon:
            pokemon.pokemonCenterHeal()
        for pokemon in self.boxPokemon:
            pokemon.pokemonCenterHeal()
        self.lastCenter = self.location

    def toJSON(self):
        partyPokemonArray = []
        for pokemon in self.partyPokemon:
            partyPokemonArray.append(pokemon.toJSON())
        boxPokemonArray = []
        for pokemon in self.boxPokemon:
            boxPokemonArray.append(pokemon.toJSON())
        itemNameArray = []
        itemAmountArray = []
        for name, amount in self.itemList.items():
            itemNameArray.append(name)
            itemAmountArray.append(amount)
        locationProgressNameArray = []
        locationProgressAmountArray = []
        for name, amount in self.locationProgressDict.items():
            locationProgressNameArray.append(name)
            locationProgressAmountArray.append(amount)
        return {
            'author': self.author,
            'name': self.name,
            'date': str(self.date),
            'location': self.location,
            'partyPokemon': partyPokemonArray,
            'boxPokemon': boxPokemonArray,
            'itemNames': itemNameArray,
            'itemAmounts': itemAmountArray,
            'locationProgressNames': locationProgressNameArray,
            'locationProgressAmounts': locationProgressAmountArray,
            'flags': self.flags,
            'lastCenter': self.lastCenter,
            'dailyProgress': self.dailyProgress
        }

    def fromJSON(self, json, data):
        self.author = json['author']
        self.name = json['name']
        self.date = datetime.strptime(json['date'], "%Y-%m-%d").date()
        self.location = json['location']
        self.dailyProgress = json['dailyProgress']
        self.lastCenter = json['lastCenter']
        self.flags = json['flags']
        partyPokemon = []
        for pokemonJSON in json['partyPokemon']:
            pokemon = Pokemon(data, pokemonJSON['name'], pokemonJSON['level'])
            pokemon.fromJSON(pokemonJSON)
            partyPokemon.append(pokemon)
        self.partyPokemon = partyPokemon
        boxPokemon = []
        for pokemonJSON in json['boxPokemon']:
            pokemon = Pokemon(data, pokemonJSON['name'], pokemonJSON['level'])
            pokemon.fromJSON(pokemonJSON)
            boxPokemon.append(pokemon)
        self.boxPokemon = boxPokemon
        locationProgressDict = {}
        for x in range(0, len(json['locationProgressNames'])):
            locationProgressDict[json['locationProgressNames'][x]] = json['locationProgressAmounts'][x]
        self.locationProgressDict = locationProgressDict
        itemDict = {}
        for x in range(0, len(json['itemNames'])):
            itemDict[json['itemNames'][x]] = json['itemAmounts'][x]
        self.itemList = itemDict