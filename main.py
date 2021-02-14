import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from Battle_Tower import Battle_Tower
from Data import pokeData
from Pokemon import Pokemon
from Battle import Battle
from Trainer import Trainer
from PIL import Image
from asyncio import sleep
import math
import traceback
from copy import copy
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    try:
        channel = bot.get_channel(800534600677326908)
        await channel.send('NOTICE: PokeDiscord is online and ready for use.')
    except:
        pass
    await saveLoop()

@bot.command(name='start', help='starts the game', aliases=['s'])
async def startGame(ctx):
    user, isNewUser = data.getUser(ctx)
    try:
        #print('isNewUser = ', isNewUser)
        if (user in data.getTradeDict(ctx).keys()):
            await ctx.send("You are waiting for a trade, please finish the trade or wait for it to timeout before starting a session.")
            return
        sessionSuccess = data.addUserSession(ctx.message.guild.id, user)
        updateStamina(user)
        #print('sessionSuccess = ', sessionSuccess)
        if (sessionSuccess):
            if (isNewUser or (len(user.partyPokemon) == 0 and len(user.boxPokemon) == 0)):
                await startNewUserUI(ctx, user)
            else:
                await startOverworldUI(ctx, user)
        else:
            #print('Unable to start session for: ' + str(ctx.message.author.display_name))
            await ctx.send('Unable to start session for: ' + str(ctx.message.author.display_name))
    except:
        #traceback.print_exc()
        user.dailyProgress += 1
        user.removeProgress(user.location)
        try:
            channel = bot.get_channel(800534600677326908)
            await channel.send(str(str(ctx.message.author.display_name) + "'s session ended in error.\n" + str(traceback.format_exc()))[-1999:])
        except:
            try:
                channel = bot.get_channel(797534055888715786)
                await channel.send(str(str(ctx.message.author.display_name) + "'s session ended in error.\n" + str(traceback.format_exc()))[-1999:])
            except:
                await ctx.send("An error occurred, please restart your session. If this persists, please report to an admin.")
        await endSession(ctx)

@bot.command(name='grantFlag', help='DEV ONLY: grants user flag, usage: "!grantFlag [flag, with _] [user]')
async def grantFlag(ctx, flag, *, userName: str="self"):
    flag = flag.replace("_", " ")
    if str(ctx.author) != 'Zetaroid#1391':
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
    if not isNewUser:
        user.addFlag(flag)
        await ctx.send(user.name + ' has been granted the flag: ' + flag + '.')
    else:
        await ctx.send("User '" + userName + "' not found, cannot grant flag.")

@bot.command(name='removeFlag', help='DEV ONLY: grants user flag, usage: "!removeFlag [flag, with _] [user]')
async def removeFlag(ctx, flag, *, userName: str="self"):
    flag = flag.replace("_", " ")
    if str(ctx.author) != 'Zetaroid#1391':
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
    if not isNewUser:
        user.removeFlag(flag)
        await ctx.send(user.name + ' has been revoked the flag: ' + flag + '.')
    else:
        await ctx.send("User '" + userName + "' not found, cannot revoke flag.")

@bot.command(name='grantStamina', help='ADMIN ONLY: grants user stamina in amount specified, usage: !grantStamina [amount] [user]')
async def grantStamina(ctx, amount, *, userName: str="self"):
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
        if not isNewUser:
            user.dailyProgress += amount
            await ctx.send(user.name + ' has been granted ' + str(amount) + ' stamina.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant stamina.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='grantItem', help='ADMIN ONLY: grants user item (use "_" for spaces in item name) in amount specified, usage: !grantItem [item] [amount] [user]')
async def grantItem(ctx, item, amount, *, userName: str="self"):
    item = item.replace('_', " ")
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
        if not isNewUser:
            user.addItem(item, amount)
            await ctx.send(user.name + ' has been granted ' + str(amount) + ' of ' + item + '.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant stamina.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='removeItem', help='ADMIN ONLY: removes user item (use "_" for spaces in item name) in amount specified, usage: !removeItem [item] [amount] [user]')
async def removeItem(ctx, item, amount, *, userName: str="self"):
    item = item.replace('_', " ")
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
        if not isNewUser:
            user.useItem(item, amount)
            await ctx.send(user.name + ' has been revoked ' + str(amount) + ' of ' + item + '.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant stamina.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='disableStamina', help='ADMIN ONLY: disables stamina cost server wide for all users')
async def disableStamina(ctx):
    if ctx.message.author.guild_permissions.administrator:
        data.staminaDict[str(ctx.message.guild.id)] = False
        await ctx.send("Stamina has been disabled on this server.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='enableStamina', help='ADMIN ONLY: enables stamina cost server wide for all users')
async def enableStamina(ctx):
    if ctx.message.author.guild_permissions.administrator:
        data.staminaDict[str(ctx.message.guild.id)] = True
        await ctx.send("Stamina has been enabled on this server.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='setLocation', help='ADMIN ONLY: sets a players location, usage: !setLocation [user#1234] [location]')
async def setLocation(ctx, userName, *, location):
    if ctx.message.author.guild_permissions.administrator:
        if userName == "self":
            userName = str(ctx.message.author)
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
        if not isNewUser:
            if location in user.locationProgressDict.keys():
                user.location = location
                await ctx.send(ctx.message.author.display_name + " was forcibly sent to: " + location + "!")
            else:
                await ctx.send('"' + location + '" has not been visited by user or does not exist.')
        else:
            await ctx.send("User '" + userName + "' not found (NOTE: for this command must be the Discord name with the '#').")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

def updateStamina(user):
    if (datetime.today().date() > user.date):
        if "elite4" in user.flags:
            if user.dailyProgress < 15:
                user.dailyProgress = 15
        else:
            if user.dailyProgress < 10:
                user.dailyProgress = 10
        user.date = datetime.today().date()

async def endSession(ctx):
    user, isNewUser = data.getUser(ctx)
    removedSuccessfully = data.removeUserSession(ctx.message.guild.id, user)
    if (removedSuccessfully):
        await ctx.send(ctx.message.author.display_name + "'s connection closed. Please start game again.")
    else:
        pass
        #print("Session unable to end, not in session list: " + str(ctx.message.author.display_name))

async def getUserTextEntryForTraining(ctx, prompt, embed, options, text=''):
    if text:
        embed.set_footer(text=text)
        await prompt.edit(embed=embed)

    for x in range(0, len(options)):
        options[x] = options[x].lower()

    def check(m):
        return (m.content.lower() in options or m.content.lower() == 'cancel') \
               and m.author == ctx.author and m.channel == prompt.channel

    try:
        response = await bot.wait_for('message', timeout=battleTimeout, check=check)
    except asyncio.TimeoutError:
        await prompt.delete()
        await ctx.send(str(ctx.author.display_name) + "'s training timed out. BP refunded. Please try again.")
        return ''
    else:
        responseContent = response.content
        try:
            await response.delete()
        except:
            pass
        if response.content.lower() == 'cancel':
            await prompt.delete()
            await ctx.send(str(ctx.author.display_name) + "'s training session cancelled. BP refunded.")
            return ''
        else:
            return response.content.lower()

@bot.command(name='getStamina', help='trade 2000 Pokedollars for 1 stamina', aliases=['gs'])
async def getStamina(ctx, amount: str="1"):
    try:
        amount = int(amount)
    except:
        await ctx.send("Invalid stamina amount.")
        return
    user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.message.author)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if not data.staminaDict[str(ctx.message.guild.id)]:
            await ctx.send("Stamina is not enabled on this server.")
            return
        updateStamina(user)
        if 'money' in user.itemList.keys():
            totalMoney = user.itemList['money']
            if totalMoney >= 2000*amount:
                user.useItem('money', 2000*amount)
                user.dailyProgress += amount
                await ctx.send("Congratulations " + ctx.message.author.display_name + "! You gained " + str(amount) + " stamina (at the cost of $" + str(2000*amount) + " mwahahaha).")
            else:
                await ctx.send("Sorry " + ctx.message.author.display_name + ", but you need at least $" + str(2000*amount) + " to trade for " + str(amount) + " stamina.")

@bot.command(name='nickname', help='nickname a Pokemon, use: "!nickname [party position] [nickname]"', aliases=['nn'])
async def nickname(ctx, partyPos, *, nickname):
    partyPos = int(partyPos) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > partyPos):
            await ctx.send(user.partyPokemon[partyPos].nickname + " was renamed to '" + nickname + "'!")
            user.partyPokemon[partyPos].nickname = nickname
        else:
            await ctx.send("No Pokemon in that party slot.")

@bot.command(name='swapMoves', help="swap two of a Pokemon's moves, use: '!swapMoves [party position] [move slot 1] [move slot 2]'", aliases=['sm'])
async def swapMoves(ctx, partyPos, moveSlot1, moveSlot2):
    partyPos = int(partyPos) - 1
    moveSlot1 = int(moveSlot1) - 1
    moveSlot2 = int(moveSlot2) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > partyPos):
            pokemon = user.partyPokemon[partyPos]
            if (len(pokemon.moves) > moveSlot1 and len(pokemon.moves) > moveSlot2):
                await ctx.send(pokemon.nickname + " had '" + pokemon.moves[moveSlot1]['names']['en'] + "' swapped with '" + pokemon.moves[moveSlot2]['names']['en'] + "'!")
                move1 = pokemon.moves[moveSlot1]
                move2 = pokemon.moves[moveSlot2]
                pp1 = pokemon.pp[moveSlot1]
                pp2 = pokemon.pp[moveSlot2]
                pokemon.moves[moveSlot1] = move2
                pokemon.moves[moveSlot2] = move1
                pokemon.pp[moveSlot1] = pp2
                pokemon.pp[moveSlot2] = pp1
            else:
                await ctx.send("Invalid move slots.")
        else:
            await ctx.send("No Pokemon in that party slot.")

@bot.command(name='battleTrainer', help="battle an NPC of another trainer, use: '!battleTrainer [trainer name]'")
async def battleTrainer(ctx, *, trainerName: str="self"):
    user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.message.author)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if user in data.getSessionList(ctx):
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot battle another player while in an active session. Please wait up to 2 minutes for session to expire.")
        else:
            if trainerName == 'self':
                await ctx.send("Must input a user to battle.")
            else:
                userToBattle, isNewUser = data.getUserByAuthor(ctx.message.guild.id, trainerName)
                if not isNewUser:
                    if user.author != userToBattle.author:
                        userToBattle = copy(userToBattle)
                        user = copy(user)
                        userToBattle.pokemonCenterHeal()
                        user.pokemonCenterHeal()
                        user.location = 'Petalburg Gym'
                        user.itemList.clear()
                        battle = Battle(data, user, userToBattle)
                        battle.startBattle()
                        await startBeforeTrainerBattleUI(ctx, False, battle, "PVP")
                    else:
                        await ctx.send("Cannot battle yourself.")
                else:
                    await ctx.send("User '" + trainerName + "' not found.")

@bot.command(name='fly', help="fly to a visited location, use: '!fly [location name]'", aliases=['f'])
async def fly(ctx, *, location: str=""):
    user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.message.author)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if 'fly' in user.flags:
            elite4Areas = ['Elite 4 Room 1', 'Elite 4 Room 2', 'Elite 4 Room 3', 'Elite 4 Room 4', 'Champion Room',
                           'Elite 4 Room 1 Lv70', 'Elite 4 Room 2 Lv70', 'Elite 4 Room 3 Lv70', 'Elite 4 Room 4 Lv70',
                           'Champion Room Lv70',
                           'Elite 4 Room 1 Lv100', 'Elite 4 Room 2 Lv100', 'Elite 4 Room 3 Lv100',
                           'Elite 4 Room 4 Lv100', 'Champion Room Lv100']
            if user in data.getSessionList(ctx):
                await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot fly while in an active session. Please wait up to 2 minutes for session to expire.")
            else:
                if location in user.locationProgressDict.keys():
                    if location in elite4Areas:
                        await ctx.send("Sorry, cannot fly to the elite 4 battle areas!")
                    elif user.location in elite4Areas:
                        await ctx.send("Sorry, cannot fly while taking on the elite 4!")
                    else:
                        user.location = location
                        await ctx.send(ctx.message.author.display_name + " used Fly! Traveled to: " + location + "!")
                else:
                    embed = discord.Embed(title="Invalid location. Please try again with one of the following (exactly as spelled and capitalized):\n\n" + user.name + "'s Available Locations",
                                          description="\n(try !fly again with '!fly [location]' from this list)", color=0x00ff00)
                    totalLength = 0
                    locationString = ''
                    for location in user.locationProgressDict.keys():
                        if location in elite4Areas:
                            continue
                        if totalLength + len(location) > 1024:
                            embed.add_field(name='Locations:',
                                            value=locationString,
                                            inline=True)
                            locationString = ''
                        locationString += location + '\n'
                        totalLength = len(locationString)
                    embed.add_field(name='Locations:',
                                    value=locationString,
                                    inline=True)
                    await ctx.send(embed=embed)
        else:
            await ctx.send("Sorry, " + ctx.message.author.display_name + ", but you have not learned how to Fly yet!")

@bot.command(name='profile', help="get a Trainer's profile, use: '!profile [trainer name]'", aliases=['p'])
async def profile(ctx, *, userName: str="self"):
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName)
    if not isNewUser:
        embed = createProfileEmbed(ctx, user)
        await ctx.send(embed=embed)
    else:
        await ctx.send("User '" + userName + "' not found.")

@bot.command(name='map', help="shows the map")
async def showMap(ctx):
    files = []
    embed = discord.Embed(title="Hoenn Map",
                          description="For your viewing pleasure.",
                          color=0x00ff00)
    file = discord.File("data/sprites/map.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    await ctx.send(embed=embed, files=files)

@bot.command(name='trade', help="trade with another user, use: '!trade [your party number to trade] [trainer name to trade with]'", aliases=['t'])
async def trade(ctx, partyNum, *, userName):
    partyNum = int(partyNum)
    userToTradeWith, isNewUser1 = data.getUserByAuthor(ctx.message.guild.id, userName)
    userTrading, isNewUser2 = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
    if isNewUser1:
        await ctx.send("User '" + userName + "' not found.")
    elif isNewUser2:
        await ctx.send("You are not yet a trainer! Use '!start' to begin your adventure.")
    elif (len(userTrading.partyPokemon) < partyNum):
        await ctx.send("No Pokemon in that party slot.")
    elif (userTrading in data.getTradeDict(ctx).keys()):
        await ctx.send("You are already waiting for a trade.")
    elif (userTrading in data.getSessionList(ctx)):
        await ctx.send("Please wait up to 2 minutes for your active session to end before trading.")
    elif (userTrading == userToTradeWith):
        await ctx.send("You cannot trade with yourself!")
    else:
        pokemonToTrade = userTrading.partyPokemon[partyNum-1]
        if userToTradeWith in data.getTradeDict(ctx).keys():
            if (data.getTradeDict(ctx)[userToTradeWith][0] == userTrading):
                data.getTradeDict(ctx)[userTrading] = (userToTradeWith, pokemonToTrade, partyNum, None)
                await confirmTrade(ctx, userTrading, pokemonToTrade, partyNum, userToTradeWith,
                                   data.getTradeDict(ctx)[userToTradeWith][1], data.getTradeDict(ctx)[userToTradeWith][2], data.getTradeDict(ctx)[userToTradeWith][3])
                return
        awaitingMessage = await ctx.send("Awaiting " + userName + " to initiate trade with you.\nYou are trading: " + pokemonToTrade.name)
        data.getTradeDict(ctx)[userTrading] = (userToTradeWith, pokemonToTrade, partyNum, awaitingMessage)
        def check(m):
            return ('!trade' in m.content.lower()
                    and (str(ctx.author).lower() in m.content.lower() or str(ctx.author.display_name).lower() in m.content.lower())
                    and (str(m.author).lower() == userName.lower() or str(m.author.display_name).lower() == userName.lower()))

        async def waitForMessage(ctx):
            try:
                msg = await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                try:
                    await awaitingMessage.delete()
                    expiredMessage = await ctx.send('Trade offer from ' + ctx.author.display_name + " timed out.")
                except:
                    pass
                try:
                    del data.getTradeDict(ctx)[userTrading]
                except:
                    pass

        await waitForMessage(ctx)

async def confirmTrade(ctx, user1, pokemonFromUser1, partyNum1, user2, pokemonFromUser2, partyNum2, awaitingMessage):
    await awaitingMessage.delete()
    message = await ctx.send("TRADE CONFIRMATION:\n" + user1.name + " and " + user2.name + " please confirm or deny trade with reaction below.\n\n" +
             user1.name + " will receive: " + pokemonFromUser2.name + "\nand\n" +
             user2.name + " will receive: " + pokemonFromUser1.name)
    messageID = message.id
    await message.add_reaction(data.getEmoji('confirm'))
    await message.add_reaction(data.getEmoji('cancel'))

    confirmedList = []

    def check(reaction, user):
        return ((str(user) == str(user1.author) or str(user) == str(user2.author)) and (
                    str(reaction.emoji) == data.getEmoji('confirm') or str(reaction.emoji) == data.getEmoji('cancel')))

    async def waitForEmoji(ctx, confirmedList):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message.delete()
            expiredMessage = await ctx.send('Trade between ' + str(user1.name) + ' and ' + str(user2.name) + " timed out.")
            if user1 in data.getTradeDict(ctx).keys():
                del data.getTradeDict(ctx)[user1]
            if user2 in data.getTradeDict(ctx).keys():
                del data.getTradeDict(ctx)[user2]
        else:
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('confirm')):
                    if str(user) == str(user1.author) and str(user1.author) not in confirmedList:
                        confirmedList.append(user1.author)
                    elif str(user) == str(user2.author)and str(user2.author) not in confirmedList:
                        confirmedList.append(user2.author)
                    if (user1.author in confirmedList and user2.author in confirmedList):
                        await message.delete()
                        tradeMessage = await ctx.send(pokemonFromUser1.name + " was sent to " + user2.name + "!"
                                                      + "\nand\n" + pokemonFromUser2.name + " was sent to " + user1.name + "!")
                        user1.partyPokemon[partyNum1-1] = pokemonFromUser2
                        user2.partyPokemon[partyNum2-1] = pokemonFromUser1
                        if user1 in data.getTradeDict(ctx).keys():
                            del data.getTradeDict(ctx)[user1]
                        if user2 in data.getTradeDict(ctx).keys():
                            del data.getTradeDict(ctx)[user2]
                        return
                elif (str(reaction.emoji) == data.getEmoji('cancel')):
                    await message.delete()
                    cancelMessage = await ctx.send(str(user) + " cancelled trade.")
                    if user1 in data.getTradeDict(ctx).keys():
                        del data.getTradeDict(ctx)[user1]
                    if user2 in data.getTradeDict(ctx).keys():
                        del data.getTradeDict(ctx)[user2]
                    return
                await waitForEmoji(ctx, confirmedList)

    await waitForEmoji(ctx, confirmedList)

@bot.command(name='guide', help='helpful guide', aliases=['g'])
async def getGuide(ctx):
    await ctx.send('Check out our guide here:\nhttps://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md')

@bot.command(name='moveInfo', help='get information about a move', aliases=['mi'])
async def getMoveInfo(ctx, *, moveName="Invalid"):
    try:
        moveData = data.getMoveData(moveName.lower())
    except:
        moveData = None
    if moveData is not None:
        moveName = moveData['names']['en']
        movePower = moveData['power']
        movePP = moveData['pp']
        moveAcc = moveData['accuracy']
        moveType = moveData['type']
        try:
            moveDesc = moveData['pokedex_entries']['Emerald']['en']
        except:
            try:
                moveDesc = moveData['pokedex_entries']['Sun']['en']
            except:
                moveDesc = 'No description'
        result = 'Name: ' + moveName + '\nPower: ' + str(movePower) + '\nPP: ' + str(movePP) + '\nAccuracy: ' + str(moveAcc) + '\nType: ' + moveType + '\nDescription: ' + moveDesc
        await ctx.send(result)
    else:
        await ctx.send('Invalid move')

@bot.command(name='evolve', help="evolves a Pokemon capable of evolution, use: '!evolve [party number]'")
async def forceEvolve(ctx, partyPos):
    partyPos = int(partyPos) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > partyPos):
            oldName = user.partyPokemon[partyPos].nickname
            success = user.partyPokemon[partyPos].forceEvolve()
            if success:
                await ctx.send(oldName + " evolved into '" + user.partyPokemon[partyPos].name + "'!")
            else:
                await ctx.send("'" + user.partyPokemon[partyPos].name + "' cannot evolve.")
        else:
            await ctx.send("No Pokemon in that party slot.")

@bot.command(name='unevolve', help="unevolves a Pokemon, use: '!unevolve [party number]'")
async def unevolve(ctx, partyPos):
    partyPos = int(partyPos) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > partyPos):
            oldName = user.partyPokemon[partyPos].nickname
            success = user.partyPokemon[partyPos].unevolve()
            if success:
                await ctx.send(oldName + " was reverted to '" + user.partyPokemon[partyPos].name + "'!")
            else:
                await ctx.send("'" + user.partyPokemon[partyPos].name + "' cannot unevolve.")
        else:
            await ctx.send("No Pokemon in that party slot.")

@bot.command(name='save', help='DEV ONLY: saves data, automatically disables bot auto save (add flag "enable" to reenable)')
async def saveCommand(ctx, flag = "disable"):
    global allowSave
    global saveLoopActive
    if str(ctx.author) != 'Zetaroid#1391':
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if flag == 'enable':
        if allowSave:
            await ctx.send("Not saving data. Auto save is currently enabled, please disable to manually save.")
            return
        else:
            data.writeUsersToJSON()
            await sleep(5)
            if saveLoopActive:
                count = 0
                while count <= 120:
                    await ctx.send("Save loop already active but autoSave=False edge case...waiting for 30 seconds and trying again...")
                    await sleep(30)
                    count += 30
                    if not saveLoopActive:
                        break
                if saveLoopActive:
                    await ctx.send("Unable to start autosave.")
                    return
                else:
                    allowSave = True
                    await ctx.send("Data saved.\nautoSave = " + str(allowSave))
                    await saveLoop()
            else:
                allowSave = True
                await ctx.send("Data saved.\nautoSave = " + str(allowSave))
                await saveLoop()
            return
    elif flag == 'disable':
        allowSave = False
        await sleep(5)
        data.writeUsersToJSON()
    await ctx.send("Data saved.\nautoSave = " + str(allowSave))

@bot.command(name='saveStatus', help='DEV ONLY: check status of autosave')
async def getSaveStatus(ctx):
    global allowSave
    if str(ctx.author) != 'Zetaroid#1391':
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    await ctx.send("autoSave = " + str(allowSave))

@bot.command(name='testWorld', help='DEV ONLY: testWorld')
async def testWorldCommand(ctx):
    if str(ctx.author) != 'Zetaroid#1391':
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    location = "Test"
    progress = 0
    pokemonPairDict = {
        "Swampert": 100
    }
    movesPokemon1 = [
        "Protect",
        "Recover",
        "Earthquake",
        "Surf"
    ]
    flagList = ["rival1", "badge1", "badge2", "badge4", "briney"]
    trainer = Trainer("Zetaroid", "Marcus", location)
    trainer.addItem("Masterball", 1)
    for pokemon, level in pokemonPairDict.items():
        trainer.addPokemon(Pokemon(data, pokemon, level), True)
    if len(movesPokemon1) > 0 and len(trainer.partyPokemon) > 0:
        moves = data.convertMoveList(movesPokemon1)
        trainer.partyPokemon[0].setMoves(moves)
    for flag in flagList:
        trainer.addFlag(flag)
    for x in range(0, progress):
        trainer.progress(location)
    await startOverworldUI(ctx, trainer)

async def startPokemonSummaryUI(ctx, trainer, partyPos, goBackTo='', battle=None, otherData=None, isFromBox=False, swapToBox=False):
    if not isFromBox:
        pokemon = trainer.partyPokemon[partyPos]
    else:
        pokemon = trainer.boxPokemon[partyPos]
    files, embed = createPokemonSummaryEmbed(ctx, pokemon)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    if (swapToBox):
        await message.add_reaction(data.getEmoji('box'))
    else:
        await message.add_reaction(data.getEmoji('swap'))
    await message.add_reaction(data.getEmoji('right arrow'))
        
    def check(reaction, user):
        return (user == ctx.message.author and (str(reaction.emoji) == data.getEmoji('right arrow') or str(reaction.emoji) == data.getEmoji('swap')
                or str(reaction.emoji) == data.getEmoji('box')))
    
    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')):
                    await message.delete()
                    if (goBackTo == 'startPartyUI'):
                        await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    elif (goBackTo == 'startBoxUI'):
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                elif (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('box') and swapToBox): #HERE
                    if (len(trainer.partyPokemon) > 1):
                        await message.delete()
                        confirmation = await ctx.send(pokemon.nickname + " sent to box! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.movePokemonPartyToBox(partyPos)
                        await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False, False, None, True, None, False)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx)
                elif (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('swap') and not swapToBox):
                    alreadyInBattle = False
                    if (battle is not None):
                        if (battle.pokemon1 == pokemon):
                            alreadyInBattle = True
                    if (goBackTo == 'startBoxUI'):
                        await message.delete()
                        if (len(trainer.partyPokemon) < 6):
                            confirmation = await ctx.send(trainer.boxPokemon[partyPos].nickname + " added to party! (continuing in 4 seconds...)")
                            await sleep(4)
                            await confirmation.delete()
                            trainer.movePokemonBoxToParty(partyPos)
                            await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        else:
                            await startPartyUI(ctx, trainer, 'startBoxUI', None, otherData, False, True, partyPos)
                    elif ('faint' not in pokemon.statusList and not alreadyInBattle):
                        await message.delete()
                        if (goBackTo == 'startPartyUI'):
                            if (battle is not None):
                                swappingFromFaint = ('faint' in battle.pokemon1.statusList)
                                battle.swapCommand(trainer, partyPos)
                                if swappingFromFaint:
                                    await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], True, False, None, False, None, True)
                                else:
                                    await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], True)
                            else:
                                trainer.swapPartyPokemon(partyPos)
                                await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)
    await waitForEmoji(ctx) 

def createPokemonSummaryEmbed(ctx, pokemon):
    files = []
    title = ''
    if (pokemon.name == pokemon.nickname):
        title = pokemon.name
    else:
        title = pokemon.nickname + " (" + pokemon.name + ")"
    if (pokemon.shiny):
        title = title + ' :star2:'
    typeString = ''
    for pokeType in pokemon.getType():
        if typeString:
            typeString = typeString + ", "
        typeString = typeString + pokeType
    hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
    levelString = "Level: " + str(pokemon.level)
    genderString = "Gender: " + pokemon.gender.capitalize()
    otString = "OT: " + pokemon.OT
    dexString = "Dex #: " + str(pokemon.getFullData()['hoenn_id'])
    natureString = "Nature: " + pokemon.nature.capitalize()
    embed = discord.Embed(title=title, description="Type: " + typeString + "\n" + hpString + "\n" + levelString + "\n" + natureString + "\n" + genderString + "\n" + otString + "\n" + dexString, color=0x00ff00)
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
    statusText = ''
    for status in pokemon.statusList:
        statusText = statusText + data.getStatusEmoji(status)
    if not statusText:
        statusText = "None"
    #embed.add_field(name='---Level---', value=str(pokemon.level), inline=True)
    #embed.add_field(name='-----OT-----', value=pokemon.OT, inline=True)
    #embed.add_field(name='---Dex Num---', value=pokemon.getFullData()['hoenn_id'], inline=True)
    #embed.add_field(name='---Nature---', value=pokemon.nature.capitalize(), inline=True)
    embed.add_field(name='---Status---', value=statusText, inline=True)
    embed.add_field(name='---EXP---', value=("Total: " + str(pokemon.exp) + "\nTo next level: " + str(pokemon.calculateExpToNextLevel())), inline=True)
    embed.add_field(name="----Stats----", value=("HP:" + str(pokemon.hp) + "\nATK: " + str(pokemon.attack) + "\nDEF: " + str(pokemon.defense) + "\nSP ATK: " + str(pokemon.special_attack) + "\nSP DEF: " + str(pokemon.special_defense) + "\nSPD: " + str(pokemon.speed)), inline=True)
    embed.add_field(name="-----IV's-----", value=("HP:" + str(pokemon.hpIV) + "\nATK: " + str(pokemon.atkIV) + "\nDEF: " + str(pokemon.defIV) + "\nSP ATK: " + str(pokemon.spAtkIV) + "\nSP DEF: " + str(pokemon.spDefIV) + "\nSPD: " + str(pokemon.spdIV)), inline=True)
    embed.add_field(name="-----EV's-----", value=("HP:" + str(pokemon.hpEV) + "\nATK: " + str(pokemon.atkEV) + "\nDEF: " + str(pokemon.defEV) + "\nSP ATK: " + str(pokemon.spAtkEV) + "\nSP DEF: " + str(pokemon.spDefEV) + "\nSPD: " + str(pokemon.spdEV)), inline=True)
    count = 0
    for move in pokemon.moves:
        physicalSpecialEmoji = ''
        bp = '\nBP: '
        if (move['category'].lower() == 'physical'):
            physicalSpecialEmoji = data.getEmoji('physical')
            bp = bp + str(move['power'])
        elif (move['category'].lower() == 'special'):
            physicalSpecialEmoji = data.getEmoji('special')
            bp = bp + str(move['power'])
        else:
            physicalSpecialEmoji = data.getEmoji('no damage')
        if (bp == '\nBP: 0' or bp == '\nBP: '):
                bp = ''
        embed.add_field(name=('-----Move ' + str(count+1) + '-----'), value=(move['names']['en'] + "\n" + move['type'] + " " + physicalSpecialEmoji + bp + "\n" + str(pokemon.pp[count]) + "/" + str(move['pp']) + " pp"), inline=True)
        count += 1
    embed.set_author(name=(ctx.message.author.display_name + "'s Pokemon Summary:"))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image2.png")
    return files, embed

async def startPartyUI(ctx, trainer, goBackTo='', battle=None, otherData=None, goStraightToBattle=False, isBoxSwap=False,
                       boxIndexToSwap=None, swapToBox=False, itemToUse=None, isFromFaint=False):
    if (goStraightToBattle):
        if (goBackTo == 'startBattleUI'):
            if isFromFaint:
                await startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False)
            else:
                await startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], True)
            return
    files, embed = createPartyUIEmbed(ctx, trainer, isBoxSwap, itemToUse)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    count = 1
    for pokemon in trainer.partyPokemon:
        await message.add_reaction(data.getEmoji(str(count)))
        count += 1
    await message.add_reaction(data.getEmoji('right arrow'))
        
    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')))
    
    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer, goBackTo, battle, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(trainer.partyPokemon) >= 1):
                    if isBoxSwap:
                        await message.delete()
                        confirmation = await ctx.send(trainer.partyPokemon[0].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(0, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[0]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                battle.sendUseItemCommand(itemToUse, pokemonForItem)
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                await sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            elif (goBackTo == "startBattleTowerUI"):
                                await message.delete()
                                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        else:
                            embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)
                            await waitForEmoji(ctx)
                    else:
                        await message.delete()
                        await startPokemonSummaryUI(ctx, trainer, 0, 'startPartyUI', battle, dataTuple, False, swapToBox)
                        return
                elif (str(reaction.emoji) == data.getEmoji('2') and len(trainer.partyPokemon) >= 2):
                    if isBoxSwap:
                        await message.delete()
                        confirmation = await ctx.send(trainer.partyPokemon[1].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(1, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[1]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        #print(itemCanBeUsed)
                        if (itemCanBeUsed):
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                battle.sendUseItemCommand(itemToUse, pokemonForItem)
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                await sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            elif (goBackTo == "startBattleTowerUI"):
                                await message.delete()
                                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        else:
                            embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)
                            await waitForEmoji(ctx)
                    else:
                        await message.delete()
                        await startPokemonSummaryUI(ctx, trainer, 1, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('3') and len(trainer.partyPokemon) >= 3):
                    if isBoxSwap:
                        await message.delete()
                        confirmation = await ctx.send(trainer.partyPokemon[2].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(2, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[2]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                battle.sendUseItemCommand(itemToUse, pokemonForItem)
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                await sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            elif (goBackTo == "startBattleTowerUI"):
                                await message.delete()
                                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        else:
                            embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)
                            await waitForEmoji(ctx)
                    else:
                        await message.delete()
                        await startPokemonSummaryUI(ctx, trainer, 2, 'startPartyUI', battle, dataTuple, False, swapToBox)
                        return
                elif (str(reaction.emoji) == data.getEmoji('4') and len(trainer.partyPokemon) >= 4):
                    if isBoxSwap:
                        await message.delete()
                        confirmation = await ctx.send(trainer.partyPokemon[3].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(3, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[3]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                battle.sendUseItemCommand(itemToUse, pokemonForItem)
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                await sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            elif (goBackTo == "startBattleTowerUI"):
                                await message.delete()
                                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        else:
                            embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)
                            await waitForEmoji(ctx)
                    else:
                        await message.delete()
                        await startPokemonSummaryUI(ctx, trainer, 3, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('5') and len(trainer.partyPokemon) >= 5):
                    if isBoxSwap:
                        await message.delete()
                        confirmation = await ctx.send(trainer.partyPokemon[4].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(4, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[4]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                battle.sendUseItemCommand(itemToUse, pokemonForItem)
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                await sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            elif (goBackTo == "startBattleTowerUI"):
                                await message.delete()
                                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        else:
                            embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)
                            await waitForEmoji(ctx)
                    else:
                        await message.delete()
                        await startPokemonSummaryUI(ctx, trainer, 4, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('6') and len(trainer.partyPokemon) >= 6):
                    if isBoxSwap:
                        await message.delete()
                        confirmation = await ctx.send(trainer.partyPokemon[5].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(5, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[5]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                battle.sendUseItemCommand(itemToUse, pokemonForItem)
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                await sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            elif (goBackTo == "startBattleTowerUI"):
                                await message.delete()
                                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        else:
                            embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)
                            await waitForEmoji(ctx)
                    else:
                        await message.delete()
                        await startPokemonSummaryUI(ctx, trainer, 5, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        await message.delete()
                        await startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    elif (goBackTo == 'startBoxUI'):
                        await message.delete()
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    elif (goBackTo == 'startOverworldUI'):
                        await message.delete()
                        await startOverworldUI(ctx, otherData[0])
                    elif (goBackTo == 'startBagUI'):
                        await message.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        return
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)
    await waitForEmoji(ctx)

def createPartyUIEmbed(ctx, trainer, isBoxSwap=False, itemToUse=None, replacementTitle=None, replacementDesc=None):
    files = []
    if replacementDesc is not None and replacementTitle is not None:
        embed = discord.Embed(title=replacementTitle, description=replacementDesc, color=0x00ff00)
    elif isBoxSwap:
        embed = discord.Embed(title="CHOOSE POKEMON TO SEND TO BOX:", description="[react to # to choose Pokemon to send to box]", color=0x00ff00)
    elif (itemToUse is not None):
        embed = discord.Embed(title="CHOOSE POKEMON TO USE " + itemToUse.upper() + " ON:", description="[react to # to use item on Pokemon]", color=0x00ff00)
    else:
        embed = discord.Embed(title="Party Summary", description="[react to # to view individual summary]", color=0x00ff00)
    count = 1
    for pokemon in trainer.partyPokemon:
        hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
        levelString = "Level: " + str(pokemon.level)
        embedValue = levelString + "\n" + hpString
        statusText = ''
        for status in pokemon.statusList:
            statusText = statusText + data.getStatusEmoji(status) + " "
        if not statusText:
            statusText = 'None'
        embedValue = embedValue + "\nStatus: " + statusText
        shinyString = ""
        if pokemon.shiny:
            shinyString = " :star2:"
        embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")" + shinyString, value=embedValue, inline=True)
        count += 1
    embed.set_author(name=(ctx.message.author.display_name))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image.png")
    return files, embed

async def startBattleUI(ctx, isWild, battle, goBackTo='', otherData=None, goStraightToResolve=False):
    pokemon1 = battle.pokemon1
    pokemon2 = battle.pokemon2
    isMoveUI = False
    isItemUI1 = False
    isItemUI2 = False
    mergeImages(pokemon1.getSpritePath(), pokemon2.getSpritePath(), battle.trainer1.location)
    files, embed = createBattleEmbed(ctx, isWild, pokemon1, pokemon2, goStraightToResolve)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    if not goStraightToResolve:
        await message.add_reaction(data.getEmoji('1'))
        await message.add_reaction(data.getEmoji('2'))
        await message.add_reaction(data.getEmoji('3'))
        await message.add_reaction(data.getEmoji('4'))
    
    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')))     
        
    async def waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2, category=""):
        if (goStraightToResolve):
            await message.clear_reactions()
            battle.addEndOfTurnCommands()
            battle.createCommandsList()
            for command in battle.commands:
                battleText = battle.resolveCommand(command)
                #("battleText: ", battleText)
                if (battleText != ''):
                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, battleText))
                    await message.edit(embed=embed)
                    await sleep(2)
                    embed.clear_fields()
                    createBattleEmbedFields(embed, pokemon1, pokemon2)
                    await message.edit(embed=embed)
                    await sleep(2)
            goStraightToResolve = False # shadows outer scope?
            battle.clearCommands()
            displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted = battle.endTurn()
            #embed.clear_fields()
            #createBattleEmbedFields(embed, pokemon1, pokemon2)
            #await message.edit(embed=embed)
            if (displayText != ''):
                embed.set_footer(text=createTextFooter(pokemon1, pokemon2, displayText))
                await message.edit(embed=embed)
                await sleep(6)
            if shouldBattleEnd:
                pokemonToEvolveList, pokemonToLearnMovesList = battle.endBattle()
                if (isWin):
                    rewardText = ''
                    if (battle.trainer2 is not None):
                        for rewardName, rewardValue in battle.trainer2.rewards.items():
                            if (rewardName == "flag"):
                                battle.trainer1.addFlag(rewardValue)
                            else:
                                if not rewardName:
                                    rewardName = 'ERROR'
                                rewardText = rewardText + "\n" + rewardName[0].capitalize() + rewardName[1:] + ": " + str(rewardValue)
                                #print("giving " + battle.trainer1.name + " " + rewardName + "x" + str(rewardValue))
                                battle.trainer1.addItem(rewardName, rewardValue)
                        for flagName in battle.trainer2.rewardFlags:
                            battle.trainer1.addFlag(flagName)
                        for flagName in battle.trainer2.rewardRemoveFlag:
                            battle.trainer1.removeFlag(flagName)
                    if rewardText:
                        rewardText = "Rewards:" + rewardText + "\n\n(returning to overworld in 4 seconds...)"
                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, rewardText))
                        await message.edit(embed=embed)
                        await sleep(4)
                    await message.delete()
                else:
                    await message.delete()
                    battle.trainer1.removeProgress(battle.trainer1.location)
                    battle.trainer1.location = battle.trainer1.lastCenter
                    battle.trainer1.pokemonCenterHeal()
                await afterBattleCleanup(ctx, battle, pokemonToEvolveList, pokemonToLearnMovesList, isWin, goBackTo, otherData)
                return
            elif isUserFainted:
                dataTuple = (isWild, battle, goBackTo, otherData)
                await message.delete()
                await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple)
                return
            elif isOpponentFainted:
                if (battle.trainer2 is not None):
                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, battle.trainer2.name + " sent out " + battle.pokemon2.name + "!"))
                    await message.edit(embed=embed)
                    await sleep(3)
                await message.delete()
                await startBattleUI(ctx, isWild, battle, goBackTo, otherData, goStraightToResolve)
                return
            #print('setting battle footer after combat')
            embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
            await message.edit(embed=embed)
            await message.add_reaction(data.getEmoji('1'))
            await message.add_reaction(data.getEmoji('2'))
            await message.add_reaction(data.getEmoji('3'))
            await message.add_reaction(data.getEmoji('4'))
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=battleTimeout, check=check)
        except asyncio.TimeoutError:
            battle.trainer1.removeProgress(battle.trainer1.location)
            await endSession(ctx)
        else:
            dataTuple = (isWild, battle, goBackTo, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        isMoveUI = True
                        response = 'Fight'
                        embed.set_footer(text=createMoveFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await message.add_reaction(data.getEmoji('right arrow'))
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 0):
                            if(pokemon1.pp[0] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(0)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[0])
                        await message.remove_reaction(reaction, user)
                    elif isItemUI1:
                        category = "Balls"
                        isItemUI1 = False
                        isItemUI2 = True
                        items = getBattleItems(category, battle)
                        embed.set_footer(text=createItemFooter(pokemon1, pokemon2, category, items, battle.trainer1))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                    elif isItemUI2:
                        items = getBattleItems(category, battle)
                        if (len(items) > 0):
                            item = items[0]
                            if (category == "Balls"):
                                if (isWild):
                                    await message.clear_reactions()
                                    ball = item
                                    battle.trainer1.useItem(ball, 1)
                                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, "Go " + ball + "!"))
                                    await message.edit(embed=embed)
                                    await sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            await sleep(2)
                                        if not caught:
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2)
                                            await message.edit(embed=embed)
                                    if (shakes == 0):
                                        failText = "Oh no! The Pokemon broke free!"
                                    elif (shakes == 1):
                                        failText = "Aww! It appeared to be caught!"
                                    elif (shakes == 2):
                                        failText = "Aargh! Almost had it!"
                                    elif (shakes == 3):
                                        failText = "Shoot! It was so close, too!"
                                    if (caught):
                                        footerText = "Gotcha! " + battle.pokemon2.name + " was caught!"
                                        if (sentToBox):
                                            footerText = footerText + "\nSent to box!"
                                        else:
                                            footerText = footerText + "\nAdded to party!"
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, footerText + "\n(returning to overworld in 6 seconds...)"))
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)
                                        await sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        await sleep(4)
                                        goStraightToResolve = True
                                        isItemUI2 = False
                            elif (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple, False, False, None, False, item)
                                return
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                elif (str(reaction.emoji) == data.getEmoji('2')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        isItemUI1 = True
                        response = 'Bag'
                        embed.set_footer(text=createItemCategoryFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await message.add_reaction(data.getEmoji('right arrow'))
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 1):
                            if(pokemon1.pp[1] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(1)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[1])
                        await message.remove_reaction(reaction, user)
                    elif isItemUI1:
                        category = "Healing Items"
                        isItemUI1 = False
                        isItemUI2 = True
                        items = getBattleItems(category, battle)
                        embed.set_footer(text=createItemFooter(pokemon1, pokemon2, category, items, battle.trainer1))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                    elif isItemUI2:
                        items = getBattleItems(category, battle)
                        if (len(items) > 1):
                            item = items[1]
                            if (category == "Balls"):
                                if (isWild):
                                    await message.clear_reactions()
                                    ball = item
                                    battle.trainer1.useItem(ball, 1)
                                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, "Go " + ball + "!"))
                                    await message.edit(embed=embed)
                                    await sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            await sleep(2)
                                        if not caught:
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2)
                                            await message.edit(embed=embed)
                                    if (shakes == 0):
                                        failText = "Oh no! The Pokemon broke free!"
                                    elif (shakes == 1):
                                        failText = "Aww! It appeared to be caught!"
                                    elif (shakes == 2):
                                        failText = "Aargh! Almost had it!"
                                    elif (shakes == 3):
                                        failText = "Shoot! It was so close, too!"
                                    if (caught):
                                        footerText = "Gotcha! " + battle.pokemon2.name + " was caught!"
                                        if (sentToBox):
                                            footerText = footerText + "\nSent to box!"
                                        else:
                                            footerText = footerText + "\nAdded to party!"
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, footerText))
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)
                                        await sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        await sleep(4)
                                        goStraightToResolve = True
                                        isItemUI2 = False
                            elif (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple, False, False, None, False, item)
                                return
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                elif (str(reaction.emoji) == data.getEmoji('3')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        response = 'Pokemon'
                        await message.delete()
                        await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple)
                        return
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 2):
                            if(pokemon1.pp[2] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(2)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[2])
                        await message.remove_reaction(reaction, user)
                    elif isItemUI1:
                        category = "Status Items"
                        isItemUI1 = False
                        isItemUI2 = True
                        items = getBattleItems(category, battle)
                        embed.set_footer(text=createItemFooter(pokemon1, pokemon2, category, items, battle.trainer1))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                    elif isItemUI2:
                        items = getBattleItems(category, battle)
                        if (len(items) > 2):
                            item = items[2]
                            if (category == "Balls"):
                                if (isWild):
                                    await message.clear_reactions()
                                    ball = item
                                    battle.trainer1.useItem(ball, 1)
                                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, "Go " + ball + "!"))
                                    await message.edit(embed=embed)
                                    await sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            await sleep(2)
                                        if not caught:
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2)
                                            await message.edit(embed=embed)
                                    if (shakes == 0):
                                        failText = "Oh no! The Pokemon broke free!"
                                    elif (shakes == 1):
                                        failText = "Aww! It appeared to be caught!"
                                    elif (shakes == 2):
                                        failText = "Aargh! Almost had it!"
                                    elif (shakes == 3):
                                        failText = "Shoot! It was so close, too!"
                                    if (caught):
                                        footerText = "Gotcha! " + battle.pokemon2.name + " was caught!"
                                        if (sentToBox):
                                            footerText = footerText + "\nSent to box!"
                                        else:
                                            footerText = footerText + "\nAdded to party!"
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, footerText))
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)
                                        await sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        await sleep(4)
                                        goStraightToResolve = True
                                        isItemUI2 = False
                            elif (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple, False, False, None, False, item)
                                return
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                elif (str(reaction.emoji) == data.getEmoji('4')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        response = 'Run'
                        await message.remove_reaction(reaction, user)
                        canRun = battle.run()
                        if canRun:
                            await message.clear_reactions()
                            embed.set_footer(text=createTextFooter(pokemon1, pokemon2, "Got away safely!\n(returning to overworld in 4 seconds...)"))
                            await message.edit(embed=embed)
                            await sleep(4)
                            await message.delete()
                            if (goBackTo == 'startOverworldUI'):
                                await startOverworldUI(ctx, otherData[0])
                            return
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 3):
                            if(pokemon1.pp[3] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(3)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[3])
                        await message.remove_reaction(reaction, user)
                    elif isItemUI2:
                        items = getBattleItems(category, battle)
                        if (len(items) > 3):
                            item = items[3]
                            if (category == "Balls"):
                                if (isWild):
                                    await message.clear_reactions()
                                    ball = item
                                    battle.trainer1.useItem(ball, 1)
                                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, "Go " + ball + "!"))
                                    await message.edit(embed=embed)
                                    await sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            await sleep(2)
                                        if not caught:
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2)
                                            await message.edit(embed=embed)
                                    if (shakes == 0):
                                        failText = "Oh no! The Pokemon broke free!"
                                    elif (shakes == 1):
                                        failText = "Aww! It appeared to be caught!"
                                    elif (shakes == 2):
                                        failText = "Aargh! Almost had it!"
                                    elif (shakes == 3):
                                        failText = "Shoot! It was so close, too!"
                                    if (caught):
                                        footerText = "Gotcha! " + battle.pokemon2.name + " was caught!"
                                        if (sentToBox):
                                            footerText = footerText + "\nSent to box!"
                                        else:
                                            footerText = footerText + "\nAdded to party!"
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, footerText))
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)
                                        await sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        await sleep(4)
                                        goStraightToResolve = True
                                        isItemUI2 = False
                            elif (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple, False, False, None, False, item)
                                return
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                elif ((isMoveUI or isItemUI1 or isItemUI2) and str(reaction.emoji) == data.getEmoji('right arrow')):
                    if not isItemUI2:
                        isMoveUI = False
                        isItemUI1 = False
                        embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.clear_reaction(reaction)
                    else:
                        isItemUI2 = False
                        isItemUI1 = True
                        embed.set_footer(text=createItemCategoryFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2, category)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2, category)

    await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
        
def createBattleEmbed(ctx, isWild, pokemon1, pokemon2, goStraightToResolve):
    files = []
    if (isWild):
        embed = discord.Embed(title="A wild " + pokemon2.name + " appeared!", description="[react to # to do commands]", color=0x00ff00)
    else:
        embed = discord.Embed(title=pokemon2.OT + " sent out " + pokemon2.name + "!", description="[react to # to do commands]", color=0x00ff00)
    file = discord.File("data/temp/merged_image.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    if not goStraightToResolve:
        embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
    else:
        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, "")) # the fuck? '‎'
    createBattleEmbedFields(embed, pokemon1, pokemon2)
    embed.set_author(name=(ctx.message.author.display_name + "'s Battle:"))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image2.png")
    return files, embed

def createBattleEmbedFields(embed, pokemon1, pokemon2, ball=None, shakeNum=None):
    statusText1 = '\u200b'
    if (pokemon1.shiny):
        statusText1 = statusText1 + ':star2:'
    for status in pokemon1.statusList:
        statusText1 = statusText1 + data.getStatusEmoji(status)
    statusText2 = '\u200b'
    if (pokemon2.shiny):
        statusText2 = statusText2 + ':star2:'
    for status in pokemon2.statusList:
        statusText2 = statusText2 + data.getStatusEmoji(status)
    if ball is not None and shakeNum is not None:
        statusText2 = ''
        for x in range(0, shakeNum):
            statusText2 = statusText2 + data.getEmoji(ball.lower()) + " "
    embed.add_field(name=pokemon1.nickname + '  Lv' + str(pokemon1.level), value=statusText1, inline=True)
    embed.add_field(name=pokemon2.nickname + '  Lv' + str(pokemon2.level), value=statusText2, inline=True)
    
def createTextFooter(pokemon1, pokemon2, text):
    return ("HP: "
             + str(pokemon1.currentHP)
             + " / "
             + str(pokemon1.hp)
             + "                                      HP: "
             + str(pokemon2.currentHP)
             + " / " + str(pokemon2.hp)
             + "\n\n"
             + text)

def getBattleItems(category, battle=None, trainer=None):
    trainerItems = []
    items = []
    ballItems = ["Pokeball", "Greatball", "Ultraball", "Masterball"]
    healthItems = ["Potion", "Super Potion", "Hyper Potion", "Max Potion"]
    statusItems = ["Full Restore", "Full Heal", "Revive", "Max Revive"]
    if (category == "Balls"):
        items = ballItems
    elif (category == "Healing Items"):
        items = healthItems
    elif (category == "Status Items"):
        items = statusItems
    elif (category == "Other Items"):
        if trainer is not None:
            for item in trainer.itemList.keys():
                if item not in ballItems and item not in healthItems and item not in statusItems and item != "money":
                    items.append(item)
    for item in items:
        if (battle is not None):
            if (item in battle.trainer1.itemList.keys() and battle.trainer1.itemList[item] > 0):
                trainerItems.append(item)
        elif (trainer is not None):
            if (item in trainer.itemList.keys() and trainer.itemList[item] > 0):
                trainerItems.append(item)
    return trainerItems

def createItemCategoryFooter(pokemon1, pokemon2):
    return ("HP: "
             + str(pokemon1.currentHP)
             + " / "
             + str(pokemon1.hp)
             + "                                      HP: "
             + str(pokemon2.currentHP)
             + " / " + str(pokemon2.hp)
             + "\n\n"
             + "Bag Pockets:\n"
            + "(1) Balls\n"
            + "(2) Healing Items\n"
            + "(3) Status Items\n")

def createItemFooter(pokemon1, pokemon2, category, items, trainer):
    itemFooter = ("HP: "
             + str(pokemon1.currentHP)
             + " / "
             + str(pokemon1.hp)
             + "                                      HP: "
             + str(pokemon2.currentHP)
             + " / " + str(pokemon2.hp)
             + "\n\n"
             + category + ":")
    count = 1
    for item in items:
        itemFooter = itemFooter + "\n(" + str(count) + ") " + item + "\n----- Owned: " + str(trainer.itemList[item])
        count += 1
    return itemFooter

def createBattleFooter(pokemon1, pokemon2):
    return ("HP: "
             + str(pokemon1.currentHP)
             + " / "
             + str(pokemon1.hp)
             + "                                      HP: "
             + str(pokemon2.currentHP)
             + " / " + str(pokemon2.hp)
             + "\n\n"
             + "(1) Fight                     (2) Bag\n(3) Pokemon            (4) Run")

def createMoveFooter(pokemon1, pokemon2):
    moveFooter = ("HP: "
             + str(pokemon1.currentHP)
             + " / "
             + str(pokemon1.hp)
             + "                                      HP: "
             + str(pokemon2.currentHP)
             + " / " + str(pokemon2.hp)
             + "\n\n")
    moveList = pokemon1.moves
    count = 0
    for move in moveList:
        count += 1
        try:
            moveName = move['names']['en']
            moveMaxPP = str(move['pp'])
            movePP = str(pokemon1.pp[count-1])
        except:
            moveName = 'ERROR'
            moveMaxPP = 'ERROR'
            movePP = 'ERROR'
        addition1 = (moveName + " (" + movePP + "/" + moveMaxPP + "pp)")
        addition2 = ''
        if (count == 1 or count == 3):
            for i in range(0, 25-len(addition1)):
                addition2 = addition2 + " "
        else:
            addition2 = "\n"
        moveFooter = moveFooter + "(" + str(count) + ") " + addition1 + addition2
    return moveFooter

async def afterBattleCleanup(ctx, battle, pokemonToEvolveList, pokemonToLearnMovesList, isWin, goBackTo, otherData):
    if (goBackTo == "PVP"):
        return
    trainer = battle.trainer1
    for pokemon in pokemonToEvolveList:
        #print('evolist')
        #print(pokemon.nickname)
        oldName = copy(pokemon.nickname)
        pokemon.evolve()
        embed = discord.Embed(title="Congratulations! " + str(ctx.message.author) + "'s " + oldName + " evolved into " + pokemon.evolveToAfterBattle + "!", description="(continuing automatically in 6 seconds...)", color=0x00ff00)
        file = discord.File(pokemon.getSpritePath(), filename="image.png")
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
        embed.set_author(name=(ctx.message.author.display_name + "'s Pokemon Evolved:"))
        message = await ctx.send(file=file, embed=embed)
        await sleep(6)
        await message.delete()
    for pokemon in pokemonToLearnMovesList:
        for move in pokemon.newMovesToLearn:
            for learnedMove in pokemon.moves:
                if learnedMove['names']['en'] == move['names']['en']:
                    continue
            if (len(pokemon.moves) >= 4):
                text = str(ctx.message.author) + "'s " + pokemon.nickname + " would like to learn " + move['names']['en'] + ". Please select move to replace."
                count = 1
                newMoveCount = count
                for learnedMove in pokemon.moves:
                    text = text  + "\n(" + str(count) + ") " + learnedMove['names']['en']
                    count += 1
                newMoveCount = count
                text = text  + "\n(" + str(count) + ") " + move['names']['en']
                message = await ctx.send(text)
                for x in range(1, count+1):
                    await message.add_reaction(data.getEmoji(str(x)))
                messageID = message.id

                def check(reaction, user):
                    return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (
                                user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (
                                        user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (
                                        user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6')))

                async def waitForEmoji(ctx, message):
                    try:
                        reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
                    except asyncio.TimeoutError:
                        await endSession(ctx)
                    else:
                        userValidated = False
                        if (messageID == reaction.message.id):
                            userValidated = True
                        if userValidated:
                            if (str(reaction.emoji) == data.getEmoji('1')):
                                if (newMoveCount != 1):
                                    oldMoveName = pokemon.moves[0]['names']['en']
                                    pokemon.replaceMove(0, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    await sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('2')):
                                if (newMoveCount != 2):
                                    oldMoveName = pokemon.moves[1]['names']['en']
                                    pokemon.replaceMove(1, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    await sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('3')):
                                if (newMoveCount != 3):
                                    oldMoveName = pokemon.moves[2]['names']['en']
                                    pokemon.replaceMove(2, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    await sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('4')):
                                if (newMoveCount != 4):
                                    oldMoveName = pokemon.moves[3]['names']['en']
                                    pokemon.replaceMove(3, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    await sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('5')):
                                await message.delete()
                                message = await ctx.send("Gave up on learning " + move['names']['en'] + "." + " (continuing automatically in 4 seconds...)")
                                await sleep(4)
                                await message.delete()

                await waitForEmoji(ctx, message)
            else:
                pokemon.learnMove(move)
                message = await ctx.send(pokemon.nickname + " learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                await sleep(4)
                await message.delete()
    battle.battleRefresh()
    for flag in trainer.flags:
        tempFlag = flag
        if 'cutscene' in flag:
            trainer.removeFlag(flag)
            await startCutsceneUI(ctx, tempFlag, trainer)
            return
    if (goBackTo == "startBattleTowerUI"):
        if isWin:
            if otherData[2]:
                otherData[0].withRestrictionStreak += 1
                otherData[1].withRestrictionStreak += 1
            else:
                otherData[0].noRestrictionsStreak += 1
                otherData[1].noRestrictionsStreak += 1
            await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
            return
        else:
            otherData[0].withRestrictionStreak = 0
            otherData[1].withRestrictionStreak = 0
            otherData[0].noRestrictionsStreak = 0
            otherData[1].noRestrictionsStreak = 0
            await startOverworldUI(ctx, otherData[0])
            return
    await startOverworldUI(ctx, trainer)

def mergeImages(path1, path2, location):
    locationDataObj = data.getLocation(location)
    if locationDataObj.battleTerrain == "grass":
        backgroundPath = 'data/sprites/background_grass.png'
    elif locationDataObj.battleTerrain == "arena":
        backgroundPath = 'data/sprites/background_arena.png'
    elif locationDataObj.battleTerrain == "cave":
        backgroundPath = 'data/sprites/background_cave.png'
    elif locationDataObj.battleTerrain == "land":
        backgroundPath = 'data/sprites/background_land.png'
    elif locationDataObj.battleTerrain == "water":
        backgroundPath = 'data/sprites/background_water.png'
    else:
        backgroundPath = 'data/sprites/background.png'
    background = Image.open(backgroundPath)
    background = background.convert('RGBA')
    image1 = Image.open(path1)
    image1 = image1.transpose(method=Image.FLIP_LEFT_RIGHT)
    image2 = Image.open(path2)
    background.paste(image1, (12,40), image1.convert('RGBA'))
    if 'gen5' in path2:
        background.paste(image2, (130, -10), image2.convert('RGBA'))
    else:
        background.paste(image2, (130, 0), image2.convert('RGBA'))
    background.save("data/temp/merged_image.png","PNG")

async def startOverworldUI(ctx, trainer):
    resetAreas(trainer)
    files, embed, overWorldCommands = createOverworldEmbed(ctx, trainer)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    count = 1
    for command in overWorldCommands:
        await message.add_reaction(data.getEmoji(str(count)))
        count += 1
    if count > 10:
        await message.add_reaction(data.getEmoji(str(0)))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('7')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('8'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('9')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('0')))

    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer,)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(overWorldCommands) > 0):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[1], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('2') and len(overWorldCommands) > 1):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[2], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('3') and len(overWorldCommands) > 2):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[3], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('4') and len(overWorldCommands) > 3):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[4], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('5') and len(overWorldCommands) > 4):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[5], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('6') and len(overWorldCommands) > 5):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[6], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('7') and len(overWorldCommands) > 6):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[7], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('8') and len(overWorldCommands) > 7):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[8], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('9') and len(overWorldCommands) > 8):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[9], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                elif (str(reaction.emoji) == data.getEmoji('0') and len(overWorldCommands) > 9):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = executeWorldCommand(ctx, trainer, overWorldCommands[10], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining)
                        return
                await message.remove_reaction(reaction, user)
                await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)

    await waitForEmoji(ctx)

async def resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining):
    embed = newEmbed
    if (reloadArea):
        await message.delete()
        await startOverworldUI(ctx, trainer)
    elif (goToBox):
        await message.delete()
        await startBoxUI(ctx, trainer, 0, 'startOverworldUI', dataTuple)
    elif (goToBag):
        await message.delete()
        await startBagUI(ctx, trainer, 'startOverworldUI', dataTuple)
    elif (goToMart):
        await message.delete()
        await startMartUI(ctx, trainer, 'startOverworldUI', dataTuple)
    elif (goToParty):
        await message.delete()
        await startPartyUI(ctx, trainer, 'startOverworldUI', None, dataTuple)
    elif (goToTMMoveTutor):
        await message.delete()
        await startMoveTutorUI(ctx, trainer, 0, True, 0, 'startOverworldUI', dataTuple)
    elif (goToLevelMoveTutor):
        await message.delete()
        await startMoveTutorUI(ctx, trainer, 0, False, 0, 'startOverworldUI', dataTuple)
    elif (goToSuperTraining):
        await message.delete()
        await startSuperTrainingUI(ctx, trainer)
    elif (battle is not None):
        battle.startBattle()
        await message.delete()
        if not battle.isWildEncounter:
            await startBeforeTrainerBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
        else:
            await startBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
    elif (goToBattleTower):
        await message.delete()
        await startBattleTowerSelectionUI(ctx, trainer, withRestrictions)

def executeWorldCommand(ctx, trainer, command, embed):
    embedNeedsUpdating = False
    reloadArea = False
    goToBox = False
    goToMart = False
    goToParty = False
    goToBag = False
    goToTMMoveTutor = False
    goToLevelMoveTutor = False
    goToBattleTower = False
    goToSuperTraining = False
    withRestrictions = True
    battle = None
    footerText = '[react to # to do commands]'
    if (command[0] == "party"):
        goToParty = True
    elif (command[0] == "bag"):
        goToBag = True
    elif (command[0] == "progress"):
        if (trainer.dailyProgress > 0 or not data.staminaDict[str(ctx.message.guild.id)]):
            if (data.staminaDict[str(ctx.message.guild.id)]):
                trainer.dailyProgress -= 1
            trainer.progress(trainer.location)
            currentProgress = trainer.checkProgress(trainer.location)
            locationDataObj = data.getLocation(trainer.location)
            event = locationDataObj.getEventForProgress(currentProgress)
            if (event is not None):
                if (event.type == "battle"):
                    if (event.subtype == "trainer"):
                        battle = Battle(data, trainer, event.trainer)
                    elif (event.subtype == "wild"):
                        alreadyOwned = False
                        for pokemon in trainer.partyPokemon:
                            if pokemon.name == event.pokemonName:
                                alreadyOwned = True
                        for pokemon in trainer.boxPokemon:
                            if pokemon.name == event.pokemonName:
                                alreadyOwned = True
                        if alreadyOwned:
                            if (data.staminaDict[str(ctx.message.guild.id)]):
                                trainer.dailyProgress += 1
                            trainer.removeProgress(trainer.location)
                            embed.set_footer(text=footerText + "\n\nCan only own 1 of: " + event.pokemonName + "!")
                            embedNeedsUpdating = True
                        else:
                            battle = Battle(data, trainer, None, locationDataObj.entryType, event.createPokemon())
            else:
                if (locationDataObj.hasWildEncounters):
                    battle = Battle(data, trainer, None, locationDataObj.entryType)
        else:
            embed.set_footer(text=footerText + "\n\nOut of stamina for today! Please come again tomorrow!")
            embedNeedsUpdating = True
    elif (command[0] == "wildEncounter"):
        if (trainer.dailyProgress > 0 or not data.staminaDict[str(ctx.message.guild.id)]):
            if (data.staminaDict[str(ctx.message.guild.id)]):
                trainer.dailyProgress -= 1
            locationDataObj = data.getLocation(trainer.location)
            if (locationDataObj.hasWildEncounters):
                battle = Battle(data, trainer, None, locationDataObj.entryType)
        else:
            embed.set_footer(text=footerText + "\n\nOut of stamina for today! Please come again tomorrow!")
            embedNeedsUpdating = True
    elif (command[0] == "heal"):
        trainer.pokemonCenterHeal()
        embed.set_footer(text=footerText+"\n\nNURSE JOY:\nYour Pokemon were healed! We hope to see you again!")
        embedNeedsUpdating = True
    elif (command[0] == "box"):
        goToBox = True
    elif (command[0] == "mart"):
        goToMart = True
    elif (command[0] == 'tmMoveTutor'):
        goToTMMoveTutor = True
    elif (command[0] == 'levelMoveTutor'):
        goToLevelMoveTutor = True
    elif (command[0] == 'superTraining'):
        if trainer.getItemAmount('BP') >= 20:
            goToSuperTraining = True
        else:
            embed.set_footer(text=footerText + "\n\nNeed at least 20 BP to do super training!")
            embedNeedsUpdating = True
    elif (command[0] == "travel"):
        trainer.location = command[1]
        reloadArea = True
    elif (command[0] == "legendaryPortal"):
        if trainer.dailyProgress > 0 or not data.staminaDict[str(ctx.message.guild.id)]:
            if (data.staminaDict[str(ctx.message.guild.id)]):
                trainer.dailyProgress -= 1
            pokemonName = data.getLegendaryPortalPokemon()
            legendaryPokemon = Pokemon(data, pokemonName, 70)
            alreadyOwned = False
            for pokemon in trainer.partyPokemon:
                if pokemon.name == pokemonName:
                    alreadyOwned = True
            for pokemon in trainer.boxPokemon:
                if pokemon.name == pokemonName:
                    alreadyOwned = True
            if alreadyOwned:
                if data.staminaDict[str(ctx.message.guild.id)]:
                    trainer.dailyProgress += 1
                embed.set_footer(text=footerText + "\n\nCan only own 1 of: " + pokemonName + "!")
                embedNeedsUpdating = True
            else:
                battle = Battle(data, trainer, None, "Walking", legendaryPokemon)
        else:
            embed.set_footer(text=footerText + "\n\nOut of stamina for today! Please come again tomorrow!")
            embedNeedsUpdating = True
    elif (command[0] == "battleTowerR" or command[0] == "battleTowerNoR"):
        if command[0] == "battleTowerNoR":
            withRestrictions = False
        goToBattleTower = True
    return embed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining

def createOverworldEmbed(ctx, trainer):
    overWorldCommands = {}
    files = []
    locationName = trainer.location
    locationObj = data.getLocation(locationName)
    progressRequired = locationObj.progressRequired
    progressText = ''
    if (progressRequired > 0 and trainer.checkProgress(locationName) < progressRequired):
        progressText = progressText + 'Progress: ' + str(trainer.checkProgress(locationName)) + ' / ' + str(progressRequired)
    elif (progressRequired == 0):
        progressText = progressText + 'Progress: N/A'
    else:
        progressText = progressText + 'Progress: COMPLETE'
    embed = discord.Embed(title=locationName,
                          description=progressText,
                          color=0x00ff00)
    file = discord.File("data/sprites/locations/" + locationObj.filename + ".png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    footerText = '[react to # to do commands]'
    if locationObj.desc is not None:
        footerText += '\n' + locationObj.desc
    embed.set_footer(text=footerText)
    if data.staminaDict[str(ctx.message.guild.id)]:
        embed.set_author(name=(ctx.message.author.display_name + " is exploring the world:\n(remaining stamina: " + str(trainer.dailyProgress) + ")"))
    else:
        embed.set_author(name=(ctx.message.author.display_name + " is exploring the world:"))

    optionsText = ''
    count = 1
    if (trainer.checkProgress(locationName) < progressRequired):
        optionsText = optionsText + "(" + str(count) + ") Make progress\n"
        overWorldCommands[count] = ('progress',)
        count += 1
    else:
        locationDataObj = data.getLocation(trainer.location)
        if (locationDataObj.hasWildEncounters):
            optionsText = optionsText + "(" + str(count) + ") Wild Encounter\n"
            overWorldCommands[count] = ('wildEncounter',)
            count += 1
    if (locationObj.isBattleTower):
        optionsText = optionsText + "(" + str(count) + ") Normal Challenge (with Restrictions)\n"
        overWorldCommands[count] = ('battleTowerR',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Legendary Challenge (no Restrictions)\n"
        overWorldCommands[count] = ('battleTowerNoR',)
        count += 1
    optionsText = optionsText + "(" + str(count) + ") Party\n"
    overWorldCommands[count] = ('party',)
    count += 1
    optionsText = optionsText + "(" + str(count) + ") Bag\n"
    overWorldCommands[count] = ('bag',)
    count += 1
    if (locationObj.hasPokemonCenter):
        optionsText = optionsText + "(" + str(count) + ") Heal at Pokemon Center\n"
        overWorldCommands[count] = ('heal',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Access the Pokemon Storage System\n"
        overWorldCommands[count] = ('box',)
        count += 1
    if (locationObj.hasMart):
        if locationName == "Battle Frontier":
            optionsText = optionsText + "(" + str(count) + ") Shop at Battle Frontier Mart\n"
        else:
            optionsText = optionsText + "(" + str(count) + ") Shop at Pokemart\n"
        overWorldCommands[count] = ('mart',)
        count += 1
    if (locationObj.hasSuperTraining):
        optionsText = optionsText + "(" + str(count) + ") Use Super Training (20 BP)\n"
        overWorldCommands[count] = ('superTraining',)
        count += 1
    if (locationObj.hasMoveTutor):
        optionsText = optionsText + "(" + str(count) + ") Use Move Tutor (TM's)\n"
        overWorldCommands[count] = ('tmMoveTutor',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Use Move Tutor (Level Up Moves)\n"
        overWorldCommands[count] = ('levelMoveTutor',)
        count += 1
    if (locationObj.hasLegendaryPortal):
        optionsText = optionsText + "(" + str(count) + ") Explore Mysterious Portal\n"
        overWorldCommands[count] = ('legendaryPortal',)
        count += 1

    for nextLocationName, nextLocationObj in locationObj.nextLocations.items():
        if (nextLocationObj.checkRequirements(trainer)):
            optionsText = optionsText + "(" + str(count) + ") Travel to " + nextLocationName + "\n"
            overWorldCommands[count] = ('travel', nextLocationName)
            count += 1

    embed.add_field(name='Options:', value=optionsText, inline=True)
    return files, embed, overWorldCommands

def resetAreas(trainer):
    currentLocation = trainer.location
    areas = ['Sky Pillar Top 2', 'Forest Ruins', 'Desert Ruins', 'Island Ruins', 'Marine Cave', 'Terra Cave', 'Northern Island',
             'Southern Island', 'Faraway Island', 'Birth Island', 'Naval Rock 1', 'Naval Rock 2']
    elite4Areas = ['Elite 4 Room 1', 'Elite 4 Room 2', 'Elite 4 Room 3', 'Elite 4 Room 4', 'Champion Room',
                   'Elite 4 Room 1 Lv70', 'Elite 4 Room 2 Lv70', 'Elite 4 Room 3 Lv70', 'Elite 4 Room 4 Lv70', 'Champion Room Lv70',
                   'Elite 4 Room 1 Lv100', 'Elite 4 Room 2 Lv100', 'Elite 4 Room 3 Lv100', 'Elite 4 Room 4 Lv100', 'Champion Room Lv100']
    for area in areas:
        if area in trainer.locationProgressDict.keys():
                trainer.locationProgressDict[area] = 0
    if currentLocation not in elite4Areas:
        for area in elite4Areas:
            if area in trainer.locationProgressDict.keys():
                trainer.locationProgressDict[area] = 0

async def startBoxUI(ctx, trainer, offset=0, goBackTo='', otherData=None):
    maxBoxes = math.ceil(len(trainer.boxPokemon)/9)
    if (maxBoxes < 1):
        maxBoxes = 1
    files, embed = createBoxEmbed(ctx, trainer, offset) # is box number
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    for x in range(1, 10):
        await message.add_reaction(data.getEmoji(str(x)))
    await message.add_reaction(data.getEmoji('party'))
    await message.add_reaction(data.getEmoji('left arrow'))
    await message.add_reaction(data.getEmoji('right arrow'))
    await message.add_reaction(data.getEmoji('down arrow'))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('7')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('8'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('9'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('left arrow'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('down arrow')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('party')))

    async def waitForEmoji(ctx, offset):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer, offset, goBackTo, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(trainer.boxPokemon) >= 1 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 0 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('2') and len(trainer.boxPokemon) >= 2 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 1 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('3') and len(trainer.boxPokemon) >= 3 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 2 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('4') and len(trainer.boxPokemon) >= 4 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 3 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('5') and len(trainer.boxPokemon) >= 5 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 4 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('6') and len(trainer.boxPokemon) >= 6 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 5 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('7') and len(trainer.boxPokemon) >= 7 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 6 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('8') and len(trainer.boxPokemon) >= 8 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 7 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('9') and len(trainer.boxPokemon) >= 9 + (offset*9)):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer, 8 + (offset*9), 'startBoxUI', None, dataTuple, True)
                elif (str(reaction.emoji) == data.getEmoji('left arrow')):
                    if (offset == 0 and maxBoxes != 1):
                        offset = maxBoxes - 1
                        files, embed = createBoxEmbed(ctx, trainer, offset)
                        await message.edit(embed=embed)
                    elif (offset > 0):
                        offset -= 1
                        files, embed = createBoxEmbed(ctx, trainer, offset)
                        await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx, offset)
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    #print(offset)
                    #print(maxBoxes)
                    if (offset+1 < maxBoxes):
                        offset += 1
                        files, embed = createBoxEmbed(ctx, trainer, offset)
                        await message.edit(embed=embed)
                    elif (offset+1 == maxBoxes and maxBoxes != 1):
                        offset = 0
                        files, embed = createBoxEmbed(ctx, trainer, offset)
                        await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx, offset)
                elif (str(reaction.emoji) == data.getEmoji('party')):
                    await message.delete()
                    await startPartyUI(ctx, trainer, 'startBoxUI', None, dataTuple, False, False, None, True)
                elif (str(reaction.emoji) == data.getEmoji('down arrow')):
                    if (goBackTo == 'startOverworldUI'):
                        await message.delete()
                        await startOverworldUI(ctx, otherData[0])
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, offset)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx, offset)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx, offset)

    await waitForEmoji(ctx, offset)

def createBoxEmbed(ctx, trainer, offset):
    files = []
    embed = discord.Embed(title="Box " + str(offset+1), description="[react to # to view individual summary]", color=0x00ff00)
    count = 1
    for x in range(offset*9, offset*9+9):
        try:
            pokemon = trainer.boxPokemon[x]
            hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
            levelString = "Level: " + str(pokemon.level)
            embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")",
                            value=levelString + "\n" + hpString, inline=True)
            count += 1
        except:
            embed.add_field(name="----Empty Slot----", value="\u200b", inline=True)
    embed.set_author(name=(ctx.message.author.display_name))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image.png")
    return files, embed

async def startMartUI(ctx, trainer, goBackTo='', otherData=None):
    itemsForPurchase1 = {
        "Pokeball": 200,
        "Potion": 300,
        "Super Potion": 700,
        "Full Heal": 600,
        "Revive": 1500
    }
    itemsForPurchase2 = {
        "Pokeball": 200,
        "Greatball": 600,
        "Potion": 300,
        "Super Potion": 700,
        "Hyper Potion": 1200,
        "Max Potion": 3000,
        "Full Heal": 600,
        "Revive": 1500
    }
    itemsForPurchase3 = {
        "Pokeball": 200,
        "Greatball": 600,
        "Ultraball": 1200,
        "Super Potion": 300,
        "Hyper Potion": 1200,
        "Full Restore": 3000,
        "Full Heal": 600,
        "Revive": 1500,
        "Max Revive": 4000
    }
    if trainer.location == "Battle Frontier":
        itemsForPurchase3 = {
            "Ultraball": 1,
            "Masterball": 50,
            "Full Restore": 1,
            "Full Heal": 1,
            "Max Revive": 1,
            "PokeDollars x1000": 1
        }
    if (trainer.checkFlag("badge5")):
        itemDict = itemsForPurchase3
    elif (trainer.checkFlag("badge3")):
        itemDict = itemsForPurchase2
    else:
        itemDict = itemsForPurchase1
    files, embed = createMartEmbed(ctx, trainer, itemDict)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    for x in range(1, len(itemDict)+1):
        await message.add_reaction(data.getEmoji(str(x)))
    await message.add_reaction(data.getEmoji('right arrow'))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('7')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('8'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('9'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')))

    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(itemDict) >= 1):
                    key = list(itemDict.keys())[0]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            #print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('2') and len(itemDict) >= 2):
                    key = list(itemDict.keys())[1]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('3') and len(itemDict) >= 3):
                    key = list(itemDict.keys())[2]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('4') and len(itemDict) >= 4):
                    key = list(itemDict.keys())[3]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('5') and len(itemDict) >= 5):
                    key = list(itemDict.keys())[4]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                              + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('6') and len(itemDict) >= 6):
                    key = list(itemDict.keys())[5]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            if key == "PokeDollars x1000":
                                trainer.addItem('money', 1000)
                                embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                      + "\nBought $1000 for " + str(itemDict[key]) + " BP.")
                            else:
                                trainer.addItem(key, 1)
                                # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                                embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                      + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('7') and len(itemDict) >= 7):
                    key = list(itemDict.keys())[6]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('8') and len(itemDict) >= 8):
                    key = list(itemDict.keys())[7]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('9') and len(itemDict) >= 9):
                    key = list(itemDict.keys())[8]
                    if trainer.location == "Battle Frontier":
                        if (trainer.getItemAmount('BP') >= itemDict[key]):
                            trainer.addItem('BP', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                                  + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                            await message.edit(embed=embed)
                    else:
                        if (trainer.getItemAmount('money') >= itemDict[key]):
                            trainer.addItem('money', -1 * itemDict[key])
                            trainer.addItem(key, 1)
                            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                                  + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    if (goBackTo == 'startOverworldUI'):
                        await message.delete()
                        await startOverworldUI(ctx, otherData[0])
                        return
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx)
                        return
                await message.remove_reaction(reaction, user)
                await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)

    await waitForEmoji(ctx)

def createMartEmbed(ctx, trainer, itemDict):
    files = []
    embed = discord.Embed(title="Pokemon Mart", description="[react to # to buy]", color=0x00ff00)
    file = discord.File("data/sprites/locations/pokemart.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    count = 1
    for item, price in itemDict.items():
        prefix = ''
        suffix = ''
        if trainer.location == 'Battle Frontier':
            suffix = " BP"
            embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP')))
        else:
            prefix = '$'
            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')))
        embed.add_field(name="(" + str(count) + ") " + item, value=prefix + str(price) + suffix, inline=True)
        count += 1
    embed.set_author(name=ctx.message.author.display_name + " is shopping:")
    return files, embed

async def startBagUI(ctx, trainer, goBackTo='', otherData=None):
    files, embed = createBagEmbed(ctx, trainer)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    await message.add_reaction(data.getEmoji(str(1)))
    await message.add_reaction(data.getEmoji(str(2)))
    await message.add_reaction(data.getEmoji(str(3)))
    await message.add_reaction(data.getEmoji(str(4)))
    await message.add_reaction(data.getEmoji('right arrow'))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')))

    async def waitForEmoji(ctx, isCategory, category):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer, goBackTo, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1')):
                    if (isCategory):
                        isCategory = False
                        category = "Balls"
                        items = getBattleItems(category, None, trainer)
                        files, embed = createBagEmbed(ctx, trainer, items)
                        await message.edit(embed=embed)
                    else:
                        items = getBattleItems(category, None, trainer)
                        if (len(items) > 0):
                            item = items[0]
                            if (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, trainer, 'startBagUI', None, dataTuple, False, False, None, False, item)
                                return
                elif (str(reaction.emoji) == data.getEmoji('2')):
                    if (isCategory):
                        isCategory = False
                        category = "Healing Items"
                        items = getBattleItems(category, None, trainer)
                        files, embed = createBagEmbed(ctx, trainer, items)
                        await message.edit(embed=embed)
                    else:
                        items = getBattleItems(category, None, trainer)
                        if (len(items) > 1):
                            item = items[1]
                            if (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, trainer, 'startBagUI', None, dataTuple, False, False, None, False, item)
                                return
                elif (str(reaction.emoji) == data.getEmoji('3')):
                    if (isCategory):
                        isCategory = False
                        category = "Status Items"
                        items = getBattleItems(category, None, trainer)
                        files, embed = createBagEmbed(ctx, trainer, items)
                        await message.edit(embed=embed)
                    else:
                        items = getBattleItems(category, None, trainer)
                        if (len(items) > 2):
                            item = items[2]
                            if (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, trainer, 'startBagUI', None, dataTuple, False, False, None, False, item)
                                return
                elif (str(reaction.emoji) == data.getEmoji('4')):
                    if (isCategory):
                        isCategory = False
                        category = "Other Items"
                        items = getBattleItems(category, None, trainer)
                        files, embed = createBagEmbed(ctx, trainer, items)
                        await message.edit(embed=embed)
                    else:
                        items = getBattleItems(category, None, trainer)
                        if (len(items) > 4):
                            item = items[4]
                            if (category == "Healing Items" or category == "Status Items"):
                                await message.delete()
                                await startPartyUI(ctx, trainer, 'startBagUI', None, dataTuple, False, False, None, False, item)
                                return
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    if (isCategory):
                        if (goBackTo == 'startOverworldUI'):
                            await message.delete()
                            await startOverworldUI(ctx, trainer)
                            return
                    else:
                        isCategory = True
                        category = ''
                        files, embed = createBagEmbed(ctx, trainer)
                        await message.edit(embed=embed)
                await message.remove_reaction(reaction, user)
                await waitForEmoji(ctx, isCategory, category)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx, isCategory, category)

    await waitForEmoji(ctx, True, "")

def createBagEmbed(ctx, trainer, items=None):
    files = []
    embed = discord.Embed(title="Bag", description="[react to # to do commands]", color=0x00ff00)
    file = discord.File("data/sprites/bag.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    if (items is None):
        embed.add_field(name="Pockets:", value="(1) Balls\n(2) Healing Items\n(3) Status Items\n(4) Other Items", inline=True)
    else:
        count = 1
        fieldString = ''
        for item in items:
            fieldString = fieldString + "(" + str(count) + ") " + item + ": " + str(trainer.itemList[item]) + " owned\n"
            count += 1
        if not fieldString:
            fieldString = 'None'
        embed.add_field(name="Items:", value=fieldString, inline=True)
    embed.set_author(name=ctx.message.author.display_name + " is looking at their items:")
    bpText = ''
    if 'BP' in trainer.itemList.keys():
        bpText = "\nBP: " + str(trainer.itemList['BP'])
    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')) + bpText)
    return files, embed

async def startBeforeTrainerBattleUI(ctx, isWildEncounter, battle, goBackTo='', otherData=None):
    files, embed = createBeforeTrainerBattleEmbed(ctx, battle.trainer2)
    message = await ctx.send(files=files, embed=embed)
    await sleep(6)
    await message.delete()
    await startBattleUI(ctx, isWildEncounter, battle, goBackTo, otherData)

def createBeforeTrainerBattleEmbed(ctx, trainer):
    files = []
    beforeBattleText = ''
    if (trainer.beforeBattleText):
        beforeBattleText = trainer.name.upper() + ': ' + '"' + trainer.beforeBattleText + '"\n\n'
    embed = discord.Embed(title=trainer.name + " wants to fight!", description=beforeBattleText + "(battle starting in 6 seconds...)", color=0x00ff00)
    file = discord.File("data/sprites/trainers/" + trainer.sprite, filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_author(name=ctx.message.author.display_name + " is about to battle:")
    return files, embed

async def startNewUserUI(ctx, trainer):
    starterList = []
    starterList.append(Pokemon(data, "Bulbasaur", 5))
    starterList.append(Pokemon(data, "Charmander", 5))
    starterList.append(Pokemon(data, "Squirtle", 5))
    starterList.append(Pokemon(data, "Chikorita", 5))
    starterList.append(Pokemon(data, "Cyndaquil", 5))
    starterList.append(Pokemon(data, "Totodile", 5))
    starterList.append(Pokemon(data, "Treecko", 5))
    starterList.append(Pokemon(data, "Torchic", 5))
    starterList.append(Pokemon(data, "Mudkip", 5))
    files, embed = createNewUserEmbed(ctx, trainer, starterList)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    for x in range(1, len(starterList) + 1):
        await message.add_reaction(data.getEmoji(str(x)))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('7')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('8'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('9')))

    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(starterList) > 0):
                    await startAdventure(ctx, message, trainer, starterList[0])
                    return
                elif (str(reaction.emoji) == data.getEmoji('2') and len(starterList) > 1):
                    await startAdventure(ctx, message, trainer, starterList[1])
                    return
                elif (str(reaction.emoji) == data.getEmoji('3') and len(starterList) > 2):
                    await startAdventure(ctx, message, trainer, starterList[2])
                    return
                elif (str(reaction.emoji) == data.getEmoji('4') and len(starterList) > 3):
                    await startAdventure(ctx, message, trainer, starterList[3])
                    return
                elif (str(reaction.emoji) == data.getEmoji('5') and len(starterList) > 4):
                    await startAdventure(ctx, message, trainer, starterList[4])
                    return
                elif (str(reaction.emoji) == data.getEmoji('6') and len(starterList) > 5):
                    await startAdventure(ctx, message, trainer, starterList[5])
                    return
                elif (str(reaction.emoji) == data.getEmoji('7') and len(starterList) > 6):
                    await startAdventure(ctx, message, trainer, starterList[6])
                    return
                elif (str(reaction.emoji) == data.getEmoji('8') and len(starterList) > 7):
                    await startAdventure(ctx, message, trainer, starterList[7])
                    return
                elif (str(reaction.emoji) == data.getEmoji('9') and len(starterList) > 8):
                    await startAdventure(ctx, message, trainer, starterList[8])
                    return
                await message.remove_reaction(reaction, user)
                await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)

    await waitForEmoji(ctx)

async def startAdventure(ctx, message, trainer, starter):
    trainer.addPokemon(starter, True)
    await message.delete()
    confirmationText = "Congratulations! You obtained " + starter.name + "! Get ready for your Pokemon adventure!\n(continuing automatically in 5 seconds...)"
    confirmation = await ctx.send(confirmationText)
    await sleep(5)
    await confirmation.delete()
    await startOverworldUI(ctx, trainer)

def createNewUserEmbed(ctx, trainer, starterList):
    files = []
    embed = discord.Embed(title="Welcome " + trainer.name + " to the world of Pokemon!", description="[react to # to choose a starter, as soon as you press a react you will obtain the Pokemon]", color=0x00ff00)
    file = discord.File("data/sprites/trainers/birch.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    count = 1
    for pokemon in starterList:
        shinyText = '\u200b'
        if (pokemon.shiny):
            shinyText = ' :star2:'
        embed.add_field(name="(" + str(count) + ") " + pokemon.name + shinyText, value='\u200b', inline=True)
        count += 1
    embed.set_author(name=ctx.message.author.display_name + " is choosing a starter:")
    return files, embed

def createProfileEmbed(ctx, trainer):
    numberOfBadges = 0
    numberOfBadges2 = 0
    numberOfBadges3 = 0
    if ('badge8' in trainer.flags or 'elite4' in trainer.flags):
        numberOfBadges = 8
    elif ('badge7' in trainer.flags):
        numberOfBadges = 7
    elif ('badge6' in trainer.flags):
        numberOfBadges = 6
    elif ('badge5' in trainer.flags):
        numberOfBadges = 5
    elif ('badge4' in trainer.flags):
        numberOfBadges = 4
    elif ('badge3' in trainer.flags):
        numberOfBadges = 3
    elif ('badge2' in trainer.flags):
        numberOfBadges = 2
    elif ('badge1' in trainer.flags):
        numberOfBadges = 1
    if ('badge8-2' in trainer.flags):
        numberOfBadges2 = 8
    elif ('badge7-2' in trainer.flags):
        numberOfBadges2 = 7
    elif ('badge6-2' in trainer.flags):
        numberOfBadges2 = 6
    elif ('badge5-2' in trainer.flags):
        numberOfBadges2 = 5
    elif ('badge4-2' in trainer.flags):
        numberOfBadges2 = 4
    elif ('badge3-2' in trainer.flags):
        numberOfBadges2 = 3
    elif ('badge2-2' in trainer.flags):
        numberOfBadges2 = 2
    elif ('badge1-2' in trainer.flags):
        numberOfBadges2 = 1
    if ('badge8-3' in trainer.flags):
        numberOfBadges3 = 8
    elif ('badge7-3' in trainer.flags):
        numberOfBadges3 = 7
    elif ('badge6-3' in trainer.flags):
        numberOfBadges3 = 6
    elif ('badge5-3' in trainer.flags):
        numberOfBadges3 = 5
    elif ('badge4-3' in trainer.flags):
        numberOfBadges3 = 4
    elif ('badge3-3' in trainer.flags):
        numberOfBadges3 = 3
    elif ('badge2-3' in trainer.flags):
        numberOfBadges3 = 2
    elif ('badge1-3' in trainer.flags):
        numberOfBadges3 = 1
    descString = "Badges: " + str(numberOfBadges)
    if ('elite4' in trainer.flags):
        descString = descString + "\nBadges Lv70: " + str(numberOfBadges2)
        descString = descString + "\nBadges Lv100: " + str(numberOfBadges3)
        descString = descString + "\nElite 4 Cleared: Yes"
        if 'elite4-2' in trainer.flags:
            descString = descString + "\nElite 4 Lv70 Cleared: Yes"
        else:
            descString = descString + "\nElite 4 Lv70 Cleared: No"
        if 'elite4-3' in trainer.flags:
            descString = descString + "\nElite 4 Lv100 Cleared: Yes"
        else:
            descString = descString + "\nElite 4 Lv100 Cleared: No"
    else:
        descString = descString + "\nElite 4 Cleared: No"
    descString = descString + "\nCurrent Location: " + trainer.location
    descString = descString + "\nPokemon Caught: " + str(len(trainer.partyPokemon) + len(trainer.boxPokemon))
    dexList = []
    for pokemon in trainer.partyPokemon:
        if pokemon.name not in dexList:
            dexList.append(pokemon.name)
    for pokemon in trainer.boxPokemon:
        if pokemon.name not in dexList:
            dexList.append(pokemon.name)
    dexNum = len(dexList)
    descString = descString + "\nDex: " + str(dexNum)
    descString = descString + "\nMoney: " + str(trainer.getItemAmount('money'))
    if 'BP' in trainer.itemList.keys():
        descString = descString + "\nBP: " + str(trainer.getItemAmount('BP'))
        descString = descString + "\nBattle Tower With Restrictions Streak: " + str(trainer.withRestrictionStreak)
        descString = descString + "\nBattle Tower No Restrictions Streak: " + str(trainer.noRestrictionsStreak)
    shinyOwned = 0
    for pokemon in trainer.partyPokemon:
        if pokemon.shiny:
            shinyOwned += 1
    for pokemon in trainer.boxPokemon:
        if pokemon.shiny:
            shinyOwned += 1
    descString = descString + "\nShiny Pokemon Owned: " + str(shinyOwned)
    descString = descString + "\n\nParty:"
    embed = discord.Embed(title=trainer.name + "'s Profile", description=descString, color=0x00ff00)
    for pokemon in trainer.partyPokemon:
        levelString = "Level: " + str(pokemon.level)
        ivString = "IV's: " + str(pokemon.hpIV) + "/" + str(pokemon.atkIV)  + "/" + str(pokemon.defIV)  + "/" \
                   + str(pokemon.spAtkIV) + "/" + str(pokemon.spDefIV)  + "/" + str(pokemon.spdIV)
        evString = "EV's: " + str(pokemon.hpEV) + "/" + str(pokemon.atkEV) + "/" + str(pokemon.defEV) + "/" \
                   + str(pokemon.spAtkEV) + "/" + str(pokemon.spDefEV) + "/" + str(pokemon.spdEV)
        natureString = 'Nature: ' + pokemon.nature.capitalize()
        obtainedString = 'Obtained: ' + pokemon.location
        moveString = ''
        count = 1
        for move in pokemon.moves:
            moveString += 'Move ' + str(count) + ': ' + move['names']['en'] + '\n'
            count += 1
        shinyString = ''
        if pokemon.shiny:
            shinyString = " :star2:"
        embedValue = levelString + '\n' + natureString + '\n' + obtainedString + '\n' + evString + '\n' + ivString + '\n' + moveString
        embed.add_field(name=pokemon.nickname + " (" + pokemon.name + ")" + shinyString, value=embedValue,
                        inline=True)
    embed.set_author(name=(ctx.message.author.display_name + " requested this profile."))
    return embed

async def startMoveTutorUI(ctx, trainer, partySlot, isTM, offset=0, goBackTo='', otherData=None):
    pokemon = trainer.partyPokemon[partySlot]
    if isTM:
        moveList = pokemon.getAllTmMoves()
    else:
        moveList = pokemon.getAllLevelUpMoves()
    maxPages = math.ceil(len(moveList)/9)
    if (maxPages < 1):
        maxPages = 1
    files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM) # is page number
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    for x in range(1, 10):
        await message.add_reaction(data.getEmoji(str(x)))
    await message.add_reaction(data.getEmoji('left arrow'))
    await message.add_reaction(data.getEmoji('right arrow'))
    await message.add_reaction(data.getEmoji('down arrow'))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('7')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('8'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('9'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('left arrow'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('down arrow')))

    async def waitForEmoji(ctx, offset, embed):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer, partySlot, isTM, offset, goBackTo, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(moveList) >= 1 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[0 + (offset*9)], 'startMoveTutorUI', dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('2') and len(moveList) >= 2 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[1 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('3') and len(moveList) >= 3 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[2 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('4') and len(moveList) >= 4 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[3 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('5') and len(moveList) >= 5 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[4 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('6') and len(moveList) >= 6 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[5 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('7') and len(moveList) >= 7 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[6 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('8') and len(moveList) >= 8 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[7 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('9') and len(moveList) >= 9 + (offset*9)):
                    await message.delete()
                    if (trainer.getItemAmount('money') < 3000):
                        embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                        await message.edit(embed=embed)
                    else:
                        await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[8 + (offset * 9)], 'startMoveTutorUI',
                                                  dataTuple)
                        return
                elif (str(reaction.emoji) == data.getEmoji('left arrow')):
                    if (offset == 0 and maxPages != 1):
                        offset = maxPages - 1
                        files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                        await message.edit(embed=embed)
                    elif (offset > 0):
                        offset -= 1
                        files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    if (offset+1 < maxPages):
                        offset += 1
                        files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                        await message.edit(embed=embed)
                    elif (offset+1 == maxPages and maxPages != 1):
                        offset = 0
                        files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('down arrow')):
                    if (goBackTo == 'startOverworldUI'):
                        await message.delete()
                        await startOverworldUI(ctx, otherData[0])
                        return
                await message.remove_reaction(reaction, user)
                await waitForEmoji(ctx, offset, embed)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx, offset,embed)

    await waitForEmoji(ctx, offset, embed)

def createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM):
    files = []
    extraTitleText = ''
    if isTM:
        extraTitleText += " (TM's)"
    else:
        extraTitleText += " (Level Up Moves)"
    embed = discord.Embed(title="Move Tutor" + extraTitleText, description="Cost: $3000\n-> select move to teach to " + pokemon.nickname + " <-\n\nPage: " + str(offset+1),
                              color=0x00ff00)
    file = discord.File("data/sprites/locations/move_tutor.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    count = 1
    for x in range(offset * 9, offset * 9 + 9):
        try:
            move = moveList[x]
            bp = '\nBP: '
            if (move['category'].lower() == 'physical'):
                physicalSpecialEmoji = data.getEmoji('physical')
                bp = bp + str(move['power'])
            elif (move['category'].lower() == 'special'):
                physicalSpecialEmoji = data.getEmoji('special')
                bp = bp + str(move['power'])
            else:
                physicalSpecialEmoji = data.getEmoji('no damage')
            if (bp == '\nBP: 0' or bp == '\nBP: '):
                bp = ''
            embed.add_field(name=('-----Move ' + str(count) + '-----'), value=(
                        move['names']['en'] + "\n" + move['type'] + " " + physicalSpecialEmoji + bp + "\nPP: " + str(move['pp']) + " pp"), inline=True)
            count += 1
        except:
            embed.add_field(name="----Empty Slot----", value="\u200b", inline=True)
    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')))
    return files, embed

async def startLearnNewMoveUI(ctx, trainer, pokemon, move, goBackTo='', otherData=None):
    alreadyLearned = False
    for learnedMove in pokemon.moves:
        if learnedMove['names']['en'] == move['names']['en']:
            alreadyLearned = True
            message = await ctx.send(pokemon.nickname + " already knows " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
            await sleep(4)
            await message.delete()
    if not alreadyLearned:
        if (len(pokemon.moves) >= 4):
            text = str(ctx.message.author) + "'s " + pokemon.nickname + " would like to learn " + move['names'][
                'en'] + ". Please select move to replace."
            count = 1
            newMoveCount = count
            for learnedMove in pokemon.moves:
                text = text + "\n(" + str(count) + ") " + learnedMove['names']['en']
                count += 1
            newMoveCount = count
            text = text + "\n(" + str(count) + ") " + move['names']['en']
            message = await ctx.send(text)
            for x in range(1, count + 1):
                await message.add_reaction(data.getEmoji(str(x)))
            messageID = message.id

            def check(reaction, user):
                return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (
                        user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                        or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (
                                user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                        or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (
                                user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6')))

            async def waitForEmoji(ctx, message):
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
                except asyncio.TimeoutError:
                    await endSession(ctx)
                else:
                    userValidated = False
                    if (messageID == reaction.message.id):
                        userValidated = True
                    if userValidated:
                        if (str(reaction.emoji) == data.getEmoji('1')):
                            if (newMoveCount != 1):
                                oldMoveName = pokemon.moves[0]['names']['en']
                                pokemon.replaceMove(0, move)
                                await message.delete()
                                trainer.useItem('money', 3000)
                                message = await ctx.send(
                                    pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                        'en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
                                await sleep(4)
                                await message.delete()
                        elif (str(reaction.emoji) == data.getEmoji('2')):
                            if (newMoveCount != 2):
                                oldMoveName = pokemon.moves[1]['names']['en']
                                pokemon.replaceMove(1, move)
                                await message.delete()
                                trainer.useItem('money', 3000)
                                message = await ctx.send(
                                    pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                        'en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
                                await sleep(4)
                                await message.delete()
                        elif (str(reaction.emoji) == data.getEmoji('3')):
                            if (newMoveCount != 3):
                                oldMoveName = pokemon.moves[2]['names']['en']
                                pokemon.replaceMove(2, move)
                                await message.delete()
                                trainer.useItem('money', 3000)
                                message = await ctx.send(
                                    pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                        'en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
                                await sleep(4)
                                await message.delete()
                        elif (str(reaction.emoji) == data.getEmoji('4')):
                            if (newMoveCount != 4):
                                oldMoveName = pokemon.moves[3]['names']['en']
                                pokemon.replaceMove(3, move)
                                await message.delete()
                                trainer.useItem('money', 3000)
                                message = await ctx.send(
                                    pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                                        'en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
                                await sleep(4)
                                await message.delete()
                        elif (str(reaction.emoji) == data.getEmoji('5')):
                            await message.delete()
                            message = await ctx.send("Gave up on learning " + move['names'][
                                'en'] + "." + " (continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await message.delete()

            await waitForEmoji(ctx, message)
        else:
            pokemon.learnMove(move)
            trainer.useItem('money', 3000)
            message = await ctx.send(
                pokemon.nickname + " learned " + move['names']['en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
            await sleep(4)
            await message.delete()
    if goBackTo == 'startMoveTutorUI':
        await startMoveTutorUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], otherData[4], otherData[5])
        return

async def startCutsceneUI(ctx, cutsceneStr, trainer, goBackTo='', otherData=None):
    files, embed = createCutsceneEmbed(ctx, cutsceneStr)
    message = await ctx.send(files=files, embed=embed)
    await sleep(8)
    await message.delete()
    await startOverworldUI(ctx, trainer)

def createCutsceneEmbed(ctx, cutsceneStr):
    files = []
    cutsceneObj = data.cutsceneDict[cutsceneStr]
    embed = discord.Embed(title=cutsceneObj['title'], description="(continuing automatically in 8 seconds...)")
    file = discord.File('data/sprites/cutscenes/' + cutsceneStr + '.png', filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=cutsceneObj['caption'])
    embed.set_author(name=(ctx.message.author.display_name + "'s Cutscene:"))
    return files, embed

def createTrainEmbed(ctx, pokemon):
    files = []
    embed = discord.Embed(title="Super Training: " + pokemon.nickname, description="(please respond in the chat to the prompts)")
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_author(name=(ctx.message.author.display_name + " is super training their Pokemon:"))
    return files, embed

async def startBattleTowerSelectionUI(ctx, trainer, withRestrictions):
    trainer.pokemonCenterHeal()
    files, embed = createPartyUIEmbed(ctx, trainer, False, None, "Battle Tower Selection", "[react to #'s to select 3 Pokemon then hit the check mark]")
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    count = 1
    for pokemon in trainer.partyPokemon:
        await message.add_reaction(data.getEmoji(str(count)))
        count += 1
    await message.add_reaction(data.getEmoji('confirm'))
    await message.add_reaction(data.getEmoji('down arrow'))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1') and len(trainer.partyPokemon) >= 1) or (
                    user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2') and len(trainer.partyPokemon) >= 2)
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3') and len(trainer.partyPokemon) >= 3) or (
                            user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4') and len(trainer.partyPokemon) >= 4)
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5') and len(trainer.partyPokemon) >= 5) or (
                            user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6') and len(trainer.partyPokemon) >= 6)
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('confirm'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('down arrow')))

    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer, withRestrictions)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('confirm')):
                    chosenPokemonNums = []
                    cache_msg = discord.utils.get(bot.cached_messages, id=messageID)
                    for userReaction in cache_msg.reactions:
                        async for reactionUser in userReaction.users():
                            if reactionUser == ctx.message.author:
                                if messageID == userReaction.message.id:
                                    if str(userReaction.emoji) == data.getEmoji('1'):
                                        chosenPokemonNums.append(1)
                                    elif str(userReaction.emoji) == data.getEmoji('2'):
                                        chosenPokemonNums.append(2)
                                    elif str(userReaction.emoji) == data.getEmoji('3'):
                                        chosenPokemonNums.append(3)
                                    elif str(userReaction.emoji) == data.getEmoji('4'):
                                        chosenPokemonNums.append(4)
                                    elif str(userReaction.emoji) == data.getEmoji('5'):
                                        chosenPokemonNums.append(5)
                                    elif str(userReaction.emoji) == data.getEmoji('6'):
                                        chosenPokemonNums.append(6)
                    if len(chosenPokemonNums) > 3:
                        await message.remove_reaction(reaction, user)
                        embed.set_footer(text="Too many Pokemon selected.")
                        await message.edit(embed=embed)
                    elif len(chosenPokemonNums) < 3:
                        await message.remove_reaction(reaction, user)
                        embed.set_footer(text="Not enough Pokemon selected.")
                        await message.edit(embed=embed)
                    else:
                        trainerCopy, valid = battleTower.getBattleTowerUserCopy(trainer, chosenPokemonNums[0], chosenPokemonNums[1], chosenPokemonNums[2], withRestrictions)
                        if valid:
                            await message.delete()
                            await startBattleTowerUI(ctx, trainer, trainerCopy, withRestrictions)
                            return
                        else:
                            await message.remove_reaction(reaction, user)
                            embed.set_footer(text="Restricted Pokemon may not be used.")
                            await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('down arrow')):
                    await message.delete()
                    await startOverworldUI(ctx, trainer)
                    return
                await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)

    await waitForEmoji(ctx)

async def startBattleTowerUI(ctx, trainer, trainerCopy, withRestrictions):
    trainer.pokemonCenterHeal()
    trainerCopy.pokemonCenterHeal()
    files, embed = createBattleTowerUI(ctx, trainer, withRestrictions)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    await message.add_reaction(data.getEmoji('1'))
    await message.add_reaction(data.getEmoji('2'))
    await message.add_reaction(data.getEmoji('3'))

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (
                    user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (
                            user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (
                            user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')))

    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer, trainerCopy, withRestrictions)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1')):
                    if (trainer.dailyProgress > 0 or not data.staminaDict[str(ctx.message.guild.id)]):
                        if (data.staminaDict[str(ctx.message.guild.id)]):
                            trainer.dailyProgress -= 1
                        await message.delete()
                        battle = Battle(data, trainerCopy, battleTower.getBattleTowerTrainer(trainer, withRestrictions))
                        battle.startBattle()
                        await startBeforeTrainerBattleUI(ctx, False, battle, 'startBattleTowerUI', dataTuple)
                        return
                    else:
                        embed.set_footer(text="Out of stamina for today! Please come again tomorrow!")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('2')):
                    await message.delete()
                    await startPartyUI(ctx, trainerCopy, 'startBattleTowerUI', None, dataTuple)
                    return
                elif (str(reaction.emoji) == data.getEmoji('3')):
                    await message.delete()
                    await startOverworldUI(ctx, trainer)
                    return
                try:
                    await message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                try:
                    await reaction.message.remove_reaction(reaction, user)
                except:
                    pass
                await waitForEmoji(ctx)

    await waitForEmoji(ctx)

def createBattleTowerUI(ctx, trainer, withRestrictions):
    if withRestrictions:
        streak = trainer.withRestrictionStreak
        titleAddition = "Normal Rank"
    else:
        streak = trainer.noRestrictionsStreak
        titleAddition = "Legendary Rank"
    files = []
    embed = discord.Embed(title="Battle Tower: " + titleAddition, description="Streak: " + str(streak))
    file = discord.File('data/sprites/locations/battle_tower_room.png', filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    if data.staminaDict[str(ctx.message.guild.id)]:
        embed.set_author(name=(ctx.message.author.display_name + "'s Battle Tower Challenge:\n(remaining stamina: " + str(trainer.dailyProgress) + ")"))
    else:
        embed.set_author(name=(ctx.message.author.display_name + "'s Battle Tower Challenge:"))

    optionsList = [
        "Battle",
        "Party",
        "Retire (progress will be saved)"
    ]

    optionsText = ''
    count = 1

    for option in optionsList:
        optionsText = optionsText + "(" + str(count) + ") " + option + "\n"
        count += 1

    embed.add_field(name='Options:', value=optionsText, inline=True)
    return files, embed

#@bot.command(name='train', help="fully trains a Pokemon at the cost of 20 Battle Points, use: '!train [party number]'")
async def startSuperTrainingUI(ctx, trainer, partyPos=1):
    bpCost = 20
    partyPos = int(partyPos) - 1
    possibleNatureList = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy", "hasty",
                  "impish","jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet", "quirky", "rash", "relaxed",
                  "sassy", "serious", "timid"]
    yesOrNoList = ['yes', 'no']
    level100Prompt = "Would you like this Pokemon to advance to level 100?"
    naturePrompt = "Please enter desired nature:"
    hpIVPrompt = "Please enter the desired HP IV:"
    atkIVPrompt = "Please enter the desired ATK IV:"
    defIVPrompt = "Please enter the desired DEF IV:"
    spAtkIVPrompt = "Please enter the desired SP ATK IV:"
    spDefIVPrompt = "Please enter the desired SP DEF IV:"
    spdIVPrompt = "Please enter the desired SPD IV:"
    hpEVPrompt = "Please enter the desired HP EV:"
    atkEVPrompt = "Please enter the desired ATK EV:"
    defEVPrompt = "Please enter the desired DEF EV:"
    spAtkEVPrompt = "Please enter the desired SP ATK EV:"
    spDefEVPrompt = "Please enter the desired SP DEF EV:"
    spdEVPrompt = "Please enter the desired SPD EV:"
    confirmPrompt = "Would you like to pay " + str(bpCost) + " BP and commit these changes?"
    possibleIVList = []
    for x in range(0, 32):
        possibleIVList.append(str(x))
    possibleEVList = []
    for x in range(0, 253):
        possibleEVList.append(str(x))
    setTo100 = ''
    nature = ''
    hpIV = ''
    atkIV = ''
    defIV = ''
    spAtkIV = ''
    spDefIV = ''
    spdIV = ''
    hpEV = ''
    atkEV = ''
    defEV = ''
    spAtkEV = ''
    spDefEV = ''
    spdEV = ''
    confirm = ''
    promptList = [
        [level100Prompt, setTo100, yesOrNoList],
        [naturePrompt, nature, possibleNatureList],
        [hpIVPrompt, hpIV, possibleIVList],
        [atkIVPrompt, atkIV, possibleIVList],
        [defIVPrompt, defIV, possibleIVList],
        [spAtkIVPrompt, spAtkIV, possibleIVList],
        [spDefIVPrompt, spDefIV, possibleIVList],
        [spdIVPrompt, spdIV, possibleIVList],
        [hpEVPrompt, hpEV, possibleEVList],
        [atkEVPrompt, atkEV, possibleEVList],
        [defEVPrompt, defEV, possibleEVList],
        [spAtkEVPrompt, spAtkEV, possibleEVList],
        [spDefEVPrompt, spDefEV, possibleEVList],
        [spdEVPrompt, spdEV, possibleEVList],
        [confirmPrompt, confirm, yesOrNoList]
    ]
    # user, isNewUser = data.getUser(ctx)
    # if isNewUser:
    #     await ctx.send("You have not yet played the game and have no Pokemon!")
    # else:
    user = trainer
    if 'BP' in user.itemList.keys():
        totalBp = user.itemList['BP']
        if totalBp >= bpCost:
            if (len(user.partyPokemon) > partyPos):
                pokemon = user.partyPokemon[partyPos]
                files, embed = createTrainEmbed(ctx, pokemon)
                message = await ctx.send(files=files, embed=embed)

                for prompt in promptList:
                    optionString = ''
                    if 'IV' in prompt[0]:
                        optionString = "0 | 1 | ... | 30 | 31"
                    elif 'EV' in prompt[0]:
                        optionString = "0 | 1 | ... | 251 | 252"
                    else:
                        for option in prompt[2]:
                            if not optionString:
                                optionString += option.capitalize()
                            else:
                                optionString += " | " + option.capitalize()
                    optionString += "  |||  Cancel"
                    prompt[1] = await getUserTextEntryForTraining(ctx, message, embed, prompt[2],
                                                                    prompt[0] + "\n" + optionString)
                    if not prompt[1]:
                        await returnToOverworldFromSuperTraining(ctx, trainer, message)
                    if prompt[0] != confirmPrompt:
                        embed.add_field(name=prompt[0], value=prompt[1].upper(), inline=True)
                try:
                    setTo100 = promptList[0][1]
                    if setTo100.lower() == 'yes':
                        setTo100 = True
                    else:
                        setTo100 = False
                    nature = promptList[1][1]
                    hpIV = int(promptList[2][1])
                    atkIV = int(promptList[3][1])
                    defIV = int(promptList[4][1])
                    spAtkIV = int(promptList[5][1])
                    spDefIV = int(promptList[6][1])
                    spdIV = int(promptList[7][1])
                    hpEV = int(promptList[8][1])
                    atkEV = int(promptList[9][1])
                    defEV = int(promptList[10][1])
                    spAtkEV = int(promptList[11][1])
                    spDefEV = int(promptList[12][1])
                    spdEV = int(promptList[13][1])
                    confirm = promptList[14][1]
                    if confirm.lower() == 'yes':
                        confirm = True
                    else:
                        confirm = False
                except:
                    await message.delete()
                    message = await ctx.send("Something went wrong. " + str(ctx.author.display_name) + "'s training session cancelled. BP refunded.")
                    await returnToOverworldFromSuperTraining(ctx, trainer, message)
                if confirm:
                    totalEV = hpEV + atkEV + defEV + spAtkEV + spDefEV + spdEV
                    if totalEV > 510:
                        await message.delete()
                        message = await ctx.send("Total combined EV's cannot exceed 510, please try again. " + str(ctx.author.display_name) + "'s training session cancelled. BP refunded.")
                        await returnToOverworldFromSuperTraining(ctx, trainer, message)
                    if setTo100:
                        pokemon.level = 100
                        pokemon.exp = pokemon.calculateExpFromLevel(100)
                    pokemon.hpIV = hpIV
                    pokemon.atkIV = atkIV
                    pokemon.defIV = defIV
                    pokemon.spAtkIV = spAtkIV
                    pokemon.spDefIV = spDefIV
                    pokemon.spdIV = spdIV
                    pokemon.hpEV = hpEV
                    pokemon.atkEV = atkEV
                    pokemon.defEV = defEV
                    pokemon.spAtkEV = spAtkEV
                    pokemon.spDefEV = spDefEV
                    pokemon.spdEV = spdEV
                    pokemon.nature = nature.lower()
                    pokemon.setStats()
                    user.useItem('BP', bpCost)
                    embed.set_footer(text=pokemon.name + " has been successfully super trained! " + str(bpCost) + " BP spent. (continuing in 10 seconds...)")
                    await message.edit(embed=embed)
                    await sleep(4)
                    await returnToOverworldFromSuperTraining(ctx, trainer, message)
                else:
                    await message.delete()
                    message = await ctx.send(str(ctx.author.display_name) + "'s training session cancelled. BP refunded.")
                    await returnToOverworldFromSuperTraining(ctx, trainer, message)
            else:
                message = await ctx.send("No Pokemon in that party slot.")
                await returnToOverworldFromSuperTraining(ctx, trainer, message)
        await ctx.send("Sorry " + ctx.message.author.display_name + ", but you need at least " + str(bpCost) + " BP to train a Pokemon.")

async def returnToOverworldFromSuperTraining(ctx, trainer, message=None):
    await sleep(6)
    if message is not None:
        try:
            await message.delete()
        except:
            pass
    await startOverworldUI(ctx, trainer)

async def saveLoop():
    global allowSave
    global saveLoopActive
    saveLoopActive = True
    timeBetweenSaves = 10
    await sleep(timeBetweenSaves)
    try:
        channel = bot.get_channel(800534600677326908)
        await channel.send("Save loop enabled successfully.")
    except:
        pass
    while allowSave:
        try:
            data.writeUsersToJSON()
        except:
            try:
                channel = bot.get_channel(800534600677326908)
                await channel.send(("Saving failed.\n" + str(traceback.format_exc()))[-1999:])
            except:
                pass
        await sleep(timeBetweenSaves)
    try:
        channel = bot.get_channel(800534600677326908)
        await channel.send("Save loop disabled successfully.")
    except:
        pass
    saveLoopActive = False

timeout = 120.0
battleTimeout = 300.0
allowSave = True
saveLoopActive = False
data = pokeData()
data.readUsersFromJSON()
battleTower = Battle_Tower(data)
bot.run(TOKEN)
