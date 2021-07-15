from Data import pokeData
from Pokemon import Pokemon
import random
import math
import traceback
from copy import copy
from asyncio import sleep
from asyncio import gather
import logging

class Battle(object):

    def __init__(self, data, trainer1, trainer2=None, entryType="Walking", fixedEncounter=None):
        self.trainer1 = trainer1
        self.trainer2 = trainer2
        if self.trainer2:
            trainerCopy = copy(self.trainer2)
            self.trainer2 = trainerCopy
            if trainer2.shouldScale:
                trainerCopy.scaleTeam(self.trainer1)
        self.data = data
        self.entryType = entryType
        self.fixedEncounter = fixedEncounter
        self.isWildEncounter = False
        self.activePokemon = []
        self.commands = []
        self.attackCommands = []
        self.commandsPriority1 = []
        self.commandsPriority2 = []
        self.weather = None
        self.gainExp = True
        self.pokemon1BadlyPoisonCounter = 0
        self.pokemon2BadlyPoisonCounter = 0
        self.pokemon1Protected = False
        self.pokemon2Protected = False
        self.aiUsedBoostMove = False
        self.isPVP = False
        self.isRaid = False
        self.raidDamage = 0
        self.uiListeners = []
        self.trainer1InputReceived = False
        self.trainer2InputReceived = False
        self.trainer2ShouldWait = True
        self.endTurnTuple = None
        self.locationToProgress = None
        self.protectDict = {}
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

    def addUiListener(self, uiListener):
        self.uiListeners.append(uiListener)

    def disableExp(self):
        self.gainExp = False

    def startBattle(self, locationToProgress=None):
        self.battleRefresh()
        self.pokemon1 = self.getTrainer1FirstPokemon()
        self.pokemon2 = self.getTrainer2FirstPokemon()
        if self.isRaid:
            self.pokemon2.addStatus("raid")
        self.locationToProgress = locationToProgress

    def endBattle(self):
        pokemonToLearnMovesList = []
        pokemonToEvolveList = []
        for pokemon in self.trainer1.partyPokemon:
            if (pokemon.evolveToAfterBattle != ''):
                pokemonToEvolveList.append(pokemon)
            if (pokemon.newMovesToLearn):
                pokemonToLearnMovesList.append(pokemon)
        if self.locationToProgress:
            self.trainer1.progress(self.locationToProgress)
        return pokemonToEvolveList, pokemonToLearnMovesList

    def battleRefresh(self):
        for pokemon in self.trainer1.partyPokemon:
            pokemon.battleRefresh()
        if (self.trainer2 is not None):
            for pokemon in self.trainer2.partyPokemon:
                pokemon.battleRefresh()
        
    def getTrainer1FirstPokemon(self):
        for pokemon in self.trainer1.partyPokemon:
            if 'faint' not in pokemon.statusList:
                return pokemon
        errorPokemon = Pokemon(self.data, "Arceus", 100)
        errorPokemon.nickname = "Missingno"
        return errorPokemon

    def getTrainer2FirstPokemon(self):
        if (self.trainer2 is None):
            self.isWildEncounter = True
            if (self.fixedEncounter is None):
                return self.generateWildPokemon()
            else:
                return self.fixedEncounter
        else:
            if not self.isRaid:
                self.trainer2.pokemonCenterHeal()
            return self.trainer2.partyPokemon[0]

    def startTurn(self):
        self.clearCommands()
        self.uiListeners.clear()

    def clearCommands(self):
        self.commands.clear()
        self.commandsPriority1.clear()
        self.commandsPriority2.clear()
        self.attackCommands.clear()

    def createCommandsList(self):
        sortedAttackCommands = []
        for attackTuple in self.attackCommands:
            if not sortedAttackCommands:
                #print('slotting ' + str(attackTuple[1].speed) + ' due to empty list')
                sortedAttackCommands.append(attackTuple)
            else:
                index = 0
                slotted = False
                for sortedAttackTuple in sortedAttackCommands:
                    move = sortedAttackTuple[3]
                    if (attackTuple[3]['priority'] > sortedAttackTuple[3]['priority']):
                        #print('slotting priority before ' + str(attackTuple[3]['priority']) + ' due to > ' + str(sortedAttackTuple[3]['priority']))
                        sortedAttackCommands.insert(index, attackTuple)
                        slotted = True
                        break
                    speed1Modified = attackTuple[1].speed * self.mainStatModifiers[attackTuple[1].statMods['speed']] * \
                                     (0.5 * ('paralysis' in attackTuple[1].statusList) + 1 * ('paralysis' not in attackTuple[1].statusList))
                    speed2Modified = sortedAttackTuple[1].speed * self.mainStatModifiers[sortedAttackTuple[1].statMods['speed']] * \
                                     (0.5 * ('paralysis' in sortedAttackTuple[1].statusList) + 1 * ('paralysis' not in sortedAttackTuple[1].statusList))
                    #print('speed1Modified: ' + str(speed1Modified) + ', speed2Modified: ' + str(speed2Modified))
                    #if (attackTuple[1].speed > sortedAttackTuple[1].speed and attackTuple[3]['priority'] == sortedAttackTuple[3]['priority']):
                    if (speed1Modified > speed2Modified and attackTuple[3]['priority'] == sortedAttackTuple[3]['priority']):
                        #print('slotting before ' + str(speed1Modified) + ' due to > ' + str(speed2Modified))
                        sortedAttackCommands.insert(index, attackTuple)
                        slotted = True
                        break
                    index += 1
                if not slotted:
                    #print('slotting after ' + str(speed1Modified) + ' due to < ' + str(speed2Modified))
                    sortedAttackCommands.append(attackTuple)
        self.commands = self.commandsPriority1 + sortedAttackCommands + self.commandsPriority2

    def resolveCommand(self, command):
        if (len(command) > 0):
            commandName = command[0]
            if (commandName == "swap"):
                return command[1]
            elif commandName == "swapPvp":
                self.swapCommand(command[2], command[3], True)
                return command[1]
            elif (commandName == "attack"):
                if self.isPVP:
                    if command[1] == self.pokemon1:
                        return self.attackCommand(command[1], self.pokemon2, command[3])
                    else:
                        return self.attackCommand(command[1], self.pokemon1, command[3])
                else:
                    return self.attackCommand(command[1], command[2], command[3])
            elif (commandName == 'status'):
                return self.statusCommand(command[1], command[2])
            elif (commandName == "useItem"):
                return self.useItemCommand(command[1], command[2])
            else:
                return "INVALID COMMAND"

    async def endTurn(self, timeout=60): # returns displayText, shouldBattleEnd (bool), isUserFainted (bool), isOpponentFainted
        count = 0
        if self.isPVP:
            while len(self.uiListeners) < 2 or not self.trainer1InputReceived or not self.trainer2InputReceived:
                # print('waiting in endTurn = ', count)
                count += 1
                if count >= timeout:
                    return None, None, None, None, None, True
                await sleep(1)
        self.trainer1InputReceived = False
        self.trainer2InputReceived = False
        self.addEndOfTurnCommands()
        self.createCommandsList()
        for command in self.commands:
            battleText = self.resolveCommand(command)
            # ("battleText: ", battleText)
            if (battleText != ''):
                if self.isPVP:
                    battleText = battleText.replace('Foe ', '')
                    battleText = battleText.replace('Foe', '')
                    commandName = command[0]
                    if commandName == 'swap' or commandName == "swapPvp":
                        # print('doing the swap thang')
                        trainer = command[2]
                        await self.uiListeners[0].updateBattleUI(trainer)
                        await self.uiListeners[1].updateBattleUI(trainer)
                    listener1 = self.uiListeners[0].resolveTurn(self.pokemon1, self.pokemon2, battleText)
                    listener2 = self.uiListeners[1].resolveTurn(self.pokemon1, self.pokemon2, battleText)
                    await gather(listener1, listener2)
                else:
                    for listener in self.uiListeners:
                        await listener.resolveTurn(self.pokemon1, self.pokemon2, battleText)
        self.clearCommands()
        self.uiListeners.clear()
        # New/old separator
        shouldBattleEnd = False
        isUserFainted = False
        isOpponentFainted = False
        isWin = False
        if self.pokemon1Protected:
            self.pokemon1Protected = False
        else:
            if self.pokemon1 in self.protectDict.keys():
                del self.protectDict[self.pokemon1]
        if self.pokemon2Protected:
            self.pokemon2Protected = False
        else:
            if self.pokemon2 in self.protectDict.keys():
                del self.protectDict[self.pokemon2]
        displayText = ''
        if ('faint' in self.pokemon1.statusList):
            isUserFainted = True
            self.pokemon1BadlyPoisonCounter = 0
            displayText = displayText + self.pokemon1.nickname + " fainted!\n"
            trainerStillHasPokemon = False
            for pokemon in self.trainer1.partyPokemon:
                if ('faint' not in pokemon.statusList):
                    trainerStillHasPokemon = True
                    break
            if not trainerStillHasPokemon:
                shouldBattleEnd = True
                isWin = False
                if not self.isPVP:
                    if self.isRaid:
                        displayText = displayText + self.trainer1.name + ' was defeated.'
                    else:
                        displayText = displayText + self.trainer1.name + ' whited out and scurried back to the nearest Pokemon Center!'
                self.endTurnTuple = (displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted)
                self.trainer2ShouldWait = False
                return displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted, False
        if ('faint' in self.pokemon2.statusList and self.isPVP):
            isOpponentFainted = True
            displayText = displayText + self.pokemon2.nickname + " fainted!\n"
            trainerStillHasPokemon2 = False
            self.pokemon2BadlyPoisonCounter = 0
            for pokemon in self.trainer2.partyPokemon:
                if ('faint' not in pokemon.statusList):
                    trainerStillHasPokemon2 = True
                    break
            if not trainerStillHasPokemon2:
                shouldBattleEnd = True
                isWin = True
        if('faint' in self.pokemon2.statusList and not self.isPVP):
            isOpponentFainted = True
            self.pokemon2BadlyPoisonCounter = 0
            self.aiUsedBoostMove = False
            displayText = displayText + "Foe " + self.pokemon2.nickname + " fainted!\n"
            expGained = self.calculateExp(self.pokemon1, self.pokemon2)
            if not isUserFainted and self.gainExp:
                if self.pokemon1.level != 100:
                    self.gainEffortValues(self.pokemon1, self.pokemon2)
                    levelUp = self.pokemon1.gainExp(expGained)
                    displayText = displayText + '\n' + self.pokemon1.nickname + ' gained ' + str(expGained) + ' experience points.\n'
                    if (levelUp):
                        displayText = displayText + self.pokemon1.nickname + ' grew to level ' + str(self.pokemon1.level) + '!\n\n'
                if (len(self.trainer1.partyPokemon) > 1):
                    displayText = displayText + '\n' + "The rest of the party " + ' gained ' + str(round(expGained/2)) + ' experience points.\n'
                for pokemon in self.trainer1.partyPokemon:
                    if (pokemon == self.pokemon1):
                        continue
                    otherLevelUp = pokemon.gainExp(round(expGained/2))
                    if (otherLevelUp):
                        displayText = displayText + pokemon.nickname + ' grew to level ' + str(pokemon.level) + '!\n'
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
                    if self.isRaid:
                        displayText = displayText + '\n' + 'Raid boss defeated!'
                        if self.data.raid:
                            self.data.raid.raidBoss.currentHP = 0
                    else:
                        self.trainer1.increasePartyHappiness()
                        displayText = displayText + '\nTrainer ' + self.trainer2.name + ' defeated!'
            else:
                shouldBattleEnd = True
                isWin = True
                self.trainer1.increasePartyHappiness()
        self.endTurnTuple = (displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted)
        self.trainer2ShouldWait = False
        return displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted, False

    def addEndOfTurnCommands(self):
        if self.isWildEncounter:
            moveIndex = random.randint(0,len(self.pokemon2.moves)-1)
            self.sendAttackCommand(self.pokemon2, self.pokemon1, self.pokemon2.moves[moveIndex])
        elif self.trainer2.identifier == 0:
            self.sendAttackCommand(self.pokemon2, self.pokemon1, self.moveAI(self.pokemon2, self.pokemon1))
        for status in self.pokemon1.statusList:
            self.sendStatusCommand(self.pokemon1, status)
        for status in self.pokemon2.statusList:
            self.sendStatusCommand(self.pokemon2, status)

    def moveAI(self, attackPokemon, defendPokemon):
        chosenMove = None
        try:
            boostMoves = []
            statusMoves = []
            confusionMoves = []
            healMoves = []
            attackMoves = []
            leechSeedMoves = []
            for move in attackPokemon.moves:
                if move['category'] == "status":
                    if move['target'] == 'user':
                        if 'stat_modifiers' in move:
                            boostMoves.append(move)
                            continue
                        if 'in_battle_properties' in move:
                            if "affect" in move['in_battle_properties']:
                                if len(move['in_battle_properties']['affect']) > 0:
                                    if move['in_battle_properties']['affect'][0]['condition'] == 'heal' and move['in_battle_properties']['affect'][0]['scale'] == 'hp':
                                        healMoves.append(move)
                                        continue
                    else:
                        if 'in_battle_properties' in move:
                            if "status_conditions" in move['in_battle_properties']:
                                if len(move['in_battle_properties']['status_conditions']) > 0:
                                    if move['in_battle_properties']['status_conditions'][0]['condition'] == 'confusion':
                                        confusionMoves.append(move)
                                        continue
                                    elif move['in_battle_properties']['status_conditions'][0]['condition'] == 'seeded':
                                        leechSeedMoves.append(move)
                                        continue
                                    else:
                                        statusMoves.append(move)
                                        continue
                attackMoves.append(move)
            willUseNonAttackMove = False
            roll = random.randint(1, 100)
            if roll <= 80:
                willUseNonAttackMove = True
            # print('willUseNonAttackMove: ', willUseNonAttackMove)
            bestMove, maxDamage = self.chooseBestMove(attackPokemon, defendPokemon, attackMoves)
            attackSpeedModified = attackPokemon.speed * self.mainStatModifiers[attackPokemon.statMods['speed']] * \
                             (0.5 * ('paralysis' in attackPokemon.statusList) + 1 * (
                                         'paralysis' not in attackPokemon.statusList))
            defendSpeedModified = defendPokemon.speed * self.mainStatModifiers[defendPokemon.statMods['speed']] * \
                             (0.5 * ('paralysis' in defendPokemon.statusList) + 1 * (
                                         'paralysis' not in defendPokemon.statusList))
            if (maxDamage > defendPokemon.hp/2) or (maxDamage > defendPokemon.hp/2.5 and attackSpeedModified > defendSpeedModified):
                # print("choosing best move due to damage output/speed combo ", maxDamage, attackSpeedModified, defendSpeedModified)
                return bestMove
            if willUseNonAttackMove:
                if healMoves and attackPokemon.currentHP/attackPokemon.hp < 0.34 and not self.isRaid:
                    # print('heal move')
                    moveIndex = random.randint(0, len(healMoves) - 1)
                    chosenMove = healMoves[moveIndex]
                elif "burn" not in defendPokemon.statusList and 'sleep' not in defendPokemon.statusList \
                    and 'freeze' not in defendPokemon.statusList and 'poisoned' not in defendPokemon.statusList \
                    and 'badly_poisoned' not in defendPokemon.statusList and 'paralysis' not in defendPokemon.statusList \
                    and statusMoves:
                    #print('status move')
                    moveIndex = random.randint(0, len(statusMoves) - 1)
                    chosenMove = statusMoves[moveIndex]
                elif "confusion" not in defendPokemon.statusList and confusionMoves:
                    # print('confusion move')
                    moveIndex = random.randint(0, len(confusionMoves) - 1)
                    chosenMove = confusionMoves[moveIndex]
                elif "seeded" not in defendPokemon.statusList and leechSeedMoves:
                    # print('seeded move')
                    moveIndex = random.randint(0, len(leechSeedMoves) - 1)
                    chosenMove = leechSeedMoves[moveIndex]
                elif not self.aiUsedBoostMove and boostMoves:
                    # print('boost move')
                    willUseBoost = False
                    roll = random.randint(1, 100)
                    if roll <= 90:
                        willUseBoost = True
                    self.aiUsedBoostMove = True
                    if willUseBoost:
                        moveIndex = random.randint(0, len(boostMoves) - 1)
                        chosenMove = boostMoves[moveIndex]
                    else:
                        # print("RNG decided not to use boost move")
                        chosenMove = self.selectRandomMove(attackPokemon)
                elif len(attackMoves) > 0:
                    # print('attack move1')
                    chosenMove = bestMove
                else:
                    # print('else: random move')
                    chosenMove = self.selectRandomMove(attackPokemon)
            elif len(attackMoves) > 0:
                # print('attack move2')
                chosenMove = bestMove
            else:
                # print('else: random move')
                chosenMove = self.selectRandomMove(attackPokemon)
        except:
            #traceback.print_exc()
            chosenMove = self.selectRandomMove(attackPokemon)
        return chosenMove

    def chooseBestMove(self, attackPokemon, defendPokemon, moveList):
        maxDamage = 0
        chosenMove = None
        for move in moveList:
            damage, isCrit, effectivenessModifier = self.calculateDamage(attackPokemon, defendPokemon, move, False)
            if damage > maxDamage:
                maxDamage = damage
                chosenMove = move
        if chosenMove is None:
            # print("picking random from attackMoveList")
            if moveList is not None and len(moveList) > 0:
                moveIndex = random.randint(0, len(moveList) - 1)
                chosenMove = moveList[moveIndex]
            else:
                chosenMove = self.selectRandomMove(attackPokemon)
        return chosenMove, maxDamage

    def selectRandomMove(self, pokemon):
        moveIndex = random.randint(0, len(pokemon.moves) - 1)
        chosenMove = pokemon.moves[moveIndex]
        return chosenMove

    def sendStatusCommand(self, pokemon, status):
        statusTuple = ("status", pokemon, status)
        self.commandsPriority2.append(statusTuple)

    def statusCommand(self, pokemon, status): # TODO implement curse, etc
        text = ''
        if 'faint' in pokemon.statusList:
            return text
        elif (status == "burn" and 'burn' in pokemon.statusList):
            text = pokemon.nickname + " was hurt by its burn!"
            damage = math.floor(pokemon.hp / 8)
            if damage < 1:
                damage = 1
            pokemon.takeDamage(damage)
        elif (status == "poisoned" and 'poisoned' in pokemon.statusList):
            text = pokemon.nickname + " was hurt by poison!"
            damage = math.floor(pokemon.hp / 8)
            if damage < 1:
                damage = 1
            pokemon.takeDamage(damage)
        elif (status == "badly_poisoned" and 'badly_poisoned' in pokemon.statusList):
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
            if damage < 1:
                damage = 1
            pokemon.takeDamage(damage)
            text = pokemon.nickname + " was badly hurt by poison!"
        elif (status == "seeded" and 'seeded' in pokemon.statusList):
            if (pokemon == self.pokemon1 and 'faint' in self.pokemon2.statusList) or (pokemon == self.pokemon2 and 'faint' in self.pokemon1.statusList):
                return text
            text = "Leech Seed sapped " + pokemon.nickname + "'s health!"
            damage = math.floor(pokemon.hp / 8)
            if damage < 1:
                damage = 1
            pokemon.takeDamage(damage)
            if pokemon == self.pokemon1:
                self.pokemon2.heal(round(damage/2))
            elif pokemon == self.pokemon2:
                self.pokemon1.heal(round(damage/2))
        elif (status == "raid" and 'raid' in pokemon.statusList):
            if self.data.raid:
                self.data.raid.raidBoss.currentHP -= self.raidDamage
                if self.data.raid.raidBoss.currentHP < 0:
                    self.data.raid.raidBoss.currentHP = 0
                self.raidDamage = 0
                deltaHP = self.pokemon2.currentHP - self.data.raid.raidBoss.currentHP
                if deltaHP > 0:
                    text = "The raid boss took " + str(deltaHP) + " damage from your comrades!"
                    self.pokemon2.currentHP = self.data.raid.raidBoss.currentHP
            else:
                text = "The raid boss has been defeated by your comrades!"
                self.pokemon2.currentHP = 0
            if self.pokemon2.currentHP <= 0:
                self.pokemon2.currentHP = 0
                self.pokemon2.addStatus('faint')
        return text

    async def updateBattleUIOnReturnFromParty(self, trainer):
        for listener in self.uiListeners:
            await listener.updateBattleUI(trainer, True)

    def sendSwapCommandforPvp(self, trainer, pokemonIndex, commandText, fromUserFaint):
        swapTuple = ('swapPvp', commandText, trainer, pokemonIndex)
        if not fromUserFaint:
            self.commandsPriority1.append(swapTuple)
        return fromUserFaint

    def swapCommand(self, trainer, pokemonIndex, bypassCheck=False):
        if not bypassCheck:
            if trainer == self.trainer1:
                self.trainer1InputReceived = True
            elif trainer == self.trainer2:
                self.trainer2InputReceived = True
        commandText = "Go " + trainer.partyPokemon[pokemonIndex].nickname + "!"
        fromUserFaint = False
        if (trainer.identifier == self.trainer1.identifier):
            if ('faint' in self.pokemon1.statusList):
                fromUserFaint = True
            if self.isPVP and not bypassCheck and not fromUserFaint:
                return self.sendSwapCommandforPvp(trainer, pokemonIndex, commandText, fromUserFaint)
            else:
                self.pokemon1 = self.trainer1.partyPokemon[pokemonIndex]
                self.pokemon1.resetStatMods()
                if "confusion" in self.pokemon1.statusList:
                    self.pokemon1.removeStatus('confusion')
                if "seeded" in self.pokemon1.statusList:
                    self.pokemon1.removeStatus('seeded')
                self.pokemon1BadlyPoisonCounter = 0
        elif (trainer.identifier == self.trainer2.identifier):
            if ('faint' in self.pokemon2.statusList):
                fromUserFaint = True
            if self.isPVP and not bypassCheck and not fromUserFaint:
                return self.sendSwapCommandforPvp(trainer, pokemonIndex, commandText, fromUserFaint)
            else:
                self.pokemon2 = self.trainer2.partyPokemon[pokemonIndex]
                self.pokemon2.resetStatMods()
                if "confusion" in self.pokemon2.statusList:
                    self.pokemon2.removeStatus('confusion')
                if "seeded" in self.pokemon2.statusList:
                    self.pokemon2.removeStatus('seeded')
                self.pokemon2BadlyPoisonCounter = 0
        swapTuple = ('swap', commandText, trainer, pokemonIndex)
        if not fromUserFaint and not bypassCheck:
            self.commandsPriority1.append(swapTuple)
        return fromUserFaint

    def sendAttackCommand(self, attackPokemon, defendPokemon, move):
        if attackPokemon == self.pokemon1:
            self.trainer1InputReceived = True
        elif attackPokemon == self.pokemon2:
            self.trainer2InputReceived = True
        attackTuple = ("attack", attackPokemon, defendPokemon, move)
        self.attackCommands.append(attackTuple)
        
    def attackCommand(self, attackPokemon, defendPokemon, move):
        damageDealt = 0
        #print("attempting to use move: " + move['names']['en'])
        moveName = move['names']['en']
        foePrefix = ''
        #print('attackPokemon.OT', attackPokemon.OT)
        if (self.trainer2 is not None):
            #print('str(self.trainer2.author)', str(self.trainer2.author))
            if (str(self.trainer2.author) == attackPokemon.OT):
                foePrefix = 'Foe '
        if (self.isWildEncounter and attackPokemon.OT == 'Mai-san'):
            #print('isWild and Mai-san')
            foePrefix = 'Foe '
        text = ''
        if ('faint' in attackPokemon.statusList or 'faint' in defendPokemon.statusList):
            return text
        for status in attackPokemon.statusList:
            if (status == 'freeze'):
                text = text + foePrefix + attackPokemon.nickname + " is frozen.\n"
                roll = random.randint(1,5)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname + " thawed out!\n"
                    attackPokemon.removeStatus('freeze')
                else:
                    text = text + foePrefix + attackPokemon.nickname + " was frozen solid!\n"
                    return text
            elif (status == 'paralysis'):
                text = text + foePrefix + attackPokemon.nickname + " is paralyzed.\n"
                roll = random.randint(1, 4)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname + " is paralyzed and cannot move!\n"
                    return text
            elif (status == 'sleep'):
                text = text + foePrefix + attackPokemon.nickname + " is fast asleep.\n"
                roll = random.randint(1,3)
                #print(roll)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname + " woke up!\n"
                    attackPokemon.removeStatus('sleep')
                else:
                    return text
            if (status == 'confusion'):
                text = text + foePrefix + attackPokemon.nickname + " is confused.\n"
                roll = random.randint(1, 4)
                if (roll == 1):
                    text = text + foePrefix + attackPokemon.nickname + " snapped out of confusion!\n"
                    attackPokemon.removeStatus('confusion')
                else:
                    roll2 = random.randint(1, 2)
                    if (roll2 == 1):
                        text = text + foePrefix + attackPokemon.nickname + " hurt itself in confusion!\n"
                        damage, isCrit, effectivenessModifier = self.calculateDamage(attackPokemon, None, None, True)
                        attackPokemon.takeDamage(damage)
                        return text

        text = text + foePrefix + attackPokemon.nickname + " used " + move['names']['en'] + "!"

        moveAffectedByProtect = True
        if 'affected_by_protect' in move:
            moveAffectedByProtect = move['affected_by_protect']
        if moveAffectedByProtect:
            if (defendPokemon == self.pokemon1 and self.pokemon1Protected) or (defendPokemon == self.pokemon2 and self.pokemon2Protected):
                return text + '\n' + foePrefix + attackPokemon.nickname + "'s attack was blocked by protect!"

        if ('in_battle_properties' in move):
            if ('requirement' in move['in_battle_properties']):
                status = None
                requirementTarget = None
                if 'status' in move['in_battle_properties']['requirement']:
                    status = move['in_battle_properties']['requirement']['status']
                if 'target' in move['in_battle_properties']['requirement']:
                    requirementTarget = move['in_battle_properties']['requirement']['target']
                if requirementTarget is not None:
                    if requirementTarget == 'self':
                        requirementTarget = attackPokemon
                    else:
                        requirementTarget = defendPokemon
                    if status is not None:
                        if status not in requirementTarget.statusList:
                            return text + '\n' + "The move has no effect!"

        accuracyRoll = random.randint(1,100)
        accuracyRoll = accuracyRoll
        moveAccuracy = move['accuracy'] * self.accuracyModifiers[attackPokemon.statMods['accuracy']] * self.evasionModifiers[defendPokemon.statMods['evasion']]
        if (moveAccuracy < accuracyRoll and moveAccuracy != 0):
            return text + '\n' + foePrefix + attackPokemon.nickname + "'s attack missed!"

        if (moveName.lower() == 'rest'):
            attackPokemon.fullHeal()

        if (move['target'] == 'user'):
            target = attackPokemon
        else:
            target = defendPokemon

        damage = 0
        if (move['category'] == 'physical' or move['category'] == 'special'):
            damage, isCrit, effectivenessModifier = self.calculateDamage(attackPokemon, target, move)
            if 'multi_hit' in move:
                maxHits = move['multi_hit']
                if maxHits == 5:
                    roll = random.randint(1, 100)
                    if roll > 88:
                        numHits = 5
                    elif roll > 76:
                        numHits = 4
                    elif roll > 38:
                        numHits = 3
                    else:
                        numHits = 2
                else:
                    numHits = maxHits
                damage = round(numHits * damage)
                text = text + "\nIt hit " + str(numHits) + " times!"
            if damage >= target.currentHP and moveName == "False Swipe":
                damage = target.currentHP - 1
                if damage < 0:
                    damage = 0
            if moveName == "Dragon Rage":
                damage = 40
            if moveName == "Sonic Boom":
                damage = 20
            if self.isRaid and (moveName == 'Guillotine' or moveName == 'Sheer Cold' or moveName == 'Horn Drill' or moveName == 'Fissure'):
                text = text + "\nThe raid boss is immune to one-hit KO moves!"
            else:
                damageDealt = target.takeDamage(damage)
                if self.isRaid and target == self.pokemon2:
                    self.raidDamage = damageDealt
                if (isCrit and 'faint' not in target.statusList and effectivenessModifier != 0):
                    text = text + " It's a critical hit!"
                if (effectivenessModifier < 1 and effectivenessModifier > 0):
                    text = text + "\nIt's not very effective..."
                elif (effectivenessModifier > 1):
                    text = text + "\nIt's super effective!"
                elif (effectivenessModifier == 0):
                    text = text + "\nIt doesn't affect " + target.nickname + "!"
                    return text

        # if 'faint' in target.statusList:
        #     return text

        if (move['target'] == 'user'):
            target = attackPokemon
        else:
            target = defendPokemon
        foePrefix = self.getFoePrefix(target.OT)

        if ('in_battle_properties' in move):
            if ("status_conditions" in move['in_battle_properties']):
                for statusCondition in move['in_battle_properties']['status_conditions']:
                    if 'affects_user' in statusCondition:
                        if statusCondition['affects_user']:
                            target = attackPokemon
                    if 'faint' in target.statusList:
                        continue
                    status = statusCondition['condition']
                    if (status == "poison"):
                        status = "poisoned"
                    probability = statusCondition['probability']
                    roll = random.randint(1, 100)
                    if (roll <= probability):
                        if ((status in target.statusList or 'burn' in target.statusList
                                or 'sleep' in target.statusList or 'paralysis' in target.statusList
                                or 'badly_poisoned' in target.statusList or 'poisoned' in target.statusList
                                or 'freeze' in target.statusList) and status != 'confusion' and status != 'seeded'):
                            text = text + '\n' + foePrefix + target.nickname + ' already has a status condition.'
                        elif (status == 'confusion' and 'confusion' in target.statusList):
                            text = text + '\n' + foePrefix + target.nickname + ' is already confused.'
                        elif (status == 'seeded' and 'seeded' in target.statusList):
                            text = text + '\n' + foePrefix + target.nickname + ' is already seeded.'
                        else:
                            if (self.weather == 'sun' and status == 'freeze'):
                                pass
                            else:
                                statusText = status
                                if statusText.lower() == "poisoned" or statusText.lower() == "badly_poisoned":
                                    statusText = "poison"
                                # typeList = target.getType()
                                # if statusText == "poison" and ("Poison" in typeList or "Steel" in typeList):
                                #     text = text + '\n' + foePrefix + target.nickname + ' can not be inflicted with ' + statusText.upper() + '!'
                                # elif statusText == "burn" and "Fire" in typeList:
                                #     text = text + '\n' + foePrefix + target.nickname + ' can not be inflicted with ' + statusText.upper() + '!'
                                # else:
                                if self.isRaid and target == self.pokemon2:
                                    text = text + '\n' + foePrefix + target.nickname + ' is IMMUNE to ' + statusText.upper() + '!'
                                else:
                                    target.addStatus(status)
                                    statusTuple = ("status", target, status)
                                    self.commands.append(statusTuple)
                                    text = text + '\n' + foePrefix + target.nickname + ' was inflicted with ' + statusText.upper() + '!'
            if ("affect" in move['in_battle_properties']):
                for affect in move['in_battle_properties']['affect']:
                    condition = affect['condition']
                    target = affect['target']
                    scale = affect['scale']
                    percent = affect['percent']/100
                    if condition == 'heal':
                        if target == 'self':
                            healTarget = attackPokemon
                        else:
                            healTarget = defendPokemon
                        if 'faint' in healTarget.statusList:
                            continue
                        healFoePrefix = ''
                        if (self.trainer2 is not None):
                            if (str(self.trainer2.author) == healTarget.OT):
                                healFoePrefix = 'Foe '
                        if (self.isWildEncounter and healTarget.OT == 'Mai-san'):
                            healFoePrefix = 'Foe '
                        healAmount = None
                        if scale == 'damage':
                            healAmount = round(damageDealt * percent)
                        elif scale == 'hp':
                            healAmount = round(attackPokemon.hp * percent)
                        if healAmount:
                            if healAmount <= 0:
                                healAmount = 1
                            if healTarget.currentHP < healTarget.hp:
                                deltaHealth = healTarget.hp - healTarget.currentHP
                                if deltaHealth < healAmount:
                                    healAmount = deltaHealth
                                healTarget.heal(healAmount)
                                text = text + '\n' + healFoePrefix + healTarget.nickname + ' was healed by ' + str(healAmount) + ' HP !'
                    if condition == 'protect':
                        if target == 'self':
                            protectTarget = attackPokemon
                        else:
                            protectTarget = defendPokemon
                        if 'faint' in protectTarget.statusList:
                            continue
                        protectFoePrefix = ''
                        if (self.trainer2 is not None):
                            if (str(self.trainer2.author) == protectTarget.OT):
                                protectFoePrefix = 'Foe '
                        if (self.isWildEncounter and protectTarget.OT == 'Mai-san'):
                            protectFoePrefix = 'Foe '
                        odds = 100
                        if protectTarget in self.protectDict.keys():
                            odds = round(odds * math.pow(0.5, self.protectDict[protectTarget]))
                            self.protectDict[protectTarget] = self.protectDict[protectTarget] + 1
                        else:
                            self.protectDict[protectTarget] = 1
                        roll = random.randint(1, 100)
                        if odds > roll:
                            if protectTarget == self.pokemon1:
                                self.pokemon1Protected = True
                            elif protectTarget == self.pokemon2:
                                self.pokemon2Protected = True
                            text = text + '\n' + protectFoePrefix + protectTarget.nickname + ' protected itself!'
                        else:
                            del self.protectDict[protectTarget]
                            text = text + '\n' + protectFoePrefix + protectTarget.nickname + ' failed to protect itself!'
                    if condition == 'recoil':
                        if target == 'self':
                            recoilTarget = attackPokemon
                        else:
                            recoilTarget = defendPokemon
                        if 'faint' in recoilTarget.statusList:
                            continue
                        recoilFoePrefix = self.getFoePrefix(recoilTarget.OT)
                        recoilAmount = None
                        if scale == 'damage':
                            recoilAmount = round(damageDealt * percent)
                        elif scale == 'currentHP':
                            recoilAmount = round(recoilTarget.currentHP * percent)
                        if recoilAmount:
                            if self.isRaid and recoilTarget == self.pokemon2:
                                text = text + '\n' + recoilTarget.nickname + ' is IMMUNE to recoil!'
                            else:
                                recoilTarget.takeDamage(recoilAmount)
                                text = text + '\n' + recoilFoePrefix + recoilTarget.nickname + ' was hurt by recoil!'

        if (move['target'] == 'user'):
            target = attackPokemon
        else:
            target = defendPokemon

        if ('stat_modifiers' in move):
            for statObj in move['stat_modifiers']:
                foePrefix = self.getFoePrefix(target.OT)
                stat = statObj['stat']
                changeBy = statObj['change_by']
                affectsUser = False
                if ('affects_user' in statObj):
                    affectsUser = statObj['affects_user']
                if affectsUser:
                    target = attackPokemon
                    foePrefix = ''
                if 'faint' in target.statusList:
                    continue
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

                if 'probability' in statObj:
                    odds = statObj['probability']
                elif (move['category'] == 'physical' or move['category'] == 'special'):
                    odds = 33
                else:
                    odds = 100
                statRoll = random.randint(1, 100)
                if odds >= statRoll:
                    success = target.modifyStatModifier(stat, changeBy)
                    if success:
                        text = text + "\n" + foePrefix + target.nickname + "'s " + stat.replace("_", " ").upper() + " was " + changeByText + "!"
                    else:
                        if (changeBy > 0):
                            changeByText2 = "higher"
                        else:
                            changeByText2 = "lower"
                        text = text + "\n" + foePrefix + target.nickname + "'s " + stat.replace("_", " ").upper() + " cannot go any " + changeByText2 + "!"
        return text

    def getFoePrefix(self, OT):
        foePrefix = ''
        if (self.trainer2 is not None):
            if (str(self.trainer2.author) == OT):
                foePrefix = 'Foe '
        if (self.isWildEncounter and OT == 'Mai-san'):
            foePrefix = 'Foe '
        return foePrefix

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
            moveName = move['names']['en']
            if moveName.lower() == "return":
                basePower = math.floor(attackPokemon.happiness / 2.5)
            if moveName.lower() == "frustration":
                basePower = math.floor((255 - attackPokemon.happiness) / 2.5)
                if basePower < 1:
                    basePower = 1
            attack, defense = self.calculatePhysOrSpecStats(attackPokemon, defendPokemon, move['category'])
        damage = math.floor(((((((2*level)/5)+2)* basePower * (attack/defense))/50) + 2) * modifier)
        if (damage < 1 and effectivenessModifier != 0):
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
        location = self.trainer1.location
        if location.endswith(' E') or location.endswith(' W') or location.endswith(' S') or location.endswith(' N'):
            location = location[:-2]
        elif location.endswith(' Under'):
            location = location[:-6]

        if (location == 'Altering Cave' and self.trainer1 is not None):
            maxLevel = 20
            minLevel = 10
            for pPokemon in self.trainer1.partyPokemon:
                if pPokemon.OT == self.trainer1.author:
                    if pPokemon.level - 2 > maxLevel:
                        deltaLevel = pPokemon.level - 2 - maxLevel
                        maxLevel = pPokemon.level - 2
                        minLevel += deltaLevel
            if maxLevel > 70:
                maxLevel = 70
                minLevel = 60
            level = random.randint(minLevel, maxLevel)
            return self.data.shinyCharmCheck(self.trainer1, Pokemon(self.data, self.trainer1.alteringPokemon, level))

        encounterList = self.data.getEncounterTable(self.trainer1, location, self.entryType)
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
            maxLevel = pokemonObj["max_level"]
            minLevel = pokemonObj["min_level"]
            roll = random.randint(1, 5)
            if roll == 5:
                if self.trainer1 is not None:
                    for pPokemon in self.trainer1.partyPokemon:
                        if pPokemon.OT == self.trainer1.author:
                            if pPokemon.level - 2 > maxLevel:
                                deltaLevel = pPokemon.level - 2 - maxLevel
                                maxLevel = pPokemon.level - 2
                                minLevel += deltaLevel
            if maxLevel > 70:
                maxLevel = 70
                minLevel = 60
            level = random.randint(minLevel, maxLevel)
            return self.data.shinyCharmCheck(self.trainer1, Pokemon(self.data, pokemonObj["pokemon"], level))
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

    def tryCatchPokemon(self, ball):
        if not self.isWildEncounter:
            return False, 0
        ballMod = 1
        if (ball == "Greatball"):
            ballMod = 1.5
        elif (ball == "Ultraball"):
            ballMod = 2
        elif (ball == "Masterball"):
            return True, 3
        statMod = 1
        if ('sleep' in self.pokemon2.statusList or 'freeze' in self.pokemon2.statusList):
            statMod = 2
        elif ('paralysis' in self.pokemon2.statusList or 'burn' in self.pokemon2.statusList or 'poisoned' in self.pokemon2.statusList
                or 'badly_poisoned' in self.pokemon2.statusList):
            statMod = 1.5
        rate = round((((3*self.pokemon2.hp - 2*self.pokemon2.currentHP) * self.pokemon2.getFullData()['catch_rate'] * ballMod) / (3*self.pokemon2.hp)) * statMod)
        odds = math.floor(1048560 / math.floor(math.sqrt(math.floor(math.sqrt(16711680 / rate)))))
        logging.debug(str(self.trainer1.identifier) + " - trying to catch " + self.pokemon2.name + " with capture rate " + str(self.pokemon2.getFullData()['catch_rate']) + " - to pass shake check need roll less than " + str(odds) + ".")
        shakes = 0
        if odds > 65535:
            return True, 3
        else:
            for x in range(0, 4):
                roll = random.randint(0, 65535)
                logging.debug(str(self.trainer1.identifier) + " - roll #" + str(x) + " = " + str(roll) + ".")
                if roll >= odds:
                    return False, shakes
                shakes += 1
            return True, 3

    def catchPokemon(self, ball): # caught, shakes, sentToBox
        sentToBox = False
        caught, shakes = self.tryCatchPokemon(ball)
        if (caught):
            self.pokemon2.setCaughtIn(ball)
            if (len(self.trainer1.partyPokemon) > 5):
                sentToBox = True
            self.trainer1.addPokemon(self.pokemon2, True)
            return True, shakes, sentToBox
        return False, shakes, sentToBox

    def sendUseItemCommand(self, item, pokemonForItem):
        itemTuple = ("useItem", item, pokemonForItem)
        self.commandsPriority1.append(itemTuple)

    def useItemCommand(self, item, pokemonForItem):
        success, itemText = pokemonForItem.useItemOnPokemon(item)
        if success:
            self.trainer1.useItem(item, 1)
        return itemText

    def run(self):
        if self.isRaid:
            return True
        return self.trainer2 is None

