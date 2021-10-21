import random
import math
import os
import uuid

class Pokemon(object):
    natureList = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy", "hasty", "impish",
                  "jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet", "quirky", "rash", "relaxed", "sassy", "serious",
                  "timid"]
    
    # The class "constructor"
    def __init__(self, data, name, level, exp=None, OT='Mai-san', location='DEBUG', moves=None, pp=None, nature=None, shiny=None, hpEV=None, atkEV=None, defEV=None,
                 spAtkEV=None, spDefEV=None, spdEV=None, hpIV=None, atkIV=None,
                 defIV=None, spAtkIV=None, spDefIV=None,
                 spdIV=None, currentHP=None, nickname=None, gender=None, statusList=None, caughtIn="Pokeball", form=None, happiness=None, distortion=None, identifier=None):
        self.data = data
        self.name = name
        if ":" in self.name:
            self.name = self.name.replace(":", "")
        self.location = location
        self.caughtIn = caughtIn
        self.fullData = None
        self.getFullData()
        self.setLevel(level, exp)
        self.setStatusList(statusList)
        self.resetStatMods()
        self.setEV(hpEV, atkEV, defEV, spAtkEV, spDefEV, spdEV)
        self.setIV(hpIV, atkIV, defIV, spAtkIV, spDefIV, spdIV)
        self.setNature(nature)
        self.setShiny(shiny)
        self.setDistortion(distortion)
        self.currentHP = 0
        self.form = 0
        self.setForm(form)
        self.setStats()
        self.setSpritePath()
        self.setCurrentHP(currentHP)
        self.setMoves(moves)
        self.resetPP(pp)
        self.setNickname(nickname)
        self.setGender(gender)
        self.evolveToAfterBattle = ''
        self.newMovesToLearn = []
        self.OT = OT
        if not identifier:
            self.identifier = str(uuid.uuid4())
        else:
            self.identifier = identifier
        if not happiness:
            self.happiness = 0
        else:
            self.happiness = happiness

    def __copy__(self):
        return type(self)(self.data, self.name, self.level, self.exp, self.OT, self.location, self.moves, self.pp.copy(), self.nature, self.shiny, self.hpEV, self.atkEV, self.defEV,
                 self.spAtkEV, self.spDefEV, self.spdEV, self.hpIV, self.atkIV,
                 self.defIV, self.spAtkIV, self.spDefIV,
                 self.spdIV, self.currentHP, self.nickname, self.gender, self.statusList.copy(), self.caughtIn, self.form, self.happiness, self.distortion, self.identifier)

    def updateForFormChange(self):
        self.setStats()
        self.setSpritePath()
        if self.currentHP > self.hp:
            self.currentHP = self.hp

    def getFormName(self):
        if len(self.fullData['variations']) == 0:
            return ''
        elif len(self.fullData['variations']) >= self.form:
            if self.form == 0:
                return "Normal"
            else:
                if 'names' in self.fullData['variations'][self.form-1]:
                    return self.fullData['variations'][self.form-1]['names']['en']
        return ''

    def megaStoneCheck(self, trainer, form, stoneList, findNextForm=True):
        # print('')
        # print('megaStoneCheck, ', form)
        if self.fullData['variations'][form]['condition'] == 'mega stone':
            stone = self.name + " Stone"
            if 'image_suffix' in self.fullData['variations'][form]:
                if self.fullData['variations'][form]['image_suffix'] == 'megay':
                    stone = self.name + " Y Stone"
                elif self.fullData['variations'][form]['image_suffix'] == 'megax':
                    stone = self.name + " X Stone"
            # print(stone)
            stoneList.append('`' + stone + '`')
            if stone in trainer.itemList and trainer.itemList[stone] > 0:
                # print('setting self.form to ', form+1)
                self.form = (form + 1)
                # print('updating to self.form = ', self.form)
                self.updateForFormChange()
                return True, ''
            else:
                # print(stone + ' not in itemlist')
                if findNextForm:
                    if len(self.fullData['variations']) > form + 1:
                        # print('recursion time')
                        success, messageStr = self.megaStoneCheck(trainer, form+1, stoneList)
                        if success:
                            return success, messageStr
                    if self.form > 0:
                        self.form = 0
                        self.updateForFormChange()
                        # print('returning true for returning to original form')
                        return True, ''
                stoneStr = ' or '.join(stoneList)
                # print('returning false, dont have stone required')
                return False, 'Needs ' + stoneStr + " to Mega Evolve."
        # print('returning None, None')
        return None, None

    def toggleForm(self, trainer=None):
        if 'variations' in self.fullData:
            if len(self.fullData['variations']) == 0:
                return False, ''
            elif len(self.fullData['variations']) > self.form:
                if trainer:
                    if 'condition' in self.fullData['variations'][self.form]:
                        success, messageStr = self.megaStoneCheck(trainer, self.form, [])
                        if success is not None:
                            return success, messageStr
                self.form += 1
                self.updateForFormChange()
                return True, ''
            elif len(self.fullData['variations']) == self.form:
                self.form = 0
                self.updateForFormChange()
                return True, ''
            else:
                return False, ''

    def increaseHappiness(self, amount=1):
        if self.happiness is None:
            self.happiness = amount
        elif self.happiness >= 255:
            self.happiness = 255
        else:
            self.happiness += amount
        if self.happiness > 255:
            self.happiness = 255
        if self.happiness < 0:
            self.happiness = 0

    def setForm(self, form, trainer=None):
        if form == self.form:
            return False, 'Already target form.'
        if form == 0 or form is None:
            self.form = 0
            self.updateForFormChange()
            return True, ''
        elif form > 0:
            if 'variations' in self.fullData:
                if len(self.fullData['variations']) >= form:
                    if trainer:
                        if 'condition' in self.fullData['variations'][form-1]:
                            success, messageStr = self.megaStoneCheck(trainer, form-1, [], False)
                            if success is not None:
                                return success, messageStr
                    self.form = form
                    self.updateForFormChange()
                    return True, ''
                else:
                    return False, 'Invalid form number.'
        return False, 'Invalid form number.'

    def setIV(self, hpIV, atkIV, defIV, spAtkIV, spDefIV, spdIV):
        if (hpIV is None):
            self.hpIV = random.randint(0,31)
        else:
            self.hpIV = hpIV
        if (atkIV is None):
            self.atkIV = random.randint(0,31)
        else:
            self.atkIV = atkIV
        if (defIV is None):
            self.defIV = random.randint(0,31)
        else:
            self.defIV = defIV
        if (spAtkIV is None):
            self.spAtkIV = random.randint(0,31)
        else:
            self.spAtkIV = spAtkIV
        if (spDefIV is None):
            self.spDefIV = random.randint(0,31)
        else:
            self.spDefIV = spDefIV
        if (spdIV is None):
            self.spdIV = random.randint(0,31)
        else:
            self.spdIV = spdIV

    def setEV(self, hpEV, atkEV, defEV, spAtkEV, spDefEV, spdEV):
        if (hpEV is None):
            self.hpEV = 0
        else:
            self.hpEV = hpEV
        if (atkEV is None):
            self.atkEV = 0
        else:
            self.atkEV = atkEV
        if (defEV is None):
            self.defEV = 0
        else:
            self.defEV = defEV
        if (spAtkEV is None):
            self.spAtkEV = 0
        else:
            self.spAtkEV = spAtkEV
        if (spDefEV is None):
            self.spDefEV = 0
        else:
            self.spDefEV = spDefEV
        if (spdEV is None):
            self.spdEV = 0
        else:
            self.spdEV = spdEV

    def setLevel(self, level, exp):
        self.level = level
        if self.level > 100:
            self.level = 100
        if (exp is None):
            self.exp = self.calculateExpFromLevel(self.level)
        else:
            self.exp = exp

    def evolve(self):
        if self.evolveToAfterBattle != '':
            if (self.name == self.nickname):
                self.nickname = self.evolveToAfterBattle
            self.name = self.evolveToAfterBattle
            self.form = 0
            self.updateForFormChange()
            self.refreshFullData()
            self.setStats()
            self.setSpritePath()
            if self.currentHP > self.hp:
                self.currentHP = self.hp

    def forceEvolve(self, target=None):
        evolutionName = self.getEvolution(target)
        if evolutionName:
            if (self.name == self.nickname):
                self.nickname = evolutionName
            self.name = evolutionName
            self.form = 0
            self.updateForFormChange()
            self.refreshFullData()
            self.setStats()
            self.setSpritePath()
            if self.currentHP > self.hp:
                self.currentHP = self.hp
            return True
        return False

    def unevolve(self):
        newPokemonName = ''
        try:
            newPokemonName = self.getFullData()['evolution_from']
        except:
            pass
        if newPokemonName:
            if (self.name == self.nickname):
                self.nickname = newPokemonName
            self.name = newPokemonName
            self.form = 0
            self.refreshFullData()
            self.setStats()
            self.setSpritePath()
            if self.currentHP > self.hp:
                self.currentHP = self.hp
            return True
        return False

    def setCaughtIn(self, ball):
        self.caughtIn = ball

    def setCaughtAt(self, location):
        self.location = location

    def gainExp(self, expGained): # returns true if level up
        if (self.level >= 100):
            return False
        #self.exp = self.exp + expGained
        expLeftToFactorIntoLevel = expGained
        gainedALevel = False
        while (expLeftToFactorIntoLevel > 0):
            if (expLeftToFactorIntoLevel < self.calculateExpToNextLevel()):
                self.exp += expLeftToFactorIntoLevel
                expLeftToFactorIntoLevel = 0
            else:
                expLeftToFactorIntoLevel = expLeftToFactorIntoLevel - self.calculateExpToNextLevel()
                self.exp += self.calculateExpToNextLevel()
                self.level += 1
                self.increaseHappiness(5)
                self.setStats()
                self.newMovesToLearn.extend(self.getLevelUpMove())
                # if (self.evolveToAfterBattle == ''):
                self.evolveToAfterBattle = self.getEvolution()
                if (self.evolveToAfterBattle):
                    postEvoMovesToLearn = self.getLevelUpMove(self.getEvolution())
                    for move in postEvoMovesToLearn:
                        if move not in self.newMovesToLearn:
                            self.newMovesToLearn.append(move)
                #print(self.name + ' will evolve into ' + self.evolveToAfterBattle + " at level " + str(self.level))
                gainedALevel = True
                if self.level >= 100:
                    return gainedALevel
        return gainedALevel

    def calculateExpToNextLevel(self):
        if (self.level == 100):
            return 0
        return self.calculateExpFromLevel(self.level + 1) - self.exp

    def calculateExpFromLevel(self, level):
        leveling_rate = self.fullData['leveling_rate']
        exp = 0
        if (leveling_rate == "Fluctuating"):
            leveling_rate = "Slow"
        if (leveling_rate == "Erratic"):
            leveling_rate = "Fast"
        if (leveling_rate == "Fast"):
            exp = math.floor((4 * level**3)/5)
        elif (leveling_rate == "Medium Fast"):
            exp = math.floor(level**3)
        elif (leveling_rate == "Medium Slow"):
            exp = math.floor( ((6/5) * level**3) - (15 * level**2) + (100 * level) - 140 )
        elif (leveling_rate == "Slow"):
            exp = exp = math.floor((5 * level**3)/4)
        else:
            exp = math.floor( ((6/5) * level**3) - (15 * level**2) + (100 * level) - 140 )
        return exp

    def battleRefresh(self):
        self.resetStatMods()
        if ('confusion' in self.statusList):
            self.removeStatus('confusion')
        if ('curse' in self.statusList):
            self.removeStatus('curse')
        if ('badly_poisoned' in self.statusList):
            self.removeStatus('badly_poisoned')
            self.addStatus('poisoned')
        self.evolveToAfterBattle = ''
        self.newMovesToLearn.clear()

    def takeDamage(self, damage):
        startingHP = self.currentHP
        damageDealt = damage
        self.currentHP = self.currentHP - damage
        if (self.currentHP <= 0):
            damageDealt = startingHP
            self.currentHP = 0
            self.clearStatus()
            self.addStatus('faint')
            self.increaseHappiness(-1)
        return damageDealt
        
    def resetStatMods(self):
        self.statMods = {
            "atk" : 0,
            "def" : 0,
            "sp_atk" : 0,
            "sp_def" : 0,
            "speed" : 0,
            "accuracy" : 0,
            "evasion" : 0,
            "critical" : 0
        }

    def setStatusList(self, statusList):
        if (statusList is None):
            self.statusList = []
        else:
            self.statusList = statusList

    def setGender(self, gender):
        if (gender is None):
            fullData = self.getFullData()
            try:
                maleRatio = fullData["gender_ratios"]["male"]
            except:
                try:
                    maleRatio = 0
                    femaleRatio = fullData["gender_ratios"]["female"]
                except:
                    self.gender = "no gender"
                    return
            if (maleRatio > 0):
                randGenderInt = random.randint(1,100)
                if (randGenderInt <= maleRatio):
                    self.gender = "male"
                else:
                    self.gender = "female"
            else:
                self.gender = "female"
        else:
            self.gender = gender

    def setNickname(self, nickname):
        if (nickname is None):
            self.nickname = self.name
        else:
            self.nickname = nickname

    def resetPP(self, pp=None):
        if not pp or pp is None:
            self.pp = []
            self.pp.clear()
            for move in self.moves:
                self.pp.append(move['pp'])
        else:
            self.pp = pp

    def usePP(self, index):
        if (index < len(self.pp)):
            self.pp[index] = self.pp[index] - 1

    def setMoves(self, moves):
        if not moves or moves is None:
            self.setMovesForLevel()
            self.resetPP()
        else:
            self.moves = moves
            self.resetPP()

    def setCurrentHP(self, currentHP):
        if (currentHP is None):
            self.currentHP = self.hp
        else:
            if currentHP > self.hp:
                self.currentHP = self.hp
            else:
                self.currentHP = currentHP

    def setNature(self, nature):
        if (nature is None or nature == "random"):
            natureInt = random.randint(0,24)
            self.nature = self.natureList[natureInt]             
        else:
            self.nature = nature
            
    def setShiny(self, shiny):
        if (shiny is None or shiny == "random"):
            shinyInt = random.randint(0,199)
            if (shinyInt == 1):
                self.shiny = True
            else:
                self.shiny = False
        else:
            self.shiny = shiny

    def setDistortion(self, distortion):
        if (distortion is None or distortion == "random"):
            distortionInt = random.randint(0, 9999)
            if (distortionInt == 1):
                self.distortion = True
                self.shiny = True
            else:
                self.distortion = False
        else:
            self.distortion = distortion
            
    def setSpritePath(self):
        filename = self.name.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":", "").replace("'", "") + ".png"
        if self.form != 0:
            if 'image_suffix' in self.fullData['variations'][self.form-1]:
                filename = self.name.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":", "").replace("'", "") + "-" + self.fullData['variations'][self.form-1]['image_suffix'] + ".png"
            elif 'sprite' in self.fullData['variations'][self.form-1]:
                filename = self.fullData['variations'][self.form - 1]['sprite']
        path = "data/sprites/"
        alt = "data/sprites/"
        custom = "data/sprites/"
        if self.distortion:
            path = path + "gen3-invert/"
            alt = alt + "gen5-invert/"
            custom = custom + "custom-pokemon-distortion/"
        elif self.shiny:
            path = path + "shiny/"
            alt = alt + "gen5-shiny/"
            custom = custom + "custom-pokemon-shiny/"
        else:
            path = path + "normal/"
            alt = alt + "gen5-normal/"
            custom = custom + "custom-pokemon/"
        path = path + filename
        alt = alt + filename
        custom = custom + filename
        self.spritePath = path
        self.altSpritePath = alt
        self.customSpritePath = custom

    def getSpritePath(self):
        if os.path.isfile(self.spritePath):
            return self.spritePath
        elif os.path.isfile(self.altSpritePath):
            return self.altSpritePath
        elif os.path.isfile(self.customSpritePath):
            return self.customSpritePath
        else:
            return "data/sprites/normal/missingno.png"

    def getEvolution(self, target=None):
        fullData = self.getFullData()
        evolutionName = ''
        levelToEvolveAt = 0
        if('evolutions' in fullData):
            if (len(fullData['evolutions']) > 0):
                if target:
                    for evolutionsObj in fullData['evolutions']:
                        tempEvolutionName = ''
                        tempLevelToEvolveAt = 0
                        if 'to' in evolutionsObj:
                            tempEvolutionName = evolutionsObj['to']
                        if ('level' in evolutionsObj):
                            tempLevelToEvolveAt = evolutionsObj['level']
                        if tempEvolutionName == target:
                            evolutionName = tempEvolutionName
                            levelToEvolveAt = tempLevelToEvolveAt
                if target is None or evolutionName == '' or levelToEvolveAt == 0:
                    roll = random.randint(0, len(fullData['evolutions'])-1)
                    evolutionsObj = fullData['evolutions'][roll]
                    if ('to' in evolutionsObj):
                        evolutionName = evolutionsObj['to']
                    if ('level' in evolutionsObj):
                        levelToEvolveAt = evolutionsObj['level']
        if (levelToEvolveAt != 0 and self.level >= levelToEvolveAt):
            return evolutionName
        else:
            return ''

    def setStats(self):
        fullData = self.fullData
        try:
            if self.form != 0:
                if "base_stats" in self.fullData['variations'][self.form-1]:
                    fullData = self.fullData['variations'][self.form-1]
        except:
            self.form = 0
        self.baseHP = fullData["base_stats"]["hp"]
        self.baseAtk = fullData["base_stats"]["atk"]
        self.baseDef = fullData["base_stats"]["def"]
        self.baseSpAtk = fullData["base_stats"]["sp_atk"]
        self.baseSpDef = fullData["base_stats"]["sp_def"]
        self.baseSpd = fullData["base_stats"]["speed"]
        self.hp = self.hpCalc()
        natureData = self.getNatureData()
        self.attack = self.otherStatCalc("atk", natureData["increased_stat"], natureData["decreased_stat"], self.atkIV, self.baseAtk, self.atkEV)
        self.defense = self.otherStatCalc("def", natureData["increased_stat"], natureData["decreased_stat"], self.defIV, self.baseDef, self.defEV)
        self.special_attack = self.otherStatCalc("sp_atk", natureData["increased_stat"], natureData["decreased_stat"], self.spAtkIV, self.baseSpAtk, self.spAtkEV)
        self.special_defense = self.otherStatCalc("sp_def", natureData["increased_stat"], natureData["decreased_stat"], self.spDefIV, self.baseSpDef, self.spDefEV)
        self.speed = self.otherStatCalc("speed", natureData["increased_stat"], natureData["decreased_stat"], self.spdIV, self.baseSpd, self.spdEV)

    def hpCalc(self):
        return math.floor(((self.hpIV + (2*self.baseHP) + (self.hpEV / 4)) * (self.level / 100)) + 10 + self.level)

    def otherStatCalc(self, stat, increased_stat, decreased_stat, iv, base, ev):
        natureMultiplier = 1
        if (stat == increased_stat):
            natureMultiplier = 1.1
        elif (stat == decreased_stat):
            natureMultiplier = 0.9
        else:
            natureMultiplier = 1
        return math.floor((((iv + (2*base) + (ev/4)) * (self.level/100)) + 5) * natureMultiplier)

    def getFullData(self):
        if (self.fullData is None):
            self.fullData = self.data.getPokemonData(self.name.lower())
        return self.fullData

    def refreshFullData(self):
        self.fullData = self.data.getPokemonData(self.name.lower())

    def getType(self):
        typeList = []
        tempFullData = self.fullData
        if self.form != 0:
            if "types" in self.fullData['variations'][self.form-1]:
                tempFullData = self.fullData['variations'][self.form-1]
        for pokeType in tempFullData["types"]:
            typeList.append(pokeType)
        return typeList

    def getCatchRate(self):
        return self.fullData["catch_rate"]

    def getNatureData(self):
        return self.data.getNatureData(self.nature)
        
    def setMovesForLevel(self):
        self.moves = self.data.getMovesForLevel(self.name.lower(), self.level)
        self.resetPP()
        
    def getLevelUpMove(self, species=None):
        if species is None:
            return self.data.getLevelUpMove(self.name.lower(), self.level)
        else:
            return self.data.getLevelUpMove(species.lower(), self.level)

    def getAllTmMoves(self):
        return self.data.getAllTmMoves(self.name.lower())

    def getAllEggMoves(self):
        return self.data.getAllEggMoves(self.name.lower())

    def getAllLevelUpMoves(self):
        return self.data.getAllLevelUpMoves(self.name.lower(), self.level)

    def learnMove(self, move):
        if (len(self.moves) < 4):
            self.moves.append(move)
            self.resetPP()
            return True
        return False
            
    def replaceMove(self, index, move):
        if (len(self.moves) < 4):
            self.learnMove(move)
        else:
            self.moves[index] = move
        self.resetPP()

    def addStatus(self, status):
        self.statusList.append(status)

    def removeStatus(self, status):
        try:
            self.statusList.remove(status)
        except:
            return

    def clearStatus(self):
        self.statusList.clear()

    def heal(self, amount):
        self.currentHP += amount
        if (self.currentHP > self.hp):
            self.currentHP = self.hp

    def fullHeal(self):
        self.clearStatus()
        self.currentHP = self.hp

    def pokemonCenterHeal(self):
        self.fullHeal()
        self.resetPP(None)
        self.battleRefresh()

    def modifyStatModifier(self, stat, modifier):
        if 'faint' in self.statusList:
            return False
        if ((self.statMods[stat] == 6 and modifier > 0) or (self.statMods[stat] == -6 and modifier < 0)):
            return False
        elif (self.statMods[stat] + modifier > 6):
            self.statMods[stat] = 6
        elif (self.statMods[stat] +  modifier < -6):
            self.statMods[stat] = -6
        else:
            self.statMods[stat] = self.statMods[stat] + modifier
        return True

    def gainEV(self, stat, amount):
        totalEVs = self.hpEV + self.atkEV + self.defEV + self.spAtkEV + self.spDefEV + self.spdEV
        if (totalEVs >= 510):
            return
        if (totalEVs + amount >= 510):
            amount = 510 - totalEVs
        if (stat == 'hp'):
            self.hpEV += amount
        elif (stat == 'atk'):
            self.atkEV += amount
        elif (stat == 'def'):
            self.defEV += amount
        elif (stat == 'sp_atk'):
            self.spAtkEV += amount
        elif (stat == 'sp_def'):
            self.spDefEV += amount
        elif (stat == 'speed'):
            self.spdEV += amount
        self.setStats()

    def useItemOnPokemon(self, item, isCheck=False):
        battleText = self.nickname + " was healed by " + item + "."
        #print(isCheck)
        #print(item)
        if (item == "Potion"):
            if (self.currentHP < self.hp and 'faint' not in self.statusList):
                if not isCheck:
                    self.heal(20)
                return True, battleText + "\n20 HP was restored."
        elif (item == "Super Potion"):
            if (self.currentHP < self.hp and 'faint' not in self.statusList):
                if not isCheck:
                    self.heal(50)
                return True, battleText + "\n50 HP was restored."
        elif (item == "Hyper Potion"):
            if (self.currentHP < self.hp and 'faint' not in self.statusList):
                if not isCheck:
                    self.heal(200)
                return True, battleText + "\n200 HP was restored."
        elif (item == "Max Potion"):
            if (self.currentHP < self.hp and 'faint' not in self.statusList):
                if not isCheck:
                    self.heal(self.hp)
                return True, battleText + "\nHP was fully restored."
        elif (item == "Full Restore"):
            #print('is FR')
            if ((self.currentHP < self.hp or len(self.statusList) > 0) and 'faint' not in self.statusList):
                #print('passed check')
                if not isCheck:
                    self.fullHeal()
                return True, battleText + "\nHP was fully restored and status conditions removed."
        elif (item == "Full Heal"):
            if (self.statusList and 'faint' not in self.statusList):
                if not isCheck:
                    self.clearStatus()
                return True, battleText + "\nStatus conditions removed."
        elif (item == "Revive"):
            if ('faint' in self.statusList):
                if not isCheck:
                    self.clearStatus()
                    self.heal(round(self.hp/2))
                return True, battleText + "\nThe pokemon was revived to half health."
        elif (item == "Max Revive"):
            if ('faint' in self.statusList):
                if not isCheck:
                    self.clearStatus()
                    self.heal(self.hp)
                return True, battleText + "\nThe pokemon was revived to full health."
        return False, "ERROR THIS SHOULDN'T BE SEEN"

    def toJSON(self):
        moveList = []
        for move in self.moves:
            moveList.append(move['names']['en'])
        return {
            'name': self.name,
            'location': self.location,
            'caughtIn': self.caughtIn,
            'level': self.level,
            'exp': self.exp,
            'OT': self.OT,
            'moves': moveList,
            'pp': self.pp,
            'nature': self.nature,
            'shiny': self.shiny,
            'hpEV': self.hpEV,
            'atkEV': self.atkEV,
            'defEV': self.defEV,
            'spAtkEV': self.spAtkEV,
            'spDefEV': self.spDefEV,
            'spdEV': self.spdEV,
            'hpIV': self.hpIV,
            'atkIV': self.atkIV,
            'defIV': self.defIV,
            'spAtkIV': self.spAtkIV,
            'spDefIV': self.spDefIV,
            'spdIV': self.spdIV,
            'currentHP': self.currentHP,
            'nickname': self.nickname,
            'gender': self.gender,
            'statusList': self.statusList,
            'form': self.form,
            'happiness': self.happiness,
            "distortion": self.distortion,
            "identifier": self.identifier
        }

    def fromJSON(self, json):
        self.name = json['name']
        if ":" in self.name:
            self.name = self.name.replace(":", "")
        self.location = json['location']
        self.caughtIn = json['caughtIn']
        self.setLevel(json['level'], json['exp'])
        self.setStatusList(json['statusList'])
        self.resetStatMods()
        self.setEV(json['hpEV'], json['atkEV'], json['defEV'], json['spAtkEV'], json['spDefEV'], json['spdEV'])
        self.setIV(json['hpIV'], json['atkIV'], json['defIV'], json['spAtkIV'], json['spDefIV'], json['spdIV'])
        self.setNature(json['nature'])
        self.setShiny(json['shiny'])
        if 'distortion' in json:
            self.setDistortion(json['distortion'])
        else:
            self.setDistortion(False)
        if 'form' in json:
            self.form = json['form']
        if 'happiness' in json:
            self.happiness = json['happiness']
        self.setStats()
        self.setSpritePath()
        self.setCurrentHP(json['currentHP'])
        moves = []
        for moveName in json['moves']:
            moves.append(self.data.getMoveData(moveName))
        self.setMoves(moves)
        self.resetPP(json['pp'])
        self.setNickname(json['nickname'])
        self.setGender(json['gender'])
        self.evolveToAfterBattle = ''
        self.newMovesToLearn = []
        self.OT = json['OT']
        if 'identifier' in json:
            self.identifier = json['identifier']
        else:
            self.identifier = str(uuid.uuid4())