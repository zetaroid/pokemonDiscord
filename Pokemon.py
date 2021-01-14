import random
import math

class Pokemon(object):
    natureList = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy", "hasty", "impish",
                  "jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet", "quirky", "rash", "relaxed", "sassy", "serious",
                  "timid"]
    
    # The class "constructor"
    def __init__(self, data, name, level, exp=None, OT='Mai-san', location='DEBUG',moves=None, pp=None, nature=None, shiny=None, hpEV=0, atkEV=0, defEV=0,
                 spAtkEV=0, spDefEV=0, spdEV=0, hpIV=random.randint(0,31), atkIV=random.randint(0,31),
                 defIV=random.randint(0,31), spAtkIV=random.randint(0,31), spDefIV=random.randint(0,31),
                 spdIV=random.randint(0,31), currentHP=None, nickname=None, gender=None, statusList=None):
        self.data = data
        self.name = name
        self.location = location
        self.fullData = None
        self.getFullData()
        self.hpEV = hpEV
        self.atkEV = atkEV
        self.defEV = defEV
        self.spAtkEV = spAtkEV
        self.spDefEV = spDefEV
        self.spdEV = spdEV
        self.hpIV = hpIV
        self.atkIV = atkIV
        self.defIV = defIV
        self.spAtkIV = spAtkIV
        self.spDefIV = spDefIV
        self.spdIV = spdIV
        self.setLevel(level, exp)
        self.setStatusList(statusList)
        self.resetStatMods()
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

    def setLevel(self, level, exp):
        self.level = level
        if (exp is None):
            self.exp = self.calculateExpFromLevel(self.level)

    def evolve(self): # moves on evolve?
        if self.evolveToAfterBattle != '':
            self.name = self.evolveToAfterBattle
            self.refreshFullData()
            self.setStats()
            self.setSpritePath()

    def gainExp(self, expGained): # returns true if level up
        if (self.level == 100):
            return False
        self.exp = self.exp + expGained
        expLeftToFactorIntoLevel = expGained
        gainedALevel = False
        while (expLeftToFactorIntoLevel > 0):
            if (expLeftToFactorIntoLevel < self.calculateExpToNextLevel()):
                expLeftToFactorIntoLevel = 0
            else:
                expLeftToFactorIntoLevel = expLeftToFactorIntoLevel - self.calculateExpToNextLevel()
                self.level += 1
                self.setStats()
                self.newMovesToLearn.extend(self.getLevelUpMove())
                if (self.evolveToAfterBattle == ''):
                    self.evolveToAfterBattle = self.getEvolution()
                    print(self.name + ' will evolve into ' + self.evolveToAfterBattle + " at level " + str(self.level))
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
            leveling_rate == "Fast"
            
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

    def resetPP(self, pp):
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
            shinyInt = random.randint(0,1)
            if (shinyInt == 1):
                self.shiny = True
            else:
                self.shiny = False
        else:
            self.shiny = shiny
            
    def setSpritePath(self):
        path = "data/sprites/"
        if self.shiny:
            path = path + "shiny/"
        else:
            path = path + "normal/"
        path = path + self.name.lower() + ".png"
        self.spritePath = path

    def getEvolution(self):
        fullData = self.getFullData()
        evolutionName = ''
        levelToEvolveAt = 0
        if('evolutions' in fullData):
            evolutionsObj = fullData['evolutions'][0]
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
        
    def getLevelUpMove(self):
        return self.data.getLevelUpMove(self.name.lower(), self.level)

    def learnMove(self, move):
        if (len(self.moves) < 4):
            self.moves.append(move)
            return True
        return False
            
    def replaceMove(self, index, move):
        if (len(self.moves) < 4):
            self.learnMove(move)
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
