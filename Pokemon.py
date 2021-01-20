import random
import math
import os

class Pokemon(object):
    natureList = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy", "hasty", "impish",
                  "jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet", "quirky", "rash", "relaxed", "sassy", "serious",
                  "timid"]
    
    # The class "constructor"
    def __init__(self, data, name, level, exp=None, OT='Mai-san', location='DEBUG', moves=None, pp=None, nature=None, shiny=None, hpEV=None, atkEV=None, defEV=None,
                 spAtkEV=None, spDefEV=None, spdEV=None, hpIV=None, atkIV=None,
                 defIV=None, spAtkIV=None, spDefIV=None,
                 spdIV=None, currentHP=None, nickname=None, gender=None, statusList=None, caughtIn="Pokeball"):
        self.data = data
        self.name = name
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
        if (exp is None):
            self.exp = self.calculateExpFromLevel(self.level)

    def evolve(self): # moves on evolve?
        if self.evolveToAfterBattle != '':
            if (self.name == self.nickname):
                self.nickname = self.evolveToAfterBattle
            self.name = self.evolveToAfterBattle
            self.refreshFullData()
            self.setStats()
            self.setSpritePath()

    def setCaughtIn(self, ball):
        self.caughtIn = ball

    def setCaughtAt(self, location):
        self.location = location

    def gainExp(self, expGained): # returns true if level up
        if (self.level == 100):
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
                self.setStats()
                self.newMovesToLearn.extend(self.getLevelUpMove())
                if (self.evolveToAfterBattle == ''):
                    self.evolveToAfterBattle = self.getEvolution()
                    #print(self.name + ' will evolve into ' + self.evolveToAfterBattle + " at level " + str(self.level))
                gainedALevel = True
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
        self.currentHP = self.currentHP - damage
        if (self.currentHP <= 0):
            self.currentHP = 0
            self.clearStatus()
            self.addStatus('faint')
            return True
        return False
        
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

    def setCurrentHP(self, currentHP):
        if (currentHP is None):
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
            
    def setSpritePath(self):
        path = "data/sprites/"
        alt = "data/sprites/"
        if self.shiny:
            path = path + "shiny/"
            alt = alt + "gen5-shiny/"
        else:
            path = path + "normal/"
            alt = alt + "gen5-normal/"
        path = path + self.name.lower() + ".png"
        alt = alt + self.name.lower() + ".png"
        self.spritePath = path
        self.altSpritePath = alt

    def getSpritePath(self):
        if os.path.isfile(self.spritePath):
            return self.spritePath
        elif os.path.isfile(self.altSpritePath):
            return self.altSpritePath

    def getEvolution(self):
        fullData = self.getFullData()
        evolutionName = ''
        levelToEvolveAt = 0
        if('evolutions' in fullData):
            if (len(fullData['evolutions']) > 0):
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
        fullData = self.getFullData()
        self.baseHP = fullData["base_stats"]["hp"]
        self.baseAtk = fullData["base_stats"]["atk"]
        self.baseDef = fullData["base_stats"]["def"]
        self.baseSpAtk = fullData["base_stats"]["sp_atk"]
        self.baseSpDef = fullData["base_stats"]["sp_def"]
        self.baseSpd = fullData["base_stats"]["speed"]
        self.hp = self.hpCalc()
        natureData = self.getNatureData()
        self.attack = self.otherStatCalc("atk", natureData["increased_stat"], natureData["decreased_stat"], self.atkIV, self.baseAtk, self.atkEV) #nature?
        self.defense = self.otherStatCalc("def", natureData["increased_stat"], natureData["decreased_stat"], self.defIV, self.baseDef, self.defEV) #nature?
        self.special_attack = self.otherStatCalc("sp_atk", natureData["increased_stat"], natureData["decreased_stat"], self.spAtkIV, self.baseSpAtk, self.spAtkEV) #nature?
        self.special_defense = self.otherStatCalc("sp_def", natureData["increased_stat"], natureData["decreased_stat"], self.spDefIV, self.baseSpDef, self.spDefEV) #nature?
        self.speed = self.otherStatCalc("speed", natureData["increased_stat"], natureData["decreased_stat"], self.spdIV, self.baseSpd, self.spdEV) #nature?

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
        for pokeType in self.fullData["types"]:
            typeList.append(pokeType)
        return typeList

    def getCatchRate(self):
        return self.fullData["catch_rate"]

    def getNatureData(self):
        return self.data.getNatureData(self.nature)
        
    def setMovesForLevel(self):
        self.moves = self.data.getMovesForLevel(self.name.lower(), self.level)
        self.resetPP()
        
    def getLevelUpMove(self):
        return self.data.getLevelUpMove(self.name.lower(), self.level)

    def learnMove(self, move):
        if (len(self.moves) < 4):
            self.moves.append(move)
            self.resetPP()
            return True
        return False
            
    def replaceMove(self, index, move):
        if (len(self.moves) < 4):
            self.learnMove(move)
            self.resetPP()
        else:
            self.moves[index] = move

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
        if (self.statMods[stat] == 6 or self.statMods[stat] == -6):
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
            'statusList': self.statusList
        }

    def fromJSON(self, json):
        self.name = json['name']
        self.location = json['location']
        self.caughtIn = json['caughtIn']
        self.setLevel(json['level'], json['exp'])
        self.setStatusList(json['statusList'])
        self.resetStatMods()
        self.setEV(json['hpEV'], json['atkEV'], json['defEV'], json['spAtkEV'], json['spDefEV'], json['spdEV'])
        self.setIV(json['hpIV'], json['atkIV'], json['defIV'], json['spAtkIV'], json['spDefIV'], json['spdIV'])
        self.setNature(json['nature'])
        self.setShiny(json['shiny'])
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