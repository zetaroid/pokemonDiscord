from Pokemon import Pokemon
from Trainer import Trainer

class Location(object):

    # The class "constructor"
    def __init__(self, data, locationData):
        self.name = locationData['name']
        self.filename = self.name.lower().replace(" ", "_").replace("-", "_")
        self.progressRequired = locationData['progress_required']
        self.hasPokemonCenter = locationData['hasPokemonCenter']
        self.hasMart = locationData['hasMart']
        self.hasWildEncounters = locationData['hasWildEncounters']
        self.entryType = locationData['entryType']
        self.progressEvents = {}
        self.nextLocations = {}
        self.createProgressEvents(data, locationData)
        self.createNextLocations(locationData)

    def createProgressEvents(self, data, locationData):
        for progressEventObj in locationData['progress_events']:
            self.progressEvents[progressEventObj['progress']] = ProgressEvent(data, progressEventObj)

    def getEventForProgress(self, progress):
        if (progress in self.progressEvents):
            return self.progressEvents[progress]
        return None

    def createNextLocations(self, locationData):
        for nextLocationObj in locationData['nextLocations']:
            self.nextLocations[nextLocationObj['name']] = NextLocation(nextLocationObj, self.name)

    def getNextLocation(self, location):
        if (location in self.nextLocations):
            return self.nextLocations[location]
        return None


class NextLocation(object):
    # The class "constructor"
    def __init__(self, nextLocationObj, currentLocationName):
        self.currentLocationName = currentLocationName
        self.name = nextLocationObj['name']
        self.requirements = {}
        self.makeRequirements(nextLocationObj)

    def makeRequirements(self, nextLocationObj):
        for requirement in nextLocationObj['requirements']:
            self.requirements[requirement['name']] = requirement['value']

    def checkRequirements(self, trainer):
        meetsRequirements = True
        for name, value in self.requirements.items():
            if (name == 'progress'):
                meetsRequirements = trainer.checkProgress(self.currentLocationName) >= value
            elif (name == 'flag'):
                meetsRequirements = trainer.checkFlag(value)
        return meetsRequirements


class ProgressEvent(object):
    # The class "constructor"
    def __init__(self, data, progressEventObj):
        self.occurAt = progressEventObj['progress']
        self.type = progressEventObj['type']
        self.subtype = progressEventObj['subtype']
        self.trainer = None
        self.pokemon = None
        self.rewardDict = {}
        if (self.type == "battle"):
            if (self.subtype == "trainer"):
                self.trainer = self.createTrainerAndReward(data, progressEventObj)
            elif(self.subtype == "wild"):
                self.pokemon = self.createPokemon(data, progressEventObj)

    def createTrainerAndReward(self, data, progressEventObj):
        trainerObj = progressEventObj['trainer']
        name = trainerObj['name']
        sprite = trainerObj['sprite']
        trainer = Trainer(name, name, "NPC Battle")
        trainer.setSprite(sprite)
        for pokemonObj in trainerObj['pokemon']:
            trainer.addPokemon(Pokemon(data, pokemonObj['name'], pokemonObj['level']), True)
        rewardDict = {}
        for rewardObj in trainerObj['rewards']:
            rewardDict[rewardObj['name']] = rewardObj['amount']
        print(rewardDict)
        trainer.setRewards(rewardDict)
        return trainer

    def createPokemon(self, data, progressEventObj):
        newPokemon = Pokemon(data, progressEventObj['pokemon']['name'], progressEventObj['pokemon']['level'])
        return newPokemon
