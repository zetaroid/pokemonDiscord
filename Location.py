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
        self.hasMoveTutor = False
        if 'hasMoveTutor' in locationData:
            self.hasMoveTutor = locationData['hasMoveTutor']
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
        self.requiredFlags = []
        self.makeRequirements(nextLocationObj)

    def makeRequirements(self, nextLocationObj):
        for requirement in nextLocationObj['requirements']:
            if (requirement['name'] == "flag"):
                self.requiredFlags.append(requirement['value'])
            else:
                self.requirements[requirement['name']] = requirement['value']

    def checkRequirements(self, trainer):
        meetsRequirements = True
        for name, value in self.requirements.items():
            if (name == 'progress'):
                meetsRequirements = trainer.checkProgress(self.currentLocationName) >= value
            if not meetsRequirements:
                return False
        for flag in self.requiredFlags:
            meetsRequirements = trainer.checkFlag(flag)
            if not meetsRequirements:
                return False
        return meetsRequirements


class ProgressEvent(object):
    # The class "constructor"
    def __init__(self, data, progressEventObj):
        self.data = data
        self.progressEventObj = progressEventObj
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
                self.pokemonName = progressEventObj['pokemon']['name']
                self.pokemon = self.createPokemon()

    def createTrainerAndReward(self, data, progressEventObj):
        trainerObj = progressEventObj['trainer']
        name = trainerObj['name']
        sprite = trainerObj['sprite']
        trainer = Trainer(name, name, "NPC Battle")
        trainer.setSprite(sprite)
        trainer.setBeforeBattleText(trainerObj['beforeBattleText'])
        for pokemonObj in trainerObj['pokemon']:
            moveList = []
            if 'moves' in pokemonObj:
                for move in pokemonObj['moves']:
                    moveList.append(data.getMoveData(move))
            newPokemon = Pokemon(data, pokemonObj['name'], pokemonObj['level'])
            if (moveList):
                newPokemon.setMoves(moveList)
            trainer.addPokemon(newPokemon, True)
        rewardDict = {}
        for rewardObj in trainerObj['rewards']:
            if (rewardObj['name'] == "flag"):
                trainer.rewardFlags.append(rewardObj['amount'])
            elif (rewardObj['name'] == "-flag"):
                trainer.rewardRemoveFlag.append(rewardObj['amount'])
            elif (rewardObj['name'] == "cutscene"):
                    trainer.rewardFlags.append("cutscene" + rewardObj['amount'])
            else:
                rewardDict[rewardObj['name']] = rewardObj['amount']
        trainer.setRewards(rewardDict)
        return trainer

    def createPokemon(self):
        newPokemon = Pokemon(self.data, self.progressEventObj['pokemon']['name'], self.progressEventObj['pokemon']['level'])
        return newPokemon
