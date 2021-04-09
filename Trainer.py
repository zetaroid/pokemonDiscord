from Pokemon import Pokemon
from datetime import datetime
from copy import copy

class Trainer(object):

    def __init__(self, identifier, author, name, location, partyPokemon=None, boxPokemon=None, locationProgressDict=None,
                 flags=None, itemList=None, lastCenter=None, dailyProgress=None, withRestrictionStreak=None,
                 noRestrictionsStreak=None, alteringPokemon=None, withRestrictionsRecord=None,
                 noRestrictionsRecord=None, pvpWins=None, pvpLosses=None):
        self.identifier = identifier
        self.author = author
        self.name = name
        self.date = datetime.today().date()
        self.location = location
        self.rewards = {}
        self.rewardFlags = []
        self.rewardRemoveFlag = []
        self.sprite = "trainerSprite.png"
        self.beforeBattleText = ""
        self.shouldScale = False

        if (alteringPokemon is None):
            self.alteringPokemon = "Smeargle"
        else:
            self.alteringPokemon = alteringPokemon

        if (withRestrictionStreak is None):
            self.withRestrictionStreak = 0
        else:
            self.withRestrictionStreak = withRestrictionStreak

        if (noRestrictionsStreak is None):
            self.noRestrictionsStreak = 0
        else:
            self.noRestrictionsStreak = noRestrictionsStreak

        if (withRestrictionsRecord is None):
            self.withRestrictionsRecord = 0
        else:
            self.withRestrictionsRecord = withRestrictionsRecord

        if (noRestrictionsRecord is None):
            self.noRestrictionsRecord = 0
        else:
            self.noRestrictionsRecord = noRestrictionsRecord

        if (pvpWins is None):
            self.pvpWins = 0
        else:
            self.pvpWins = pvpWins

        if (pvpLosses is None):
            self.pvpLosses = 0
        else:
            self.pvpLosses = pvpLosses

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

    def __copy__(self):
        copiedPartyPokemon = []
        for pokemon in self.partyPokemon:
            copiedPartyPokemon.append(copy(pokemon))
        copiedBoxPokemon = []
        for pokemon in self.boxPokemon:
            copiedBoxPokemon.append(copy(pokemon))
        trainerCopy = type(self)(self.identifier, self.author, self.name, self.location, copiedPartyPokemon, copiedBoxPokemon,
                          self.locationProgressDict.copy(), self.flags.copy(), self.itemList.copy(),
                          self.lastCenter, self.dailyProgress, self.withRestrictionStreak, self.noRestrictionsStreak,
                          self.alteringPokemon, self.withRestrictionsRecord, self.noRestrictionsRecord, self.pvpWins, self.pvpLosses)
        trainerCopy.sprite = self.sprite
        trainerCopy.rewards = self.rewards
        trainerCopy.rewardFlags = self.rewardFlags
        trainerCopy.rewardRemoveFlag = self.rewardRemoveFlag
        trainerCopy.beforeBattleText = self.beforeBattleText
        return trainerCopy

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

    def removeFlag(self, flag):
        if flag in self.flags:
            self.flags.remove(flag)
            return True
        return False

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

    def scaleTeam(self, trainerToScaleTo=None, level=None):
        levelToScaleTo = 1
        if trainerToScaleTo:
            for pokemon in trainerToScaleTo.partyPokemon:
                if pokemon.level > levelToScaleTo:
                    levelToScaleTo = pokemon.level
        elif level:
            levelToScaleTo = level
        for pokemon in self.partyPokemon:
            pokemon.level = levelToScaleTo
            pokemon.setStats()

    def getPvpWinLossRatio(self):
        if self.pvpLosses == 0:
            if self.pvpWins > 0:
                return self.pvpWins
            else:
                return 0
        ratio = round(self.pvpWins/self.pvpLosses, 2)
        return ratio

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
            'identifier': self.identifier,
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
            'dailyProgress': self.dailyProgress,
            'withRestrictionStreak': self.withRestrictionStreak,
            'noRestrictionsStreak': self.noRestrictionsStreak,
            'alteringPokemon': self.alteringPokemon,
            'withRestrictionsRecord': self.withRestrictionsRecord,
            'noRestrictionsRecord': self.noRestrictionsRecord,
            'pvpWins': self.pvpWins,
            'pvpLosses': self.pvpLosses,
            "sprite": self.sprite
        }

    def fromJSON(self, json, data):
        if 'identifier' in json:
            self.identifier = json['identifier']
        self.author = json['author']
        self.name = json['name']
        self.date = datetime.strptime(json['date'], "%Y-%m-%d").date()
        self.location = json['location']
        self.dailyProgress = json['dailyProgress']
        self.lastCenter = json['lastCenter']
        self.flags = json['flags']
        if 'alteringPokemon' in json:
            self.alteringPokemon = json['alteringPokemon']
        if 'withRestrictionStreak' in json:
            self.withRestrictionStreak = json['withRestrictionStreak']
        if 'noRestrictionsStreak' in json:
            self.noRestrictionsStreak = json['noRestrictionsStreak']
        if 'withRestrictionsRecord' in json:
            self.withRestrictionsRecord = json['withRestrictionsRecord']
        else:
            self.withRestrictionsRecord = self.withRestrictionStreak
        if 'noRestrictionsRecord' in json:
            self.noRestrictionsRecord = json['noRestrictionsRecord']
        else:
            self.noRestrictionsRecord = self.noRestrictionsStreak
        if 'pvpWins' in json:
            self.pvpWins = json['pvpWins']
        if 'pvpLosses' in json:
            self.pvpLosses = json['pvpLosses']
        if 'sprite' in json:
            self.sprite = json['sprite']
        else:
            self.sprite = "trainerSprite.png"
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