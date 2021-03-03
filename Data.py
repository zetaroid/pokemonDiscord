import json
import os
from Location import Location
from Trainer import Trainer
from datetime import datetime
from shutil import copyfile

class pokeData(object):
    pokemonDict = {}
    moveDict = {}
    typeDict = {}
    natureDict = {}
    locationDict = {}
    locationObjDict = {}
    regionDict = []
    cutsceneDict = {}
    staminaDict = {}
    legendaryPortalDict = {}
    battleTowerPokemonJson = None
    battleTowerTrainersJson = None

    def __init__(self):
        #print("data object initialized")
        self.loadData()
        self.userDict = {}
        self.sessionDict = {}
        self.tradeDictByServerId = {}
        
    def loadData(self):
        self.loadRegionDataFromJSON()
        self.loadPokemonDataFromJSON()
        self.loadMoveDataFromJSON()
        self.loadTypeDataFromJSON()
        self.loadNatureDataFromJSON()
        self.loadLocationDataFromJSON()
        self.loadCutsceneDataFromJSON()
        self.loadLegendaryPortalDataFromJSON()
        self.loadBattleTowerPokemonFromJSON()
        self.loadBattleTowerTrainersFromJSON()

    def loadBattleTowerTrainersFromJSON(self):
        filename = 'battle_tower_trainers.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.battleTowerTrainersJson = data

    def loadBattleTowerPokemonFromJSON(self):
        filename = 'battle_tower_pokemon.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.battleTowerPokemonJson = data

    def loadLegendaryPortalDataFromJSON(self):
        filename = 'rotating_legends.json'
        name = filename[:-5]
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.legendaryPortalDict[name] = data

    def loadCutsceneDataFromJSON(self):
        for filename in os.listdir("data/cutscene"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/cutscene/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.cutsceneDict[name] = data

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
        # emeraldFound = False
        # for gameObj in pokemonObj["move_learnsets"]:
        #     for gameName in gameObj["games"]:
        #         if (gameName.lower() == "emerald"):
        #             emeraldFound = True
        #             for moveObj in gameObj["learnset"]:
        #                 if "tm" in moveObj:
        #                     try:
        #                         moveList.append(self.getMoveData(moveObj["move"].lower()))
        #                     except:
        #                         continue
        # if not emeraldFound:
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
        # emeraldFound = False
        # for gameObj in pokemonObj["move_learnsets"]:
        #     for gameName in gameObj["games"]:
        #         if (gameName.lower() == "emerald"):
        #             emeraldFound = True
        #             for moveObj in gameObj["learnset"]:
        #                 try:
        #                     if (level >= moveObj["level"]):
        #                         moveList.append(moveObj["move"])
        #                 except:
        #                     continue
        # if not emeraldFound:
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
        return self.moveDict[move.lower().replace(" ", "_").replace("-", "_").replace("'", "_")]

    def getTypeData(self, typeName):
        return self.typeDict[typeName.lower()]

    def getNatureData(self, nature):
        return self.natureDict[nature]

    def getLegendaryPortalPokemon(self):
        today = datetime.now()
        month = today.month
        day = today.day
        evenOrOdd = "odd"
        if month % 2 == 0:
            evenOrOdd = "even"
        try:
            return self.legendaryPortalDict['rotating_legends'][evenOrOdd][str(day)]
        except:
            return "Pikachu"

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
        elif (status == 'seeded'):
            return(':seedling:')
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
        copyfile("trainerData.json", "backup.json")
        data = {}
        data['timestamp'] = str(datetime.today())
        for server_id in self.userDict.keys():
            data[server_id] = {}
            data[server_id]['staminaEnabled'] = self.staminaDict[server_id]
            data[server_id]['users'] = []
            for user in self.userDict[server_id]:
                data[server_id]['users'].append(user.toJSON())
        with open('trainerData.json', 'w') as outfile:
            json.dump(data, outfile)

    def readUsersFromJSON(self):
        with open('trainerData.json', encoding='utf8') as json_file:
            data = json.load(json_file)
            for server_id in data:
                self.staminaDict[server_id] = data[server_id]['staminaEnabled']
                for userJSON in data[server_id]['users']:
                    user = Trainer(userJSON['author'], userJSON['name'], userJSON['location'])
                    user.fromJSON(userJSON, self)
                    self.addUser(server_id, user)

    def getUser(self, ctx): # user, isNewUser
        server_id = str(ctx.message.guild.id)
        if server_id in self.userDict.keys():
            for user in self.userDict[server_id]:
                if str(user.author) == str(ctx.message.author):
                    self.updateDisplayName(ctx, user)
                    return user, False
        newUser = Trainer(str(ctx.message.author), str(ctx.message.author.display_name), "Littleroot Town")
        self.addUser(server_id, newUser)
        return newUser, True

    def updateDisplayName(self, ctx, user):
        if user.name != ctx.message.author.display_name:
            user.name = ctx.message.author.display_name

    def getUserByAuthor(self, server_id, author, fetched_user=None): # user, isNewUser
        server_id = str(server_id)
        if server_id in self.userDict.keys():
            for user in self.userDict[server_id]:
                if str(user.author).lower() == str(author).lower():
                    return user, False
                if (str(user.name).lower() == str(author).lower()):
                    return user, False
                if fetched_user:
                    if fetched_user.display_name.lower() == str(user.author).lower()\
                            or fetched_user.display_name.lower() == str(user.name).lower():
                        return user, False
        return None, True

    def addUser(self, server_id, user):
        server_id = str(server_id)
        if server_id in self.userDict.keys():
            self.userDict[str(server_id)].append(user)
        else:
            if server_id not in self.staminaDict.keys():
                self.staminaDict[str(server_id)] = True
            self.userDict[str(server_id)] = []
            self.userDict[str(server_id)].append(user)

    def addUserSession(self, server_id, user):
        server_id = str(server_id)
        if server_id in self.sessionDict.keys():
            if (user not in self.sessionDict[server_id] and user in self.userDict[str(server_id)]):
                self.sessionDict[server_id].append(user)
                return True
        else:
            if server_id in self.userDict.keys():
                if user in self.userDict[server_id]:
                    self.sessionDict[server_id] = []
                    self.sessionDict[server_id].append(user)
                    return True
        return False

    def removeUserSession(self, server_id, user):
        server_id = str(server_id)
        if server_id in self.sessionDict.keys():
            if (user in self.sessionDict[server_id]):
                self.sessionDict[server_id].remove(user)
                return True
        return False

    def getSessionList(self, ctx):
        server_id = str(ctx.message.guild.id)
        if server_id in self.sessionDict.keys():
            return self.sessionDict[server_id]
        return []

    def getTradeDict(self, ctx):
        server_id = str(ctx.message.guild.id)
        if server_id in self.tradeDictByServerId.keys():
            return self.tradeDictByServerId[server_id]
        else:
            self.tradeDictByServerId[server_id] = {}
            return self.tradeDictByServerId[server_id]
