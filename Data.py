import json
import os
from Location import Location
from Trainer import Trainer


class pokeData(object):
    pokemonDict = {}
    moveDict = {}
    typeDict = {}
    natureDict = {}
    locationDict = {}
    locationObjDict = {}
    regionDict = []

    def __init__(self):
        #print("data object initialized")
        self.loadData()
        self.userList = []
        self.sessionList = []
        self.tradeDict = {}
        
    def loadData(self):
        self.loadRegionDataFromJSON()
        self.loadPokemonDataFromJSON()
        self.loadMoveDataFromJSON()
        self.loadTypeDataFromJSON()
        self.loadNatureDataFromJSON()
        self.loadLocationDataFromJSON()

    def loadLocationDataFromJSON(self):
        for filename in os.listdir("data/location"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/location/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.locationDict[name] = data
                    self.locationObjDict[name] = Location(self, data)
        #print("location data loaded")

    def loadRegionDataFromJSON(self):
        #global regionDict
        with open("data/region/hoenn.json", "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.regionDict = data
        #print("region data loaded")

    def loadPokemonDataFromJSON(self):
        #global pokemonDict
        for filename in os.listdir("data/pokemon"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/pokemon/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.pokemonDict[name] = data
        #print("pokemon data loaded")

    def loadMoveDataFromJSON(self):
        #global moveDict
        for filename in os.listdir("data/move"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/move/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.moveDict[name] = data
        #print("move data loaded")

    def loadTypeDataFromJSON(self):
        #global typeDict
        for filename in os.listdir("data/type"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/type/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.typeDict[name] = data
        #print("type data loaded")

    def loadNatureDataFromJSON(self):
        #global natureDict
        for filename in os.listdir("data/nature"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/nature/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.natureDict[name] = data
        #print("nature data loaded")

    def getMovesForLevel(self, pokemon, level):
        moveList = []
        pokemonObj = self.getPokemonData(pokemon)
        emeraldFound = False
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "emerald"):
                    emeraldFound = True
                    for moveObj in gameObj["learnset"]:
                        try:
                            if (level >= moveObj["level"]):
                                moveList.append(moveObj["move"])
                                if (len(moveList) > 4):
                                    moveList.pop(0)
                        except:
                            continue
        if not emeraldFound:
            for gameObj in pokemonObj["move_learnsets"]:
                for gameName in gameObj["games"]:
                    if (gameName.lower() == "sun"):
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
        emeraldFound = False
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "emerald"):
                    emeraldFound = True
                    for moveObj in gameObj["learnset"]:
                        try:
                            if (moveObj["level"] == level):
                                moveList.append(moveObj["move"])   
                        except:
                            continue
        if not emeraldFound:
            for gameObj in pokemonObj["move_learnsets"]:
                for gameName in gameObj["games"]:
                    if (gameName.lower() == "sun"):
                        for moveObj in gameObj["learnset"]:
                            try:
                                if (moveObj["level"] == level):
                                    moveList.append(moveObj["move"])
                            except:
                                continue
        return self.convertMoveList(moveList)

    def getAllTmMoves(self, pokemon):
        moveList = []
        pokemonObj = self.getPokemonData(pokemon)
        emeraldFound = False
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "emerald"):
                    emeraldFound = True
                    for moveObj in gameObj["learnset"]:
                        if "tm" in moveObj:
                            try:
                                moveList.append(self.getMoveData(moveObj["move"].lower()))
                            except:
                                continue
        if not emeraldFound:
            for gameObj in pokemonObj["move_learnsets"]:
                for gameName in gameObj["games"]:
                    if (gameName.lower() == "sun"):
                        for moveObj in gameObj["learnset"]:
                            if "tm" in moveObj:
                                try:
                                    moveList.append(self.getMoveData(moveObj["move"].lower()))
                                except:
                                    continue
        return moveList

    def getAllLevelUpMoves(self, pokemon, level):
        moveList = []
        pokemonObj = self.getPokemonData(pokemon)
        emeraldFound = False
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "emerald"):
                    emeraldFound = True
                    for moveObj in gameObj["learnset"]:
                        try:
                            if (level >= moveObj["level"]):
                                moveList.append(moveObj["move"])
                        except:
                            continue
        if not emeraldFound:
            for gameObj in pokemonObj["move_learnsets"]:
                for gameName in gameObj["games"]:
                    if (gameName.lower() == "sun"):
                        for moveObj in gameObj["learnset"]:
                            try:
                                if (level >= moveObj["level"]):
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

    def getLocationData(self, location):
        return self.locationDict[location.lower().replace(" ", "_").replace("-", "_")]

    def getLocation(self, location):
        try:
            return self.locationObjDict[location.lower().replace(" ", "_").replace("-", "_")]
        except:
            return self.locationObjDict['littleroot_town']

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
        elif (name == '7'):
            return '\u0037\u20E3'
        elif (name == '8'):
            return '\u0038\u20E3'
        elif (name == '9'):
            return '\u0039\u20E3'
        elif (name == '0'):
            return '\u0030\u20E3'
        elif (name == 'right arrow'):
            return ("▶️")
        elif (name == 'left arrow'):
            return("⬅️")
        elif (name == 'down arrow'):
            return('⏬')
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
        elif (name == 'masterball'):
            return("🟣")
        elif (name == 'box'):
            return('📥')
        elif (name == 'party'):
            return('🎊')
        elif (name == 'fly'):
            return('✈️')
        elif (name == "confirm"):
            return('☑️')
        elif (name == "cancel"):
            return('🇽')
        else:
            return '\u0034\u20E3'

    def writeUsersToJSON(self):
        data = {}
        data['users'] = []
        for user in self.userList:
            data['users'].append(user.toJSON())
        with open('trainerData.json', 'w') as outfile:
            json.dump(data, outfile)

    def readUsersFromJSON(self):
        with open('trainerData.json', encoding='utf8') as json_file:
            data = json.load(json_file)
            for userJSON in data['users']:
                user = Trainer(userJSON['author'], userJSON['name'], userJSON['location'])
                user.fromJSON(userJSON, self)
                self.addUser(user)

    def getUser(self, ctx): # user, isNewUser
        for user in self.userList:
            if str(user.author) == str(ctx.message.author):
                return user, False
        newUser = Trainer(str(ctx.message.author), str(ctx.message.author.display_name), "Littleroot Town")
        self.addUser(newUser)
        return newUser, True

    def getUserByAuthor(self, author): # user, isNewUser
        for user in self.userList:
            if str(user.author).lower() == str(author).lower():
                return user, False
            if (str(user.name).lower() == str(author).lower()):
                return user, False
        return None, True

    def addUser(self, user):
        self.userList.append(user)

    def addUserSession(self, user):
        if (user not in self.sessionList and user in self.userList):
            self.sessionList.append(user)
            return True
        return False

    def removeUserSession(self, user):
        if (user in self.sessionList):
            self.sessionList.remove(user)
            return True
        return False
