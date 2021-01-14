import random
import json
import os

class pokeData(object):
    pokemonDict = {}
    moveDict = {}
    typeDict = {}
    natureDict = {}
    regionDict = []

    def __init__(self):
        print("data object initialized")
        self.loadData()
        
    def loadData(self):
        self.loadLocationDataFromJSON()
        self.loadPokemonDataFromJSON()
        self.loadMoveDataFromJSON()
        self.loadTypeDataFromJSON()
        self.loadNatureDataFromJSON()
        
    def loadLocationDataFromJSON(self):
        #global regionDict
        with open("data/region/hoenn.json", "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.regionDict = data
        print("location data loaded")

    def loadPokemonDataFromJSON(self):
        #global pokemonDict
        for filename in os.listdir("data/pokemon"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/pokemon/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.pokemonDict[name] = data
        print("pokemon data loaded")

    def loadMoveDataFromJSON(self):
        #global moveDict
        for filename in os.listdir("data/move"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/move/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.moveDict[name] = data
        print("move data loaded")

    def loadTypeDataFromJSON(self):
        #global typeDict
        for filename in os.listdir("data/type"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/type/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.typeDict[name] = data
        print("type data loaded")

    def loadNatureDataFromJSON(self):
        #global natureDict
        for filename in os.listdir("data/nature"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/nature/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.natureDict[name] = data
        print("nature data loaded")

    def getMovesForLevel(self, pokemon, level):
        moveList = []
        pokemonObj = self.getPokemonData(pokemon)
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "emerald"):
                    for moveObj in gameObj["learnset"]:
                        try:
                            if (level >= moveObj["level"]):
                                moveList.append(moveObj["move"])
                                if (len(moveList) > 4):
                                    moveList.pop(0)
                        except:
                            continue
        return self.convertMoveList(moveList)

    def getLevelUpMove(self, pokemon, level):
        moveList = []
        pokemonObj = self.getPokemonData(pokemon)
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "emerald"):
                    for moveObj in gameObj["learnset"]:
                        try:
                            if (moveObj["level"] == level):
                                moveList.append(moveObj["move"])   
                        except:
                            continue
        return self.convertMoveList(moveList)

    def convertMoveList(self, moveList):
        newMoveList = []
        for moveName in moveList:
            newMoveList.append(self.getMoveData(moveName.lower()))
        return newMoveList

    def getEncounterTable(self, desiredLocation, encounterType):
        #global regionDict
        encounterList = []
        for location in self.regionDict["locations"]:
            if (location["names"]["en"] == desiredLocation):
                for pokemonLocationInfo in location["pokemon"]:
                    for gameName in pokemonLocationInfo["games"]:
                        if (gameName.lower() == "emerald" and pokemonLocationInfo["location"] == encounterType):
                            encounterList.append(pokemonLocationInfo)
                break
        return encounterList

    def getPokemonData(self, pokemon):
        return self.pokemonDict[pokemon.lower().replace(" ", "_").replace("-", "_")]

    def getMoveData(self, move):
        return self.moveDict[move.lower().replace(" ", "_").replace("-", "_")]

    def getTypeData(self, typeName):
        return self.typeDict[typeName.lower()]

    def getNatureData(self, nature):
        return self.natureDict[nature]

    def getStatusEmoji(self, status):
        if (status == 'burn'):
            return ':fire:'
        elif (status == 'sleep'):
            return ':sleeping:'
        elif (status == 'freeze'):
            return ':ice_cube:'
        elif (status == 'poisoned'):
            return ':biohazard:'
        elif (status == 'badly_poisoned'):
            return ':biohazard:'
        elif (status == 'paralysis'):
            return ':cloud_lightning:'
        elif (status == 'faint'):
            return ':skull_crossbones:'
        elif (status == 'confusion'):
            return ':question:'
        elif (status == 'curse'):
            return(":ghost:")
        else:
            return '\u200b'

    def getEmoji(self, name):
        if (name == '1'):
            return '\u0031\u20E3'
        elif (name == '2'):
            return '\u0032\u20E3'
        elif (name == '3'):
            return '\u0033\u20E3'
        elif (name == '4'):
            return '\u0034\u20E3'
        elif (name == '5'):
            return '\u0035\u20E3'
        elif (name == '6'):
            return '\u0036\u20E3'
        elif (name == 'right arrow'):
            return ("▶️")
        elif (name == 'left arrow'):
            return("◀️")
        elif (name == 'physical'):
            return("🤜")
        elif (name == 'special'):
            return("🪄")
        elif (name == 'no damage'):
            return("🚫")
        elif (name == 'swap'):
            return("🔄")
        elif (name == 'pokeball'):
            return("🔴")
        elif (name == 'greatball'):
            return("🔵")
        elif (name == 'ultraball'):
            return("🟡")
        else:
            return '\u0034\u20E3'
