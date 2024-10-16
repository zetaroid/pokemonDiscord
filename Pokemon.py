import random
import math
import os
import uuid
from PIL import Image


class Pokemon(object):
    natureList = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy", "hasty",
                  "impish",
                  "jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet", "quirky", "rash", "relaxed",
                  "sassy", "serious",
                  "timid"]

    # The class "constructor"
    def __init__(self, data, name, level, exp=None, OT='Mai-san', location='DEBUG', moves=None, pp=None, nature=None,
                 shiny=None, hpEV=None, atkEV=None, defEV=None,
                 spAtkEV=None, spDefEV=None, spdEV=None, hpIV=None, atkIV=None,
                 defIV=None, spAtkIV=None, spDefIV=None,
                 spdIV=None, currentHP=None, nickname=None, gender=None, statusList=None, caughtIn="Pokeball",
                 form=None,
                 happiness=None, distortion=None, identifier=None, shadow=None, invulerable=None, altShiny=None,
                 teraType=None):
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
        self.hpOverride = None
        self.customHP = None
        self.customAtk = None
        self.customDef = None
        self.customSpAtk = None
        self.customSpDef = None
        self.customSpeed = None
        self.setNature(nature)
        self.setShiny(shiny)
        self.setDistortion(distortion)
        self.setAltShiny(altShiny)
        if not shadow:
            self.shadow = False
        else:
            self.shadow = shadow
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
        self.overrideHiddenPowerType = None
        self.teraActive = False
        if teraType:
            self.teraType = teraType
        else:
            typeList = self.getType()
            if len(typeList) > 0:
                self.teraType = typeList[0]
        if not identifier:
            self.identifier = str(uuid.uuid4())
        else:
            self.identifier = identifier
        if not happiness:
            self.happiness = 0
        else:
            self.happiness = happiness
        if not invulerable:
            self.invulnerable = False
        else:
            self.invulnerable = invulerable

    def __copy__(self):
        newPokemon = type(self)(self.data, self.name, self.level, self.exp, self.OT, self.location, self.moves.copy(),
                                self.pp.copy(), self.nature, self.shiny, self.hpEV, self.atkEV, self.defEV,
                                self.spAtkEV, self.spDefEV, self.spdEV, self.hpIV, self.atkIV,
                                self.defIV, self.spAtkIV, self.spDefIV, self.spdIV, self.currentHP,
                                self.nickname, self.gender, self.statusList.copy(), self.caughtIn, self.form,
                                self.happiness, self.distortion, self.identifier, self.shadow, self.invulnerable,
                                self.altShiny, self.teraType)
        newPokemon.overrideHiddenPowerType = self.overrideHiddenPowerType
        newPokemon.hpOverride = self.hpOverride
        newPokemon.customHP = self.customHP
        newPokemon.customAtk = self.customAtk
        newPokemon.customDef = self.customDef
        newPokemon.customSpAtk = self.customSpAtk
        newPokemon.customSpDef = self.customSpDef
        newPokemon.customSpeed = self.customSpeed
        newPokemon.setStats()
        return newPokemon

    def __str__(self):
        prtString = ''
        space_separator = " / "
        line_separator = '\n'
        prtString += self.name + line_separator
        prtString += str(self.level) + line_separator
        prtString += self.nature + line_separator
        prtString += 'Shiny: ' + str(self.shiny) + line_separator
        prtString += 'Distortion ' + str(self.distortion) + line_separator
        prtString += "EV's: " + str(self.hpEV) + space_separator + str(self.atkEV) + space_separator + str(
            self.defEV) + space_separator + str(self.spAtkEV) + space_separator + str(
            self.spDefEV) + space_separator + str(self.spdEV) + line_separator
        prtString += "IV's: " + str(self.hpIV) + space_separator + str(self.atkIV) + space_separator + str(
            self.defIV) + space_separator + str(self.spAtkIV) + space_separator + str(
            self.spDefIV) + space_separator + str(self.spdIV) + line_separator
        prtString += "Stats: " + str(self.hp) + space_separator + str(self.attack) + space_separator + str(
            self.defense) + space_separator + str(self.special_attack) + space_separator + str(
            self.special_defense) + space_separator + str(self.speed) + line_separator
        prtString += 'Tera Type: ' + str(self.teraType) + line_separator
        return prtString

    def updateForFormChange(self):
        self.setStats()
        self.setSpritePath()
        if self.currentHP > self.hp:
            self.currentHP = self.hp

    def getVariations(self):
        if 'variations' in self.fullData:
            return self.fullData['variations']
        else:
            return []

    def getFormName(self):
        if len(self.getVariations()) == 0:
            return ''
        elif len(self.getVariations()) >= self.form:
            if self.form == 0:
                return "Normal"
            else:
                if 'names' in self.getVariations()[self.form - 1]:
                    return self.getVariations()[self.form - 1]['names']['en']
        return ''

    def megaStoneCheck(self, trainer, form, stoneList, findNextForm=True):
        # print('')
        # print('megaStoneCheck, ', form)
        if self.getVariations()[form]['condition'] == 'mega stone':
            stone = self.name + " Stone"
            if 'image_suffix' in self.getVariations()[form]:
                if self.getVariations()[form]['image_suffix'] == 'megay':
                    stone = self.name + " Y Stone"
                elif self.getVariations()[form]['image_suffix'] == 'megax':
                    stone = self.name + " X Stone"
                elif "gmax" in self.getVariations()[form]['image_suffix']:
                    stone = self.name + " GMAX Crystal"
            # print(stone)
            stoneList.append('`' + stone + '`')
            if stone in trainer.itemList and trainer.getItemAmount(stone) > 0:
                # print('setting self.form to ', form+1)
                self.form = (form + 1)
                # print('updating to self.form = ', self.form)
                self.updateForFormChange()
                return True, ''
            else:
                # print(stone + ' not in itemlist')
                if findNextForm:
                    if len(self.getVariations()) > form + 1:
                        # print('recursion time')
                        success, messageStr = self.megaStoneCheck(trainer, form + 1, stoneList)
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
            for variation in self.getVariations():
                if variation['condition'] == 'random_evolution':
                    return False, ''
            if len(self.getVariations()) == 0:
                return False, ''
            elif len(self.getVariations()) > self.form:
                if 'condition' in self.getVariations()[self.form]:
                    if trainer:
                        success, messageStr = self.megaStoneCheck(trainer, self.form, [])
                        if success is not None:
                            return success, messageStr
                self.form += 1
                self.updateForFormChange()
                return True, ''
            elif len(self.getVariations()) == self.form:
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
                if len(self.getVariations()) >= form:
                    if trainer:
                        if 'condition' in self.getVariations()[form - 1]:
                            success, messageStr = self.megaStoneCheck(trainer, form - 1, [], False)
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
            self.hpIV = random.randint(0, 31)
        else:
            self.hpIV = hpIV
        if (atkIV is None):
            self.atkIV = random.randint(0, 31)
        else:
            self.atkIV = atkIV
        if (defIV is None):
            self.defIV = random.randint(0, 31)
        else:
            self.defIV = defIV
        if (spAtkIV is None):
            self.spAtkIV = random.randint(0, 31)
        else:
            self.spAtkIV = spAtkIV
        if (spDefIV is None):
            self.spDefIV = random.randint(0, 31)
        else:
            self.spDefIV = spDefIV
        if (spdIV is None):
            self.spdIV = random.randint(0, 31)
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
            self.evolution_form_check()
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
            self.evolution_form_check()
            self.setStats()
            self.setSpritePath()
            if self.currentHP > self.hp:
                self.currentHP = self.hp
            return True
        return False

    def unevolve(self):
        if self.name == "Dudunsparce" or self.name == "Maushold":
            return False
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

    def evolution_form_check(self):
        if len(self.getVariations()) > self.form:
            if 'condition' in self.getVariations()[self.form]:
                if self.getVariations()[self.form]['condition'] == 'random_evolution':
                    rand_int = random.randint(1, self.getVariations()[self.form]['odds'])
                    if rand_int == 1:
                        self.form = 1
                        self.updateForFormChange()

    def setCaughtIn(self, ball):
        self.caughtIn = ball

    def setCaughtAt(self, location):
        self.location = location

    def gainExp(self, expGained):  # returns true if level up
        if (self.level >= 100):
            return False
        # self.exp = self.exp + expGained
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
                # print(self.name + ' will evolve into ' + self.evolveToAfterBattle + " at level " + str(self.level))
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
            exp = math.floor((4 * level ** 3) / 5)
        elif (leveling_rate == "Medium Fast"):
            exp = math.floor(level ** 3)
        elif (leveling_rate == "Medium Slow"):
            exp = math.floor(((6 / 5) * level ** 3) - (15 * level ** 2) + (100 * level) - 140)
        elif (leveling_rate == "Slow"):
            exp = math.floor((5 * level ** 3) / 4)
        else:
            exp = math.floor(((6 / 5) * level ** 3) - (15 * level ** 2) + (100 * level) - 140)
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
        self.teraActive = False
        self.evolveToAfterBattle = ''
        self.newMovesToLearn.clear()

    def takeDamage(self, damage):
        startingHP = self.currentHP
        damageDealt = damage
        self.currentHP = self.currentHP - damage
        if (self.currentHP <= 0):
            if self.invulnerable:
                damageDealt = startingHP - 1
                self.currentHP = 1
                self.addStatus('invulnerable')
            else:
                damageDealt = startingHP
                self.currentHP = 0
                self.clearStatus()
                self.addStatus('faint')
                self.increaseHappiness(-1)
        return damageDealt

    def resetStatMods(self):
        self.statMods = {
            "atk": 0,
            "def": 0,
            "sp_atk": 0,
            "sp_def": 0,
            "speed": 0,
            "accuracy": 0,
            "evasion": 0,
            "critical": 0
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
                randGenderInt = random.randint(1, 100)
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

    def setShadowMoves(self):
        moves = []
        moves.append(self.data.getMoveData("Shadow Rush"))
        moves.append(self.data.getMoveData("Shadow Blast"))
        moves.append(self.data.getMoveData("Shadow Down"))
        moves.append(self.data.getMoveData("Shadow Panic"))
        self.setMoves(moves)

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
            natureInt = random.randint(0, 24)
            self.nature = self.natureList[natureInt]
        else:
            self.nature = nature

    def setShiny(self, shiny):
        if (shiny is None or shiny == "random"):
            shinyInt = random.randint(0, 199)
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

    def setAltShiny(self, altShiny):
        if (altShiny is None or altShiny == "random"):
            self.altShiny = False
        else:
            self.altShiny = altShiny

    def rollAltShiny(self, extraRolls=0):
        odds = 8192
        if extraRolls == 1:
            odds = 7500
        elif extraRolls == 2:
            odds = 7000
        elif extraRolls == 3:
            odds = 6500
        elif extraRolls == 4:
            odds = 6000
        elif extraRolls == 5:
            odds = 5500
        elif extraRolls == 6:
            odds = 5000
        elif extraRolls == 7:
            odds = 4000
        elif extraRolls == 8:
            odds = 3000
        elif extraRolls == 9:
            odds = 2500
        elif extraRolls >= 10:
            odds = 1000
        altShinyInt = random.randint(1, odds)
        if altShinyInt == 1:
            self.altShiny = True
            self.shiny = True
            self.setSpritePath()

    def setSpritePath(self):
        filename = self.name.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":", "").replace("'",
                                                                                                                   "") + ".png"
        if self.form != 0:
            if 'image_suffix' in self.getVariations()[self.form - 1]:
                filename = self.name.lower().replace(" ", "_").replace("-", "_").replace(".", "").replace(":",
                                                                                                          "").replace(
                    "'", "") + "-" + self.getVariations()[self.form - 1]['image_suffix'] + ".png"
            elif 'sprite' in self.getVariations()[self.form - 1]:
                filename = self.getVariations()[self.form - 1]['sprite']
        path = "data/sprites/"
        alt = "data/sprites/"
        custom = "data/sprites/"
        if self.altShiny:
            path = path + "alt-shiny/"
            alt = alt + "alt-shiny/"
            custom = custom + "alt-shiny/"
        elif self.distortion:
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
        if self.shadow and filename[0:6] != "shadow":
            new_path = self.createShadowPokemonSprite(path, alt, custom, filename)
            path = new_path
            alt = new_path
            custom = new_path
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

    def createShadowPokemonSprite(self, path, alt, custom, filename):
        if os.path.isfile(path):
            base_path = path
        elif os.path.isfile(alt):
            base_path = alt
        elif os.path.isfile(custom):
            base_path = custom
        else:
            return "data/sprites/normal/missingno.png"
        aura_path = 'data/sprites/shadow_aura.png'
        transparency = 80  # percentage

        aura = Image.open(aura_path)
        aura = aura.convert('RGBA')
        pokemon = Image.open(base_path)
        pokemon = pokemon.convert('RGBA')

        if aura.mode != 'RGBA':
            alpha = Image.new('L', aura.size, 255)
            aura.putalpha(alpha)

        paste_mask = aura.split()[3].point(lambda i: i * transparency / 100.)
        pokemon.paste(aura, (0, 0), mask=paste_mask)
        filename = "data/temp/merged_image_" + filename
        pokemon.save(filename, "PNG")
        return filename

    def getEvolution(self, target=None):
        fullData = self.getFullData()
        evolutionName = ''
        levelToEvolveAt = 0
        if ('evolutions' in fullData):
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
                    roll = random.randint(0, len(fullData['evolutions']) - 1)
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
                if "base_stats" in self.getVariations()[self.form - 1]:
                    fullData = self.getVariations()[self.form - 1]
        except:
            self.form = 0
        if self.customHP is not None:
            self.baseHP = self.customHP
        else:
            self.baseHP = fullData["base_stats"]["hp"]
        if self.customAtk is not None:
            self.baseAtk = self.customAtk
        else:
            self.baseAtk = fullData["base_stats"]["atk"]
        if self.customDef is not None:
            self.baseDef = self.customDef
        else:
            self.baseDef = fullData["base_stats"]["def"]
        if self.customSpAtk is not None:
            self.baseSpAtk = self.customSpAtk
        else:
            self.baseSpAtk = fullData["base_stats"]["sp_atk"]
        if self.customSpDef is not None:
            self.baseSpDef = self.customSpDef
        else:
            self.baseSpDef = fullData["base_stats"]["sp_def"]
        if self.customSpeed is not None:
            self.baseSpd = self.customSpeed
        else:
            self.baseSpd = fullData["base_stats"]["speed"]
        if self.hpOverride is not None:
            self.hp = self.hpOverride
        else:
            self.hp = self.hpCalc()
        natureData = self.getNatureData()
        self.attack = self.otherStatCalc("atk", natureData["increased_stat"], natureData["decreased_stat"], self.atkIV,
                                         self.baseAtk, self.atkEV)
        self.defense = self.otherStatCalc("def", natureData["increased_stat"], natureData["decreased_stat"], self.defIV,
                                          self.baseDef, self.defEV)
        self.special_attack = self.otherStatCalc("sp_atk", natureData["increased_stat"], natureData["decreased_stat"],
                                                 self.spAtkIV, self.baseSpAtk, self.spAtkEV)
        self.special_defense = self.otherStatCalc("sp_def", natureData["increased_stat"], natureData["decreased_stat"],
                                                  self.spDefIV, self.baseSpDef, self.spDefEV)
        self.speed = self.otherStatCalc("speed", natureData["increased_stat"], natureData["decreased_stat"], self.spdIV,
                                        self.baseSpd, self.spdEV)

    def hpCalc(self):
        return math.floor(((self.hpIV + (2 * self.baseHP) + (self.hpEV / 4)) * (self.level / 100)) + 10 + self.level)

    def otherStatCalc(self, stat, increased_stat, decreased_stat, iv, base, ev):
        natureMultiplier = 1
        if (stat == increased_stat):
            natureMultiplier = 1.1
        elif (stat == decreased_stat):
            natureMultiplier = 0.9
        else:
            natureMultiplier = 1
        return math.floor((((iv + (2 * base) + (ev / 4)) * (self.level / 100)) + 5) * natureMultiplier)

    def getFullData(self):
        if (self.fullData is None):
            self.fullData = self.data.getPokemonData(self.name.lower())
        return self.fullData

    def refreshFullData(self):
        self.fullData = self.data.getPokemonData(self.name.lower())

    def getType(self):
        if self.teraActive and self.teraType:
            return [self.teraType]
        return self.getTrueType()

    def getTrueType(self):
        typeList = []
        tempFullData = self.fullData
        if self.form != 0:
            if "types" in self.getVariations()[self.form - 1]:
                tempFullData = self.getVariations()[self.form - 1]
        for pokeType in tempFullData["types"]:
            typeList.append(pokeType)
        return typeList

    def doesTeraTypeMatch(self):
        if self.teraType in self.getTrueType():
            return True
        return False

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
        return self.data.getAllLevelUpMoves(self.name.lower(), self.level, self.shadow)

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
        typeList = self.getType()
        if 'Electric' in typeList and status == "paralysis":
            return False
        elif 'Fire' in typeList and status == "burn":
            return False
        elif 'Ice' in typeList and status == 'freeze':
            return False
        elif ('Poison' in typeList or 'Steel' in typeList) and (status == 'poisoned' or status == 'badly_poisoned'):
            return False
        elif 'Grass' in typeList and status == 'seeded':
            return False
        else:
            self.statusList.append(status)
            return True

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
        elif (self.statMods[stat] + modifier < -6):
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
        itemObj = self.data.getItemByName(item)
        success, text, includeHealText = itemObj.perform_effect(self, isCheck)
        if includeHealText:
            battleText += text
        else:
            battleText = text
        return success, battleText

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
            "identifier": self.identifier,
            "shadow": self.shadow,
            "altShiny": self.altShiny,
            "teraType": self.teraType,
            "hiddenPower": self.overrideHiddenPowerType
        }

    def fromJSON(self, json):
        self.name = json['name']
        if self.name == "Quaquavel":
            self.name = "Quaquaval"
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
        if 'shadow' in json:
            self.shadow = json['shadow']
        if 'distortion' in json:
            self.setDistortion(json['distortion'])
        else:
            self.setDistortion(False)
        if 'altShiny' in json:
            self.setAltShiny(json['altShiny'])
        else:
            self.setAltShiny(False)
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
        if 'hiddenPower' in json:
            self.overrideHiddenPowerType = json['hiddenPower']
        if 'teraType' in json:
            self.teraType = json['teraType']
        else:
            typeList = self.getType()
            if len(typeList) > 0:
                self.teraType = typeList[0]
        if 'identifier' in json:
            self.identifier = json['identifier']
        else:
            self.identifier = str(uuid.uuid4())