from Pokemon import Pokemon
from Trainer import Trainer

class Location(object):

    # The class "constructor"
    def __init__(self, data, locationData):
        self.name = locationData['name']
        if "region" in locationData:
            self.region = locationData['region']
        else:
            self.region = 'hoenn'
        if 'image' in locationData:
            self.filename = self.region + "/" + locationData['image'].lower().replace(" ", "_").replace("-", "_")
        else:
            self.filename = self.region + "/" + self.name.lower().replace(" ", "_").replace("-", "_")
        self.progressRequired = locationData['progress_required']
        self.hasPokemonCenter = locationData['hasPokemonCenter']
        self.hasMart = locationData['hasMart']
        self.hasWildEncounters = locationData['hasWildEncounters']
        self.entryType = locationData['entryType']
        self.secretBaseType = None
        if 'secretBase' in locationData:
            self.secretBaseType = locationData['secretBase']
        self.battleTerrain = None
        if 'battleTerrain' in locationData:
            self.battleTerrain = locationData['battleTerrain']
        self.desc = None
        if 'desc' in locationData:
            self.desc = locationData['desc']
        self.hasSuperTraining = None
        if 'hasSuperTraining' in locationData:
            self.hasSuperTraining = locationData['hasSuperTraining']
        self.hasMoveTutor = False
        if 'hasMoveTutor' in locationData:
            self.hasMoveTutor = locationData['hasMoveTutor']
        self.hasLegendaryPortal = False
        if 'hasLegendaryPortal' in locationData:
            self.hasLegendaryPortal = locationData['hasLegendaryPortal']
        self.isBattleTower = False
        if 'isBattleTower' in locationData:
            self.isBattleTower = locationData['isBattleTower']
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
        self.prohibitedFlags = []
        self.requiredItems = []
        self.makeRequirements(nextLocationObj)

    def makeRequirements(self, nextLocationObj):
        for requirement in nextLocationObj['requirements']:
            if (requirement['name'] == "flag"):
                self.requiredFlags.append(requirement['value'])
            elif (requirement['name'] == '-flag'):
                self.prohibitedFlags.append(requirement['value'])
            elif (requirement['name'] == 'item'):
                self.requiredItems.append(requirement['value'])
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
            trainerHasFlag = trainer.checkFlag(flag)
            if not trainerHasFlag:
                return False
        for flag in self.prohibitedFlags:
            trainerHasFlag = trainer.checkFlag(flag)
            if trainerHasFlag:
                return False
        for itemName in self.requiredItems:
            if itemName not in trainer.itemList.keys():
                return False
            else:
                if trainer.itemList[itemName] < 1:
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
        trainer = Trainer(0, name, name, "NPC Battle")
        if 'shouldScale' in trainerObj:
            trainer.shouldScale = trainerObj['shouldScale']
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
            if 'form' in pokemonObj:
                newForm = pokemonObj['form']
                newPokemon.setForm(newForm)
            if 'shiny' in pokemonObj:
                newPokemon.shiny = pokemonObj['shiny']
                newPokemon.setSpritePath()
            if 'distortion' in pokemonObj:
                newPokemon.distortion = pokemonObj['distortion']
                newPokemon.setSpritePath()
            if 'shadow' in pokemonObj:
                newPokemon.shadow = pokemonObj['shadow']
                newPokemon.setSpritePath()
                if newPokemon.shadow:
                    newPokemon.setShadowMoves()
            if 'invulnerable' in pokemonObj:
                newPokemon.invulnerable = pokemonObj['invulnerable']
            if 'hp_ev' in pokemonObj:
                newPokemon.hpEV = pokemonObj['hp_ev']
            if 'atk_ev' in pokemonObj:
                newPokemon.atkEV = pokemonObj['atk_ev']
            if 'def_ev' in pokemonObj:
                newPokemon.spAtkEV = pokemonObj['def_ev']
            if 'sp_atk_ev' in pokemonObj:
                newPokemon.spAtkEV = pokemonObj['sp_atk_ev']
            if 'sp_def_ev' in pokemonObj:
                newPokemon.spDefEV = pokemonObj['sp_def_ev']
            if 'speed_ev' in pokemonObj:
                newPokemon.spdEV = pokemonObj['speed_ev']
            if 'iv' in pokemonObj:
                if pokemonObj['iv']:
                    newPokemon.hpIV = 31
                    newPokemon.atkIV = 31
                    newPokemon.defIV = 31
                    newPokemon.spAtkIV = 31
                    newPokemon.spDefIV = 31
                    newPokemon.spdIV = 31
            if 'nature' in pokemonObj:
                newPokemon.nature = pokemonObj['nature']
            newPokemon.setStats()
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
