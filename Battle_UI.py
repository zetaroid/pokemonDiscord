import disnake as discord
import os
from PIL import Image
from asyncio import sleep
from copy import copy
import uuid
import logging

import PokeNavComponents


class Battle_UI(object):

    def __init__(self, data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI, startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI):
        self.data = data
        self.timeout = timeout
        self.battleTimeout = battleTimeout
        self.pvpTimeout = pvpTimeout
        self.getBattleItems = getBattleItems
        self.startNewUI = startNewUI
        self.continueUI = continueUI
        self.startPartyUI = startPartyUI
        self.startOverworldUI = startOverworldUI
        self.startBattleTowerUI = startBattleTowerUI
        self.startCutsceneUI = startCutsceneUI
        self.invertTrainers = False
        self.inter = None
        self.isWild = None
        self.battle = None
        self.goBackTo = ''
        self.otherData = None
        self.goStraightToResolve = False
        self.message = None
        self.embed = None

    async def startBattleUI(self, inter, isWild, battle, goBackTo='', otherData=None, goStraightToResolve=False,
                            invertTrainers=False, isFromFaint=False):
        logging.debug(str(inter.author.id) + " - startBattleUI()")
        self.invertTrainers = invertTrainers
        self.inter = inter
        self.isWild = isWild
        self.battle = battle
        self.goBackTo = goBackTo
        self.otherData = otherData
        self.goStraightToResolve = goStraightToResolve
        dataTuple = (isWild, battle, goBackTo, otherData, invertTrainers)
        isMoveUI = False
        isItemUI1 = False
        isItemUI2 = False

        if isFromFaint and battle.isPVP:
            count = 0
            if invertTrainers:
                tempStatusList = battle.pokemon1.statusList
            else:
                tempStatusList = battle.pokemon2.statusList
            waitingMessage = None
            if 'faint' in tempStatusList:
                waitingMessage = await inter.channel.send("`Waiting for opponent to switch Pokemon...`")
            while 'faint' in tempStatusList:
                if invertTrainers:
                    tempStatusList = battle.pokemon1.statusList
                else:
                    tempStatusList = battle.pokemon2.statusList
                if count >= self.pvpTimeout:
                    try:
                        await waitingMessage.delete()
                    except:
                        pass
                    await inter.channel.send(str(
                        inter.author.mention) + ", the other player has timed out - battle has ended. You win the battle.")
                    self.recordPVPWinLoss(True, self.trainer1)
                    return
                count += 1
                await sleep(1)
            try:
                await waitingMessage.delete()
            except:
                pass

        self.updatePokemon()
        filename = self.mergeImages(self.pokemon1.getSpritePath(), self.pokemon2.getSpritePath(), self.trainer1.location)
        files, embed = self.createBattleEmbed(inter, isWild, self.pokemon1, self.pokemon2, goStraightToResolve, filename, self.trainer2)
        self.embed = embed
        emojiNameList = []
        buttonList = []
        if not goStraightToResolve:
            buttonList.append(PokeNavComponents.OverworldUIButton(label="Fight", style=discord.ButtonStyle.green, row=0,
                                                                  identifier='1'))
            buttonList.append(PokeNavComponents.OverworldUIButton(label="Bag", style=discord.ButtonStyle.blurple, row=0,
                                                                  identifier='2'))
            buttonList.append(PokeNavComponents.OverworldUIButton(label="Pokémon", style=discord.ButtonStyle.grey, row=0,
                                                                  identifier='3'))
            run_button = PokeNavComponents.OverworldUIButton(label="Run", style=discord.ButtonStyle.red, row=0,
                                                                  identifier='4')
            if not self.isWild and not self.battle.isPVP and not self.battle.isRaid:
                run_button.disabled = True
            buttonList.append(run_button)
            emojiNameList.append('1')
            emojiNameList.append('2')
            emojiNameList.append('3')
            emojiNameList.append('4')

        if battle.isPVP:
            tempTimeout = self.pvpTimeout
        else:
            tempTimeout = self.battleTimeout

        # battle.addUiListener(self)
        # print('isFromFaint = ' + str(isFromFaint))

        chosenEmoji, message = await self.startNewUI(inter, self.embed, files, buttonList, tempTimeout, None, None, False,
                                                battle.isPVP, battle.isRaid, battle.isBattleTower)
        try:
            os.remove(filename)
        except:
            pass
        self.message = message

        if goStraightToResolve:
            emojiNameList.append('1')
            emojiNameList.append('2')
            emojiNameList.append('3')
            emojiNameList.append('4')

        while True:
            if (chosenEmoji == None and self.message == None):
                if battle.isPVP:
                    await inter.channel.send(
                        str(inter.author.mention) + ", you have timed out - battle has ended. You lose the battle.")
                    self.recordPVPWinLoss(False, self.trainer1)
                    return
                elif battle.isRaid:
                    await inter.channel.send(
                        str(inter.author.mention) + ", you have timed out - raid battle has ended.")
                    return
                else:
                    # self.trainer1.removeProgress(self.trainer1.location)
                    break
            if chosenEmoji == None:
                if self.message == "bt_reset":
                    if self.battle.battleTowerType == "wr":
                        otherData[0].withRestrictionStreak = 0
                    elif self.battle.battleTowerType == 'nr':
                        otherData[0].noRestrictionsStreak = 0
                    break
            bpReward = 0
            if (goStraightToResolve):
                #await self.message.clear_reactions()
                await self.message.edit(view=None)
                if self not in battle.uiListeners:
                    battle.addUiListener(self)
                goStraightToResolve = False

                if battle.isPVP:
                    self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2, "Waiting for other player..."))
                    await self.message.edit(embed=self.embed)
                    if not invertTrainers:
                        displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted, isTimeout = await battle.endTurn(
                            self.pvpTimeout)
                        if isTimeout:
                            await inter.channel.send(str(
                                inter.author.mention) + ", the other player has timed out - battle has ended. You win the battle.")
                            self.recordPVPWinLoss(True, self.trainer1)
                            return
                    else:
                        count = 0
                        while battle.trainer2ShouldWait:
                            # print("Trainer 2 waiting = ", count)
                            count += 1
                            if count >= self.pvpTimeout:
                                # await self.message.delete()
                                await inter.channel.send(str(
                                    inter.author.mention) + ", the other player has timed out - battle has ended. You win the battle.")
                                self.recordPVPWinLoss(True, self.trainer1)
                                return
                            await sleep(1)
                        if battle.trainer1Ran:
                            displayText = "Opponent left the trainer battle."
                            shouldBattleEnd = True
                            isWin = True
                            isUserFainted = False
                            isOpponentFainted = False
                        else:
                            battle.trainer2ShouldWait = True
                            displayText = battle.endTurnTuple[0]
                            shouldBattleEnd = battle.endTurnTuple[1]
                            isWin = not battle.endTurnTuple[2]
                            isUserFainted = battle.endTurnTuple[4]
                            isOpponentFainted = battle.endTurnTuple[3]
                    if (displayText != ''):
                        self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2, displayText))
                        await self.message.edit(embed=self.embed)
                        await sleep(6)
                    if shouldBattleEnd:
                        winText = ''
                        if (isWin):
                            winText = "You win!"
                        else:
                            winText = "You lose!"
                        self.recordPVPWinLoss(isWin, self.trainer1)
                        self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2, winText))
                        await self.message.edit(embed=self.embed)
                        await sleep(4)
                        break
                    if isUserFainted:
                        await self.message.delete()
                        await self.startPartyUI(inter, self.trainer1, 'startBattleUI', battle, dataTuple)
                        break
                    if isOpponentFainted:
                        count = 0
                        self.embed.set_footer(
                            text=self.createTextFooter(self.pokemon1, self.pokemon2, "Waiting for other player to switch Pokemon..."))
                        await self.message.edit(embed=self.embed)
                        tempName = ''
                        if invertTrainers:
                            while 'faint' in battle.pokemon1.statusList:
                                # print("Trainer 2 waiting for switch = ", count)
                                count += 1
                                if count >= self.pvpTimeout:
                                    # await self.message.delete()
                                    await inter.channel.send(str(
                                        inter.author.mention) + ", the other player has timed out - battle has ended. You win the battle.")
                                    return
                                await sleep(1)
                            tempName = battle.pokemon1.nickname
                        else:
                            while 'faint' in battle.pokemon2.statusList:
                                # print("Trainer 1 waiting for switch = ", count)
                                count += 1
                                if count >= self.pvpTimeout:
                                    # await self.message.delete()
                                    await inter.channel.send(str(
                                        inter.author.mention) + ", the other player has timed out - battle has ended. You win the battle.")
                                    return
                                await sleep(1)
                            tempName = battle.pokemon2.nickname
                        self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2,
                                                               self.trainer2.name + " sent out " + tempName + "!"))
                        await self.message.edit(embed=self.embed)
                        await sleep(3)
                        await self.message.delete()
                        await self.startBattleUI(inter, isWild, battle, goBackTo, otherData, goStraightToResolve,
                                            invertTrainers)
                        break
                else:
                    displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted, isTimeout = await battle.endTurn()
                    if (displayText != ''):
                        self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2, displayText))
                        await self.message.edit(embed=self.embed)
                        await sleep(6)
                    if shouldBattleEnd:
                        pokemonToEvolveList, pokemonToLearnMovesList = battle.endBattle()
                        if (isWin):
                            rewardText = ''
                            if (self.trainer2 is not None):
                                if not battle.isRaid:
                                    self.trainer1.trainerDefeatedEvent(self.trainer2)
                                for rewardName, rewardValue in self.trainer2.rewards.items():
                                    if (rewardName == "flag"):
                                        self.trainer1.addFlag(rewardValue)
                                    else:
                                        if (rewardName.lower() == "bp"):
                                            bpReward = rewardValue
                                        if not rewardName:
                                            rewardName = 'ERROR'
                                        rewardText = rewardText + "\n" + rewardName[0].capitalize() + rewardName[
                                                                                                      1:] + ": " + str(
                                            rewardValue)
                                        # print("giving " + trainer1.name + " " + rewardName + "x" + str(rewardValue))
                                        self.trainer1.addItem(rewardName, rewardValue)
                                for flagName in self.trainer2.rewardFlags:
                                    self.trainer1.addFlag(flagName)
                                for flagName in self.trainer2.rewardRemoveFlag:
                                    self.trainer1.removeFlag(flagName)
                            else:
                                self.trainer1.wildDefeatedEvent(self.pokemon2, self.trainer1.location, self.data)
                            if rewardText:
                                rewardText = "Rewards:" + rewardText + "\n\n(returning to overworld in 4 seconds...)"
                                self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2, rewardText))
                                await self.message.edit(embed=self.embed)
                                await sleep(4)
                            await self.message.delete()
                        else:
                            await self.message.delete()
                            self.trainer1.removeProgress(self.trainer1.location)
                            self.trainer1.location = self.trainer1.lastCenter
                        await self.afterBattleCleanup(inter, battle, pokemonToEvolveList, pokemonToLearnMovesList, isWin,
                                                 goBackTo,
                                                 otherData, bpReward)
                        break
                    elif isUserFainted:
                        await self.message.delete()
                        await self.startPartyUI(inter, self.trainer1, 'startBattleUI', battle, dataTuple)
                        break
                    elif isOpponentFainted:
                        self.updatePokemon()
                        if (self.trainer2 is not None):
                            self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2,
                                                                   self.trainer2.name + " sent out " + self.pokemon2.name + "!"))
                            await self.message.edit(embed=self.embed)
                            await sleep(3)
                        await self.message.delete()
                        await self.startBattleUI(inter, isWild, battle, goBackTo, otherData, goStraightToResolve)
                        break
                # print('setting battle footer after combat')
                self.embed.set_footer(text=self.createBattleFooter(self.pokemon1, self.pokemon2, self.trainer1.iphone))
                view = self.createHomeView(inter.author)
                await self.message.edit(embed=self.embed, view=view)
                # await self.message.add_reaction(self.data.getEmoji('1'))
                # await self.message.add_reaction(self.data.getEmoji('2'))
                # await self.message.add_reaction(self.data.getEmoji('3'))
                # await self.message.add_reaction(self.data.getEmoji('4'))

            new_category = ""
            move_num = 0
            item_num = 0
            skipToEnd = False
            if (isMoveUI and (chosenEmoji == '1' or chosenEmoji == '2'
                              or chosenEmoji == '3' or chosenEmoji == '4') and
                    ((len(self.pokemon1.moves) > 0 and self.pokemon1.pp[0] == 0 and self.pokemon1.pp[1] == 0
                      and self.pokemon1.pp[2] == 0 and self.pokemon1.pp[3] == 0) or
                     len(self.pokemon1.moves) == 0)):
                goStraightToResolve = True
                isMoveUI = False
                battle.sendAttackCommand(self.pokemon1, self.pokemon2, self.data.getMoveData("Struggle"))
                chosenEmoji = None
                continue
            elif (chosenEmoji == '1'):
                new_category = "Balls"
                move_num = 0
                item_num = 0
                if not isMoveUI and not isItemUI1 and not isItemUI2:
                    isMoveUI = True
                    self.embed.set_footer(text=self.createMoveFooter(self.pokemon1, self.pokemon2, self.trainer1.iphone))
                    view = self.createMovesView(inter.author, self.pokemon1)
                    await self.message.edit(embed=self.embed, view=view)
                    emojiNameList.append('right arrow')
                    skipToEnd = True
            elif (chosenEmoji == '2'):
                new_category = "Healing Items"
                move_num = 1
                item_num = 1
                if not isMoveUI and not isItemUI1 and not isItemUI2 and not battle.isPVP:
                    isItemUI1 = True
                    self.embed.set_footer(text=self.createItemCategoryFooter(self.pokemon1, self.pokemon2, self.trainer1.iphone))
                    view = self.createNumberedView(inter.author, 3)
                    await self.message.edit(embed=self.embed, view=view)
                    emojiNameList.append('right arrow')
                    skipToEnd = True
            elif (chosenEmoji == '3'):
                new_category = "Status Items"
                move_num = 2
                item_num = 2
                if not isMoveUI and not isItemUI1 and not isItemUI2:
                    await self.message.delete()
                    await self.startPartyUI(inter, self.trainer1, 'startBattleUI', battle, dataTuple)
                    break
            elif (chosenEmoji == '4'):
                move_num = 3
                item_num = 3
                if not isMoveUI and not isItemUI1 and not isItemUI2:
                    canRun = battle.run()
                    skipToEnd = True
                    if canRun:
                        if battle.isPVP:
                            if invertTrainers:
                                battle.trainer2Ran = True
                            else:
                                battle.trainer1Ran = True
                                battle.trainer2ShouldWait = False
                            self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2,
                                                                             "You left the trainer battle."))
                        else:
                            self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2,
                                                                   "Got away safely!\n(returning to overworld in 4 seconds...)"))
                        await self.message.edit(embed=self.embed, view=None)
                        await sleep(4)
                        self.battle.endBattle()
                        if not battle.isPVP:
                            await self.message.delete()
                        if (goBackTo == 'startOverworldUI'):
                            await self.startOverworldUI(inter, otherData[0])
                        break
            elif (chosenEmoji == '5'):
                item_num = 4
            elif (chosenEmoji == '6'):
                item_num = 5
            elif (chosenEmoji == '7'):
                item_num = 6
            elif (chosenEmoji == '8'):
                item_num = 7
            elif (chosenEmoji == '9'):
                item_num = 8
            elif ((isMoveUI or isItemUI1 or isItemUI2) and chosenEmoji == 'right arrow'):
                skipToEnd = True
                if not isItemUI2:
                    isMoveUI = False
                    isItemUI1 = False
                    self.embed.set_footer(text=self.createBattleFooter(self.pokemon1, self.pokemon2, self.trainer1.iphone))
                    view = self.createHomeView(inter.author)
                    await self.message.edit(embed=self.embed, view=view)
                else:
                    isItemUI2 = False
                    isItemUI1 = True
                    self.embed.set_footer(text=self.createItemCategoryFooter(self.pokemon1, self.pokemon2, self.trainer1.iphone))
                    view = self.createNumberedView(inter.author, 3)
                    await self.message.edit(embed=self.embed, view=view)

            if chosenEmoji and not skipToEnd:
                if not isMoveUI and not isItemUI1 and not isItemUI2:
                    isMoveUI = True
                    self.embed.set_footer(text=self.createMoveFooter(self.pokemon1, self.pokemon2, self.trainer1.iphone))
                    view = self.createMovesView(inter.author, self.pokemon1)
                    await self.message.edit(embed=self.embed, view=view)
                    emojiNameList.append('right arrow')
                elif isMoveUI:
                    if (len(self.pokemon1.moves) > move_num):
                        if (self.pokemon1.pp[move_num] > 0):
                            goStraightToResolve = True
                            isMoveUI = False
                            self.pokemon1.usePP(move_num)
                            battle.sendAttackCommand(self.pokemon1, self.pokemon2, self.pokemon1.moves[move_num])
                            chosenEmoji = None
                            continue
                elif isItemUI1 and chosenEmoji != "4":
                    category = new_category
                    isItemUI1 = False
                    isItemUI2 = True
                    items = self.getBattleItems(category, battle)
                    self.embed.set_footer(
                        text=self.createItemFooter(self.pokemon1, self.pokemon2, category, items, self.trainer1))
                    view = self.createNumberedView(inter.author, len(items))
                    await self.message.edit(embed=self.embed, view=view)
                elif isItemUI2:
                    items = self.getBattleItems(category, battle)
                    if (len(items) > item_num):
                        item = items[item_num]
                        if (category == "Balls"):
                            if (isWild or self.pokemon2.shadow):
                                ball = item
                                self.trainer1.useItem(ball, 1)
                                self.embed.set_footer(
                                    text=self.createTextFooter(self.pokemon1, self.pokemon2, "Go " + ball + "!"))
                                await self.message.edit(embed=self.embed, view=None)
                                await sleep(3)
                                caught, shakes, sentToBox = battle.catchPokemon(ball)
                                failText = ''
                                if (shakes > 0):
                                    for x in range(0, shakes):
                                        self.embed.clear_fields()
                                        self.createBattleEmbedFields(self.embed, self.pokemon1, self.pokemon2, ball, x + 1)
                                        await self.message.edit(embed=self.embed)
                                        await sleep(2)
                                    if not caught:
                                        self.embed.clear_fields()
                                        self.createBattleEmbedFields(self.embed, self.pokemon1, self.pokemon2)
                                        await self.message.edit(embed=self.embed)
                                if (shakes == 0):
                                    failText = "Oh no! The Pokemon broke free!"
                                elif (shakes == 1):
                                    failText = "Aww! It appeared to be caught!"
                                elif (shakes == 2):
                                    failText = "Aargh! Almost had it!"
                                elif (shakes == 3):
                                    failText = "Shoot! It was so close, too!"
                                footerText = "Gotcha! " + self.pokemon2.name + " was caught!"
                                if (sentToBox):
                                    footerText = footerText + "\nSent to box!"
                                else:
                                    footerText = footerText + "\nAdded to party!"
                                if caught and not self.pokemon2.shadow:
                                    self.embed.set_footer(text=self.createTextFooter(self.pokemon1, self.pokemon2,
                                                                                     footerText + "\n(returning to overworld in 6 seconds...)"))
                                    await self.message.edit(embed=self.embed)
                                    await sleep(6)
                                    await self.message.delete()
                                    battle.battleRefresh()
                                    await self.startOverworldUI(inter, self.trainer1)
                                    break
                                elif caught and self.pokemon2.shadow:
                                    self.embed.set_footer(
                                        text=self.createTextFooter(self.pokemon1, self.pokemon2, footerText))
                                    await self.message.edit(embed=self.embed)
                                    await sleep(4)
                                    goStraightToResolve = True
                                    isItemUI2 = False
                                    chosenEmoji = None
                                    self.pokemon2.addStatus("shadow_caught")
                                    continue
                                else:
                                    self.embed.set_footer(
                                        text=self.createTextFooter(self.pokemon1, self.pokemon2, failText))
                                    await self.message.edit(embed=self.embed)
                                    await sleep(4)
                                    goStraightToResolve = True
                                    isItemUI2 = False
                                    chosenEmoji = None
                                    continue
                        elif (category == "Healing Items" or category == "Status Items"):
                            await self.message.delete()
                            await self.startPartyUI(inter, self.trainer1, 'startBattleUI', battle, dataTuple, False,
                                                    False, None, False, item)
                            break

            chosenEmoji, message = await self.continueUI(inter, self.message, emojiNameList, tempTimeout, None, False, battle.isPVP, battle.isRaid, battle.isBattleTower)
            self.message = message
            try:
                os.remove(filename)
            except:
                pass

    def mergeImages(self, path1, path2, location):
        locationDataObj = self.data.getLocation(location)
        folderPath = 'data/sprites/battle_backgrounds/gen3/'
        if self.trainer1.backgroundPreference == 3:
            folderPath = 'data/sprites/battle_backgrounds/gen3/'
        elif self.trainer1.backgroundPreference == 5:
            folderPath = 'data/sprites/battle_backgrounds/gen5/'
        if locationDataObj.battleTerrain == "grass":
            backgroundPath = folderPath + 'background_grass.png'
        elif locationDataObj.battleTerrain == "arena":
            backgroundPath = folderPath + 'background_arena.png'
        elif locationDataObj.battleTerrain == "cave":
            backgroundPath = folderPath + 'background_cave.png'
        elif locationDataObj.battleTerrain == "land":
            backgroundPath = folderPath + 'background_land.png'
        elif locationDataObj.battleTerrain == "water":
            backgroundPath = folderPath + 'background_water.png'
        elif locationDataObj.battleTerrain == "space":
            backgroundPath = folderPath + 'background_space.png'
        elif locationDataObj.battleTerrain == "desert":
            backgroundPath = folderPath + 'background_desert.png'
        else:
            backgroundPath = folderPath + 'background.png'
        background = Image.open(backgroundPath)
        background = background.convert('RGBA')
        image1 = Image.open(path1)
        image1 = image1.transpose(method=Image.FLIP_LEFT_RIGHT)
        image2 = Image.open(path2)

        image1 = self.cropBackground(image1)
        image2 = self.cropBackground(image2)

        if self.trainer1.backgroundPreference == 5:
            bottom_center_1 = (72, 184)
            bottom_center_1 = (round(bottom_center_1[0] - image1.width / 2), bottom_center_1[1] - image1.height)
            bottom_center_2 = (189, 96)
        else: # gen 3
            bottom_center_1 = (59, 140)
            bottom_center_1 = (round(bottom_center_1[0] - image1.width / 2), background.height - round(3 / 4 * image1.height))
            bottom_center_2 = (175, 69)
        bottom_center_2 = (round(bottom_center_2[0] - image2.width / 2), bottom_center_2[1] - image2.height)

        background.paste(image1, bottom_center_1, image1.convert('RGBA'))
        background.paste(image2, bottom_center_2, image2.convert('RGBA'))

        temp_uuid = uuid.uuid4()
        filename = "data/temp/merged_image" + str(temp_uuid) + ".png"
        background.save(filename, "PNG")
        return filename

    def cropBackground(self, im, border=0):
        bbox = im.convert("RGBA").getbbox()

        # Crop the image to the contents of the bounding box
        image = im.crop(bbox)

        # Determine the width and height of the cropped image
        (width, height) = image.size

        # Add border
        width += border * 2
        height += border * 2

        # Create a new image object for the output image
        cropped_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Paste the cropped image onto the new image
        cropped_image.paste(image, (border, border))

        return cropped_image

    def calculateNonFaintedPokemon(self, trainer):
        nonFaintedNum = 0
        for pokemon in trainer.partyPokemon:
            if 'faint' not in pokemon.statusList and 'shadow_caught' not in pokemon.statusList:
                nonFaintedNum += 1
        return nonFaintedNum

    def createBattleEmbed(self, inter, isWild, pokemon1, pokemon2, goStraightToResolve, filename, trainer2):
        files = []
        caught = False
        if isWild:
            if self.trainer1:
                if pokemon2.name in self.trainer1.pokedex:
                    caught = True
            caughtText = ""
            if caught:
                caughtText = " 📒"
            embed = discord.Embed(title="A wild " + pokemon2.name + " appeared!" + caughtText,
                                  description="[use buttons below to play]", color=0x00ff00)

        else:
            embed = discord.Embed(title=trainer2.name + " sent out " + pokemon2.name + "!",
                                  description="[Remaining Pokemon: " + str(self.calculateNonFaintedPokemon(trainer2)) + " / " + str(len(trainer2.partyPokemon)) + "]", color=0x00ff00)
        file = discord.File(filename, filename="image.png")
        files.append(file)
        embed.set_image(url="attachment://image.png")
        if not goStraightToResolve:
            embed.set_footer(text=self.createBattleFooter(pokemon1, pokemon2, self.trainer1.iphone))
        else:
            embed.set_footer(text=self.createTextFooter(pokemon1, pokemon2, ""))
        self.createBattleEmbedFields(embed, pokemon1, pokemon2, None, None)
        embed.set_author(name=(inter.author.display_name + "'s Battle:"))
        return files, embed

    def createBattleEmbedFields(self, embed, pokemon1, pokemon2, ball=None, shakeNum=None):
        statusText1 = '\u200b'
        if pokemon1.altShiny:
            statusText1 = statusText1 + ':sparkles:'
        elif pokemon1.distortion:
            statusText1 = statusText1 + ':nazar_amulet:'
        elif pokemon1.shiny:
            statusText1 = statusText1 + ':star2:'
        if pokemon1.shadow:
            statusText1 = statusText1 + ':waxing_crescent_moon:'
        for status in pokemon1.statusList:
            statusText1 = statusText1 + self.data.getStatusEmoji(status)
        statusText2 = '\u200b'
        if pokemon2.altShiny:
            statusText2 = statusText2 + ':sparkles:'
        elif pokemon2.distortion:
            statusText2 = statusText2 + ':nazar_amulet:'
        elif pokemon2.shiny:
            statusText2 = statusText2 + ':star2:'
        if pokemon2.shadow:
            statusText2 = statusText2 + ':waxing_crescent_moon:'
        for status in pokemon2.statusList:
            statusText2 = statusText2 + self.data.getStatusEmoji(status)
        if ball is not None and shakeNum is not None:
            statusText2 = ''
            for x in range(0, shakeNum):
                statusText2 = statusText2 + self.data.getEmoji(ball.replace(" ", "").lower()) + " "
        embed.add_field(name=pokemon1.nickname + '  Lv' + str(pokemon1.level), value=statusText1, inline=True)
        embed.add_field(name=pokemon2.nickname + '  Lv' + str(pokemon2.level), value=statusText2, inline=True)

    def createTextFooter(self, pokemon1, pokemon2, text):
        return ("HP: "
                + str(pokemon1.currentHP)
                + " / "
                + str(pokemon1.hp)
                + "                                      HP: "
                + str(pokemon2.currentHP)
                + " / " + str(pokemon2.hp)
                + "\n\n"
                + text)

    def createItemCategoryFooter(self, pokemon1, pokemon2, phoneFix=False):
        itemCategoryFooter = ("HP: "
                                + str(pokemon1.currentHP)
                                + " / "
                                + str(pokemon1.hp)
                                + "                                      HP: "
                                + str(pokemon2.currentHP)
                                + " / " + str(pokemon2.hp)
                                + "\n")
        if phoneFix:
            itemCategoryFooter += "(1) Balls ||| (2) Healing ||| (3) Status |||"
        else:
            itemCategoryFooter += "\n"
            itemCategoryFooter += ("Bag Pockets:\n"
                                    + "(1) Balls\n"
                                    + "(2) Healing Items\n"
                                    + "(3) Status Items\n")
        return itemCategoryFooter

    def createItemFooter(self, pokemon1, pokemon2, category, items, trainer):
        phoneFix = trainer.iphone
        itemFooter = ("HP: "
                      + str(pokemon1.currentHP)
                      + " / "
                      + str(pokemon1.hp)
                      + "                                      HP: "
                      + str(pokemon2.currentHP)
                      + " / " + str(pokemon2.hp)
                      + "\n")
        if phoneFix:
            count = 1
            for item in items:
                itemFooter = itemFooter + " (" + str(count) + ") " + item + " |||"
                count += 1
        else:
            itemFooter += "\n"
            itemFooter += category + ":"
            count = 1
            for item in items:
                itemFooter = itemFooter + "\n(" + str(count) + ") " + item + "\n----- Owned: " + str(trainer.getItemAmount(item))
                count += 1
        return itemFooter

    def createBattleFooter(self, pokemon1, pokemon2, phoneFix=False):
        battleFooter = ("HP: "
                        + str(pokemon1.currentHP)
                        + " / "
                        + str(pokemon1.hp)
                        + "                                      HP: "
                        + str(pokemon2.currentHP)
                        + " / " + str(pokemon2.hp)
                        + "\n")
        if not phoneFix:
            battleFooter += '\n'
        # battleFooter += ("(1) Fight                     (2) Bag\n(3) Pokemon            (4) Run")

        return battleFooter

    def createMoveFooter(self, pokemon1, pokemon2, phoneFix=False):
        moveFooter = ("HP: "
                      + str(pokemon1.currentHP)
                      + " / "
                      + str(pokemon1.hp)
                      + "                                      HP: "
                      + str(pokemon2.currentHP)
                      + " / " + str(pokemon2.hp)
                      + "\n")
        if not phoneFix:
            moveFooter += '\n'
        moveList = pokemon1.moves
        count = 0
        for move in moveList:
            count += 1
            try:
                moveName = move['names']['en']
                moveMaxPP = str(move['pp'])
                movePP = str(pokemon1.pp[count - 1])
            except:
                moveName = 'ERROR'
                moveMaxPP = 'ERROR'
                movePP = 'ERROR'
            addition1 = (moveName + " (" + movePP + "/" + moveMaxPP + "pp)")
            addition2 = ''
            if (count == 1 or count == 3):
                for i in range(0, 25 - len(addition1)):
                    addition2 = addition2 + " "
            else:
                addition2 = "\n"
            # moveFooter = moveFooter + "(" + str(count) + ") " + addition1 + addition2
        return moveFooter

    async def afterBattleCleanup(self, inter, battle, pokemonToEvolveList, pokemonToLearnMovesList, isWin, goBackTo, otherData,
                                 bpReward=0):
        logging.debug(str(inter.author.id) + " - afterBattleCleanup()")
        if (goBackTo == "BattleCopy"):
            return
        trainer = battle.trainer1
        for pokemon in pokemonToEvolveList:
            # print('evolist')
            # print(pokemon.nickname)
            oldName = copy(pokemon.nickname)
            pokemon.evolve()
            self.trainer1.update_pokedex(pokemon.name)
            embed = discord.Embed(title="Congratulations! " + str(
                inter.author) + "'s " + oldName + " evolved into " + pokemon.evolveToAfterBattle + "!",
                                  description="(continuing automatically in 6 seconds...)", color=0x00ff00)
            file = discord.File(pokemon.getSpritePath(), filename="image.png")
            embed.set_image(url="attachment://image.png")
            embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
            embed.set_author(name=(inter.author.display_name + "'s Pokemon Evolved:"))
            message = await inter.channel.send(file=file, embed=embed)
            await sleep(6)
            await message.delete()
        for pokemon in pokemonToLearnMovesList:
            for move in pokemon.newMovesToLearn:
                alreadyLearned = False
                for learnedMove in pokemon.moves:
                    if learnedMove['names']['en'] == move['names']['en']:
                        alreadyLearned = True
                if alreadyLearned:
                    continue
                if (len(pokemon.moves) >= 4):
                    title = str(inter.author) + "'s " + pokemon.nickname + " would like to learn " + move['names'][
                        'en'] + ".\nPlease select move to replace."
                    count = 1
                    text = ''
                    newMoveCount = count
                    for learnedMove in pokemon.moves:
                        text = text + "\n(" + str(count) + ") " + learnedMove['names']['en']
                        count += 1
                    newMoveCount = count
                    text = text + "\n(" + str(count) + ") " + move['names']['en']
                    #message = await inter.channel.send(text)
                    embed = discord.Embed(title=title, description=text)
                    emojiNameList = []
                    buttonList = []
                    for x in range(1, count + 1):
                        emojiNameList.append(str(x))
                        buttonList.append(
                            PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji(str(x)),
                                                                style=discord.ButtonStyle.grey, row=0,
                                                                identifier=str(x)))
                        #await message.add_reaction(self.data.getEmoji(str(x)))
                    chosenEmoji, message = await self.startNewUI(inter, embed, None, buttonList, self.timeout)
                    if (chosenEmoji == None and message == None):
                        return
                    if (chosenEmoji == '1'):
                        if (newMoveCount != 1):
                            oldMoveName = pokemon.moves[0]['names']['en']
                            pokemon.replaceMove(0, move)
                            await message.delete()
                            message = await inter.channel.send(
                                pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                    'en'] + "!" + " (continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await message.delete()
                    elif (chosenEmoji == '2'):
                        if (newMoveCount != 2):
                            oldMoveName = pokemon.moves[1]['names']['en']
                            pokemon.replaceMove(1, move)
                            await message.delete()
                            message = await inter.channel.send(
                                pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                    'en'] + "!" + " (continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await message.delete()
                    elif (chosenEmoji == '3'):
                        if (newMoveCount != 3):
                            oldMoveName = pokemon.moves[2]['names']['en']
                            pokemon.replaceMove(2, move)
                            await message.delete()
                            message = await inter.channel.send(
                                pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                    'en'] + "!" + " (continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await message.delete()
                    elif (chosenEmoji == '4'):
                        if (newMoveCount != 4):
                            oldMoveName = pokemon.moves[3]['names']['en']
                            pokemon.replaceMove(3, move)
                            await message.delete()
                            message = await inter.channel.send(
                                pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                    'en'] + "!" + " (continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await message.delete()
                    elif (chosenEmoji == '5'):
                        await message.delete()
                        message = await inter.channel.send("Gave up on learning " + move['names'][
                            'en'] + "." + " (continuing automatically in 4 seconds...)")
                        await sleep(4)
                        await message.delete()
                else:
                    pokemon.learnMove(move)
                    message = await inter.channel.send(pokemon.nickname + " learned " + move['names'][
                        'en'] + "!" + " (continuing automatically in 4 seconds...)")
                    await sleep(4)
                    await message.delete()
        battle.battleRefresh()
        if not isWin:
            battle.trainer1.pokemonCenterHeal()
        for flag in trainer.flags:
            tempFlag = flag
            if 'cutscene' in flag:
                trainer.removeFlag(flag)
                await self.startCutsceneUI(inter, tempFlag, trainer)
                return
        if (goBackTo == "startBattleTowerUI"):
            if isWin:
                if otherData[2]:
                    otherData[0].withRestrictionStreak += 1
                    if otherData[0].withRestrictionsRecord < otherData[0].withRestrictionStreak:
                        otherData[0].withRestrictionsRecord = otherData[0].withRestrictionStreak
                    # otherData[1].withRestrictionStreak += 1
                else:
                    otherData[0].noRestrictionsStreak += 1
                    if otherData[0].noRestrictionsRecord < otherData[0].noRestrictionsStreak:
                        otherData[0].noRestrictionsRecord = otherData[0].noRestrictionsStreak
                    # otherData[1].noRestrictionsStreak += 1
                await self.startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2], bpReward)
                return
            else:
                if otherData[2]:
                    otherData[0].withRestrictionStreak = 0
                else:
                    otherData[0].noRestrictionsStreak = 0
                await self.startOverworldUI(inter, otherData[0])
                return
        await self.startOverworldUI(inter, trainer)

    async def resolveTurn(self, pokemon1, pokemon2, battleText):
        if self.invertTrainers:
            tempPokemon1 = pokemon2
            tempPokemon2 = pokemon1
        else:
            tempPokemon1 = pokemon1
            tempPokemon2 = pokemon2
        self.embed.set_footer(text=self.createTextFooter(tempPokemon1, tempPokemon2, battleText))
        await self.message.edit(embed=self.embed)
        await sleep(2)
        self.embed.clear_fields()
        self.createBattleEmbedFields(self.embed, tempPokemon1, tempPokemon2)
        await self.message.edit(embed=self.embed)
        await sleep(2)

    def updatePokemon(self):
        if self.invertTrainers:
            self.trainer1 = self.battle.trainer2
            self.trainer2 = self.battle.trainer1
            self.pokemon1 = self.battle.pokemon2
            self.pokemon2 = self.battle.pokemon1
        else:
            self.trainer1 = self.battle.trainer1
            self.trainer2 = self.battle.trainer2
            self.pokemon1 = self.battle.pokemon1
            self.pokemon2 = self.battle.pokemon2

    async def updateBattleUI(self, trainer, resetToDefault=False):
        # if trainer.identifier == self.inter.author.id:
        #     return
        try:
            await self.message.delete()
        except:
            pass
        tempGoStraightToResolve = True
        self.updatePokemon()
        filename = self.mergeImages(self.pokemon1.getSpritePath(), self.pokemon2.getSpritePath(), self.trainer1.location)
        # print(self.pokemon1.name)
        # print(self.pokemon2.name)
        files, embed = self.createBattleEmbed(self.inter, self.isWild, self.pokemon1, self.pokemon2, tempGoStraightToResolve, filename, self.trainer2) #goStraight?
        self.embed = embed
        emojiNameList = []
        if not tempGoStraightToResolve:
            emojiNameList.append('1')
            emojiNameList.append('2')
            emojiNameList.append('3')
            emojiNameList.append('4')

        view = None
        if not tempGoStraightToResolve:
            view = self.createHomeView(self.inter.author)

        message = await self.inter.channel.send(files=files, embed=self.embed, view=view)

        # for emojiName in emojiNameList:
        #     await message.add_reaction(self.data.getEmoji(emojiName))

        try:
            os.remove(filename)
        except:
            pass
        self.message = message

    def recordPVPWinLoss(self, isWin, trainerCopy, inter=None):
        if inter:
            tempinter = inter
        else:
            tempinter = self.inter
        identifier = trainerCopy.identifier
        if identifier != -1:
            user = self.data.getUserById(tempinter.guild.id, identifier)
            if isWin:
                user.pvpWins += 1
            else:
                user.pvpLosses += 1

    def createHomeView(self, author):
        buttonList = []
        buttonList.append(PokeNavComponents.OverworldUIButton(label="Fight", style=discord.ButtonStyle.green, row=0,
                                                              identifier='1'))
        buttonList.append(PokeNavComponents.OverworldUIButton(label="Bag", style=discord.ButtonStyle.blurple, row=0,
                                                              identifier='2'))
        buttonList.append(PokeNavComponents.OverworldUIButton(label="Pokémon", style=discord.ButtonStyle.grey, row=0,
                                                              identifier='3'))
        run_button = PokeNavComponents.OverworldUIButton(label="Run", style=discord.ButtonStyle.red, row=0,
                                                              identifier='4')
        if not self.isWild and not self.battle.isPVP and not self.battle.isRaid:
            run_button.disabled = True
        buttonList.append(run_button)
        if self.battle.isPVP:
            tempTimeout = self.pvpTimeout
        else:
            tempTimeout = self.battleTimeout
        view = PokeNavComponents.OverworldUIView(author, buttonList, tempTimeout)
        return view

    def createNumberedView(self, author, num=4):
        buttonList = []
        for x in range(0, num):
            buttonList.append(PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji(str(x+1)), style=discord.ButtonStyle.blurple,
                                                                  identifier=str(x+1)))
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'), style=discord.ButtonStyle.grey,
                                                identifier='right arrow'))
        if self.battle.isPVP:
            tempTimeout = self.pvpTimeout
        else:
            tempTimeout = self.battleTimeout
        view = PokeNavComponents.OverworldUIView(author, buttonList, tempTimeout)
        return view

    def createMovesView(self, author, pokemon):
        buttonList = []
        count = 0
        for move in pokemon.moves:
            if count < 2:
                row = 0
            else:
                row = 1
            try:
                moveName = move['names']['en']
                moveMaxPP = str(move['pp'])
                movePP = str(pokemon.pp[count])
            except:
                moveName = 'ERROR'
                moveMaxPP = 'ERROR'
                movePP = 'ERROR'
            label = (moveName + " (" + movePP + "/" + moveMaxPP + "pp)")
            buttonList.append(PokeNavComponents.OverworldUIButton(label=label, style=discord.ButtonStyle.green, row=row,
                                                                  identifier=str(count+1)))
            count += 1
        while count < 4:
            if count < 2:
                row = 0
            else:
                row = 1
            button = PokeNavComponents.OverworldUIButton(label="---", style=discord.ButtonStyle.grey, row=row,
                                                                  identifier=str(count+1))
            button.disabled = True
            buttonList.append(button)
            count += 1
        buttonList.append(PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=1,
                                                     identifier='right arrow'))
        if self.battle.isPVP:
            tempTimeout = self.pvpTimeout
        else:
            tempTimeout = self.battleTimeout
        view = PokeNavComponents.OverworldUIView(author, buttonList, tempTimeout)
        return view
