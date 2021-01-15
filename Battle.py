from Data import pokeData
from Pokemon import Pokemon
import random
import math

class Battle(object):

    def __init__(self, data, trainer1, trainer2=None, entryType="Walking"):
        self.trainer1 = trainer1
        self.trainer2 = trainer2
        self.data = data
        self.entryType = entryType
        self.isWildEncounter = False
        self.activePokemon = []
        self.commands = []
        self.attackCommands = []
        self.commandsPriority1 = []
        self.commandsPriority2 = []
        self.weather = None
        self.pokemon1BadlyPoisonCounter = 0
        self.pokemon2BadlyPoisonCounter = 0
        self.mainStatModifiers = {
            -6: 0.25,
            -5: 0.285,
            -4: 0.33,
            -3: 0.4,
            -2: 0.5,
            -1: 0.66,
            0: 1,
            1: 1.5,
            2: 2,
            3: 2.5,
            4: 3,
            5: 3.5,
            6: 4
        }

        self.accuracyModifiers = {
            -6: 0.33,
            -5: 0.375,
            -4: 0.428,
            -3: 0.5,
            -2: 0.6,
            -1: 0.75,
            0: 1,
            1: 1.33,
            2: 1.66,
            3: 2,
            4: 2.33,
            5: 2.66,
            6: 3
        }

        self.evasionModifiers = {
            -6: 3,
            -5: 2.66,
            -4: 2.33,
            -3: 2,
            -2: 1.66,
            -1: 1.33,
            0: 1,
            1: 0.75,
            2: 0.6,
            3: 0.5,
            4: 0.428,
            5: 0.375,
            6: 0.33
        }

    def startBattle(self):
        self.battleRefresh()
        self.pokemon1 = self.getTrainer1FirstPokemon()
        self.pokemon2 = self.getTrainer2FirstPokemon()

    def endBattle(self):
        pokemonToLearnMovesList = []
        pokemonToEvolveList = []
        for pokemon in self.trainer1.partyPokemon:
            if (pokemon.evolveToAfterBattle != ''):
                pokemonToEvolveList.append(pokemon)
            if (pokemon.newMovesToLearn):
                pokemonToLearnMovesList.append(pokemon)
        return pokemonToEvolveList, pokemonToLearnMovesList

    def battleRefresh(self):
        for pokemon in self.trainer1.partyPokemon:
            pokemon.battleRefresh()
        if (self.trainer2 is not None):
            for pokemon in self.trainer2.partyPokemon:
                pokemon.battleRefresh()
        
    def getTrainer1FirstPokemon(self):
        return self.trainer1.partyPokemon[0]

    def getTrainer2FirstPokemon(self):
        if (self.trainer2 is None):
            self.isWildEncounter = True
            return self.generateWildPokemon()
        else:
            return self.trainer2.partyPokemon[0]

    def startTurn(self):
        self.clearCommands()

    def clearCommands(self):
        self.commands.clear()
        self.commandsPriority1.clear()
        self.commandsPriority2.clear()
        self.attackCommands.clear()

    def createCommandsList(self):
        sortedAttackCommands = []
        for attackTuple in self.attackCommands:
            if not sortedAttackCommands:
                print('slotting ' + str(attackTuple[1].speed) + ' due to empty list')
                sortedAttackCommands.append(attackTuple)
            else:
                index = 0
                slotted = False
                for sortedAttackTuple in sortedAttackCommands:
                    move = sortedAttackTuple[3]
                    if (attackTuple[3]['priority'] > sortedAttackTuple[3]['priority']):
                        print('slotting before ' + str(attackTuple[3]['priority']) + ' due to > ' + str(sortedAttackTuple[3]['priority']))
                        sortedAttackCommands.insert(index, attackTuple)
                        slotted = True
                        break
                    if (attackTuple[1].speed > sortedAttackTuple[1].speed and attackTuple[3]['priority'] == sortedAttackTuple[3]['priority']):
                        print('slotting before ' + str(attackTuple[1].speed) + ' due to > ' + str(sortedAttackTuple[1].speed))
                        sortedAttackCommands.insert(index, attackTuple)
                        slotted = True
                        break
                    index += 1
                if not slotted:
                    print('slotting after ' + str(attackTuple[1].speed) + ' due to < ' + str(sortedAttackTuple[1].speed))
                    sortedAttackCommands.append(attackTuple)
        self.commands = self.commandsPriority1 + sortedAttackCommands + self.commandsPriority2

    def resolveCommand(self, command):
        if (len(command) > 0):
            commandName = command[0]
            if (commandName == "swap"):
                return command[1]
            elif (commandName == "attack"):
                return self.attackCommand(command[1], command[2], command[3])
            elif (commandName == 'status'):
                return self.statusCommand(command[1], command[2])
            else:
                return "INVALID COMMAND"

    def endTurn(self): # returns displayText, shouldBattleEnd (bool), isUserFainted (bool), isOpponentFainted
        shouldBattleEnd = False
        isUserFainted = False
        isOpponentFainted = False
        isWin = False
        displayText = ''
        if ('faint' in self.pokemon1.statusList):
            isUserFainted = True
            displayText = displayText + self.pokemon1.nickname.capitalize() + " fainted!\n"
            trainerStillHasPokemon = False
            for pokemon in self.trainer1.partyPokemon:
                if ('faint' not in pokemon.statusList):
                    trainerStillHasPokemon = True
                    break
            if not trainerStillHasPokemon:
                shouldBattleEnd = True
                isWin = False
                displayText = displayText + self.trainer1.name + ' whited out and scurried back to the nearest Pokemon Center!'
                return displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted
        if('faint' in self.pokemon2.statusList):
            isOpponentFainted = True
            displayText = displayText + self.pokemon2.nickname.capitalize() + " fainted!\n"
            expGained = self.calculateExp(self.pokemon1, self.pokemon2)
            if not isUserFainted and self.pokemon1.level != 100:
                self.gainEffortValues(self.pokemon1, self.pokemon2)
                levelUp = self.pokemon1.gainExp(expGained)
                displayText = displayText + '\n' + self.pokemon1.nickname.capitalize() + ' gained ' + str(expGained) + ' experience points.\n'
                if (levelUp):
                    displayText = displayText + self.pokemon1.nickname.capitalize() + ' grew to level ' + str(self.pokemon1.level) + '!\n\n'
            if (self.trainer2 is not None):
                trainerStillHasPokemon2 = False
                for pokemon in self.trainer2.partyPokemon:
                    if ('faint' not in pokemon.statusList):
                        trainerStillHasPokemon2 = True
                        self.pokemon2 = pokemon
                        break
                if not trainerStillHasPokemon2:
                    shouldBattleEnd = True
                    isWin = True
                    displayText = displayText + '\nTrainer ' + self.trainer2.name + ' defeated!'
            else:
                shouldBattleEnd = True
                isWin = True
        return displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted

    def addEndOfTurnCommands(self):
        moveIndex = random.randint(0,len(self.pokemon2.moves)-1)
        self.sendAttackCommand(self.pokemon2, self.pokemon1, self.pokemon2.moves[moveIndex])
        for status in self.pokemon1.statusList:
            self.sendStatusCommand(self.pokemon1, status)
        for status in self.pokemon2.statusList:
            self.sendStatusCommand(self.pokemon2, status)

    def sendStatusCommand(self, pokemon, status):
        statusTuple = ("status", pokemon, status)
        self.commandsPriority2.append(statusTuple)

    def statusCommand(self, pokemon, status): #TODO implement curse
        text = ''
        if (status == "burn"):
            text = pokemon.nickname + " was hurt by it's burn!"
            damage = math.floor(pokemon.hp / 8)
            pokemon.takeDamage(damage)
        elif (status == "poisoned"):
            text = pokemon.nickname + " was hurt by poison!"
            damage = math.floor(pokemon.hp / 8)
            pokemon.takeDamage(damage)
        elif (status == "badly_poisoned"):
            if (pokemon == self.pokemon1):
                self.pokemon1BadlyPoisonCounter += 1
                if (self.pokemon1BadlyPoisonCounter > 16):
                    self.pokemon1BadlyPoisonCounter = 16
                damage = math.floor(pokemon.hp * (self.pokemon1BadlyPoisonCounter/16))
            elif (pokemon == self.pokemon2):
                self.pokemon2BadlyPoisonCounter += 1
                if (self.pokemon2BadlyPoisonCounter > 16):
                    self.pokemon2BadlyPoisonCounter = 16
                damage = math.floor(pokemon.hp * (self.pokemon2BadlyPoisonCounter/16))
            pokemon.takeDamage(damage)
            text = pokemon.nickname + " was badly hurt by poison!"
        return text

    def swapCommand(self, trainer, pokemonIndex):
        commandText = "Go " + trainer.partyPokemon[pokemonIndex].name + "!"
        if (trainer.author == self.trainer1.author):
            self.pokemon1 = self.trainer1.partyPokemon[pokemonIndex]
            self.pokemon1.resetStatMods()
            self.pokemon1BadlyPoisonCounter = 0
        else:
            if (self.trainer2 is not None):
                self.pokemon2 = self.trainer2.partyPokemon[pokemonIndex]
                self.pokemon2.resetStatMods()
                self.pokemon2BadlyPoisonCounter = 0
        swapTuple = ('swap', commandText)
        self.commandsPriority1.append(swapTuple)

    def sendAttackCommand(self, attackPokemon, defendPokemon, move):
        attackTuple = ("attack", attackPokemon, defendPokemon, move)
        self.attackCommands.append(attackTuple)
        
    def attackCommand(self, attackPokemon, defendPokemon, move):
        print("attempting to use move: " + move['names']['en'])
        moveName = move['names']['en']
        foePrefix = ''
        print('attackPokemon.OT', attackPokemon.OT)
        if (self.trainer2 is not None):
            print('str(self.trainer2.author)', str(self.trainer2.author))
            if (str(self.trainer2.author) == attackPokemon.OT):
                foePrefix = 'Foe '
        if (self.isWildEncounter and attackPokemon.OT == 'Mai-san'):
            print('isWild and Mai-san')
            foePrefix = 'Foe '
        text = ''
        if ('faint' in attackPokemon.statusList or 'faint' in defendPokemon.statusList):
            return text
        for status in attackPokemon.statusList:
            if (status == 'freeze'):
                text = text + foePrefix + attackPokemon.nickname.capitalize() + " is frozen.\n"
                roll = random.randint(1,5)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname.capitalize() + " thawed out!\n"
                    attackPokemon.removeStatus('freeze')
                else:
                    text = text + foePrefix + attackPokemon.nickname.capitalize() + " was frozen solid!\n"
                    return text
            elif (status == 'paralysis'):
                text = text + foePrefix + attackPokemon.nickname.capitalize() + " is paralyzed.\n"
                roll = random.randint(1, 4)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname.capitalize() + " is paralyzed and cannot move!\n"
                    return text
            elif (status == 'sleep'):
                text = text + foePrefix + attackPokemon.nickname.capitalize() + " is fast asleep.\n"
                roll = random.randint(1,3)
                print(roll)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname.capitalize() + " woke up!\n"
                    attackPokemon.removeStatus('sleep')
                else:
                    return text
            elif (status == 'confusion'):
                text = text + foePrefix + attackPokemon.nickname.capitalize() + " is confused.\n"
                roll = random.randint(1, 4)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname.capitalize() + " snapped out of confusion!\n"
                    attackPokemon.removeStatus('confusion')
                else:
                    roll2 = random.randint(1, 2)
                    if (roll2 == 1):
                        text = text + foePrefix + attackPokemon.nickname.capitalize() + " hurt itself in confusion!\n"
                        damage, isCrit, effectivenessModifier = self.calculateDamage(attackPokemon, None, None, True)
                        attackPokemon.takeDamage(damage)
                        return text

        text = text + foePrefix + attackPokemon.nickname + " used " + move['names']['en'] + "!"

        accuracyRoll = random.randint(1,100)
        accuracyRoll = accuracyRoll * self.accuracyModifiers[attackPokemon.statMods['accuracy']] * self.evasionModifiers[defendPokemon.statMods['evasion']]
        moveAccuracy = move['accuracy']
        if (moveAccuracy < accuracyRoll and moveAccuracy != 0):
            return text + '\n' + foePrefix + attackPokemon.nickname + "'s attack missed!"

        if (moveName.lower() == 'rest'):
            attackPokemon.fullHeal()

        if (move['target'] == 'user'):
            target = attackPokemon
        else:
            target = defendPokemon
            
        if (move['category'] == 'physical' or move['category'] == 'special'):
            damage, isCrit, effectivenessModifier = self.calculateDamage(attackPokemon, target, move)
            if (damage < 1):
                if (effectivenessModifier == 0):
                    damage = 0
                else:
                    damage = 1
            target.takeDamage(damage)
            if (isCrit):
                text = text + " It's a critical hit!"
            if (effectivenessModifier < 1 and effectivenessModifier > 0):
                text = text + "\nIt's not very effective..."
            elif (effectivenessModifier > 1):
                text = text + "\nIt's super effective!"
            elif (effectivenessModifier == 0):
                text = text + "\nIt doesn't affect " + target.nickname.capitalize() + "!"
                return text

        if (move['target'] == 'user'):
            target = attackPokemon
        else:
            target = defendPokemon
        if (moveName.lower() == "outrage"):
            target = attackPokemon
        foePrefix = ''
        if (self.trainer2 is not None):
            if (str(self.trainer2.author) == target.OT):
                foePrefix = 'Foe '
        if (self.isWildEncounter and target.OT == 'Mai-san'):
            foePrefix = 'Foe '

        if ('in_battle_properties' in move):
            if ("status_conditions" in move['in_battle_properties']):
                for statusCondition in move['in_battle_properties']['status_conditions']:
                    status = statusCondition['condition']
                    probability = statusCondition['probability']
                    roll = random.randint(1, 100)
                    if (roll <= probability):
                        if (status in target.statusList or 'burn' in target.statusList
                                or 'sleep' in target.statusList or 'paralysis' in target.statusList
                                or 'badly_poisoned' in target.statusList or 'poisoned' in target.statusList
                                or 'freeze' in target.statusList):
                            text = text + '\n' + foePrefix + target.nickname.capitalize() + ' already has a status condition.'
                        else:
                            if (self.weather == 'sun' and status == 'freeze'):
                                pass
                            else:
                                target.addStatus(status)
                                text = text + '\n' + foePrefix + target.nickname.capitalize() + ' was inflicted with ' + status.upper() + '!'

        if (move['target'] == 'user'):
            target = attackPokemon
        else:
            target = defendPokemon
        foePrefix = ''
        if (moveName.lower() == "ancient power"):
            target = attackPokemon
        if (self.trainer2 is not None):
            if (str(self.trainer2.author) == target.OT):
                foePrefix = 'Foe '
        if (self.isWildEncounter and target.OT == 'Mai-san'):
            foePrefix = 'Foe '

        if ('stat_modifiers' in move):
            for statObj in move['stat_modifiers']:
                stat = statObj['stat']
                changeBy = statObj['change_by']
                changeByText = ''
                if (changeBy >= 3):
                    changeByText = 'drastically raised'
                elif (changeBy == 2):
                    changeByText = 'sharply raised'
                elif (changeBy == 1):
                    changeByText = 'raised'
                elif (changeBy == -1):
                    changeByText = 'lowered'
                elif (changeBy == -2):
                    changeByText = 'sharply lowered'
                elif (changeBy <= -3):
                    changeByText = 'drastically lowered'
                else:
                    changeByText = 'ERROR'
                if (move['category'] == 'physical' or move['category'] == 'special'):
                    statRoll = random.randint(0,3)
                    if (statRoll == 0):
                        success = target.modifyStatModifier(stat, changeBy)
                        if success:
                            text = text + "\n" + foePrefix + target.nickname.capitalize() + "'s " + stat.upper() + " was " + changeByText + "!"
                else:
                    success = target.modifyStatModifier(stat, changeBy)
                    if success:
                        text = text + "\n" + foePrefix + target.nickname.capitalize() + "'s " + stat.upper() + " was " + changeByText + "!"
                    else:
                        if (changeBy > 0):
                            changeByText2 = "higher"
                        else:
                            changeByText2 = "lower"
                        text = text + "\n" + foePrefix + target.nickname.capitalize() + "'s " + stat.upper() + " cannot go any " + changeByText2 + "!"
        return text
        
    def calculateDamage(self, attackPokemon, defendPokemon, move, isConfusion=False):
        randomModifier = random.randint(85,100) / 100
        level = attackPokemon.level
        if isConfusion:
            modifier = 1
            isCrit = False
            effectivenessModifier = 1
            basePower = 40
            attack, defense = self.calculatePhysOrSpecStats(attackPokemon, attackPokemon, 'physical')
        else:
            weatherModifier = self.calculateWeather(move)
            critModifier, isCrit = self.calculateCrit(attackPokemon, move)
            stabModifier = self.calculateStab(attackPokemon, move)
            effectivenessModifier = self.calculateEffectiveness(defendPokemon, move)
            burnModifier = self.calculateBurn(attackPokemon, move)
            modifier = randomModifier * critModifier * stabModifier * effectivenessModifier * burnModifier * weatherModifier
            basePower = move['power']
            attack, defense = self.calculatePhysOrSpecStats(attackPokemon, defendPokemon, move['category'])
        damage = math.floor(((((((2*level)/5)+2)* basePower * (attack/defense))/50) + 2) * modifier)
        if (damage < 1):
            damage = 1
        return damage, isCrit, effectivenessModifier
        
    def calculatePhysOrSpecStats(self, attackPokemon, defendPokemon, category):
        if (category == 'physical'):
            return (attackPokemon.attack * self.mainStatModifiers[attackPokemon.statMods['atk']]), (defendPokemon.defense * self.mainStatModifiers[defendPokemon.statMods['def']])
        else:
            return (attackPokemon.special_attack * self.mainStatModifiers[attackPokemon.statMods['sp_atk']]), (defendPokemon.special_defense * self.mainStatModifiers[defendPokemon.statMods['sp_def']])

    def calculateWeather(self, move):
        moveType = move['type'].lower()
        if (self.weather is not None):
            if (self.weather == 'rain'):
                if (moveType == 'water'):
                    return 2
                if (moveType == 'fire'):
                    return 0.5
            if (self.weather == 'sun'):
                if (moveType == 'water'):
                    return 0.5
                if (moveType == 'fire'):
                    return 2
        return 1
        
    def calculateCrit(self, pokemon, move):
        critStage = pokemon.statMods['critical'] + move['critical_hit']
        if (critStage >= 4):
            if(random.randint(0,1) == 0):
                return 2, True
        elif (critStage == 3):
            if(random.randint(0,2) == 0):
                return 2, True
        elif (critStage  == 2):
            if(random.randint(0,3) == 0):
                return 2, True
        elif (critStage  == 1):
            if(random.randint(0,7) == 0):
                return 2, True
        else:
            if(random.randint(0,15) == 0):
                return 2, True
        return 1, False
    
    def calculateStab(self, pokemon, move):
        moveType = move['type'].lower()
        for pokeType in pokemon.getType():
            if (pokeType.lower() == moveType.lower()):
                return 1.5
        return 1

    def calculateEffectiveness(self, pokemon, move):
        moveTypeObj = self.data.getTypeData(move['type'].lower())
        multiplier = 1
        for pokeType in pokemon.getType():
            multiplier = multiplier * moveTypeObj['effectivness'][pokeType.lower().capitalize()]
        return multiplier

    def calculateBurn(self, pokemon, move):
        if (move['category'] == 'physical'):
            if ('burn' in pokemon.statusList):
                return 0.5
        return 1
        
    def generateWildPokemon(self):
        encounterList = self.data.getEncounterTable(self.trainer1.location, self.entryType)
        commonList = []
        uncommonList = []
        rareList = []
        for pokemonLocationObj in encounterList:
            if (pokemonLocationObj["rarity"] == "rare"):
                rareList.append(pokemonLocationObj)
            elif (pokemonLocationObj["rarity"] == "uncommon"):
                uncommonList.append(pokemonLocationObj)
            else:
                commonList.append(pokemonLocationObj)
        roll = random.randint(0,99)
        pokemonObj = None
        if not rareList and not uncommonList and not commonList:
            pokemonObj = None
        elif not rareList and not uncommonList and commonList:
            randInt = random.randint(0,len(commonList)-1)
            pokemonObj = commonList[randInt]
        elif not rareList and uncommonList and not commonList:
            randInt = random.randint(0,len(uncommonList)-1)
            pokemonObj = uncommonList[randInt]
        elif rareList and not uncommonList and not commonList:
            randInt = random.randint(0,len(rareList)-1)
            pokemonObj = rareList[randInt]
        elif not rareList and uncommonList and commonList:
            if (roll >= 60):
                randInt = random.randint(0,len(uncommonList)-1)
                pokemonObj = uncommonList[randInt]
            else:
                randInt = random.randint(0,len(commonList)-1)
                pokemonObj = commonList[randInt]
        elif rareList and not uncommonList and commonList:
            if (roll >= 90):
                randInt = random.randint(0,len(rareList)-1)
                pokemonObj = rareList[randInt]
            else:
                randInt = random.randint(0,len(commonList)-1)
                pokemonObj = commonList[randInt]
        elif rareList and uncommonList and not commonList:
            if (roll >= 90):
                randInt = random.randint(0,len(rareList)-1)
                pokemonObj = rareList[randInt]
            else:
                randInt = random.randint(0,len(uncommonList)-1)
                pokemonObj = uncommonList[randInt]
        else:
            if (roll >= 90):
                randInt = random.randint(0,len(rareList)-1)
                pokemonObj = rareList[randInt]
            elif (roll >= 60):
                randInt = random.randint(0,len(uncommonList)-1)
                pokemonObj = uncommonList[randInt]
            else:
                randInt = random.randint(0,len(commonList)-1)
                pokemonObj = commonList[randInt]
        if (pokemonObj is not None):
            level = random.randint(pokemonObj["min_level"],pokemonObj["max_level"])
            return Pokemon(self.data, pokemonObj["pokemon"], level)
        else:
            return Pokemon(self.data, "Rayquaza", 100, [], "adamant", True)

    def calculateExp(self, attackingPokemon, defeatedPokemon):
        if (self.trainer2 is None):
            a = 1
        else:
            a = 1.5
        b = defeatedPokemon.getFullData()['base_exp_yield']
        L = defeatedPokemon.level
        if (str(self.trainer1.author) == attackingPokemon.OT):
            t = 1
        else:
            t = 1.5
        s = 1 # should be total number of pokemon that participated
        exp = math.floor((a * t * b * L) / (7 * s))
        return exp

    def gainEffortValues(self, pokemonToGain, pokemonGainingFrom):
        if ('ev_yield' in pokemonGainingFrom.getFullData()):
            hpYield = pokemonGainingFrom.getFullData()['ev_yield']['hp']
            atkYield = pokemonGainingFrom.getFullData()['ev_yield']['atk']
            defYield = pokemonGainingFrom.getFullData()['ev_yield']['def']
            sp_atkYield = pokemonGainingFrom.getFullData()['ev_yield']['sp_atk']
            sp_defYield = pokemonGainingFrom.getFullData()['ev_yield']['sp_def']
            speedYield = pokemonGainingFrom.getFullData()['ev_yield']['speed']
            if (hpYield > 0):
                pokemonToGain.gainEV('hp', hpYield)
            if (atkYield > 0):
                pokemonToGain.gainEV('atk', atkYield)
            if (defYield > 0):
                pokemonToGain.gainEV('def', defYield)
            if (sp_atkYield > 0):
                pokemonToGain.gainEV('sp_atk', sp_atkYield)
            if (sp_defYield > 0):
                pokemonToGain.gainEV('sp_def', sp_defYield)
            if (speedYield > 0):
                pokemonToGain.gainEV('speed', speedYield)

    def run(self):
        return self.trainer2 is None

