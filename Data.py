import json
import os
import traceback
from copy import copy
import PokeNavComponents
import TrainerIcons
from Item import Item
from Location import Location
from PokeEvent import PokeEvent
from Quests import Quest
from Shop_Item import Shop_Item
from Trainer import Trainer
from datetime import datetime, timedelta
from shutil import copyfile
from Secret_Base_Area import Secret_Base_Area
from Secret_Base_Item import Secret_Base_Item
from Secret_Base_Item import Secret_Base_Item_Type
import random
import logging


class pokeData(object):
    pokemonDict = {}
    moveDict = {}
    typeDict = {}
    natureDict = {}
    secretBaseAreaDict = {}
    secretBaseItemTypes = {}
    secretBaseItems = {}
    locationDict = {}
    locationObjDict = {}
    regionDict = {}
    cutsceneDict = {}
    staminaDict = {}
    shopDict = {}
    itemDict = {}
    legendaryPortalDict = {}
    battleTowerPokemonJson = None
    battleTowerTrainersJson = None

    def __init__(self):
        # print("data object initialized")
        self.userDict = {}
        self.sessionDict = {}
        self.pvpDictByServerId = {}
        self.overworldSessions = {}
        self.expiredSessions = []
        self.matchmakingDict = {}
        self.globalSaveDict = {}
        self.recentActivityDict = {}
        self.alteringCaveRestrictions = []
        self.battleTowerRestrictions = []
        self.flyRestrictions = {}
        self.alternative_shinies = {}
        self.eventDict = {}
        self.questDict = {}
        self.iconList = []
        self.icon_subcategory = []
        self.activeEvent = ''
        self.eventActive = False
        self.lastRaidTime = None
        self.lastRaidCheck = None
        self.raid = None
        self.bot = None
        self.dex = []
        self.extra_dex = []
        self.dex_segments = {}
        self.swarmLocation = ""
        self.swarmPokemon = ""
        self.swarmDate = None
        self.refreshSwarmDaily = True
        self.mirageIslandDate = None
        self.mirageIslandNum = ""
        self.pokemonByDexNum = {'extra': []}
        self.loadData()

    def loadData(self):
        self.loadRegionDataFromJSON()
        self.loadPokemonDataFromJSON()
        self.loadMoveDataFromJSON()
        self.loadTypeDataFromJSON()
        self.loadNatureDataFromJSON()
        self.loadQuestDataFromJSON()
        self.loadLocationDataFromJSON()
        self.loadEventDataFromJSON()
        self.loadCutsceneDataFromJSON()
        self.loadLegendaryPortalDataFromJSON()
        self.loadBattleTowerPokemonFromJSON()
        self.loadBattleTowerTrainersFromJSON()
        self.loadSecretBaseAreaDataFromJSON()
        self.loadSecretBaseItemDataFromJSON()
        self.loadShopDataFromJSON()
        self.loadTrainerIconDataFromJSON()
        self.loadAlteringCaveRestrictionsFromJSON()
        self.loadBattleTowerRestrictionsFromJSON()
        self.loadFlyRestrictionsFromJSON()
        self.loadAltShiniesFromJSON()
        self.loadDexSegmentsFromJSON()
        self.loadItemsFromJSON()

    def loadTrainerIconDataFromJSON(self):
        filename = 'trainer_card_data.json'
        with open("data/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.iconList.clear()
            for iconJson in data:
                icon = TrainerIcons.TrainerIcon(iconJson['name'],
                                                'data/sprites/trainer_card_sprites/' + iconJson['filename'],
                                                iconJson['price'], iconJson['category'], iconJson['subcategory'])
                self.iconList.append(icon)
            self.icon_subcategory = {'Owned': []}
            for icon in self.iconList:
                if icon.category not in self.icon_subcategory.keys():
                    self.icon_subcategory[icon.category] = []
                if icon.subcategory and icon.subcategory not in self.icon_subcategory[icon.category]:
                    self.icon_subcategory[icon.category].append(icon.subcategory)
                    self.icon_subcategory[icon.category].sort()

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

    def loadBattleTowerRestrictionsFromJSON(self):
        filename = 'battle_tower_restrictions.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.battleTowerRestrictions = data

    def loadFlyRestrictionsFromJSON(self):
        filename = 'fly_restrictions.json'
        with open("data/location/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.flyRestrictions["both"] = data['both']
            self.flyRestrictions["to"] = data['to']

    def loadAltShiniesFromJSON(self):
        filename = 'alternative_shiny_list.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.alternative_shinies["available"] = data['available']
            self.alternative_shinies["other"] = data['other']
            self.alternative_shinies["all"] = self.alternative_shinies["available"] + data['other']
            self.alternative_shinies["locations"] = data['locations']

    def loadDexSegmentsFromJSON(self):
        filename = 'dex_segments.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            genstr = data['gen1']
            genstrlist = genstr.split(':')
            self.dex_segments["gen1"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen2']
            genstrlist = genstr.split(':')
            self.dex_segments["gen2"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen3']
            genstrlist = genstr.split(':')
            self.dex_segments["gen3"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen4']
            genstrlist = genstr.split(':')
            self.dex_segments["gen4"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen5']
            genstrlist = genstr.split(':')
            self.dex_segments["gen5"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen6']
            genstrlist = genstr.split(':')
            self.dex_segments["gen6"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen7']
            genstrlist = genstr.split(':')
            self.dex_segments["gen7"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen8']
            genstrlist = genstr.split(':')
            self.dex_segments["gen8"] = [int(genstrlist[0]), int(genstrlist[1])]
            genstr = data['gen9']
            genstrlist = genstr.split(':')
            self.dex_segments["gen9"] = [int(genstrlist[0]), int(genstrlist[1])]

    def loadAlteringCaveRestrictionsFromJSON(self):
        filename = 'altering_cave_restrictions.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.alteringCaveRestrictions = data

    def loadLegendaryPortalDataFromJSON(self):
        filename = 'rotating_legends.json'
        name = filename[:-5]
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.legendaryPortalDict[name] = data

    def loadQuestDataFromJSON(self):
        filename = 'quests.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            questData = data['quests']
            for quest_json in questData:
                quest = Quest()
                quest.from_json(quest_json, self)
                self.questDict[quest.identifier] = quest

    def loadEventDataFromJSON(self):
        filename = 'events.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            events = data['events']
            for event in events:
                footer = ''
                if 'footer' in event:
                    footer = event['footer']
                quest_list = []
                if 'quests' in event:
                    quest_nums = event['quests']
                    for num in quest_nums:
                        quest_list.append(copy(self.questDict[num]))
                self.eventDict[event['name']] = PokeEvent(event['name'], event['item'], event['image'], event['desc'],
                                                          footer, quest_list)

    def loadItemsFromJSON(self):
        filename = 'items.json'
        with open("data/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            categories = data['categories']
            for category in categories:
                categoryItems = categories[category]
                itemList = []
                for item in categoryItems:
                    new_item = Item(item['name'])
                    if "multiplier" in item:
                        new_item.multiplier = item['multiplier']
                    if "price" in item:
                        new_item.price = item['price']
                    if "mart_tier" in item:
                        new_item.mart_tier = item['mart_tier']
                    if "bp_price" in item:
                        new_item.bp_price = item['bp_price']
                    if "effect" in item:
                        new_item.effects = item['effect']
                    if "amount" in item:
                        new_item.amount = item['amount']
                    if "battle_frontier_mart" in item:
                        new_item.battle_frontier_mart = item['battle_frontier_mart']
                    itemList.append(new_item)
                self.itemDict[category] = itemList

    def loadShopDataFromJSON(self):
        filename = 'shop.json'
        with open("data/end_game/" + filename, "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            categories = data['categories']
            for category in categories:
                categoryItems = categories[category]
                itemList = []
                for item in categoryItems:
                    item_obj = Shop_Item(item['item'], item['price'], item['currency'])
                    if 'type' in item:
                        item_obj.item_type = item['type']
                    itemList.append(item_obj)
                self.shopDict[category] = itemList

    def loadCutsceneDataFromJSON(self):
        for filename in os.listdir("data/cutscene"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/cutscene/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.cutsceneDict[name] = data

    def loadLocationDataFromJSON(self):
        for subdir, dirs, files in os.walk("data/location"):
            for filename in files:
                if filename.endswith(".json") and filename != "fly_restrictions.json":
                    name = filename[:-5]
                    with open(subdir + "/" + filename, "r", encoding="utf8") as read_file:
                        data = json.load(read_file)
                        self.locationDict[name] = data
                        self.locationObjDict[name] = Location(self, data)
        # print("location data loaded")

    def loadRegionDataFromJSON(self):
        # global regionDict
        with open("data/region/hoenn.json", "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.regionDict['hoenn'] = data
        with open("data/region/sinnoh.json", "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.regionDict['sinnoh'] = data
        with open("data/region/event.json", "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.regionDict['event'] = data
        with open("data/region/kanto.json", "r", encoding="utf8") as read_file:
            data = json.load(read_file)
            self.regionDict['kanto'] = data
        # print("region data loaded")

    def loadPokemonDataFromJSON(self):
        # global pokemonDict
        self.extra_dex.clear()
        self.dex.clear()
        self.pokemonByDexNum['extra'] = []
        for filename in os.listdir("data/pokemon"):
            #print("COMMENT THIS")
            try:
                if filename.endswith(".json"):
                    name = filename[:-5]
                    with open("data/pokemon/" + filename, "r", encoding="utf8") as read_file:
                        data = json.load(read_file)
                        self.pokemonDict[name] = data
                        if "exclude_from_all_dex" in data and data["exclude_from_all_dex"]:
                            pass
                        elif "exclude_from_dex" in data and data["exclude_from_dex"]:
                            self.extra_dex.append(name)
                            self.pokemonByDexNum['extra'].append(data['names']['en'])
                        else:
                            self.dex.append(name)
                            self.pokemonByDexNum[data['national_id']] = data['names']['en']
            except:
                print(filename)
                traceback.print_exc()
                print('')
        # print("pokemon data loaded")

    def loadMoveDataFromJSON(self):
        # global moveDict
        for filename in os.listdir("data/move"):
            if filename.endswith(".json"):
                try:
                    name = filename[:-5]
                    with open("data/move/" + filename, "r", encoding="utf8") as read_file:
                        data = json.load(read_file)
                        self.moveDict[name] = data
                except:
                    print(filename)
                    traceback.print_exc()
                    print('')
        # print("move data loaded")

    def loadTypeDataFromJSON(self):
        # global typeDict
        for filename in os.listdir("data/type"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/type/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.typeDict[name] = data
        # print("type data loaded")

    def loadNatureDataFromJSON(self):
        # global natureDict
        for filename in os.listdir("data/nature"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open("data/nature/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.natureDict[name] = data
        # print("nature data loaded")

    def loadSecretBaseAreaDataFromJSON(self):
        dir = "data/base/areas/"
        for filename in os.listdir(dir):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open(dir + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.secretBaseAreaDict[name] = Secret_Base_Area(name, data['name'], data['sprite'],
                                                                     data['validTiles'], data['validWallTiles'])

    def loadSecretBaseItemDataFromJSON(self):
        dir = "data/base/items/"
        for filename in os.listdir(dir + "_categories"):
            if filename.endswith(".json"):
                name = filename[:-5]
                with open(dir + "_categories/" + filename, "r", encoding="utf8") as read_file:
                    data = json.load(read_file)
                    self.secretBaseItemTypes[data['category']] = Secret_Base_Item_Type(data['category'], data['height'],
                                                                                       data['width'],
                                                                                       data['canItemsBePlacedOn'],
                                                                                       data['canPlaceOnSameLayer'],
                                                                                       data['layer'], data['wallItem'],
                                                                                       data['price'], data['currency'])
        for subdir, dirs, files in os.walk(dir):
            for filename in files:
                if "_categories" in subdir:
                    continue
                else:
                    if filename.endswith(".json"):
                        name = filename[:-5]
                        with open(os.path.join(subdir, filename), "r", encoding="utf8") as read_file:
                            data = json.load(read_file)
                            category = data['category']
                            categoryObj = None
                            if category in self.secretBaseItemTypes.keys():
                                categoryObj = self.secretBaseItemTypes[category]
                            elif category == 'custom':
                                categoryObj = Secret_Base_Item_Type(data['category'], data['height'], data['width'],
                                                                    data['canItemsBePlacedOn'],
                                                                    data['canPlaceOnSameLayer'],
                                                                    data['layer'], data['wallItem'], data['price'],
                                                                    data['currency'])
                            self.secretBaseItems[data['name']] = Secret_Base_Item(data['name'], name, data['sprite'],
                                                                                  categoryObj)

    def getAllTrainerIconsInCategory(self, category, subcategory=None, trainer=None):
        newList = []
        if category == "Owned" and trainer:
            trainer.trainer_icons.sort()
            for icon in self.iconList:
                if icon.name in trainer.trainer_icons:
                    newList.append(icon)
        else:
            for icon in self.iconList:
                if icon.category == category and (subcategory is None or icon.subcategory == subcategory):
                    newList.append(icon)
        return newList

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
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "sun"):
                    for moveObj in gameObj["learnset"]:
                        if "tm" in moveObj:
                            try:
                                moveList.append(self.getMoveData(moveObj["move"].lower()))
                            except:
                                continue
        moveList.append(self.getMoveData('tera blast'))
        return moveList

    def getAllEggMoves(self, pokemon):
        moveList = []
        pokemonObj = self.getPokemonData(pokemon)
        for gameObj in pokemonObj["move_learnsets"]:
            for gameName in gameObj["games"]:
                if (gameName.lower() == "sun"):
                    for moveObj in gameObj["learnset"]:
                        if "egg_move" in moveObj:
                            try:
                                moveList.append(self.getMoveData(moveObj["move"].lower()))
                            except:
                                continue
        return moveList

    def getAllLevelUpMoves(self, pokemon, level, isShadow=False):
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
        if isShadow:
            moveList.append("Shadow Rush")
            moveList.append("Shadow Blast")
            moveList.append("Shadow Down")
            moveList.append("Shadow Panic")
        return self.convertMoveList(moveList)

    def convertMoveList(self, moveList):
        newMoveList = []
        for moveName in moveList:
            newMoveList.append(self.getMoveData(moveName.lower()))
        return newMoveList

    def getEncounterTable(self, trainer, desiredLocation, encounterType):
        # global regionDict
        encounterList = []
        allowSurfing = 'surf' in trainer.flags and trainer.surfEncounters
        try:
            locationObj = self.getLocation(desiredLocation)
            region = locationObj.region
        except:
            region = 'hoenn'
        if region == 'sinnoh':
            game = 'platinum'
        elif region == 'kanto':
            game = 'firered'
        else:
            game = 'emerald'
        for location in self.regionDict[region]["locations"]:
            if (location["names"]["en"].lower() == desiredLocation.lower()):
                for pokemonLocationInfo in location["pokemon"]:
                    for gameName in pokemonLocationInfo["games"]:
                        if (gameName.lower() == game and pokemonLocationInfo["location"] == encounterType):
                            encounterList.append(pokemonLocationInfo)
                        elif (allowSurfing and gameName.lower() == game and
                              (pokemonLocationInfo["location"] == 'Surfing'
                               or pokemonLocationInfo["location"] == 'Old Rod'
                               or pokemonLocationInfo["location"] == 'Good Rod'
                               or pokemonLocationInfo["location"] == 'Super Rod')):
                            encounterList.append(pokemonLocationInfo)
                break
        return encounterList

    def getPokemonData(self, pokemon):
        return self.pokemonDict[
            pokemon.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":", "").replace("'", "")]

    def getGenByDexNum(self, dexNum):
        for gen, minMaxPair in self.dex_segments.items():
            min = minMaxPair[0]
            max = minMaxPair[1]
            if min <= dexNum <= max:
                return gen

    def getAllPokemonInGen(self, genNum):
        if genNum == "extra" or genNum == "event":
            return self.pokemonByDexNum['extra']
        gen = "gen" + str(genNum)
        minMaxPair = self.dex_segments[gen]
        minRange = minMaxPair[0]
        maxRange = minMaxPair[1]
        pokemonList = []
        dexNumRange = range(minRange, maxRange + 1)
        for dexNum in dexNumRange:
            name = self.getPokemonNameByDexNum(dexNum)
            pokemonList.append(name)
        return pokemonList

    def getPokemonNameByDexNum(self, dexNum):
        if dexNum in self.pokemonByDexNum.keys():
            return self.pokemonByDexNum[dexNum]
        return ""

    def getNumberOfPokemonInGen(self, genNum):
        gen = "gen" + str(genNum)
        minMaxPair = self.dex_segments[gen]
        min = minMaxPair[0]
        max = minMaxPair[1]
        return max - min + 1

    def getStartAndEndOfGenNums(self, genNum):
        if genNum == "event" or genNum == "extra":
            return 1, len(self.extra_dex)
        gen = "gen" + str(genNum)
        minMaxPair = self.dex_segments[gen]
        min = minMaxPair[0]
        max = minMaxPair[1]
        return min, max

    def getNumberOfPokemon(self, dexType=None):
        if dexType:
            if dexType == "non-event":
                return len(self.dex)
            elif dexType == "event":
                return len(self.extra_dex)
        return len(self.pokemonDict)

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

    def get_item_from_shop(self, item_name):
        for category, itemList in self.shopDict.items():
            for item in itemList:
                if item.itemName.lower() == item_name.lower():
                    return item

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
            return (":ghost:")
        elif (status == 'seeded'):
            return (':seedling:')
        elif (status == 'raid'):
            return (':boom:')
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
            return ("➡️")
        elif (name == 'left arrow'):
            return ("⬅️")
        elif (name == 'down arrow'):
            return ('↩️')
        elif (name == 'physical'):
            return ("🤜")
        elif (name == 'special'):
            return ("🪄")
        elif (name == 'no damage'):
            return ("🚫")
        elif (name == 'swap'):
            return ("🔄")
        elif (name == 'pokeball'):
            return ("🔴")
        elif (name == 'greatball'):
            return ("🔵")
        elif (name == 'ultraball'):
            return ("🟡")
        elif (name == 'masterball'):
            return ("🟣")
        elif (name == 'repeatball'):
            return ("🟠")
        elif (name == 'premierball'):
            return ("⚪")
        elif (name == 'quickball'):
            return ("🟢")
        elif (name == 'timerball'):
            return ("🟤")
        elif (name == 'box'):
            return ('📥')
        elif (name == 'party'):
            return ('🎊')
        elif (name == 'fly'):
            return ('✈️')
        elif (name == "confirm"):
            return ('☑️')
        elif (name == "cancel"):
            return ('🇽')
        elif (name == "edit"):
            return ('🔨')
        elif (name == "tera"):
            return ('💎')
        else:
            return '\u0034\u20E3'

    def writeOtherDataToJSON(self):
        data = {}
        data['swarmLocation'] = self.swarmLocation
        data['swarmPokemon'] = self.swarmPokemon
        data['swarmDate'] = str(self.swarmDate)
        data['refreshSwarmDaily'] = self.refreshSwarmDaily
        data['activeEvent'] = self.activeEvent
        data['eventActive'] = self.eventActive
        data['mirageIslandDate'] = str(self.mirageIslandDate)
        data['mirageIslandNum'] = self.mirageIslandNum
        with open('otherData.json', 'w') as outfile:
            json.dump(data, outfile)

    def readOtherDataFromJSON(self):
        with open('otherData.json', encoding='utf8') as json_file:
            data = json.load(json_file)
            if 'refreshSwarmDaily' in data:
                self.refreshSwarmDaily = data['refreshSwarmDaily']
            if not self.refreshSwarmDaily:
                if 'swarmLocation' in data:
                    self.swarmLocation = data['swarmLocation']
                if 'swarmPokemon' in data:
                    self.swarmPokemon = data['swarmPokemon']
            elif 'swarmDate' in data:
                try:
                    date = datetime.strptime(data['swarmDate'], "%Y-%m-%d").date()
                    if datetime.today().date() == date:
                        if 'swarmLocation' in data:
                            self.swarmLocation = data['swarmLocation']
                        if 'swarmPokemon' in data:
                            self.swarmPokemon = data['swarmPokemon']
                        self.swarmDate = date
                except:
                    pass
            if 'activeEvent' in data:
                self.activeEvent = data['activeEvent']
            if 'eventActive' in data:
                self.eventActive = data['eventActive']
            if 'mirageIslandDate' in data:
                try:
                    date = datetime.strptime(data['mirageIslandDate'], "%Y-%m-%d").date()
                    if datetime.today().date() == date:
                        if 'mirageIslandNum' in data:
                            self.mirageIslandNum = data['mirageIslandNum']
                        self.mirageIslandDate = date
                except:
                    pass

    def writeUsersToJSON(self):
        copyfile("trainerData.json", "backup.json")
        data = {}
        data['timestamp'] = str(datetime.today())
        data['globalSaves'] = []
        for identifier, globalTuple in self.globalSaveDict.items():
            data['globalSaves'].append({'identifier': identifier,
                                        'server_id': globalTuple[0],
                                        'author': globalTuple[1]})
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
                if server_id == "timestamp":
                    continue
                if server_id == 'globalSaves':
                    for globalSaveObj in data['globalSaves']:
                        identifier = globalSaveObj['identifier']
                        server_id = globalSaveObj['server_id']
                        author = globalSaveObj['author']
                        self.globalSaveDict[int(identifier)] = (server_id, author)
                    continue
                self.staminaDict[server_id] = data[server_id]['staminaEnabled']
                for userJSON in data[server_id]['users']:
                    identifier = -1
                    if 'identifier' in userJSON:
                        identifier = userJSON['identifier']
                    user = Trainer(identifier, userJSON['author'], userJSON['name'], userJSON['location'])
                    user.fromJSON(userJSON, self)
                    self.addUser(server_id, user)

    def getUser(self, inter):  # user, isNewUser
        server_id = str(inter.guild.id)
        user = self.checkForGlobalSave(inter)
        if user:
            return user, False
        if server_id in self.userDict.keys():
            for user in self.userDict[server_id]:
                if user.identifier == inter.author.id:
                    self.updateDisplayNameAndAuthor(inter, user)
                    return user, False
            for user in self.userDict[server_id]:
                if str(user.author) == str(inter.author):
                    self.updateIdentifier(inter, user)
                    self.updateDisplayNameAndAuthor(inter, user)
                    return user, False
        newUser = Trainer(inter.author.id, str(inter.author), str(inter.author.display_name), "Littleroot Town")
        self.addUser(server_id, newUser)
        self.globalSaveDict[inter.author.id] = (inter.guild.id, str(inter.author))  # make save global by default
        return newUser, True

    def clone_user(self, user_to_clone, new_id):
        clone = copy(user_to_clone)
        clone.identifier = new_id
        clone.questList = copy(user_to_clone.questList)
        clone.completedQuestList = copy(user_to_clone.completedQuestList)
        self.addUser("CLONED", clone)
        self.globalSaveDict[clone.identifier] = ("CLONED", clone.author)
        user_to_clone.closed = True

    def checkForGlobalSave(self, inter=None, identifier=None):
        if inter is None and identifier is None:
            return None
        if identifier is None:
            identifier = inter.author.id
        if identifier in self.globalSaveDict.keys():
            globalServerId, authorStr = self.globalSaveDict[identifier]
            globalServerId = str(globalServerId)
            if globalServerId in self.userDict.keys():
                for user in self.userDict[globalServerId]:
                    if user.identifier == identifier:
                        self.updateDisplayNameAndAuthor(inter, user)
                        if inter:
                            if str(inter.guild.id) not in self.staminaDict.keys():
                                self.staminaDict[str(inter.guild.id)] = False
                        return user
        return None

    def updateIdentifier(self, inter, user):
        if user.identifier != inter.author.id:
            user.identifier = inter.author.id

    def updateDisplayNameAndAuthor(self, inter, user):
        if inter is None or user is None:
            return
        if user.name != str(inter.author):
            user.name = str(inter.author)
        if str(user.author) != str(inter.author):
            user.author = str(inter.author)

    def getUserById(self, server_id, identifier, skip_global=False):  # user
        server_id = str(server_id)
        user = None
        if not skip_global:
            user = self.checkForGlobalSave(None, identifier)
        if user:
            return user
        if server_id in self.userDict.keys():
            for user in self.userDict[server_id]:
                if user.identifier == identifier:
                    return user
        return None

    # def getUserByAuthor(self, server_id, author, fetched_user=None): # user, isNewUser
    #     server_id = str(server_id)
    #     for globalAuthorId, globalTuple in self.globalSaveDict.items():
    #         globalServerId = str(globalTuple[0])
    #         authorStr = globalTuple[1]
    #         if authorStr.lower() == str(author).lower():
    #             if globalServerId in self.userDict.keys():
    #                 for user in self.userDict[globalServerId]:
    #                     if user.identifier == globalAuthorId:
    #                         return user, False
    #     if server_id in self.userDict.keys():
    #         for user in self.userDict[server_id]:
    #             if str(user.author).lower() == str(author).lower():
    #                 return user, False
    #             if (str(user.name).lower() == str(author).lower()):
    #                 return user, False
    #             if fetched_user:
    #                 if fetched_user.display_name.lower() == str(user.author).lower()\
    #                         or fetched_user.display_name.lower() == str(user.name).lower():
    #                     return user, False
    #     return None, True

    def addUser(self, server_id, user):
        server_id = str(server_id)
        if server_id in self.userDict.keys():
            self.userDict[str(server_id)].append(user)
        else:
            if server_id not in self.staminaDict.keys():
                self.staminaDict[str(server_id)] = False
            self.userDict[str(server_id)] = []
            self.userDict[str(server_id)].append(user)

    def deleteUser(self, server_id, user):
        if str(server_id) in self.userDict.keys():
            if user in self.userDict[str(server_id)]:
                self.userDict[str(server_id)].remove(user)
                return True
        return False

    def isUserInSession(self, inter, user):
        if user.identifier in self.globalSaveDict:
            if str(user.identifier) in self.sessionDict.keys():
                if len(self.sessionDict[str(user.identifier)]) > 0:
                    return True
            return False
        if user in self.getSessionList(inter):
            return True
        return False

    def isUserInAnySession(self, user):
        if user.identifier in self.globalSaveDict:
            if str(user.identifier) in self.sessionDict.keys():
                if len(self.sessionDict[str(user.identifier)]) > 0:
                    return True
            return False
        for server_id, serverList in self.sessionDict.items():
            for activeUser in serverList:
                if user.identifier == activeUser.identifier:
                    return True
        return False

    def addUserSession(self, server_id, user):
        server_id = str(server_id)
        if user.identifier in self.globalSaveDict:
            if str(user.identifier) in self.sessionDict.keys():
                if (user not in self.sessionDict[str(user.identifier)]):
                    self.sessionDict[str(user.identifier)].append(user)
                    return True
            else:
                self.sessionDict[str(user.identifier)] = []
                self.sessionDict[str(user.identifier)].append(user)
                return True
            return False
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

    def doesUserHaveActiveSession(self, server_id, user):
        server_id = str(server_id)
        if user.identifier in self.globalSaveDict:
            if str(user.identifier) in self.sessionDict.keys():
                if (user not in self.sessionDict[str(user.identifier)]):
                    return False
            else:
                return False
            return True
        if server_id in self.sessionDict.keys():
            if (user not in self.sessionDict[server_id] and user in self.userDict[str(server_id)]):
                return False
        return True

    def removeUserSession(self, server_id, user):
        globalSuccess = self.removeUserSessionGlobal(user)
        localSuccess = self.removeUserSessionLocal(server_id, user)
        success = globalSuccess or localSuccess
        return success

    def removeUserSessionGlobal(self, user):
        if user.identifier in self.globalSaveDict:
            if str(user.identifier) in self.sessionDict.keys():
                if user in self.sessionDict[str(user.identifier)]:
                    self.sessionDict[str(user.identifier)].remove(user)
                    return True
            return False

    def removeUserSessionLocal(self, server_id, user):
        server_id = str(server_id)
        if server_id in self.sessionDict.keys():
            if (user in self.sessionDict[server_id]):
                self.sessionDict[server_id].remove(user)
                return True
        return False

    def getSessionList(self, inter):
        server_id = str(inter.guild.id)
        if server_id in self.sessionDict.keys():
            return self.sessionDict[server_id]
        return []

    def isUserIdInUserDict(self, server_id, user_id):
        if str(server_id) in self.userDict:
            for user in self.userDict[str(server_id)]:
                if user.identifier == user_id:
                    return True
        return False

    def addOverworldSession(self, inter, user, message, temp_uuid):
        self.removeOverworldSession(inter, user)
        server_id = inter.guild.id
        if user:
            userIdentifier = user.identifier
        else:
            userIdentifier = inter.author.id
        if userIdentifier in self.globalSaveDict:
            if "global" in self.overworldSessions.keys():
                if userIdentifier not in self.overworldSessions["global"]:
                    self.overworldSessions["global"][userIdentifier] = (message, temp_uuid)
                    return True
            else:
                self.overworldSessions["global"] = {}
                self.overworldSessions["global"][userIdentifier] = (message, temp_uuid)
                return True
            return False
        if server_id in self.overworldSessions.keys():
            if userIdentifier not in self.overworldSessions[server_id] and self.isUserIdInUserDict(server_id,
                                                                                                   userIdentifier):
                self.overworldSessions[server_id][userIdentifier] = (message, temp_uuid)
                return True
        else:
            if str(server_id) in self.userDict.keys():
                if self.isUserIdInUserDict(server_id, userIdentifier):
                    self.overworldSessions[server_id] = {}
                    self.overworldSessions[server_id][userIdentifier] = (message, temp_uuid)
                    return True
        return False

    def removeOverworldSession(self, inter, user=None):
        if user:
            userIdentifier = user.identifier
        else:
            userIdentifier = inter.author.id
        overworldTuple, isGlobal = self.userInOverworldSession(inter, user)
        if overworldTuple:
            if isGlobal:
                server_id = "global"
            else:
                server_id = inter.guild.id
            try:
                del self.overworldSessions[server_id][userIdentifier]
                return True
            except:
                return False
        else:
            return False

    def userInOverworldSession(self, inter, user=None):
        server_id = inter.guild.id
        if user:
            userIdentifier = user.identifier
        else:
            userIdentifier = inter.author.id
        if userIdentifier in self.globalSaveDict:
            if "global" in self.overworldSessions.keys():
                if userIdentifier in self.overworldSessions["global"]:
                    return self.overworldSessions["global"][userIdentifier], True
                else:
                    return None, True
        if server_id in self.overworldSessions.keys():
            if userIdentifier in self.overworldSessions[server_id] and self.isUserIdInUserDict(server_id,
                                                                                               userIdentifier):
                return self.overworldSessions[server_id][userIdentifier], False
        return None, False

    def getServerPVPDict(self, inter):
        server_id = str(inter.guild.id)
        if server_id in self.pvpDictByServerId.keys():
            return self.pvpDictByServerId[server_id]
        else:
            self.pvpDictByServerId[server_id] = {}
            return self.pvpDictByServerId[server_id]

    def updateRecentActivityDict(self, inter, user):
        user_id = user.identifier
        self.recentActivityDict[user_id] = (
        datetime.today(), inter.guild.id, inter.channel.id, user.checkFlag('elite4'))

    def getNumOfRecentUsersForRaid(self, guild_id=None, channel_id=None):
        count = 0
        now = datetime.today()
        toDelete = []
        channelList = []
        for user_id, recentTuple in self.recentActivityDict.items():
            date = recentTuple[0]
            temp_guild__id = recentTuple[1]
            temp_channel_id = recentTuple[2]
            beatElite4 = recentTuple[3]
            if (now - timedelta(hours=5) <= date <= now) and (guild_id is None or guild_id == temp_guild__id) \
                    and (channel_id is None or channel_id == temp_channel_id) and beatElite4:
                if temp_channel_id not in channelList:
                    channelList.append(temp_channel_id)
                count += 1
            else:
                toDelete.append(user_id)
        for user_id in toDelete:
            try:
                del self.recentActivityDict[user_id]
            except:
                pass
        return count, channelList

    def isUserInRaidList(self, user):
        if self.raid:
            return self.raid.isUserInRaidList(user)
        return False

    def setBot(self, bot):
        self.bot = bot

    def getChannelById(self, channel_id):
        return self.bot.get_channel(channel_id)

    def getGuildById(self, guild_id):
        return self.bot.get_guild(guild_id)

    def getRoleById(self, guild_id, role_id):
        guild = self.getGuildById(guild_id)
        return guild.get_role(role_id)

    async def setRaid(self, raid):
        logging.debug("raid - setRaid in data.py")
        if self.raid and not self.raid.raidEnded:
            logging.debug("raid - ending previous raid as failure")
            await self.raid.endRaid(False)
        self.raid = raid

    def getItemByName(self, name):
        for category in self.itemDict.keys():
            for item in self.itemDict[category]:
                if item.name == name:
                    return item
        return None

    def getItemsForMartTier(self, tier):
        tiered_item_dict = {}
        if tier == "battle_frontier":
            for category in self.itemDict.keys():
                itemList = []
                for item in self.itemDict[category]:
                    if item.battle_frontier_mart:
                        itemList.append(item)
                tiered_item_dict[category] = itemList
        else:
            try:
                tier = int(tier)
            except:
                return tiered_item_dict
            for category in self.itemDict.keys():
                itemList = []
                for item in self.itemDict[category]:
                    if tier in item.mart_tier:
                        itemList.append(item)
                tiered_item_dict[category] = itemList
        return tiered_item_dict

    def shinyCharmCheck(self, trainer, pokemon):
        if 'Shiny Charm' in trainer.itemList.keys():
            if trainer.getItemAmount('Shiny Charm') > 0:
                if not pokemon.shiny:
                    shinyInt = random.randint(1, 50)
                    # shinyInt = random.randint(1, 1)
                    if (shinyInt == 1):
                        pokemon.shiny = True
                        pokemon.setSpritePath()
                if pokemon.shiny:
                    trainer.useItem('Shiny Charm', 1)
        return pokemon
