import asyncio
import disnake as discord
import os
from PIL import Image
import logging

import PokeNavComponents


class Secret_Base_UI(object):

    def __init__(self, bot, timeout, data, startNewUI, continueUI, startOverworldUI, endSession):
        self.bot = bot
        self.timeout = timeout
        self.data = data
        self.startNewUI = startNewUI
        self.continueUI = continueUI
        self.startOverworldUI = startOverworldUI
        self.endSession = endSession
        self.baseType = "desert_2"

    def createBaseImage(self, secretBase, gridOn=False):
        basePath = secretBase.baseObj.sprite
        gridPath = 'data/sprites/base/base_areas/grid.png'
        baseImage = Image.open(basePath)
        baseImage = baseImage.convert('RGBA')
        multiplier = 16
        rowOffset = 0
        columnOffset = 0
        for (column, row), itemList in secretBase.placedItems.items():
            for item in itemList:
                # print(item.name)
                itemImage = Image.open(item.sprite)
                baseImage.paste(itemImage, (column*multiplier+columnOffset, row*multiplier+rowOffset), itemImage.convert('RGBA'))
        # print('')
        if gridOn:
            gridImage = Image.open(gridPath)
            baseImage.paste(gridImage, (0, 0), gridImage.convert('RGBA'))
        baseImage.save(secretBase.filename, "PNG")
        # baseImage.show()
        return secretBase.filename

    async def sendPreviewMessage(self, inter, item):
        embed = discord.Embed(title="Item Preview:", description=item.name, color=0x00ff00)
        file = discord.File(item.sprite, filename="image.png")
        embed.set_image(url="attachment://image.png")
        message = await inter.channel.send(embed=embed, file=file)
        return message

    def getSecretBaseUI(self, inter, trainer):
        logging.debug(str(inter.author.id) + " - viewSecretBaseUI()")
        secretBase = trainer.secretBase
        filename = self.createBaseImage(secretBase)
        files, embed = self.createSecretBaseEmbed(inter, trainer, filename, True)
        return embed, files

    async def startSecretBaseUI(self, inter, trainer, fromOverworld=True):
        logging.debug(str(inter.author.id) + " - startSecretBaseUI()")
        secretBase = trainer.secretBase
        filename = self.createBaseImage(secretBase)
        files, embed = self.createSecretBaseEmbed(inter, trainer, filename)
        emojiNameList = []
        buttonList = []
        buttonList.append(PokeNavComponents.OverworldUIButton(label="Edit", emoji=self.data.getEmoji('edit'),style=discord.ButtonStyle.red,
                                                              identifier='edit'))
        emojiNameList.append('edit')
        if fromOverworld:
            buttonList.append(PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'),
                                                                  style=discord.ButtonStyle.grey,
                                                                  identifier='right arrow'))
            emojiNameList.append('right arrow')

        chosenEmoji, message = await self.startNewUI(inter, embed, files, buttonList)
        try:
            os.remove(filename)
        except:
            pass

        while True:
            if (chosenEmoji == None and message == None):
                break
            elif (chosenEmoji == 'edit'):
                trainer.secretBase.gridOn = True
                await message.delete()
                await self.startSecretBaseEditUI(inter, trainer, fromOverworld)
                break
            elif (chosenEmoji == 'right arrow'):
                trainer.location = secretBase.location
                await message.delete()
                await self.startOverworldUI(inter, trainer)
                break
            chosenEmoji, message = await self.continueUI(inter, message, emojiNameList)

    def createSecretBaseEmbed(self, inter, trainer, filename, viewOnly=False):
        files = []
        desc = '[react to emoji to edit or leave]'
        if viewOnly:
            desc = 'Located in: ' + trainer.secretBase.location
        embed = discord.Embed(title=trainer.name + "'s Secret Base", description=desc, color=0x00ff00)
        file = discord.File(filename, filename="image.png")
        files.append(file)
        embed.set_image(url="attachment://image.png")
        if viewOnly:
            embed.set_author(name=inter.author.display_name + " requested to view a secret base:")
        else:
            embed.set_author(name=inter.author.display_name + " is exploring the world:")
        return files, embed

    def createSecretBaseEditEmbed(self, inter, trainer, filename, options):
        files = []
        embed = discord.Embed(title=trainer.name + "'s Secret Base", description="[type # or word in chat to select]", color=0x00ff00)
        file = discord.File(filename, filename="image.png")
        files.append(file)
        embed.set_image(url="attachment://image.png")
        embed.set_author(name=inter.author.display_name + " is editing their base:")
        embed = self.createOptionsField(embed, options)
        return files, embed

    def createOptionsField(self, embed, options, title="Options:"):
        optionStr = ''
        count = 1
        for option in options:
            optionStr += str(count) + ". `" + option.title() + "`\n"
            count += 1
        embed.add_field(name=title, value=optionStr, inline=False)
        return embed

    def createCategoryField(self, embed, trainer, category):
        optionStrList = ['']
        index = 0
        count = 1
        options = []
        itemList = []
        if category == "other":
            trueCategory = "custom"
        else:
            trueCategory = category
        for item, amount in trainer.secretBaseItems.items():
            itemObj = self.data.secretBaseItems[item]
            if trueCategory.lower() in itemObj.getCategory().lower():
                toAppend = str(count) + ". `" + item.title() + '`\n   (owned: ' + str(amount) + ') [H:' + str(itemObj.getHeight()) + ' | W:' + str(itemObj.getWidth()) + ']\n'
                if len(optionStrList[index] + toAppend) > 1024:
                    optionStrList.append(toAppend)
                    index += 1
                else:
                    optionStrList[index] += toAppend
                options.append(str(count))
                itemList.append(item)
                count += 1
        optionStrList[index] += str(count) + ". `Back`" + '\n'
        options.append("back")
        first = True
        for optionStr in optionStrList:
            if first:
                title = category.title()
            else:
                title = '\u200b'
            embed.add_field(name=title, value=optionStr, inline=True)
        return embed, options, itemList

    async def continueTextEntryUI(self, message, inter, options):
        if message:
            logging.debug(str(inter.author.id) + " - continueUI(), message.content = " + message.content)
        else:
            logging.debug(str(inter.author.id) + " - continueUI(), message = None")
        return await self.startNewTextEntryUI(inter, None, None, options, message)

    async def startNewTextEntryUI(self, inter, embed, files, options, message=None):
        if not message:
            message = await inter.channel.send(files=files, embed=embed)

        options = options.copy()
        for x in range(1, len(options)+1):
            options.append(str(x))

        def check(m):
            return (m.content.lower() in options or not options)\
                   and m.author.id == inter.author.id and m.channel == message.channel

        try:
            response = await self.bot.wait_for('message', timeout=self.timeout, check=check)
        except asyncio.TimeoutError:
            await message.delete()
            await self.endSession(inter)
            return None, None
        else:
            responseContent = response.content.lower()
            await response.delete()
            return responseContent, message

    async def startSecretBaseEditUI(self, inter, trainer, fromOverworld):
        logging.debug(str(inter.author.id) + " - startSecretBaseEditUI()")
        secretBase = trainer.secretBase
        filename = self.createBaseImage(secretBase, True)
        defaultOptions = ['place item', 'remove item', "exit"]
        categories = ['chair', 'cushion', 'desk', 'doll', 'plant', 'poster', 'rug', 'statue', 'other', 'back']
        itemList = []
        selectedItem = None
        options = defaultOptions
        files, embed = self.createSecretBaseEditEmbed(inter, trainer, filename, options)
        flag = 'main'
        previewMessage = None

        responseContent, message = await self.startNewTextEntryUI(inter, embed, files, options)

        try:
            os.remove(filename)
        except:
            pass

        while True:
            if responseContent == None and message == None:
                return
            if flag == 'main':
                if responseContent == '1' or responseContent == "place item":
                    flag = 'categories'
                    embed.clear_fields()
                    embed = self.createOptionsField(embed, categories, "Place Item | Categories:")
                    await message.edit(embed=embed)
                    options = categories
                elif responseContent == '2' or responseContent == "remove item":
                    flag = 'remove'
                    embed.clear_fields()
                    embed.add_field(name="Remove Item:", value="Type the coordinate of the item you want to remove. For items large than 1x1, use the coordinate of the top left most part of the item.\nExample: F7\n\nType `back` to cancel.", inline=False)
                    options = []
                    await message.edit(embed=embed)
                elif responseContent == '3' or responseContent == 'exit':
                    await message.delete()
                    await self.startSecretBaseUI(inter, trainer, fromOverworld)
                    return
            elif flag == 'categories':
                index = None
                try:
                    index = int(responseContent)-1
                except:
                    if responseContent in categories:
                        index = categories.index(responseContent)
                if isinstance(index, int) and index < len(categories):
                    if categories[index] == 'back':
                        flag = 'main'
                        options = defaultOptions
                        embed.clear_fields()
                        embed = self.createOptionsField(embed, options)
                        await message.edit(embed=embed)
                    else:
                        flag = categories[index]
                        embed.clear_fields()
                        embed, options, itemList = self.createCategoryField(embed, trainer, flag)
                        await message.edit(embed=embed)
                        options = []
            elif flag == "remove":
                if responseContent == 'back' or responseContent == 'cancel' or responseContent == 'exit':
                    flag = 'main'
                    options = defaultOptions
                    embed.clear_fields()
                    embed.set_footer(text='')
                    embed = self.createOptionsField(embed, options)
                    await message.edit(embed=embed)
                else:
                    responseContent = responseContent.replace(' ', '')
                    valid = True
                    errorMessage = 'No item in that position.'
                    try:
                        column = responseContent[0].capitalize()
                        row = int(responseContent[1:])
                    except:
                        valid = False
                        errorMessage = 'Invalid input. Please enter a valid spot on the base for items.\nExamples: F12, C4, J9'
                    if valid:
                        valid, itemName = trainer.secretBase.removeItemByLetter(column, row)
                        if valid:
                            if itemName in trainer.secretBaseItems.keys():
                                trainer.secretBaseItems[itemName] = trainer.secretBaseItems[itemName] + 1
                            else:
                                trainer.secretBaseItems[itemName] = 1
                            flag = 'main'
                            await message.delete()
                            filename = self.createBaseImage(secretBase, True)
                            itemList = []
                            selectedItem = None
                            options = defaultOptions
                            files, embed = self.createSecretBaseEditEmbed(inter, trainer, filename, options)
                            message = await inter.channel.send(embed=embed, files=files)
                    if not valid:
                        embed.set_footer(text=errorMessage)
                        await message.edit(embed=embed)
            elif flag == "place":
                if responseContent == 'back' or responseContent == 'cancel' or responseContent == 'exit':
                    try:
                        await previewMessage.delete()
                    except:
                        pass
                    flag = 'categories'
                    options = categories
                    embed.clear_fields()
                    embed.set_footer(text='')
                    embed = self.createOptionsField(embed, options, "Place Item | Categories:")
                    await message.edit(embed=embed)
                else:
                    responseContent = responseContent.replace(' ', '')
                    valid = True
                    errorMessage = ''
                    try:
                        column = responseContent[0].capitalize()
                        row = int(responseContent[1:])
                    except:
                        valid = False
                        errorMessage = 'Invalid input. Please enter a valid spot on the base for items.\nExamples: F12, C4, J9'
                    if valid:
                        valid, errorMessage = trainer.secretBase.placeItemByLetter(column, row, self.data.secretBaseItems[selectedItem])
                        if valid:
                            try:
                                await previewMessage.delete()
                            except:
                                pass
                            trainer.secretBaseItems[selectedItem] = trainer.secretBaseItems[selectedItem] - 1
                            if trainer.secretBaseItems[selectedItem] == 0:
                                del trainer.secretBaseItems[selectedItem]
                            flag = 'main'
                            await message.delete()
                            filename = self.createBaseImage(secretBase, True)
                            itemList = []
                            selectedItem = None
                            options = defaultOptions
                            files, embed = self.createSecretBaseEditEmbed(inter, trainer, filename, options)
                            message = await inter.channel.send(embed=embed, files=files)
                    if not valid:
                        embed.set_footer(text=errorMessage)
                        await message.edit(embed=embed)
            else:
                index = None
                selectedItem = None
                try:
                    index = int(responseContent) - 1
                except:
                    if responseContent in categories:
                        index = categories.index(responseContent)
                    if itemList and responseContent.title() in itemList:
                        selectedItem = responseContent.title()
                if isinstance(index, int) and itemList and index < len(itemList):
                    selectedItem = itemList[index]
                if selectedItem:
                    flag = 'place'
                    embed.clear_fields()
                    embed.add_field(name="Placing Item: " + selectedItem.title(),
                                    value="Type the coordinate of where to place. For items large than 1x1, use the coordinate of the top left most part of the item.\nExample: `F7`\n\nType `back` to cancel.",
                                    inline=False)
                    options = []
                    await message.edit(embed=embed)
                    previewMessage = await self.sendPreviewMessage(inter, self.data.secretBaseItems[selectedItem])
                if responseContent == 'back' or (isinstance(index, int) and index == len(itemList)):
                    flag = 'categories'
                    options = categories
                    embed.clear_fields()
                    embed = self.createOptionsField(embed, options, "Place Item | Categories:")
                    await message.edit(embed=embed)
            responseContent, message = await self.continueTextEntryUI(message, inter, options)
