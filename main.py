import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from Battle_Tower import Battle_Tower
from Battle_UI import Battle_UI
from Data import pokeData
from Pokemon import Pokemon
from Battle import Battle
from Trainer import Trainer
from PIL import Image, ImageDraw, ImageFont
from asyncio import sleep
import math
import traceback
from copy import copy
from datetime import datetime
import uuid
import random
import logging
from asyncio import gather

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!', help_command=None)

@bot.event
async def on_ready():
    try:
        channel = bot.get_channel(804463066241957981)
        await channel.send('NOTICE: PokeDiscord is online and ready for use.')
    except:
        pass
    logging.debug("PokeDiscord is online and ready for use.")
    await saveLoop()

@bot.command(name='start', help='starts the game', aliases=['s', 'begin'])
async def startGame(ctx):
    global allowSave
    logging.debug(str(ctx.author.id) + " - !start")
    if not allowSave:
        logging.debug(str(ctx.author.id) + " - not starting session, bot is down for maintenance")
        await ctx.send("Our apologies, but PokeDiscord is currently down for maintenance. Please try again later.")
        return
    user, isNewUser = data.getUser(ctx)
    try:
        #print('isNewUser = ', isNewUser)
        if (user in data.getTradeDict(ctx).keys()):
            logging.debug(str(ctx.author.id) + " - not starting session, user is waiting for a trade")
            await ctx.send("You are waiting for a trade, please finish the trade or wait for it to timeout before starting a session.")
            return
        sessionSuccess = data.addUserSession(ctx.message.guild.id, user)
        updateStamina(user)
        #print('sessionSuccess = ', sessionSuccess)
        if (sessionSuccess):
            if (isNewUser or (len(user.partyPokemon) == 0 and len(user.boxPokemon) == 0)):
                logging.debug(str(ctx.author.id) + " - is new user, picking starter Pokemon UI starting")
                await startNewUserUI(ctx, user)
            else:
                logging.debug(str(ctx.author.id) + " - is returning user, starting overworld UI")
                await startOverworldUI(ctx, user)
        else:
            logging.debug(str(ctx.author.id) + " - session failed to start, reason unknown but likely already has active session")
            #print('Unable to start session for: ' + str(ctx.message.author.display_name))
            await ctx.send('Unable to start session for: ' + str(ctx.message.author.display_name) + '. If you already have an active session, please end it before starting another one.')
    except:
        logging.error(str(ctx.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()) + "\n")
        #traceback.print_exc()
        user.dailyProgress += 1
        user.removeProgress(user.location)
        try:
            channel = bot.get_channel(804463066241957981)
            await channel.send(str(str(ctx.message.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()))[-1999:])
        except:
            try:
                channel = bot.get_channel(800534600677326908)
                await channel.send(str(str(ctx.message.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()))[-1999:])
            except:
                #print('e1')
                await ctx.send("An error occurred, please restart your session. If this persists, please report to an admin.")
        logging.error(str(ctx.author.id) + " - calling endSession() due to error")
        await endSession(ctx)

@bot.command(name='help', help='help command')
async def help(ctx):
    await ctx.send(str(ctx.message.author.mention) + ", Professor Birch will assist you in your Direct Messages.")
    files = []
    newline = "\n\n"
    halfNewline = "\n"
    embed = discord.Embed(title="PokeDiscord", description="Hello " + ctx.author.display_name + "," + newline +
                                                           "Professor Birch here! Let's get you the help you need!" + newline +
                                                           "For a full information guide, please see our website:\n[PokeDiscord website](https://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md)" + newline +
                                                           "If you need support, please join our official PokeDiscord server!\n[PokeDiscord official server](https://discord.gg/HwYME4Vwj9)" + newline +
                                                           "Otherwise, here is a list of commands, although all you need to begin using the bot is `!start`." + newline +
                                                           "`!start` - begin your adventure, use this each time you want to start a new session" + halfNewline +
                                                           "`!fly <location>` - after obtaining 6th badge, use to fly to any visited location" + halfNewline +
                                                           "`!map` - shows a visual map of the Hoenn region" + halfNewline +
                                                           "`!endSession` - while in the overworld, will end your current session" + halfNewline +
                                                           "`!profile [@user]` - get a trainer's profile" + halfNewline +
                                                           "`!trainerCard [@user]` - get a trainer's card" + halfNewline +
                                                           "`!nickname <party number> <name>` - nickname a Pokemon" + halfNewline +
                                                           "`!moveInfo <move name>` - get information about a move" + halfNewline +
                                                           "`!swapMoves <partyPos> <moveSlot1> <moveSlot2>` - swap 2 moves" + halfNewline +
                                                           "`!setAlteringCave <pokemonName>` - trade 10 BP to set the Pokemon in Altering Cave" + halfNewline +
                                                           "`!trade <partyNum> <@user>` - trade with another user" + halfNewline +
                                                           "`!pvp` - get matched with someone else at random to PVP them" + halfNewline +
                                                           "`!battle <@user>` - battle another user on the server" + halfNewline +
                                                           "`!battleCopy <@user>` - battle an NPC copy of another user on the server" + halfNewline +
                                                           "`!evolve <party number> [optional: Pokemon to evolve into]` - evolves a Pokemon capable of evolution" + halfNewline +
                                                           "`!unevolve <party number>` - unevolves a Pokemon with a pre-evolution" + halfNewline +
                                                           "`!releasePartyPokemon <partyNum>` - release a Pokemon from your party" + halfNewline +
                                                           "`!resetSave` - permanently reset your save file on a server" + halfNewline +
                                                           "`!guide` - guide to help you figure out where to go next" + halfNewline +
                                                           "`!getStamina [amount]` - trade 2000 Pokedollars per 1 stamina" + newline +
                                                           "Cheers,\nProfessor Birch",
                          color=0x00ff00)
    embed.set_footer(text="------------------------------------\nZetaroid#1391 - PokeDiscord Developer")
    try:
        if ctx.message.author.guild_permissions.administrator:
            embed.add_field(name='------------------------------------\nAdmin Commands:',
                            value="Oh hello there!\nI see you are an admin! Here are some extra commands for you:" + halfNewline +
                                  "`!disableStamina` - disables stamina for the server" + halfNewline +
                                  "`!enableStamina` - enables stamina for the server - on by default" + halfNewline +
                                  "`!grantItem <item> <amount> [@user]` - grants a specified item in amount to user (replace space in item name with '\_')" + halfNewline +
                                  "`!removeItem <item> <amount> [@user]` - removes a specified item in amount to user (replace space in item name with '\_')" + halfNewline +
                                  "`!grantStamina <amount> [@user]` - grants specified amount of stamina to user" + halfNewline +
                                  "`!setLocation <@user> <location>` - forcibly sets a user's location, (use while user is not in active session)" + halfNewline +
                                  "`!forceEndSession [@user]` - if user is unable to start a new session due to a bug, use this to unstuckify them"
                                  ,
                            inline=False)
    except:
        pass
    if str(ctx.author) == 'Zetaroid#1391':
        embed.add_field(name='------------------------------------\nDev Commands:',
                        value="Oh hello there!\nI see you are a dev! Here are some extra commands for you:" + halfNewline +
                        "`!grantFlag <flag> [userName] [server_id]` - grants flag to user" + halfNewline +
                        "`!removeFlag <flag> [userName=self] [server_id]` - removes flag from user" + halfNewline +
                        "`!save [flag=disable]` - disable save and manually save" + halfNewline +
                        "`!saveStatus` - view status of save variables" + halfNewline +
                        "`!test` - test things" + halfNewline +
                        "`!verifyChampion [userName]` - verify elite 4 victory for user" + halfNewline +
                        "`!displaySessionList` - display full active session list" + halfNewline +
                        "`!forceEndSession [user id num]` - remove user id from active session list" + halfNewline +
                        "`!linkSave [sourceServer] [targetServer]` - copy/link save from source to target" + halfNewline +
                        "`!viewFlags [userName=self] [server_id]` - views user flags (use '_' for spaces in flag name)"
                        ,
                        inline=False)
    thumbnailImage = discord.File("logo.png", filename="thumb.png")
    files.append(thumbnailImage)
    embed.set_thumbnail(url="attachment://thumb.png")
    channel = await ctx.author.create_dm()
    await channel.send(embed=embed,files=files)

@bot.command(name='resetSave', help='resets save file, this will wipe all of your data')
async def resetSave(ctx):
    logging.debug(str(ctx.author.id) + " - !resetSave")
    server_id = ctx.message.guild.id
    user, isNewUser = data.getUserByAuthor(server_id, ctx.author)
    if not isNewUser:
        if user in data.getSessionList(ctx):
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot reset your save while in an active session. Please wait up to 2 minutes for session to expire.")
            return

        confirmMessage = await ctx.send(str(ctx.author) + '\n\nWARNING: This command will reset your save data PERMANENTLY.\n\nType the following EXACTLY (including capitalization and punctuation) to confirm: "I WANT TO DELETE MY SAVE FILE."\n\nType "cancel" to cancel.')

        def check(m):
            return (m.content == 'I WANT TO DELETE MY SAVE FILE.' or m.content.lower() == 'cancel') \
                   and m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await bot.wait_for('message', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await confirmMessage.delete()
            await ctx.send(str(ctx.author.display_name) + "'s reset request timed out. Please try again.")
        else:
            responseContent = response.content
            if responseContent.lower() == 'cancel':
                await confirmMessage.delete()
                await ctx.send(str(ctx.author.display_name) + "'s reset request cancelled.")
                return ''
            elif responseContent == 'I WANT TO DELETE MY SAVE FILE.':
                success = data.deleteUser(server_id, user)
                if success:
                    await ctx.send(str(ctx.author.display_name) + "'s save file has been deleted. Poof.")
                else:
                    await ctx.send("There was an error deleting the save file.")
            else:
                await ctx.send(str(ctx.author.display_name) + " has provided an invalid response. Please try again.")
    else:
        await ctx.send("User '" + str(ctx.author) + "' not found, no save to reset...")

@bot.command(name='releasePartyPokemon', help="release a specified party Pokemon, cannot be undone, '!releasePartyPokemon [your party number to release]'")
async def releasePartyPokemon(ctx, partyNum):
    logging.debug(str(ctx.author.id) + " - !releasePartyPokemon")
    partyNum = int(partyNum)-1
    server_id = ctx.message.guild.id
    user, isNewUser = data.getUserByAuthor(server_id, ctx.author)
    if not isNewUser:
        if user in data.getSessionList(ctx):
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot release Pokemon while in an active session. Please wait up to 2 minutes for session to expire.")
            return

        if len(user.partyPokemon) <= 1:
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot release Pokemon when you only have 1 in your party.")
            return

        if partyNum >= len(user.partyPokemon) or partyNum < 0:
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you do not have a Pokemon in that slot.")
            return

        name = user.partyPokemon[partyNum].name
        confirmMessage = await ctx.send(str(ctx.author) + " is releasing: " + name + '\n\nWARNING: This command will release your selected Pokemon PERMANENTLY.\n\nType the following EXACTLY (including capitalization and punctuation) to confirm: "I WANT TO RELEASE MY POKEMON."\n\nType "cancel" to cancel.')

        def check(m):
            return (m.content == 'I WANT TO RELEASE MY POKEMON.' or m.content.lower() == 'cancel') \
                   and m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await bot.wait_for('message', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await confirmMessage.delete()
            await ctx.send(str(ctx.author.display_name) + "'s release request timed out. Please try again.")
        else:
            responseContent = response.content
            if responseContent.lower() == 'cancel':
                await confirmMessage.delete()
                await ctx.send(str(ctx.author.display_name) + "'s release request cancelled.")
                return ''
            elif responseContent == 'I WANT TO RELEASE MY POKEMON.':
                try:
                    del user.partyPokemon[partyNum]
                    await ctx.send(str(ctx.author.display_name) + "'s Pokemon was released. Bye bye " + name + "!")
                except:
                    await ctx.send("There was an error releasing the Pokemon.")
            else:
                await ctx.send(str(ctx.author.display_name) + " has provided an invalid response. Please try again.")
    else:
        await ctx.send("User '" + str(ctx.author) + "' not found, no Pokemon to release...")

@bot.command(name='verifyChampion', help='DEV ONLY: verify if user has beaten the elite 4')
async def verifyChampion(ctx, *, userName: str="self"):
    server_id = str(ctx.message.guild.id)
    fetched_user = await fetchUserFromServer(ctx, userName)
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(server_id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(server_id, userName, fetched_user)
    if not isNewUser:
        if 'elite4' in user.flags:
            await ctx.send(user.name + " is a league champion!")
        else:
            await ctx.send(user.name + " has NOT beaten the elite 4.")
    else:
        await ctx.send("User '" + userName + "' not found, cannot verify.")

@bot.command(name='grantFlag', help='DEV ONLY: grants user flag (use "_" for spaces in flag name), usage: "!grantFlag [flag, with _] [user] [server id = None]')
async def grantFlag(ctx, flag, userName: str="self", server_id=None):
    if not server_id:
        server_id = ctx.message.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = ctx.message.guild.id
    fetched_user = await fetchUserFromServer(ctx, userName)
    flag = flag.replace("_", " ")
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(server_id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(server_id, userName, fetched_user)
    if not isNewUser:
        user.addFlag(flag)
        await ctx.send(user.name + ' has been granted the flag: "' + flag + '".')
    else:
        await ctx.send("User '" + userName + "' not found, cannot grant flag.")

@bot.command(name='viewFlags', help='DEV ONLY: views user flags, usage: "!viewFlags [user] [server id = None]')
async def viewFlags(ctx, userName: str="self", server_id=None):
    if not server_id:
        server_id = ctx.message.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = ctx.message.guild.id
    fetched_user = await fetchUserFromServer(ctx, userName)
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(server_id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(server_id, userName, fetched_user)
    if not isNewUser:
        await ctx.send(user.name + ' flags:\n' + str(user.flags))
    else:
        await ctx.send("User '" + userName + "' not found, cannot revoke flag.")

@bot.command(name='removeFlag', help='DEV ONLY: grants user flag (use "_" for spaces in flag name), usage: "!removeFlag [flag, with _] [user] [server id = None]')
async def removeFlag(ctx, flag, userName: str="self", server_id=None):
    if not server_id:
        server_id = ctx.message.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = ctx.message.guild.id
    fetched_user = await fetchUserFromServer(ctx, userName)
    flag = flag.replace("_", " ")
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(server_id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(server_id, userName, fetched_user)
    if not isNewUser:
        if user.removeFlag(flag):
            await ctx.send(user.name + ' has been revoked the flag: "' + flag + '".')
        else:
            await ctx.send(user.name + ' did not have the flag: "' + flag + '". Nothing to revoke.')
    else:
        await ctx.send("User '" + userName + "' not found, cannot revoke flag.")

@bot.command(name='linkSave', help='DEV ONLY: copy my save to PokeDiscord server from Apparently a Chat')
async def linkSaveCommand(ctx, sourceServer=None, targetServer=None):
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    linkZetaroidSave(ctx.author, sourceServer, targetServer)
    await ctx.send("Data copied successfully.")

def linkZetaroidSave(author=None, sourceServer=None, targetServer=None):
    if not author:
        author = "Zetaroid#1391"
    if not sourceServer:
        aac_id = 303282588901179394
    else:
        aac_id = int(sourceServer)
    if not targetServer:
        pd_id = 805976403140542476
    else:
        pd_id = int(targetServer)
    user, isNewUser = data.getUserByAuthor(aac_id, author)
    oldUser, isNewUser2 = data.getUserByAuthor(pd_id, author)
    try:
        data.userDict[str(pd_id)].remove(oldUser)
    except:
        pass
    data.userDict[str(pd_id)].append(user)

@bot.command(name='displaySessionList', help='DEV ONLY: display the active session list')
async def displaySessionList(ctx):
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    messageStr = 'Active session list:\n\nserver: [user id 1, user id 2, ...]\n\n'
    for key, userList in data.sessionDict.items():
        messageStr += str(key) + ': ['
        first = True
        for user in userList:
            if not first:
                messageStr += ", "
            first = False
            identifier = str(user.identifier)
            if identifier == -1:
                identifier = str(user.author)
            messageStr += identifier
        messageStr += "]\n\n"
    await ctx.send(messageStr)

@bot.command(name='forceEndSession', help='ADMIN ONLY: forcibly removes user from active sessions list, usage: !forceEndSession [user]')
async def forceEndSession(ctx, *, userName: str="self"):
    fetched_user = await fetchUserFromServer(ctx, userName)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !forceEndsession for " + userName)

        if ctx.author.id == 189312357892096000:
            try:
                userName = int(userName)
                logging.debug("Trying to find user by number.")
                found = False
                selectedServer = ''
                for key, userList in data.sessionDict.items():
                    for user in userList:
                        if user.identifier == userName:
                            userList.remove(user)
                            found = True
                            selectedServer = key
                if found:
                    logging.debug(str(ctx.author.id) + " - user " + str(userName) + " has been removed from active session list from server '" + str(selectedServer) + "'")
                    await ctx.send("User '" + str(userName) + "' has been removed from active session list from server '" + str(selectedServer) + "'")
                    return
                else:
                    logging.debug(str(ctx.author.id) + " - user " + str(userName) + " not found")
                    await ctx.send("User '" + str(userName) + "' not found.")
                    return
            except:
                logging.debug("forceEndSession input is not a number, continuing as normal")

        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
        if not isNewUser:
            success = data.removeUserSession(ctx.message.guild.id, user)
            if success:
                logging.debug(str(ctx.author.id) + " - user " + str(userName) + " has been removed from active session list")
                await ctx.send("User '" + str(userName) + "' has been removed from the active session list.")
            else:
                logging.debug(str(ctx.author.id) + " - user " + str(userName) + " not in active session list")
                await ctx.send("User '" + str(userName) + "' not in active session list.")
        else:
            logging.debug(str(ctx.author.id) + " - user " + str(userName) + " not found")
            await ctx.send("User '" + str(userName) + "' not found.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='grantStamina', help='ADMIN ONLY: grants user stamina in amount specified, usage: !grantStamina [amount] [user]')
async def grantStamina(ctx, amount, *, userName: str="self"):
    fetched_user = await fetchUserFromServer(ctx, userName)
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !grantStamina for " + userName)
        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
        if not isNewUser:
            user.dailyProgress += amount
            await ctx.send(user.name + ' has been granted ' + str(amount) + ' stamina.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant stamina.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='grantItem', help='ADMIN ONLY: grants user item (use "_" for spaces in item name) in amount specified, usage: !grantItem [item] [amount] [user]')
async def grantItem(ctx, item, amount, *, userName: str="self"):
    fetched_user = await fetchUserFromServer(ctx, userName)
    item = item.replace('_', " ")
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !grantItem " + item + " for " + userName)
        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
        if not isNewUser:
            user.addItem(item, amount)
            await ctx.send(user.name + ' has been granted ' + str(amount) + ' of ' + item + '.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant stamina.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='removeItem', help='ADMIN ONLY: removes user item (use "_" for spaces in item name) in amount specified, usage: !removeItem [item] [amount] [user]')
async def removeItem(ctx, item, amount, *, userName: str="self"):
    fetched_user = await fetchUserFromServer(ctx, userName)
    item = item.replace('_', " ")
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !removeItem " + item + " for " + userName)
        if userName == 'self':
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
        else:
            user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
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
        logging.debug(str(ctx.author.id) + " - !disableStamina")
        data.staminaDict[str(ctx.message.guild.id)] = False
        await ctx.send("Stamina has been disabled on this server.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='enableStamina', help='ADMIN ONLY: enables stamina cost server wide for all users')
async def enableStamina(ctx):
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !enableStamina")
        data.staminaDict[str(ctx.message.guild.id)] = True
        await ctx.send("Stamina has been enabled on this server.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='setLocation', help='ADMIN ONLY: sets a players location, usage: !setLocation [user#1234] [location]')
async def setLocation(ctx, userName, *, location):
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !setLocation to " + location + " for " + userName)
        fetched_user = await fetchUserFromServer(ctx, userName)
        if userName == "self":
            userName = str(ctx.message.author)
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
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
    logging.debug(str(ctx.author.id) + " - endSession() called")
    user, isNewUser = data.getUser(ctx)
    removedSuccessfully = data.removeUserSession(ctx.message.guild.id, user)
    # if ctx.message.author in data.overworldSessions:
    #     try:
    #         data.overworldSessions[ctx.message.author][0].close()
    #         del data.overworldSessions[ctx.message.author]
    #     except:
    #         pass
    if (removedSuccessfully):
        logging.debug(str(ctx.author.id) + " - endSession() session ended successfully, connection closed")
        await ctx.send(ctx.message.author.display_name + "'s session ended. Please start game again with `!start`.")
    else:
        logging.debug(str(ctx.author.id) + " - endSession() session unable to end, not in session list")
        try:
            channel = bot.get_channel(804463066241957981)
            await channel.send("Session unable to end, not in session list: " + str(ctx.message.author.id))
        except:
            try:
                channel = bot.get_channel(800534600677326908)
                await channel.send("Session unable to end, not in session list: " + str(ctx.message.author.id))
            except:
                #print('e2')
                await ctx.send("An error occurred when ending session, please restart your session. If this persists, please report to an admin.")

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
    logging.debug(str(ctx.author.id) + " - !getStamina " + str(amount))
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

@bot.command(name='setAlteringCave', help='trade 10 BP to set the Pokemon in Altering Cave (requirements: must have beaten Elite 4, no legendaries), use: "!sac [Pokemon name]"', aliases=['sac'])
async def setAlteringCave(ctx, *, pokemonName):
    logging.debug(str(ctx.author.id) + " - !setAlteringCave " + pokemonName)
    bpCost = 10
    bannedList = [
        "Articuno",
        "Zapdos",
        "Moltres",
        "Raikou",
        "Entei",
        "Suicune",
        "Uxie",
        "Mesprit",
        "Azelf",
        "Heatran",
        "Regigigas",
        "Cresselia",
        "Cobalion",
        "Terrakion",
        "Virizion",
        "Tornadus",
        "Thundurus",
        "Landorus",
        "Silvally",
        "Tapu Koko",
        "Tapu Lele",
        "Tapu Bulu",
        "Tapu Fini",
        "Nihilego",
        "Buzzwole",
        "Pheromosa",
        "Xurkitree",
        "Celesteela",
        "Kartana",
        "Guzzlord",
        "Naganadel",
        "Stakataka",
        "Blacephalon",
        "Mewtwo",
        "Dialga",
        "Palkia",
        "Giratina",
        "Reshiram",
        "Zekrom",
        "Kyurem",
        "Xerneas",
        "Yveltal",
        "Zygarde",
        "Marshadow",
        "Magearna",
        "Solgaleo",
        "Lunala",
        "Necrozma",
        "Celebi",
        "Jirachi",
        "Zeraora",
        "Manaphy",
        "Darkrai",
        "Shaymin",
        "Arceus",
        "Victini",
        "Keldeo",
        "Meloetta",
        "Genesect",
        "Diancie",
        "Hoopa",
        "Volcanion",
        "Regirock",
        "Regice",
        "Registeel",
        "Latios",
        "Latias",
        "Mew",
        "Lugia",
        "Ho-Oh",
        "Kyogre",
        "Groudon",
        "Rayquaza",
        "Deoxys"
    ]
    user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.message.author)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        pokemon = None
        try:
            pokemon = data.getPokemonData(pokemonName)
        except:
            pass
        if pokemon is not None:
            if pokemon['names']['en'] not in bannedList:
                if 'BP' in user.itemList.keys():
                    totalBp = user.itemList['BP']
                    if totalBp >= bpCost:
                        user.useItem('BP', bpCost)
                        user.alteringPokemon = pokemon['names']['en']
                        await ctx.send("Congratulations " + ctx.message.author.display_name + "! You set the Altering Cave Pokemon to be " + pokemon['names']['en'] + "! (at the cost of " + str(bpCost) + " BP mwahahaha).")
                    else:
                        await ctx.send("Sorry " + ctx.message.author.display_name + ", but you need at least " + str(bpCost) + " to trade for setting the Altering Cave Pokemon.")
                else:
                    await ctx.send("Sorry " + ctx.message.author.display_name + ", but you need at least " + str(bpCost) + " to trade for setting the Altering Cave Pokemon.")
            else:
                await ctx.send("Pokemon '" + pokemonName + "' cannot be set for Altering Cave.")
        else:
            await ctx.send("Pokemon '" + pokemonName + "' not found.")

@bot.command(name='nickname', help='nickname a Pokemon, use: "!nickname [party position] [nickname]"', aliases=['nn'])
async def nickname(ctx, partyPos, *, nickname):
    logging.debug(str(ctx.author.id) + " - !nickname " + str(partyPos) + ' ' + nickname)
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
    logging.debug(str(ctx.author.id) + " - !swapMoves " + str(partyPos) + ' ' +  str(moveSlot1) + ' ' + str(moveSlot2))
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

@bot.command(name='battle', help="battle an another user on the server, use: '!battle [trainer name]'", aliases=['b', 'battleTrainer', 'duel', 'pvp'])
async def battleTrainer(ctx, *, trainerName: str="self"):
    logging.debug(str(ctx.author.id) + " - !battle " + trainerName)
    user, isNewUser = data.getUser(ctx)
    if '<' in trainerName and '>' in trainerName and '@' in trainerName and '!' in trainerName:
        idToBattle = int(trainerName.replace("<", "").replace("@", "").replace(">", "").replace("!", ""))
    elif trainerName == 'self':
        pass
    else:
        await ctx.send("Please @ a user to battle.\nExample: `!battle @Zetaroid`")
        return
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if user in data.getSessionList(ctx):
            await ctx.send("Sorry " + str(ctx.message.author.mention) + ", but you cannot battle another player while in an active session. Please end current session with `!endSession` or wait for it to timeout.")
        else:
            if trainerName == 'self':
                # await ctx.send("Must input a user to battle.\nExample: `!battle @Zetaroid`")
                if user in data.matchmakingDict:
                    await ctx.send("You are already in a PVP battle.")
                    return
                await ctx.send("Looking for match...")
                if len(data.matchmakingDict.keys()) == 0:
                    data.matchmakingDict[user] = (ctx, False)
                    count = 0
                    while count < pvpTimeout:
                        if user in data.matchmakingDict:
                            matchStarted = data.matchmakingDict[user][1]
                            if matchStarted:
                                break
                        else:
                            break
                        if count == pvpTimeout/2:
                            await ctx.send("Still looking for match...")
                        await sleep(5)
                        count += 5
                    if count >= pvpTimeout:
                        try:
                            del data.matchmakingDict[user]
                        except:
                            pass
                        await ctx.send("Matchmaking timed out. No opponent found.")
                else:
                    userToBattle = None
                    userToBattleCopy = None
                    ctx2 = None
                    for tempUser, matchmakingTuple in data.matchmakingDict.items():
                        matchFoundAlready = matchmakingTuple[1]
                        if not matchFoundAlready:
                            data.matchmakingDict[tempUser] = (matchmakingTuple[0], True)
                            userToBattle = tempUser
                            userToBattleCopy = copy(tempUser)
                            ctx2 = matchmakingTuple[0]
                            break
                    if userToBattleCopy is None or ctx2 is None:
                        await ctx.send("Matchmaking timed out. No opponent found.")
                        return
                    else:
                        await ctx.send("Match found.")
                        await ctx2.send("Match found.")
                        data.matchmakingDict[user] = (ctx, True)
                    userCopy = copy(user)
                    userCopy.scaleTeam(None, 100)
                    userToBattleCopy.scaleTeam(None, 100)
                    userCopy.pokemonCenterHeal()
                    userToBattleCopy.pokemonCenterHeal()
                    userCopy.location = 'Petalburg Gym'
                    userToBattleCopy.location = 'Petalburg Gym'
                    ctx1 = ctx
                    battle = Battle(data, userToBattleCopy, userCopy)
                    battle.startBattle()
                    battle.disableExp()
                    battle.isPVP = True
                    battle_ui1 = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                           startNewUI, continueUI, startPartyUI, startOverworldUI,
                                           startBattleTowerUI, startCutsceneUI)
                    battle_ui2 = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                           startNewUI, continueUI, startPartyUI, startOverworldUI,
                                           startBattleTowerUI, startCutsceneUI)
                    ui1 = battle_ui1.startBattleUI(ctx1, False, battle, '', None, False, True)
                    ui2 = battle_ui2.startBattleUI(ctx2, False, battle, '', None, False, False)
                    await gather(ui1, ui2)
                    await ctx1.send("Battle has ended.")
                    await ctx2.send("Battle has ended.")
                    try:
                        del data.matchmakingDict[userToBattle]
                        del data.matchmakingDict[user]
                    except:
                        pass
            else:
                fetched_user = await fetchUserFromServer(ctx, trainerName)
                userToBattle = data.getUserById(ctx.message.guild.id, idToBattle)
                if userToBattle:
                    if user.author != userToBattle.author:
                        serverPvpDict = data.getServerPVPDict(ctx)
                        matchFound = False
                        for tempUser in list(serverPvpDict.keys()):
                            if tempUser.identifier == user.identifier:
                                if userToBattle.identifier == serverPvpDict[tempUser][0].identifier:
                                    matchFound = True
                                    await ctx.send("Battle has been accepted. Starting battle...")
                                    await serverPvpDict[tempUser][1].send("Battle has been accepted. Starting battle...")
                                    userCopy = copy(user)
                                    userToBattleCopy = copy(serverPvpDict[tempUser][0])
                                    userCopy.scaleTeam(None, 100)
                                    userToBattleCopy.scaleTeam(None, 100)
                                    userCopy.pokemonCenterHeal()
                                    userToBattleCopy.pokemonCenterHeal()
                                    userCopy.location = 'Petalburg Gym'
                                    userToBattleCopy.location = 'Petalburg Gym'
                                    ctx1 = ctx
                                    ctx2 = serverPvpDict[tempUser][1]
                                    battle = Battle(data, userToBattleCopy, userCopy)
                                    battle.startBattle()
                                    battle.disableExp()
                                    battle.isPVP = True
                                    serverPvpDict[tempUser] = (serverPvpDict[tempUser][0], serverPvpDict[tempUser][1], True)
                                    battle_ui1 = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                                          startNewUI, continueUI, startPartyUI, startOverworldUI,
                                                          startBattleTowerUI, startCutsceneUI)
                                    battle_ui2 = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                                          startNewUI, continueUI, startPartyUI, startOverworldUI,
                                                          startBattleTowerUI, startCutsceneUI)
                                    ui1 = battle_ui1.startBattleUI(ctx1, False, battle, '', None, False, True)
                                    ui2 = battle_ui2.startBattleUI(ctx2, False, battle, '', None, False, False)
                                    await gather(ui1, ui2)
                                    await ctx.send("Battle has ended.")
                                    await serverPvpDict[tempUser][1].send("Battle has ended.")
                                    if tempUser in serverPvpDict.keys():
                                        del serverPvpDict[tempUser]
                        if not matchFound:
                            match_started = False
                            serverPvpDict[userToBattle] = (user, ctx, match_started)
                            await ctx.send(str(ctx.author.mention) + " has requested a battle against " + trainerName + ". They have 2 minutes to respond.")
                            await sleep(pvpTimeout)
                            if userToBattle in serverPvpDict.keys():
                                if not serverPvpDict[userToBattle][2]:
                                    del serverPvpDict[userToBattle]
                                    await ctx.send(trainerName + " did not respond to battle request. Please try again. If you would instead like to battle an NPC-controlled copy of this user, please use `!battleCopy @user`.")
                    else:
                        await ctx.send("Cannot battle yourself.")
                else:
                    await ctx.send("User '" + trainerName + "' not found.")

@bot.command(name='battleCopy', help="battle an NPC of another trainer, use: '!battleCopy [trainer name]'")
async def battleCopy(ctx, *, trainerName: str="self"):
    logging.debug(str(ctx.author.id) + " - !battleCopy " + trainerName)
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
                fetched_user = await fetchUserFromServer(ctx, trainerName)
                userToBattle, isNewUser = data.getUserByAuthor(ctx.message.guild.id, trainerName, fetched_user)
                if not isNewUser:
                    if user.author != userToBattle.author:
                        userToBattle = copy(userToBattle)
                        user = copy(user)
                        user.scaleTeam(None, 100)
                        userToBattle.scaleTeam(None, 100)
                        userToBattle.pokemonCenterHeal()
                        user.pokemonCenterHeal()
                        user.location = 'Petalburg Gym'
                        user.itemList.clear()
                        battle = Battle(data, user, userToBattle)
                        battle.disableExp()
                        battle.startBattle()
                        await startBeforeTrainerBattleUI(ctx, False, battle, "PVP")
                    else:
                        await ctx.send("Cannot battle yourself.")
                else:
                    await ctx.send("User '" + trainerName + "' not found.")

@bot.command(name='endSession', help="ends the current session", aliases=['es', 'end', 'quit', 'close', 'endsession'])
async def endSessionCommand(ctx):
    logging.debug(str(ctx.author.id) + " - !endSession - Command")
    user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.message.author)
    if isNewUser:
        logging.debug(str(ctx.author.id) + " - not ending session, have not started game yet")
        await ctx.send("You have not yet played the game and have no active session!")
    else:
        if ctx.message.author in data.overworldSessions.keys():
            try:
                message = data.overworldSessions[ctx.message.author][0]
                await message.delete()
                data.expiredSessions.append(data.overworldSessions[ctx.message.author][1])
                del data.overworldSessions[ctx.message.author]
            except:
                logging.error(str(ctx.author.id) + " - end session command had an error\n" + str(traceback.format_exc()))
                try:
                    channel = bot.get_channel(804463066241957981)
                    await channel.send(str(
                        str(ctx.message.author.id) + "'s end session command attempt had an error.\n" + str(traceback.format_exc()))[
                                       -1999:])
                except:
                    try:
                        channel = bot.get_channel(800534600677326908)
                        await channel.send(str(str(ctx.message.author.id) + "'s end session command attempt had an error.\n" + str(
                            traceback.format_exc()))[-1999:])
                    except:
                        pass
            logging.debug(str(ctx.author.id) + " - calling endSession() from endSessionCommand()")
            await endSession(ctx)
        else:
            logging.debug(str(ctx.author.id) + " - not ending session, not in overworld or not active session")
            await ctx.send("You must be in the overworld in an active session to end a session.")

@bot.command(name='fly', help="fly to a visited location, use: '!fly [location name]'", aliases=['f'])
async def fly(ctx, *, location: str=""):
    logging.debug(str(ctx.author.id) + " - !fly " + location)
    user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.message.author)
    if isNewUser:
        logging.debug(str(ctx.author.id) + " - not flying, have not started game yet")
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if 'fly' in user.flags:
            elite4Areas = ['Elite 4 Room 1', 'Elite 4 Room 2', 'Elite 4 Room 3', 'Elite 4 Room 4', 'Champion Room',
                           'Elite 4 Room 1 Lv70', 'Elite 4 Room 2 Lv70', 'Elite 4 Room 3 Lv70', 'Elite 4 Room 4 Lv70',
                           'Champion Room Lv70',
                           'Elite 4 Room 1 Lv100', 'Elite 4 Room 2 Lv100', 'Elite 4 Room 3 Lv100',
                           'Elite 4 Room 4 Lv100', 'Champion Room Lv100']
            if user not in data.getSessionList(ctx):
                logging.debug(str(ctx.author.id) + " - not flying, not in active session")
                await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot fly without being in an active session. Please start a session with '!start'.")
            else:
                if location in user.locationProgressDict.keys():
                    if location in elite4Areas:
                        logging.debug(str(ctx.author.id) + " - not flying, cannot fly to elite 4 areas")
                        await ctx.send("Sorry, cannot fly to the elite 4 battle areas!")
                    elif user.location in elite4Areas:
                        logging.debug(str(ctx.author.id) + " - not flying, cannot fly while fighting elite 4")
                        await ctx.send("Sorry, cannot fly while taking on the elite 4!")
                    else:
                        if ctx.message.author in data.overworldSessions.keys():
                            try:
                                # data.overworldSessions[ctx.message.author][0].close()
                                message = data.overworldSessions[ctx.message.author][0]
                                await message.delete()
                                data.expiredSessions.append(data.overworldSessions[ctx.message.author][1])
                                del data.overworldSessions[ctx.message.author]
                            except:
                                #traceback.print_exc()
                                logging.error(str(ctx.author.id) + " - flying had an error\n" + str(traceback.format_exc()))
                                try:
                                    channel = bot.get_channel(804463066241957981)
                                    await channel.send(str(str(ctx.message.author.id) + "'s fly attempt had an error.\n" + str(traceback.format_exc()))[-1999:])
                                except:
                                    try:
                                        channel = bot.get_channel(800534600677326908)
                                        await channel.send(str(str(ctx.message.author.id) + "'s fly attempt had an error.\n" + str(traceback.format_exc()))[-1999:])
                                    except:
                                        pass
                            logging.debug(str(ctx.author.id) + " - flying successful")
                            user.location = location
                            flyMessage = await ctx.send(ctx.message.author.display_name + " used Fly! Traveled to: " + location + "!\n(continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await flyMessage.delete()
                            await startOverworldUI(ctx, user)
                        else:
                            logging.debug(str(ctx.author.id) + " - not flying, not in overworld")
                            await ctx.send("Cannot fly while not in the overworld.")
                else:
                    logging.debug(str(ctx.author.id) + " - not flying, invalid location")
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
            logging.debug(str(ctx.author.id) + " - not flying, have not earned 6th badge")
            await ctx.send("Sorry, " + ctx.message.author.display_name + ", but you have not learned how to Fly yet!")

@bot.command(name='profile', help="get a Trainer's profile, use: '!profile [trainer name]'", aliases=['p'])
async def profile(ctx, *, userName: str="self"):
    logging.debug(str(ctx.author.id) + " - !profile " + userName)
    fetched_user = await fetchUserFromServer(ctx, userName)
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
    if not isNewUser:
        embed = createProfileEmbed(ctx, user)
        await ctx.send(embed=embed)
    else:
        if userName == 'self':
            userName = str(ctx.author)
        await ctx.send("User '" + userName + "' not found.")

@bot.command(name='trainerCard', help="get a Trainer's card, use: '!trainerCard [trainer name]'", aliases=['tc'])
async def trainerCard(ctx, *, userName: str="self"):
    logging.debug(str(ctx.author.id) + " - !trainerCard " + userName)
    fetched_user = await fetchUserFromServer(ctx, userName)
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
    if not isNewUser:
        createTrainerCard(user)
        await ctx.send(file=discord.File('data/temp/trainerCardNew.png'))
    else:
        if userName == 'self':
            userName = str(ctx.author)
        await ctx.send("User '" + userName + "' not found.")

@bot.command(name='map', help="shows the map")
async def showMap(ctx, region='hoenn'):
    logging.debug(str(ctx.author.id) + " - !map")
    files = []
    if region.lower() == 'sinnoh':
        title = "Sinnoh Map"
        file = discord.File("data/sprites/map_sinnoh.png", filename="image.png")
    else:
        title = "Hoenn Map"
        file = discord.File("data/sprites/map.png", filename="image.png")
    files.append(file)
    embed = discord.Embed(title=title,
                          description="For your viewing pleasure.",
                          color=0x00ff00)
    embed.set_image(url="attachment://image.png")
    await ctx.send(embed=embed, files=files)

@bot.command(name='trade', help="trade with another user, use: '!trade [your party number to trade] [trainer name to trade with]'", aliases=['t'])
async def trade(ctx, partyNum, *, userName):
    logging.debug(str(ctx.author.id) + " - !trade " + str(partyNum) + " " + userName)
    partyNum = int(partyNum)
    fetched_user = await fetchUserFromServer(ctx, userName)
    userToTradeWith, isNewUser1 = data.getUserByAuthor(ctx.message.guild.id, userName, fetched_user)
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

    def check(payload):
        payloadAuthor = payload.member.name + "#" + payload.member.discriminator
        return ((payloadAuthor == str(user1.author) or payloadAuthor == str(user2.author)) and (
                    payload.emoji == data.getEmoji('confirm') or payload.emoji == data.getEmoji('cancel')))

    async def waitForEmoji(ctx, confirmedList):
        try:
            payload = await bot.wait_for('raw_reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message.delete()
            expiredMessage = await ctx.send('Trade between ' + str(user1.name) + ' and ' + str(user2.name) + " timed out.")
            if user1 in data.getTradeDict(ctx).keys():
                del data.getTradeDict(ctx)[user1]
            if user2 in data.getTradeDict(ctx).keys():
                del data.getTradeDict(ctx)[user2]
        else:
            payloadAuthor = payload.member.name + "#" + payload.member.discriminator
            userValidated = False
            if (messageID == payload.message_id):
                userValidated = True
            if userValidated:
                if (payload.emoji == data.getEmoji('confirm')):
                    if payloadAuthor == str(user1.author) and str(user1.author) not in confirmedList:
                        confirmedList.append(user1.author)
                    elif payloadAuthor == str(user2.author) and str(user2.author) not in confirmedList:
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
                elif (payload.emoji == data.getEmoji('cancel')):
                    await message.delete()
                    cancelMessage = await ctx.send(payloadAuthor + " cancelled trade.")
                    if user1 in data.getTradeDict(ctx).keys():
                        del data.getTradeDict(ctx)[user1]
                    if user2 in data.getTradeDict(ctx).keys():
                        del data.getTradeDict(ctx)[user2]
                    return
                await waitForEmoji(ctx, confirmedList)

    await waitForEmoji(ctx, confirmedList)

@bot.command(name='guide', help='helpful guide', aliases=['g'])
async def getGuide(ctx):
    await ctx.send('Check out our guide here:\nhttps://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md#Guide')

@bot.command(name='moveInfo', help='get information about a move', aliases=['mi'])
async def getMoveInfo(ctx, *, moveName="Invalid"):
    logging.debug(str(ctx.author.id) + " - !getMoveInfo " + moveName)
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

@bot.command(name='evolve', help="evolves a Pokemon capable of evolution, use: '!evolve [party number] <pokemon to evolve into, random if not given or invalid'")
async def forceEvolve(ctx, partyPos, targetPokemon=None):
    logging.debug(str(ctx.author.id) + " - !evolve " + str(partyPos))
    partyPos = int(partyPos) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > partyPos):
            oldName = user.partyPokemon[partyPos].nickname
            success = user.partyPokemon[partyPos].forceEvolve(targetPokemon)
            if success:
                await ctx.send(oldName + " evolved into '" + user.partyPokemon[partyPos].name + "'!")
            else:
                await ctx.send("'" + user.partyPokemon[partyPos].name + "' cannot evolve.")
        else:
            await ctx.send("No Pokemon in that party slot.")

@bot.command(name='unevolve', help="unevolves a Pokemon, use: '!unevolve [party number]'")
async def unevolve(ctx, partyPos):
    logging.debug(str(ctx.author.id) + " - !unevolve " + str(partyPos))
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
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    logging.debug(str(ctx.author.id) + " - !save " + flag)
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
    global saveLoopActive
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    await ctx.send("allowSave = " + str(allowSave) + '\n' + 'saveLoopActive = ' + str(saveLoopActive))

@bot.command(name='test', help='DEV ONLY: test various features')
async def testWorldCommand(ctx):
    if ctx.author.id != 189312357892096000:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return
    location = "Route 103 W"
    progress = 3
    pokemonPairDict = {
        "Mudkip": 5,
        "Piplup": 5
    }
    movesPokemon1 = [
        "Tackle",
        "Earthquake",
        "Ice Beam",
        "Headbutt"
    ]
    flagList = ["rival1", "badge1", "badge2", "badge4", "briney", "surf"]
    trainer = Trainer(123, "Zetaroid", "Marcus", location)
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
    temp_uuid = uuid.uuid4()
    filename = "data/temp/merged_image" + str(temp_uuid) + ".png"
    background.save(filename,"PNG")
    return filename

def createTrainerCard(trainer):
    numberOfBadges = 0
    backgroundPath = 'data/sprites/trainerCard.png'
    pokemonPathDict = {}
    for index in range(0, 6):
        if len(trainer.partyPokemon) > index:
            pokemonPathDict[index+1] = trainer.partyPokemon[index].getSpritePath()
    background = Image.open(backgroundPath)
    background = background.convert('RGBA')
    trainerSpritePath = 'data/sprites/trainerSprite.png'
    trainerSprite = Image.open(trainerSpritePath)
    badgePath = "data/sprites/badges/badge"
    badgeImage1 = Image.open(badgePath + '1.png')
    badgeImage2 = Image.open(badgePath + '2.png')
    badgeImage3 = Image.open(badgePath + '3.png')
    badgeImage4 = Image.open(badgePath + '4.png')
    badgeImage5 = Image.open(badgePath + '5.png')
    badgeImage6 = Image.open(badgePath + '6.png')
    badgeImage7 = Image.open(badgePath + '7.png')
    badgeImage8 = Image.open(badgePath + '8.png')
    background.paste(trainerSprite, (10, 75), trainerSprite.convert('RGBA'))
    if len(pokemonPathDict.keys()) >= 1:
        image1 = Image.open(pokemonPathDict[1])
        background.paste(image1, (180, 65), image1.convert('RGBA'))
    if len(pokemonPathDict.keys()) >= 2:
        image2 = Image.open(pokemonPathDict[2])
        background.paste(image2, (305, 65), image2.convert('RGBA'))
    if len(pokemonPathDict.keys()) >= 3:
        image3 = Image.open(pokemonPathDict[3])
        background.paste(image3, (430, 65), image3.convert('RGBA'))
    if len(pokemonPathDict.keys()) >= 4:
        image4 = Image.open(pokemonPathDict[4])
        background.paste(image4, (180, 150), image4.convert('RGBA'))
    if len(pokemonPathDict.keys()) >= 5:
        image5 = Image.open(pokemonPathDict[5])
        background.paste(image5, (305, 150), image5.convert('RGBA'))
    if len(pokemonPathDict.keys()) >= 6:
        image6 = Image.open(pokemonPathDict[6])
        background.paste(image6, (430, 150), image6.convert('RGBA'))
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
    if numberOfBadges >= 8:
        background.paste(badgeImage8, (454, 288), badgeImage8.convert('RGBA'))
    if numberOfBadges >= 7:
        background.paste(badgeImage7, (397, 288), badgeImage7.convert('RGBA'))
    if numberOfBadges >= 6:
        background.paste(badgeImage6, (340, 288), badgeImage6.convert('RGBA'))
    if numberOfBadges >= 5:
        background.paste(badgeImage5, (283, 288), badgeImage5.convert('RGBA'))
    if numberOfBadges >= 4:
        background.paste(badgeImage4, (226, 288), badgeImage4.convert('RGBA'))
    if numberOfBadges >= 3:
        background.paste(badgeImage3, (169, 288), badgeImage3.convert('RGBA'))
    if numberOfBadges >= 2:
        background.paste(badgeImage2, (112, 288), badgeImage2.convert('RGBA'))
    if numberOfBadges >= 1:
        background.paste(badgeImage1, (55, 288), badgeImage1.convert('RGBA'))
    fnt = ImageFont.truetype('data/fonts/pokemonGB.ttf', 10)
    d = ImageDraw.Draw(background)
    d.text((310, 40), trainer.name, font=fnt, fill=(0, 0, 0))
    background.save("data/temp/trainerCardNew.png", "PNG")

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
            battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                  startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
            await battle_ui.startBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
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
    try:
        logging.debug(str(ctx.author.id) + " - executeWorldCommand(), command[0] = " + str(command[0]))
    except:
        pass
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
                    if (event.subtype == "trainer"): # DEEPTOOT
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
             'Southern Island', 'Faraway Island', 'Birth Island', 'Naval Rock 1', 'Naval Rock 2', 'Lake Verity Cavern']
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

def createBoxEmbed(ctx, trainer, offset):
    files = []
    embed = discord.Embed(title="Box " + str(offset+1), description="[react to # to view individual summary]", color=0x00ff00)
    count = 1
    for x in range(offset*9, offset*9+9):
        try:
            pokemon = trainer.boxPokemon[x]
            hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
            levelString = "Level: " + str(pokemon.level)
            shinyString = ""
            if pokemon.shiny:
                shinyString = " :star2:"
            embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")"+ shinyString,
                            value=levelString + "\n" + hpString, inline=True)
            count += 1
        except:
            embed.add_field(name="----Empty Slot----", value="\u200b", inline=True)
    embed.set_author(name=(ctx.message.author.display_name))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image.png")
    return files, embed

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
        descString = descString + "\nBattle Tower With Restrictions Record: " + str(trainer.withRestrictionsRecord)
        descString = descString + "\nBattle Tower No Restrictions Record: " + str(trainer.noRestrictionsRecord)
        descString = descString + "\nBattle Tower With Restrictions Current Streak: " + str(trainer.withRestrictionStreak)
        descString = descString + "\nBattle Tower No Restrictions Current Streak: " + str(trainer.noRestrictionsStreak)
    descString = descString + "\nPVP Win/Loss Ratio: " + str(trainer.getPvpWinLossRatio())
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

def createCutsceneEmbed(ctx, cutsceneStr):
    files = []
    cutsceneObj = data.cutsceneDict[cutsceneStr]
    embed = discord.Embed(title=cutsceneObj['title'], description=cutsceneObj['caption'])
    file = discord.File('data/sprites/cutscenes/' + cutsceneStr + '.png', filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text="(continuing automatically in 10 seconds...)")
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

async def saveLoop():
    global allowSave
    global saveLoopActive
    global timeBetweenSave
    logging.debug("saveLoop()")
    if saveLoopActive:
        try:
            channel = bot.get_channel(804463066241957981)
            logging.debug("Save loop tried to enable but save loop is already active.")
            await channel.send("Save loop tried to enable but save loop is already active.")
        except:
            pass
        return
    saveLoopActive = True
    await sleep(timeBetweenSaves)
    try:
        channel = bot.get_channel(804463066241957981)
        logging.debug("Save loop enabled successfully.")
        await channel.send("Save loop enabled successfully.")
    except:
        pass
    while allowSave:
        try:
            logging.debug("Saved.")
            data.writeUsersToJSON()
        except:
            logging.error("Saving failed.\n" + str(traceback.format_exc()))
            try:
                channel = bot.get_channel(804463066241957981)
                await channel.send(("Saving failed.\n" + str(traceback.format_exc()))[-1999:])
            except:
                pass
        await sleep(timeBetweenSaves)
    logging.debug("Save loop disabled successfully.")
    try:
        channel = bot.get_channel(804463066241957981)
        await channel.send("Save loop disabled successfully.")
    except:
        pass
    saveLoopActive = False

async def continueUI(ctx, message, emojiNameList, local_timeout=None, ignoreList=None, isOverworld=False, isPVP=False):
    if message:
        logging.debug(str(ctx.author.id) + " - continueUI(), message.content = " + message.content)
    else:
        logging.debug(str(ctx.author.id) + " - continueUI(), message = None")
    if local_timeout is None:
        local_timeout = timeout
    return await startNewUI(ctx, None, None, emojiNameList, local_timeout, message, ignoreList, isOverworld, isPVP)

async def startNewUI(ctx, embed, files, emojiNameList, local_timeout=None, message=None, ignoreList=None, isOverworld=False, isPVP=False):
    global allowSave
    if local_timeout is None:
        local_timeout = timeout
    temp_uuid = uuid.uuid4()
    embed_title = "No Title"
    try:
        embed_title = embed.title
    except:
        try:
            embed_title = message.content
        except:
            pass
    logging.debug(str(ctx.author.id) + " - startNewUI() called, uuid = " + str(temp_uuid) + ", title = " + embed_title)
    if not allowSave:
        logging.debug(str(ctx.author.id) + " - not starting new UI, bot is down for maintenance, calling endSession()")
        await endSession(ctx)
        await ctx.send("Our apologies, " + str(ctx.message.author.mention) + ", but PokeDiscord is currently down for maintenance. Please try again later.")
        return None, None
    # print(embed_title, ' - ', temp_uuid)
    if not ignoreList:
        ignoreList = []
    if not message:
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - message is None, creating new message")
        message = await ctx.send(files=files, embed=embed)
        for emojiName in emojiNameList:
            await message.add_reaction(data.getEmoji(emojiName))
    messageID = message.id

    if isOverworld:
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - isOverworld=True, removing old from data.overworldSessions and adding new")
        if ctx.message.author in data.overworldSessions:
            try:
                del data.overworldSessions[ctx.message.author]
            except:
                pass
        data.overworldSessions[ctx.message.author] = (message, temp_uuid)

    if not emojiNameList:
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - emojiNameList is None or empty, returning [None, message]")
        return None, message

    def check(payload):
        user_id = payload.user_id
        return user_id == ctx.message.author.id and messageID == payload.message_id

    async def waitForEmoji(ctx):
        commandNum = None
        while commandNum is None:
            try:
                logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - waiting for emoji")
                payload = await bot.wait_for('raw_reaction_add', timeout=local_timeout, check=check)
                user = payload.member
                emoji = payload.emoji
                emojiName = emoji.name
            except asyncio.TimeoutError:
                if not isPVP:
                    logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - timeout")
                    # print('attempting to end session: ', embed_title, ' - ', temp_uuid)
                    if isOverworld:
                        if ctx.message.author in data.overworldSessions:
                            uuidToCompare = data.overworldSessions[ctx.message.author][1]
                            if uuidToCompare != temp_uuid:
                                logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - isOverworld=True and uuid's do not match, returning [None, None]")
                                return None, None
                        if temp_uuid in data.expiredSessions:
                            logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - isOverworld=True and temp_uuid in data.expiredSessions, returning [None, None]")
                            return None, None
                    # print('ending session: ', embed_title, ' - ', temp_uuid, '\n')
                    logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - calling endSession()")
                    await endSession(ctx)
                return None, None
            else:
                logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - reaction input given, emojiName = " + emojiName)
                for name in emojiNameList:
                    if emojiName == data.getEmoji(name):
                        commandNum = name
                try:
                    canRemove = True
                    for name in ignoreList:
                        if emoji.name == data.getEmoji(name):
                            canRemove = False
                    if canRemove:
                        await message.remove_reaction(emoji, user)
                except:
                    pass
                # try:
                #     fetched_message = await fetchMessageFromServer(ctx, payload)
                #     await fetched_message.remove_reaction(emoji, user)
                # except:
                #     pass
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - returning [" + str(commandNum) + ", message]")
        return commandNum, message

    return await waitForEmoji(ctx)

async def fetchUserFromServer(ctx, userName):
    try:
        id = int(userName.replace("<", "").replace("@", "").replace(">", "").replace("!", ""))
        fetched_user = await ctx.guild.fetch_member(id)
        return fetched_user
    except:
        return None

async def fetchMessageFromServerByPayload(ctx, payload):
    try:
        guild = ctx.guild
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        return message
    except:
        return None

async def fetchMessageFromServerByCtx(ctx, msg_id):
    try:
        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        return message
    except:
        return None

def strToInt(inputStr):
    try:
        newInt = int(inputStr)
    except:
        newInt = None
    return newInt

async def startOverworldUI(ctx, trainer):
    logging.debug(str(ctx.author.id) + " - startOverworldUI()")
    resetAreas(trainer)
    dataTuple = (trainer,)
    files, embed, overWorldCommands = createOverworldEmbed(ctx, trainer)
    emojiNameList = []
    count = 1
    for command in overWorldCommands:
        if count >= 10:
            continue
        emojiNameList.append(str(count))
        count += 1
    if len(overWorldCommands) >= 10:
        emojiNameList.append(str(0))

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList, timeout, None, None, True)
    if chosenEmoji == '0':
        chosenEmoji = '10'
    commandNum = strToInt(chosenEmoji)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if commandNum is not None:
            newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, \
            goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining = \
                executeWorldCommand(ctx, trainer, overWorldCommands[commandNum], embed)
            if (embedNeedsUpdating):
                await message.edit(embed=newEmbed)
            else:
                if ctx.message.author in data.overworldSessions:
                    try:
                        del data.overworldSessions[ctx.message.author]
                    except:
                        pass
                await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating,
                                          reloadArea, goToBox, goToBag, goToMart, goToParty, battle,
                                          goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower,
                                          withRestrictions, goToSuperTraining)
                break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList, timeout, None, True)
        if chosenEmoji == '0':
            chosenEmoji = '10'
        commandNum = strToInt(chosenEmoji)

async def startPartyUI(ctx, trainer, goBackTo='', battle=None, otherData=None, goStraightToBattle=False,
                       isBoxSwap=False,
                       boxIndexToSwap=None, swapToBox=False, itemToUse=None, isFromFaint=False):
    logging.debug(str(ctx.author.id) + " - startPartyUI()")
    dataTuple = (trainer, goBackTo, battle, otherData)
    if (goStraightToBattle):
        if (goBackTo == 'startBattleUI'):
            if isFromFaint:
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                      startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False, otherData[4], isFromFaint)
            else:
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                      startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], True, otherData[4], isFromFaint)
            return
    files, embed = createPartyUIEmbed(ctx, trainer, isBoxSwap, itemToUse)
    emojiNameList = []
    count = 1
    for pokemon in trainer.partyPokemon:
        emojiNameList.append(str(count))
        count += 1
    emojiNameList.append('right arrow')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1' and len(trainer.partyPokemon) >= 1):
            if isBoxSwap:
                await message.delete()
                confirmation = await ctx.send(
                    trainer.partyPokemon[0].nickname + " sent to box and " + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(0, boxIndexToSwap)
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (itemToUse is not None):
                pokemonForItem = trainer.partyPokemon[0]
                itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                if (itemCanBeUsed):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        battle.sendUseItemCommand(itemToUse, pokemonForItem)
                        await message.delete()
                        battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI,
                                              continueUI, startPartyUI, startOverworldUI, startBattleTowerUI,
                                              startCutsceneUI)
                        await battle_ui.startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True, otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(ctx)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(ctx)
            else:
                await message.delete()
                await startPokemonSummaryUI(ctx, trainer, 0, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '2' and len(trainer.partyPokemon) >= 2):
            if isBoxSwap:
                await message.delete()
                confirmation = await ctx.send(
                    trainer.partyPokemon[1].nickname + " sent to box and " + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(1, boxIndexToSwap)
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (itemToUse is not None):
                pokemonForItem = trainer.partyPokemon[1]
                itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                # print(itemCanBeUsed)
                if (itemCanBeUsed):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        battle.sendUseItemCommand(itemToUse, pokemonForItem)
                        await message.delete()
                        battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI,
                                              continueUI, startPartyUI, startOverworldUI, startBattleTowerUI,
                                              startCutsceneUI)
                        await battle_ui.startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True, otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(ctx)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(ctx)
            else:
                await message.delete()
                await startPokemonSummaryUI(ctx, trainer, 1, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '3' and len(trainer.partyPokemon) >= 3):
            if isBoxSwap:
                await message.delete()
                confirmation = await ctx.send(
                    trainer.partyPokemon[2].nickname + " sent to box and " + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(2, boxIndexToSwap)
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (itemToUse is not None):
                pokemonForItem = trainer.partyPokemon[2]
                itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                if (itemCanBeUsed):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        battle.sendUseItemCommand(itemToUse, pokemonForItem)
                        await message.delete()
                        battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI,
                                              continueUI, startPartyUI, startOverworldUI, startBattleTowerUI,
                                              startCutsceneUI)
                        await battle_ui.startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True, otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(ctx)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(ctx)
            else:
                await message.delete()
                await startPokemonSummaryUI(ctx, trainer, 2, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '4' and len(trainer.partyPokemon) >= 4):
            if isBoxSwap:
                await message.delete()
                confirmation = await ctx.send(
                    trainer.partyPokemon[3].nickname + " sent to box and " + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(3, boxIndexToSwap)
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (itemToUse is not None):
                pokemonForItem = trainer.partyPokemon[3]
                itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                if (itemCanBeUsed):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        battle.sendUseItemCommand(itemToUse, pokemonForItem)
                        await message.delete()
                        battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI,
                                              continueUI, startPartyUI, startOverworldUI, startBattleTowerUI,
                                              startCutsceneUI)
                        await battle_ui.startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True, otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(ctx)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(ctx)
            else:
                await message.delete()
                await startPokemonSummaryUI(ctx, trainer, 3, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '5' and len(trainer.partyPokemon) >= 5):
            if isBoxSwap:
                await message.delete()
                confirmation = await ctx.send(
                    trainer.partyPokemon[4].nickname + " sent to box and " + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(4, boxIndexToSwap)
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (itemToUse is not None):
                pokemonForItem = trainer.partyPokemon[4]
                itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                if (itemCanBeUsed):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        battle.sendUseItemCommand(itemToUse, pokemonForItem)
                        await message.delete()
                        battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI,
                                              continueUI, startPartyUI, startOverworldUI, startBattleTowerUI,
                                              startCutsceneUI)
                        await battle_ui.startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True, otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(ctx)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(ctx)
            else:
                await message.delete()
                await startPokemonSummaryUI(ctx, trainer, 4, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '6' and len(trainer.partyPokemon) >= 6):
            if isBoxSwap:
                await message.delete()
                confirmation = await ctx.send(
                    trainer.partyPokemon[5].nickname + " sent to box and " + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(5, boxIndexToSwap)
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (itemToUse is not None):
                pokemonForItem = trainer.partyPokemon[5]
                itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                if (itemCanBeUsed):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        battle.sendUseItemCommand(itemToUse, pokemonForItem)
                        await message.delete()
                        battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI,
                                              continueUI, startPartyUI, startOverworldUI, startBattleTowerUI,
                                              startCutsceneUI)
                        await battle_ui.startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True, otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(ctx)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(ctx)
            else:
                await message.delete()
                await startPokemonSummaryUI(ctx, trainer, 5, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == 'right arrow'):
            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                await message.delete()
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI, startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False, otherData[4])
                break
            elif (goBackTo == 'startBoxUI'):
                await message.delete()
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(ctx, otherData[0])
                break
            elif (goBackTo == 'startBagUI'):
                await message.delete()
                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                break
            elif (goBackTo == "startBattleTowerUI"):
                await message.delete()
                await startBattleTowerUI(ctx, otherData[0], otherData[1], otherData[2])
                break
            # else:
            #     await message.remove_reaction(reaction, user)
            #     await waitForEmoji(ctx)
        # else:
        #     await message.remove_reaction(reaction, user)
        #     await waitForEmoji(ctx)
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startPokemonSummaryUI(ctx, trainer, partyPos, goBackTo='', battle=None, otherData=None, isFromBox=False,
                                swapToBox=False):
    logging.debug(str(ctx.author.id) + " - startPokemonSummaryUI()")
    if not isFromBox:
        pokemon = trainer.partyPokemon[partyPos]
    else:
        pokemon = trainer.boxPokemon[partyPos]
    files, embed = createPokemonSummaryEmbed(ctx, pokemon)
    emojiNameList = []
    if (swapToBox):
        emojiNameList.append('box')
    else:
        emojiNameList.append('swap')
    emojiNameList.append('right arrow')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == 'right arrow'):
            await message.delete()
            if (goBackTo == 'startPartyUI'):
                await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (goBackTo == 'startBoxUI'):
                await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                break
        elif (chosenEmoji == 'box' and swapToBox):
            if (len(trainer.partyPokemon) > 1):
                await message.delete()
                confirmation = await ctx.send(pokemon.nickname + " sent to box! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.movePokemonPartyToBox(partyPos)
                await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False, False,
                                   None, True, None, False)
                break
        elif (chosenEmoji == 'swap' and not swapToBox):
            alreadyInBattle = False
            if (battle is not None):
                if (battle.pokemon1 == pokemon):
                    alreadyInBattle = True
            if (goBackTo == 'startBoxUI'):
                await message.delete()
                if (len(trainer.partyPokemon) < 6):
                    confirmation = await ctx.send(
                        trainer.boxPokemon[partyPos].nickname + " added to party! (continuing in 4 seconds...)")
                    await sleep(4)
                    await confirmation.delete()
                    trainer.movePokemonBoxToParty(partyPos)
                    await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    break
                else:
                    await startPartyUI(ctx, trainer, 'startBoxUI', None, otherData, False, True, partyPos)
                    break
            elif ('faint' not in pokemon.statusList and not alreadyInBattle):
                await message.delete()
                if (goBackTo == 'startPartyUI'):
                    if (battle is not None):
                        # swappingFromFaint = ('faint' in battle.pokemon1.statusList)
                        swappingFromFaint = battle.swapCommand(trainer, partyPos)
                        if swappingFromFaint:
                            await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3],
                                               True, False, None, False, None, True)
                            break
                        else:
                            await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3],
                                               True)
                            break
                    else:
                        trainer.swapPartyPokemon(partyPos)
                        await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], False)
                        break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startBoxUI(ctx, trainer, offset=0, goBackTo='', otherData=None):
    logging.debug(str(ctx.author.id) + " - startBoxUI()")
    dataTuple = (trainer, offset, goBackTo, otherData)
    maxBoxes = math.ceil(len(trainer.boxPokemon)/9)
    if (maxBoxes < 1):
        maxBoxes = 1
    files, embed = createBoxEmbed(ctx, trainer, offset) # is box number
    emojiNameList = []
    for x in range(1, 10):
        emojiNameList.append(str(x))
    emojiNameList.append('party')
    emojiNameList.append('left arrow')
    emojiNameList.append('right arrow')
    emojiNameList.append('down arrow')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1' and len(trainer.boxPokemon) >= 1 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 0 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '2' and len(trainer.boxPokemon) >= 2 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 1 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '3' and len(trainer.boxPokemon) >= 3 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 2 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '4' and len(trainer.boxPokemon) >= 4 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 3 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '5' and len(trainer.boxPokemon) >= 5 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 4 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '6' and len(trainer.boxPokemon) >= 6 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 5 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '7' and len(trainer.boxPokemon) >= 7 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 6 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '8' and len(trainer.boxPokemon) >= 8 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 7 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '9' and len(trainer.boxPokemon) >= 9 + (offset*9)):
            await message.delete()
            await startPokemonSummaryUI(ctx, trainer, 8 + (offset*9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == 'left arrow'):
            if (offset == 0 and maxBoxes != 1):
                offset = maxBoxes - 1
                files, embed = createBoxEmbed(ctx, trainer, offset)
                await message.edit(embed=embed)
            elif (offset > 0):
                offset -= 1
                files, embed = createBoxEmbed(ctx, trainer, offset)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'right arrow'):
            if (offset+1 < maxBoxes):
                offset += 1
                files, embed = createBoxEmbed(ctx, trainer, offset)
                await message.edit(embed=embed)
            elif (offset+1 == maxBoxes and maxBoxes != 1):
                offset = 0
                files, embed = createBoxEmbed(ctx, trainer, offset)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'party'):
            await message.delete()
            await startPartyUI(ctx, trainer, 'startBoxUI', None, dataTuple, False, False, None, True)
            break
        elif (chosenEmoji == 'down arrow'):
            if (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(ctx, otherData[0])
                break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startMartUI(ctx, trainer, goBackTo='', otherData=None):
    logging.debug(str(ctx.author.id) + " - startMartUI()")
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
    emojiNameList = []
    for x in range(1, len(itemDict)+1):
        emojiNameList.append(str(x))
    emojiNameList.append('right arrow')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1' and len(itemDict) >= 1):
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
        elif (chosenEmoji == '2' and len(itemDict) >= 2):
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
        elif (chosenEmoji == '3' and len(itemDict) >= 3):
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
        elif (chosenEmoji == '4' and len(itemDict) >= 4):
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
        elif (chosenEmoji == '5' and len(itemDict) >= 5):
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
        elif (chosenEmoji == '6' and len(itemDict) >= 6):
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
        elif (chosenEmoji == '7' and len(itemDict) >= 7):
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
        elif (chosenEmoji == '8' and len(itemDict) >= 8):
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
        elif (chosenEmoji == '9' and len(itemDict) >= 9):
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
        elif (chosenEmoji == 'right arrow'):
            if (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(ctx, otherData[0])
                break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startBagUI(ctx, trainer, goBackTo='', otherData=None):
    logging.debug(str(ctx.author.id) + " - startBagUI()")
    dataTuple = (trainer, goBackTo, otherData)
    files, embed = createBagEmbed(ctx, trainer)
    emojiNameList = []
    emojiNameList.append('1')
    emojiNameList.append('2')
    emojiNameList.append('3')
    emojiNameList.append('4')
    emojiNameList.append('right arrow')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    isCategory = True
    category = ''
    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1'):
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
                        break
        elif (chosenEmoji == '2'):
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
                        break
        elif (chosenEmoji == '3'):
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
                        break
        elif (chosenEmoji == '4'):
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
                        break
        elif (chosenEmoji == 'right arrow'):
            if (isCategory):
                if (goBackTo == 'startOverworldUI'):
                    await message.delete()
                    await startOverworldUI(ctx, trainer)
                    break
            else:
                isCategory = True
                category = ''
                files, embed = createBagEmbed(ctx, trainer)
                await message.edit(embed=embed)
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startBeforeTrainerBattleUI(ctx, isWildEncounter, battle, goBackTo='', otherData=None):
    logging.debug(str(ctx.author.id) + " - startBeforeTrainerBattleUI()")
    files, embed = createBeforeTrainerBattleEmbed(ctx, battle.trainer2)
    message = await ctx.send(files=files, embed=embed)
    await sleep(6)
    await message.delete()
    battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                          startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
    await battle_ui.startBattleUI(ctx, isWildEncounter, battle, goBackTo, otherData)

async def startNewUserUI(ctx, trainer):
    logging.debug(str(ctx.author.id) + " - startNewUserUI()")
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
    emojiNameList = []
    for x in range(1, len(starterList) + 1):
        emojiNameList.append(str(x))

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    if (chosenEmoji == '1' and len(starterList) > 0):
        await startAdventure(ctx, message, trainer, starterList[0])
        return
    elif (chosenEmoji == '2' and len(starterList) > 1):
        await startAdventure(ctx, message, trainer, starterList[1])
        return
    elif (chosenEmoji == '3' and len(starterList) > 2):
        await startAdventure(ctx, message, trainer, starterList[2])
        return
    elif (chosenEmoji == '4' and len(starterList) > 3):
        await startAdventure(ctx, message, trainer, starterList[3])
        return
    elif (chosenEmoji == '5' and len(starterList) > 4):
        await startAdventure(ctx, message, trainer, starterList[4])
        return
    elif (chosenEmoji == '6' and len(starterList) > 5):
        await startAdventure(ctx, message, trainer, starterList[5])
        return
    elif (chosenEmoji == '7' and len(starterList) > 6):
        await startAdventure(ctx, message, trainer, starterList[6])
        return
    elif (chosenEmoji == '8' and len(starterList) > 7):
        await startAdventure(ctx, message, trainer, starterList[7])
        return
    elif (chosenEmoji == '9' and len(starterList) > 8):
        await startAdventure(ctx, message, trainer, starterList[8])
        return

async def startAdventure(ctx, message, trainer, starter):
    trainer.addPokemon(starter, True)
    await message.delete()
    confirmationText = "Congratulations! You obtained " + starter.name + "! Get ready for your Pokemon adventure!\n(continuing automatically in 5 seconds...)"
    confirmation = await ctx.send(confirmationText)
    await sleep(5)
    await confirmation.delete()
    await startOverworldUI(ctx, trainer)

async def startMoveTutorUI(ctx, trainer, partySlot, isTM, offset=0, goBackTo='', otherData=None):
    logging.debug(str(ctx.author.id) + " - startMoveTutorUI()")
    dataTuple = (trainer, partySlot, isTM, offset, goBackTo, otherData)
    pokemon = trainer.partyPokemon[partySlot]
    if isTM:
        moveList = pokemon.getAllTmMoves()
    else:
        moveList = pokemon.getAllLevelUpMoves()
    maxPages = math.ceil(len(moveList)/9)
    if (maxPages < 1):
        maxPages = 1
    files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM) # is page number
    emojiNameList = []
    for x in range(1, 10):
        emojiNameList.append(str(x))
    emojiNameList.append('left arrow')
    emojiNameList.append('right arrow')
    emojiNameList.append('down arrow')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1' and len(moveList) >= 1 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[0 + (offset*9)], 'startMoveTutorUI', dataTuple)
                break
        elif (chosenEmoji == '2' and len(moveList) >= 2 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[1 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '3' and len(moveList) >= 3 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[2 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '4' and len(moveList) >= 4 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[3 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '5' and len(moveList) >= 5 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[4 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '6' and len(moveList) >= 6 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[5 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '7' and len(moveList) >= 7 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[6 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '8' and len(moveList) >= 8 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[7 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == '9' and len(moveList) >= 9 + (offset*9)):
            await message.delete()
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[8 + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        elif (chosenEmoji == 'left arrow'):
            if (offset == 0 and maxPages != 1):
                offset = maxPages - 1
                files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
            elif (offset > 0):
                offset -= 1
                files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'right arrow'):
            if (offset+1 < maxPages):
                offset += 1
                files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
            elif (offset+1 == maxPages and maxPages != 1):
                offset = 0
                files, embed = createMoveTutorEmbed(ctx, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'down arrow'):
            if (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(ctx, otherData[0])
                break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startLearnNewMoveUI(ctx, trainer, pokemon, move, goBackTo='', otherData=None):
    logging.debug(str(ctx.author.id) + " - startLearnNewMoveUI()")
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
            emojiNameList = []
            for x in range(1, count + 1):
                emojiNameList.append(str(x))
                await message.add_reaction(data.getEmoji(str(x)))

            chosenEmoji, message = await startNewUI(ctx, None, None, emojiNameList, timeout, message=message)

            if (chosenEmoji == '1'):
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
            elif (chosenEmoji == '2'):
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
            elif (chosenEmoji == '3'):
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
            elif (chosenEmoji == '4'):
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
            elif (chosenEmoji == '5'):
                await message.delete()
                message = await ctx.send("Gave up on learning " + move['names'][
                    'en'] + "." + " (continuing automatically in 4 seconds...)")
                await sleep(4)
                await message.delete()
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
    logging.debug(str(ctx.author.id) + " - startCutsceneUI()")
    files, embed = createCutsceneEmbed(ctx, cutsceneStr)
    message = await ctx.send(files=files, embed=embed)
    await sleep(10)
    await message.delete()
    await startOverworldUI(ctx, trainer)

async def startBattleTowerSelectionUI(ctx, trainer, withRestrictions):
    logging.debug(str(ctx.author.id) + " - startBattleTowerSelectionUI()")
    dataTuple = (trainer, withRestrictions)
    trainer.pokemonCenterHeal()
    files, embed = createPartyUIEmbed(ctx, trainer, False, None, "Battle Tower Selection", "[react to #'s to select 3 Pokemon then hit the check mark]")
    emojiNameList = []
    count = 1
    for pokemon in trainer.partyPokemon:
        emojiNameList.append(str(count))
        count += 1
    emojiNameList.append('confirm')
    emojiNameList.append('down arrow')

    ignoreList = ['1', '2', '3', '4', '5', '6']
    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList, timeout, None, ignoreList)
    messageID = message.id

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == 'confirm'):
            chosenPokemonNums = []
            cache_msg = await fetchMessageFromServerByCtx(ctx, messageID)
            # cache_msg = discord.utils.get(bot.cached_messages, id=messageID)
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
                embed.set_footer(text="Too many Pokemon selected.")
                await message.edit(embed=embed)
            elif len(chosenPokemonNums) < 3:
                embed.set_footer(text="Not enough Pokemon selected.")
                await message.edit(embed=embed)
            else:
                trainerCopy, valid = battleTower.getBattleTowerUserCopy(trainer, chosenPokemonNums[0], chosenPokemonNums[1], chosenPokemonNums[2], withRestrictions)
                if valid:
                    await message.delete()
                    await startBattleTowerUI(ctx, trainer, trainerCopy, withRestrictions)
                    break
                else:
                    embed.set_footer(text="Restricted Pokemon may not be used.")
                    await message.edit(embed=embed)
        elif (chosenEmoji == 'down arrow'):
            await message.delete()
            await startOverworldUI(ctx, trainer)
            break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList, timeout, ignoreList)

async def startBattleTowerUI(ctx, trainer, trainerCopy, withRestrictions, bpToEarn=0):
    logging.debug(str(ctx.author.id) + " - startBattleTowerUI()")
    if bpToEarn > 0:
        trainer.addItem('BP', bpToEarn)
    trainer.pokemonCenterHeal()
    trainerCopy.pokemonCenterHeal()
    dataTuple = (trainer, trainerCopy, withRestrictions)
    files, embed = createBattleTowerUI(ctx, trainer, withRestrictions)
    emojiNameList = []
    emojiNameList.append('1')
    emojiNameList.append('2')
    emojiNameList.append('3')

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1'):
            if (trainer.dailyProgress > 0 or not data.staminaDict[str(ctx.message.guild.id)]):
                if (data.staminaDict[str(ctx.message.guild.id)]):
                    trainer.dailyProgress -= 1
                await message.delete()
                battle = Battle(data, trainerCopy, battleTower.getBattleTowerTrainer(trainer, withRestrictions))
                battle.disableExp()
                battle.startBattle()
                await startBeforeTrainerBattleUI(ctx, False, battle, 'startBattleTowerUI', dataTuple)
                break
            else:
                embed.set_footer(text="Out of stamina for today! Please come again tomorrow!")
                await message.edit(embed=embed)
        elif (chosenEmoji == '2'):
            await message.delete()
            await startPartyUI(ctx, trainerCopy, 'startBattleTowerUI', None, dataTuple)
            break
        elif (chosenEmoji == '3'):
            await message.delete()
            await startOverworldUI(ctx, trainer)
            break
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList)

async def startSuperTrainingUI(ctx, trainer, partyPos=1):
    logging.debug(str(ctx.author.id) + " - startSuperTrainingUI()")
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

pokeDiscordLogger = logging.getLogger()
pokeDiscordLogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='pokeDiscord_log.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s'))
pokeDiscordLogger.addHandler(handler)
discordLogger = logging.getLogger('discord')
# discordLogger.propagate = False
discordLogger.setLevel(logging.ERROR)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# discordLogger.addHandler(handler)
imageLogger = logging.getLogger('PIL.PngImagePlugin')
imageLogger.setLevel(logging.ERROR)
timeout = 600
battleTimeout = 900
pvpTimeout = 120
allowSave = True
saveLoopActive = False
timeBetweenSaves = 60
data = pokeData()
data.readUsersFromJSON()
linkZetaroidSave()
battleTower = Battle_Tower(data)
bot.run(TOKEN)
