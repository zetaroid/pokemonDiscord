import asyncio
import math

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
        embed = discord.Embed(title=trainer.name + "'s Secret Base", description="[use the drop down or buttons]", color=0x00ff00)
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

    async def startSecretBaseEditUI(self, inter, trainer, fromOverworld):
        logging.debug(str(inter.author.id) + " - startSecretBaseEditUI()")
        secretBase = trainer.secretBase
        filename = self.createBaseImage(secretBase, True)
        defaultOptions = ['place item', 'remove item', "exit"]
        categories = ['Chair', 'Cushion', 'Desk', 'Doll', 'Plant', 'Poster', 'Rug', 'Statue', 'Other']
        coordinates_X = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', "I", "J", "K", "L", 'M']
        coordinates_Y = ['1', '2', '3', '4', '5', '6', '7', '8', "9", "10", "11", "12", '13']
        selectedItem = None
        options = defaultOptions
        files, embed = self.createSecretBaseEditEmbed(inter, trainer, filename, options)
        flag = 'main'
        previewMessage = None

        componentList = []

        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Place Item", style=discord.ButtonStyle.green,
                                                identifier='place'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Remove Item", style=discord.ButtonStyle.red,
                                                identifier='remove'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Exit", style=discord.ButtonStyle.grey,
                                                identifier='exit'))

        responseContent, message = await self.startNewUI(inter, embed, files, componentList)

        try:
            os.remove(filename)
        except:
            pass

        x_coordinate = '0'
        y_coordinate = '0'
        offset = 0

        while True:
            if responseContent is None and message is None:
                return
            if flag == 'main':
                if responseContent == "place":
                    flag = 'categories'
                    embed, view = self.get_categories_ui(inter, embed, categories)
                    await message.edit(embed=embed, view=view)
                elif responseContent == "remove":
                    flag = 'remove'
                    x_coordinate = '0'
                    y_coordinate = '0'
                    embed, view = self.get_remove_ui(inter, embed, coordinates_X, coordinates_Y)
                    await message.edit(embed=embed, view=view)
                elif responseContent == 'exit':
                    await message.delete()
                    await self.startSecretBaseUI(inter, trainer, fromOverworld)
                    return
            elif flag == 'categories':
                if responseContent == "back":
                    flag = 'main'
                    embed, view = self.get_main_secret_base_ui(inter, embed)
                    await message.edit(embed=embed, view=view)
                else:
                    offset = 0
                    flag = responseContent.lower()
                    embed, view = self.get_items_ui(inter, embed, trainer, flag)
                    await message.edit(embed=embed, view=view)
            elif flag == "remove":
                if responseContent == 'back':
                    flag = 'main'
                    embed, view = self.get_main_secret_base_ui(inter, embed)
                    await message.edit(embed=embed, view=view)
                elif responseContent in coordinates_X:
                    x_coordinate = responseContent
                elif responseContent in coordinates_Y:
                    y_coordinate = responseContent
                elif responseContent == "confirm_remove":
                    valid, itemName = trainer.secretBase.removeItemByLetter(x_coordinate, y_coordinate)
                    if valid:
                        if itemName in trainer.secretBaseItems.keys():
                            trainer.secretBaseItems[itemName] = trainer.secretBaseItems[itemName] + 1
                        else:
                            trainer.secretBaseItems[itemName] = 1
                        flag = 'main'
                        await message.delete()
                        filename = self.createBaseImage(secretBase, True)
                        selectedItem = None
                        options = defaultOptions
                        files, embed = self.createSecretBaseEditEmbed(inter, trainer, filename, options)
                        embed, view = self.get_main_secret_base_ui(inter, embed)
                        message = await inter.channel.send(embed=embed, view=view, files=files)
                    else:
                        errorMessage = 'Invalid input. Please enter a valid spot on the base for items.\nExamples: F12, C4, J9'
                        embed.set_footer(text=errorMessage)
                        await message.edit(embed=embed)
            elif flag == "place":
                if responseContent == 'back':
                    try:
                        await previewMessage.delete()
                    except:
                        pass
                    flag = 'categories'
                    embed, view = self.get_categories_ui(inter, embed, categories)
                    await message.edit(embed=embed, view=view)
                elif responseContent in coordinates_X:
                    x_coordinate = responseContent
                elif responseContent in coordinates_Y:
                    y_coordinate = responseContent
                elif responseContent == "confirm_place":
                    errorMessageDefault = 'Invalid input. Please enter a valid spot on the base for items.\nExamples: F12, C4, J9'
                    valid, errorMessage = trainer.secretBase.placeItemByLetter(x_coordinate, y_coordinate,
                                                                               self.data.secretBaseItems[selectedItem])
                    if not errorMessage:
                        errorMessage = errorMessageDefault
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
                        selectedItem = None
                        files, embed = self.createSecretBaseEditEmbed(inter, trainer, filename, options)
                        embed, view = self.get_main_secret_base_ui(inter, embed)
                        message = await inter.channel.send(embed=embed, view=view, files=files)
                    else:
                        embed.set_footer(text=errorMessage)
                        await message.edit(embed=embed)
            else:
                embed, options, itemList = self.createCategoryField(embed, trainer, flag)
                maxPages = math.ceil(len(itemList) / 25)
                if responseContent == 'back':
                    flag = 'categories'
                    embed, view = self.get_categories_ui(inter, embed, categories)
                    embed.remove_footer()
                    await message.edit(embed=embed, view=view)
                elif responseContent == "left":
                    if offset == 0:
                        offset = maxPages-1
                    else:
                        offset -= 1
                    embed, view = self.get_items_ui(inter, embed, trainer, flag, offset)
                    await message.edit(embed=embed, view=view)
                elif responseContent == "right":
                    if offset == maxPages-1:
                        offset = 0
                    else:
                        offset += 1
                    embed, view = self.get_items_ui(inter, embed, trainer, flag, offset)
                    await message.edit(embed=embed, view=view)
                else:
                    flag = 'place'
                    selectedItem = responseContent
                    embed, view = self.get_place_ui(inter, embed, coordinates_X, coordinates_Y)
                    await message.edit(embed=embed, view=view)
                    previewMessage = await self.sendPreviewMessage(inter, self.data.secretBaseItems[selectedItem])
            responseContent, message = await self.continueUI(inter, message, componentList)

    def get_main_secret_base_ui(self, inter, embed):
        defaultOptions = ['place item', 'remove item', "exit"]

        embed.clear_fields()
        embed = self.createOptionsField(embed, defaultOptions)

        componentList = []
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Place Item", style=discord.ButtonStyle.green,
                                                identifier='place'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Remove Item", style=discord.ButtonStyle.red,
                                                identifier='remove'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Exit", style=discord.ButtonStyle.grey,
                                                identifier='exit'))
        view = PokeNavComponents.OverworldUIView(inter.author, componentList)
        return embed, view

    def get_categories_ui(self, inter, embed, categories):
        embed.clear_fields()
        embed = self.createOptionsField(embed, categories, "Place Item | Categories:")
        componentList = []
        select = PokeNavComponents.get_generic_select(categories, "Select category")
        componentList.append(select)
        componentList.append(
            PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'),
                                                style=discord.ButtonStyle.grey,
                                                identifier='back'))
        view = PokeNavComponents.OverworldUIView(inter.author, componentList)
        return embed, view

    def get_items_ui(self, inter, embed, trainer, flag, offset=0):
        embed.clear_fields()
        embed, options, itemList = self.createCategoryField(embed, trainer, flag)
        componentList = []
        itemListSubset = itemList[offset*25:offset*25+25]
        itemListSubsetWithNums = []
        count = 25*offset+1
        for item in itemListSubset:
            itemListSubsetWithNums.append(str(count) + ". " + item)
            count += 1
        if itemListSubset:
            select = PokeNavComponents.get_generic_select(itemListSubsetWithNums, "Select item", valueList=itemListSubset)
            componentList.append(select)
        if len(itemList) > 25:
            embed.set_footer(text="Viewing items " + str(offset*25+1) + " through " + str(offset*25+25) + ". Use the arrows to view more.")
            componentList.append(
                PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('left arrow'),
                                                    style=discord.ButtonStyle.blurple,
                                                    identifier='left'))
            componentList.append(
                PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('right arrow'),
                                                    style=discord.ButtonStyle.blurple,
                                                    identifier='right'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'),
                                                style=discord.ButtonStyle.grey,
                                                identifier='back'))
        view = PokeNavComponents.OverworldUIView(inter.author, componentList)
        return embed, view

    def get_place_ui(self, inter, embed, coordinates_X, coordinates_Y):
        embed.clear_fields()
        embed.add_field(name="Placing Item:",
                        value="Use the drop down menus to select and X and Y coordinate to place your item. For items large than 1x1, use the coordinate of the top left most part of the item.\nExample: F7\n\nClick the back arrow to cancel.",
                        inline=False)
        componentList = []
        select_X = PokeNavComponents.get_generic_select(coordinates_X, "Select X coordinate")
        select_Y = PokeNavComponents.get_generic_select(coordinates_Y, "Select Y coordinate")
        componentList.append(select_X)
        componentList.append(select_Y)
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Confirm Placement", style=discord.ButtonStyle.green,
                                                identifier='confirm_place'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'),
                                                style=discord.ButtonStyle.grey,
                                                identifier='back'))
        view = PokeNavComponents.OverworldUIView(inter.author, componentList)
        return embed, view

    def get_remove_ui(self, inter, embed, coordinates_X, coordinates_Y):
        embed.clear_fields()
        embed.add_field(name="Remove Item:",
                        value="Use the drop down menus to select and X and Y coordinate to remove your item from. For items large than 1x1, use the coordinate of the top left most part of the item.\nExample: F7\n\nClick the back arrow to cancel.",
                        inline=False)
        componentList = []
        select_X = PokeNavComponents.get_generic_select(coordinates_X, "Select X coordinate")
        select_Y = PokeNavComponents.get_generic_select(coordinates_Y, "Select Y coordinate")
        componentList.append(select_X)
        componentList.append(select_Y)
        componentList.append(
            PokeNavComponents.OverworldUIButton(label="Confirm Removal", style=discord.ButtonStyle.red,
                                                identifier='confirm_remove'))
        componentList.append(
            PokeNavComponents.OverworldUIButton(emoji=self.data.getEmoji('down arrow'),
                                                style=discord.ButtonStyle.grey,
                                                identifier='back'))
        view = PokeNavComponents.OverworldUIView(inter.author, componentList)
        return embed, view



