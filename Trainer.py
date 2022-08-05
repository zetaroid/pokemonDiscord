import Secret_Base
from Pokemon import Pokemon
from datetime import datetime, timedelta
from copy import copy

from Quests import Quest


class Trainer(object):

    def __init__(self, identifier, author, name, location, partyPokemon=None, boxPokemon=None, locationProgressDict=None,
                 flags=None, itemList=None, lastCenter=None, dailyProgress=None, withRestrictionStreak=None,
                 noRestrictionsStreak=None, alteringPokemon=None, withRestrictionsRecord=None,
                 noRestrictionsRecord=None, pvpWins=None, pvpLosses=None, secretBase=None, secretBaseItems=None, iphone=None,
                 storeAmount=None, teamsList=None, lastBoxNum=None):
        self.identifier = identifier
        self.author = author
        self.name = name
        self.date = datetime.today().date()
        self.location = location
        self.rewards = {}
        self.rewardFlags = []
        self.rewardRemoveFlag = []
        self.sprite = "data/sprites/trainer_card_sprites/trainerSprite.png"
        self.beforeBattleText = ""
        self.shouldScale = False
        self.secretBase = secretBase
        self.pokedex = []
        self.trainer_icons = ['Default']
        self.questList = []
        self.completedQuestList = []
        self.closed = False
        self.last_quest_claim = (datetime.today() - timedelta(days=1)).date()
        self.last_vote = (datetime.today() - timedelta(days=1)).date()
        self.vote_reward_claimed = False
        self.swarmChain = 0

        if not storeAmount:
            self.storeAmount = 1
        else:
            self.storeAmount = storeAmount

        if not iphone:
            self.iphone = False
        else:
            self.iphone = iphone

        if secretBaseItems is None:
            self.secretBaseItems = {}
        else:
            self.secretBaseItems = secretBaseItems

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

        if teamsList is None:
            self.teamDict = {}
        else:
            self.teamDict = teamsList

        if (lastBoxNum is None):
            self.lastBoxNum = 0
        else:
            self.lastBoxNum = lastBoxNum

        self.current_trade_id = 0
        self.trade_requested_to = False

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
                          self.alteringPokemon, self.withRestrictionsRecord, self.noRestrictionsRecord, self.pvpWins,
                          self.pvpLosses, self.secretBase, self.secretBaseItems, self.iphone, self.storeAmount, self.teamDict,
                          self.lastBoxNum)
        trainerCopy.sprite = self.sprite
        trainerCopy.rewards = self.rewards
        trainerCopy.rewardFlags = self.rewardFlags
        trainerCopy.rewardRemoveFlag = self.rewardRemoveFlag
        trainerCopy.beforeBattleText = self.beforeBattleText
        trainerCopy.current_trade_id = self.current_trade_id
        trainerCopy.closed = self.closed
        return trainerCopy

    def createTeamStrFromParty(self):
        teamStr = ''
        for pokemon in self.partyPokemon:
            teamStr += pokemon.identifier + ","
        if teamStr.endswith(","):
            teamStr = teamStr[:-1]
        return teamStr

    def createTeamFromParty(self, teamNum, teamName=None):
        teamNum = int(teamNum)
        teamStr = self.createTeamStrFromParty()
        newTeam = Team(teamNum, teamName, teamStr)
        # print("New team " + str(teamNum) + " created: ", teamStr)
        self.teamDict[teamNum] = newTeam

    def createTeamFromStr(self, teamStr, teamNum, teamName=None):
        teamNum = int(teamNum)
        newTeam = Team(teamNum, teamName, teamStr)
        self.teamDict[teamNum] = newTeam

    def setTeam(self, teamNum=None, teamName=None):
        teamToSet = None
        self.createTeamFromParty(0, "Party")
        errorReason = ''
        if teamName:
            for tempTeamNum, tempTeam in self.teamDict.items():
                if tempTeam.name.lower() == teamName.lower():
                    teamToSet = tempTeam
        elif teamNum:
            teamNum = int(teamNum)
            if teamNum in self.teamDict:
                teamToSet = self.teamDict[teamNum]
        if teamToSet:
            if teamToSet.teamStr:
                success, errorReason = self.setTeamByStr(teamToSet.teamStr)
                if success:
                    try:
                         del self.teamDict[0]
                    except:
                        pass
                    return success, teamToSet.name, errorReason
                # print("setting party again")
                successParty, errorReasonParty = self.setTeamByStr(self.teamDict[0].teamStr)
        try:
            del self.teamDict[0]
        except:
            pass
        return False, '', errorReason

    def setTeamByStr(self, teamStr):
        pokemonIdentifierList = teamStr.split(',')
        errorReason = ''
        if len(pokemonIdentifierList) > 0:
            self.dumpPartyToBox()
            tempIdList = []
            missingIdentifier = ''
            for identifier in pokemonIdentifierList:
                # print('looking for: ', identifier)
                identifierFound = False
                boxNum = 0
                for pokemon in self.boxPokemon:
                    # print(pokemon.identifier)
                    if pokemon.identifier == identifier:
                        identifierFound = True
                        # print('found')
                        self.movePokemonBoxToParty(boxNum)
                        # self.partyPokemon.append(pokemon)
                        tempIdList.append(pokemon.identifier)
                        break
                    boxNum += 1
                if not identifierFound:
                    missingIdentifier = identifier
                    # print('id not found = ', missingIdentifier)
                    errorReason = 'Pokemon previously a part of team missing.'
                    break
            # print("tempIdList = ", tempIdList)
            # print("missingIdentifier = ", missingIdentifier)
            # print("pokemonIdentifierList = ", pokemonIdentifierList)
            if missingIdentifier == '':
                return True, errorReason
        return False, errorReason

    def dumpPartyToBox(self):
        # print('dump')
        for x in range(0, len(self.partyPokemon)):
            self.movePokemonPartyToBox(0, True)

    def setBeforeBattleText(self, text):
        self.beforeBattleText = text

    def setSprite(self, sprite):
        self.sprite = sprite

    def getSecretBaseLocation(self):
        if self.secretBase:
            return self.secretBase.location
        return "Test"

    def setRewards(self, rewards):
        self.rewards = rewards

    def addSecretBaseItem(self, item, amount):
        if item in self.secretBaseItems:
            self.secretBaseItems[item] = self.secretBaseItems[item] + amount
        else:
            self.secretBaseItems[item] = amount

    def addItem(self, item, amount):
        if (item in self.itemList):
            self.itemList[item] = self.itemList[item] + amount
        else:
            self.itemList[item] = amount

    def useItem(self, item, amount):
        if (item in self.itemList):
            self.itemList[item] = self.itemList[item] - amount
            if self.itemList[item] < 0:
                self.itemList[item] = 0
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

    def increasePartyHappiness(self, amount=1):
        for pokemon in self.partyPokemon:
            pokemon.increaseHappiness(amount)

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

    def addPokemon(self, pokemon, changeOT, wasCaught=False, locationOverride=""):
        if changeOT:
            pokemon.OT = self.author
        if wasCaught:
            if locationOverride:
                self.caughtEvent(pokemon, locationOverride)
            else:
                self.caughtEvent(pokemon, self.location)
        self.update_pokedex(pokemon.name)
        pokemon.setCaughtAt(self.location)
        if locationOverride:
            pokemon.setCaughtAt(locationOverride)
        if (len(self.partyPokemon) < 6):
            self.partyPokemon.append(pokemon)
        else:
            self.boxPokemon.append(pokemon)

    def caughtEvent(self, pokemon, location):
        for quest in self.questList:
            quest.catch_pokemon(pokemon, location)
            self.update_quest(quest)

    def trainerDefeatedEvent(self, trainer=None):
        for quest in self.questList:
            quest.defeat_trainer(trainer)
            self.update_quest(quest)

    def wildDefeatedEvent(self, pokemon, location, data):
        for quest in self.questList:
            quest.defeat_pokemon(pokemon, location)
            self.update_quest(quest)
        if data.swarmPokemon == pokemon.name and data.swarmLocation == location:
            self.swarmChain += 1

    def raidDefeatedEvent(self, raidTrainer=None):
        for quest in self.questList:
            quest.defeat_raid()
            self.update_quest(quest)

    def update_quest(self, quest):
        quest.check_complete()

    def num_quests_completed(self):
        num_completed = 0
        for quest in self.questList:
            if quest.complete:
                num_completed +=1
        return num_completed

    def clear_completed_quests(self):
        self.completedQuestList.clear()

    def swapPartyPokemon(self, pos):
        if (pos != 0):
            self.partyPokemon[0], self.partyPokemon[pos] = self.partyPokemon[pos], self.partyPokemon[0] 

    def movePokemonPartyToBox(self, index, overrideCheck=False):
        if (len(self.partyPokemon) > 1) or overrideCheck:
            pokemon = self.partyPokemon.pop(index)
            self.boxPokemon.append(pokemon)
            # print(pokemon.name + " moved to box.")
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

    def update_pokedex(self, pokemon_name):
        if pokemon_name not in self.pokedex:
            self.pokedex.append(pokemon_name)

    def get_number_caught(self, data, dexType=None):
        if dexType:
            count = 0
            if dexType == "non-event":
                for pokemon_name in self.pokedex:
                    modified_name = pokemon_name.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":", "").replace("'", "")
                    if modified_name.lower() in data.dex:
                        count += 1
            elif dexType == "event":
                for pokemon_name in self.pokedex:
                    modified_name = pokemon_name.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":", "").replace("'", "")
                    if modified_name.lower() in data.extra_dex:
                        count += 1
            elif "gen" in dexType:
                try:
                    genNum = int(dexType[-1])
                except:
                    return -1
                for pokemon_name in self.pokedex:
                    pokemonData = data.getPokemonData(pokemon_name)
                    if "national_id" in pokemonData:
                        pokemonNum = pokemonData["national_id"]
                    else:
                        return -1
                    genStr = data.getGenByDexNum(pokemonNum)
                    if genStr == dexType:
                        count += 1
            return count
        return len(self.pokedex)

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

    def ready_for_daily_vote(self):
        if self.last_vote:
            if datetime.today().date() > self.last_vote:
                self.vote_reward_claimed = False
                return True
        else:
            self.vote_reward_claimed = False
            return True
        return False

    def ready_for_daily_quest(self):
        if self.last_quest_claim:
            if datetime.today().date() > self.last_quest_claim:
                for quest in self.questList:
                    if 'daily' in quest.title.lower():
                        return False
                return True
        else:
            return True
        return False

    def claim_daily_quest(self):
        self.last_quest_claim = datetime.today().date()
        # TODO: Generate quest and add it
        quest = Quest()
        quest.title = "Daily Quest - " + str(self.last_quest_claim)
        quest.task = 'defeat_specific_pokemon'
        quest.defeat_specific_pokemon['Poochyena'] = 1
        quest.defeat_specific_pokemon_original['Poochyena'] = 1
        quest.started = True
        self.questList.append(quest)

    def toJSON(self):
        partyPokemonArray = []
        for pokemon in self.partyPokemon:
            partyPokemonArray.append(pokemon.toJSON())
        boxPokemonArray = []
        for pokemon in self.boxPokemon:
            boxPokemonArray.append(pokemon.toJSON())
        questArray = []
        for quest in self.questList:
            questArray.append(quest.to_json())
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
        teamList = []
        for team in self.teamDict.values():
            teamList.append(team.toJSON())
        jsonDict = {
            'identifier': self.identifier,
            'author': self.author,
            'name': self.name,
            'date': str(self.date),
            'location': self.location,
            'lastCenter': self.lastCenter,
            'dailyProgress': self.dailyProgress,
            'withRestrictionStreak': self.withRestrictionStreak,
            'noRestrictionsStreak': self.noRestrictionsStreak,
            'alteringPokemon': self.alteringPokemon,
            'withRestrictionsRecord': self.withRestrictionsRecord,
            'noRestrictionsRecord': self.noRestrictionsRecord,
            'pvpWins': self.pvpWins,
            'pvpLosses': self.pvpLosses,
            "sprite": self.sprite,
            "iphone": self.iphone,
            "storeAmount": self.storeAmount,
            "lastBoxNum": self.lastBoxNum,
            'partyPokemon': partyPokemonArray,
            'boxPokemon': boxPokemonArray,
            'itemNames': itemNameArray,
            'itemAmounts': itemAmountArray,
            'locationProgressNames': locationProgressNameArray,
            'locationProgressAmounts': locationProgressAmountArray,
            'flags': self.flags,
            'teamList': teamList,
            'questList': questArray,
            'last_quest_claim': str(self.last_quest_claim),
            'last_vote': str(self.last_vote),
            'vote_reward_claimed': self.vote_reward_claimed,
            "completedQuestList": self.completedQuestList,
            "trainer_icons": self.trainer_icons,
            "closed": self.closed,
            "swarmChain": self.swarmChain
        }
        if self.secretBase:
            jsonDict['secretBase'] = self.secretBase.toJSON()
        return jsonDict

    def fromJSON(self, json, data):
        if 'identifier' in json:
            self.identifier = json['identifier']
        self.author = json['author']
        self.name = json['name']
        self.date = datetime.strptime(json['date'], "%Y-%m-%d").date()
        if 'last_quest_claim' in json:
            self.last_quest_claim = datetime.strptime(json['last_quest_claim'], "%Y-%m-%d").date()
        if 'last_vote' in json:
            self.last_vote = datetime.strptime(json['last_vote'], "%Y-%m-%d").date()
        self.location = json['location']
        self.dailyProgress = json['dailyProgress']
        self.lastCenter = json['lastCenter']
        self.flags = json['flags']
        if 'secretBase' in json:
            self.secretBase = Secret_Base.fromJSON(data, json['secretBase'])
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
        if 'swarmChain' in json:
            self.swarmChain = json['swarmChain']
        if 'pvpWins' in json:
            self.pvpWins = json['pvpWins']
        if 'pvpLosses' in json:
            self.pvpLosses = json['pvpLosses']
        if 'sprite' in json:
            path = json['sprite']
            if 'data' not in path:
                path = "data/sprites/trainer_card_sprites/" + path
            self.sprite = path
        if 'storeAmount' in json:
            self.storeAmount = json['storeAmount']
        if 'iphone' in json:
            self.iphone = json['iphone']
        if 'questList' in json:
            for questJSON in json['questList']:
                quest = Quest()
                quest.from_json(questJSON, data)
                quest.started = True
                quest.check_complete()
                self.questList.append(quest)
        if 'completedQuestList' in json:
            for questTitle in json['completedQuestList']:
                self.completedQuestList.append(questTitle)
        if 'trainer_icons' in json:
            for icon_name in json['trainer_icons']:
                self.trainer_icons.append(icon_name)
        partyPokemon = []
        for pokemonJSON in json['partyPokemon']:
            pokemon_name = pokemonJSON['name']
            pokemon = Pokemon(data, pokemon_name, pokemonJSON['level'])
            pokemon.fromJSON(pokemonJSON)
            partyPokemon.append(pokemon)
        self.partyPokemon = partyPokemon
        boxPokemon = []
        for pokemonJSON in json['boxPokemon']:
            pokemon_name = pokemonJSON['name']
            pokemon = Pokemon(data, pokemon_name, pokemonJSON['level'])
            pokemon.fromJSON(pokemonJSON)
            boxPokemon.append(pokemon)
        self.boxPokemon = boxPokemon
        if 'pokedex' in json:
            for pokemon_name in json['pokedex']:
                self.update_pokedex(pokemon_name)
        else:
            for pokemon in self.partyPokemon:
                self.update_pokedex(pokemon.name)
            for pokemon in self.boxPokemon:
                self.update_pokedex(pokemon.name)
        # Temp fix:
        for pokemon in self.partyPokemon:
            self.update_pokedex(pokemon.name)
        for pokemon in self.boxPokemon:
            self.update_pokedex(pokemon.name)
        if 'lastBoxNum' in json:
            self.lastBoxNum = json['lastBoxNum']
        if 'teamList' in json:
            for teamJSON in json['teamList']:
                number = int(teamJSON['number'])
                newTeam = Team(number, teamJSON['name'], teamJSON['teamStr'])
                self.teamDict[number] = newTeam
        if 'closed' in json:
            self.closed = json['closed']
        if 'vote_reward_claimed' in json:
            self.vote_reward_claimed = json['vote_reward_claimed']
        locationProgressDict = {}
        for x in range(0, len(json['locationProgressNames'])):
            locationProgressDict[json['locationProgressNames'][x]] = json['locationProgressAmounts'][x]
        self.locationProgressDict = locationProgressDict
        itemDict = {}
        for x in range(0, len(json['itemNames'])):
            itemDict[json['itemNames'][x]] = json['itemAmounts'][x]
        self.itemList = itemDict


class Team(object):

    def __init__(self, number, name=None, teamStr=None):
        self.number = number
        if name is not None:
            self.name = name
        else:
            self.name = "Team " + str(number)
        if teamStr is not None:
            self.teamStr = teamStr
        else:
            self.teamStr = ''

    def getNameList(self, trainer):
        nameList = []
        for identifier in self.teamStr.split(','):
            idFound = False
            for pokemon in trainer.partyPokemon:
                if pokemon.identifier == identifier:
                    idFound = True
                    nameList.append(pokemon.name)
                    break
            if not idFound:
                for pokemon in trainer.boxPokemon:
                    if pokemon.identifier == identifier:
                        idFound = True
                        nameList.append(pokemon.name)
                        break
            if not idFound:
                nameList.append("\~\~MISSING\~\~")
        return nameList

    def toJSON(self):
        return {
            'number': self.number,
            'name': self.name,
            'teamStr': self.teamStr
        }