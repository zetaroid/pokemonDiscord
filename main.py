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
from Raid import Raid
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
from Secret_Base_UI import Secret_Base_UI
from Secret_Base import Secret_Base
from Shop_Item import Shop_Item

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!', help_command=None)

@bot.event
async def on_ready():
    try:
        channel = bot.get_channel(errorChannel1)
        await channel.send('NOTICE: PokéNav is online and ready for use.')
    except:
        pass
    logging.debug("PokéNav is online and ready for use.")
    await saveLoop()

@bot.command(name='start', help='starts the game', aliases=['s', 'begin'])
async def startGame(ctx):
    global allowSave
    logging.debug(str(ctx.author.id) + " - !start - in server: " + str(ctx.guild.id))
    if not allowSave:
        logging.debug(str(ctx.author.id) + " - not starting session, bot is down for maintenance")
        await ctx.send("Our apologies, but PokéNav is currently down for maintenance. Please try again later.")
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
            data.updateRecentActivityDict(ctx, user)
            await eventCheck(ctx, user)
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
    except discord.errors.Forbidden:
        await forbiddenErrorHandle(ctx)
    except:
        await sessionErrorHandle(ctx, user, traceback)

async def raidCheck():
    global raidsEnabled
    if not raidsEnabled:
        return

    startNewRaid = False

    if data.raid:
        if await data.raid.hasRaidExpired():
            return

    # Check when last time checked
    if data.lastRaidCheck:
        timeSinceLastCheck = datetime.today() - data.lastRaidCheck
        elapsedSecondsSinceCheck = timeSinceLastCheck.total_seconds()
        if elapsedSecondsSinceCheck < 1800:
            return
    logging.debug("raid - Running raid check.")
    data.lastRaidCheck = datetime.today()

    # Check when last raid was
    if data.lastRaidTime:
        elapsedTime = datetime.today() - data.lastRaidTime
        elapsedHours = elapsedTime.total_seconds() / 3600
        odds = 0
        if elapsedHours >= 1 and elapsedHours <= 2:
            odds = 10
        elif elapsedHours >= 2 and elapsedHours <= 3:
            odds = 30
        elif elapsedHours >= 3 and elapsedHours <= 5:
            odds = 65
        elif elapsedHours > 5:
            startNewRaid = True
        raidInt = random.randint(1, 100)
        # if odds >= raidInt and data.raid is None:
        if odds >= raidInt:
            startNewRaid = True
    else:
        startNewRaid = True
    if startNewRaid:
        logging.debug("raid - Starting new raid.")
        raid = Raid(data, battleTower)
        started = await raid.startRaid()
        if started:
            await data.setRaid(raid)
        else:
            data.lastRaidCheck = None
    else:
        logging.debug("raid - No new raid started.")

async def forbiddenErrorHandle(ctx):
    logging.error(str(ctx.author.id) + " - session ended in discord.errors.Forbidden error.\n" + str(traceback.format_exc()) + "\n")
    logging.error(str(ctx.author.id) + " - calling endSession() due to error")
    try:
        await endSession(ctx)
    except:
        pass
    forbiddenMessage = "Hello! Professor Birch here! It appears you revoked some required bot permissions that are required for PokéNav to function! The bot will not work without these."
    try:
        await ctx.send(forbiddenMessage)
    except:
        channel = await ctx.author.create_dm()
        await channel.send(forbiddenMessage)
    disregardStr = "Error for '" + str(ctx.author.id) + "' was due to missing permissions. You can safely disregard."
    logging.error(str(ctx.author.id) + " - " + disregardStr)
    # await sendDiscordErrorMessage(ctx, traceback, disregardStr)

async def sessionErrorHandle(ctx, user, traceback):
    logging.error(str(ctx.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()) + "\n")
    # traceback.print_exc()
    user.dailyProgress += 1
    # user.removeProgress(user.location)
    await sendDiscordErrorMessage(ctx, traceback)
    logging.error(str(ctx.author.id) + " - calling endSession() due to error")
    await endSession(ctx)

async def sendDiscordErrorMessage(ctx, traceback, message=None):
    exceptMessage = "An error occurred, please restart your session. If this persists, please report to an admin."
    if message:
        try:
            channel = bot.get_channel(errorChannel1)
            await channel.send(message)
        except:
            try:
                channel = bot.get_channel(errorChannel2)
                await channel.send(message)
            except:
                # print('e1-mess')
                await ctx.send(exceptMessage)
    else:
        tracebackMessage = str(str(ctx.message.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()))[-1999:]
        try:
            channel = bot.get_channel(errorChannel1)
            await channel.send(tracebackMessage)
        except:
            try:
                channel = bot.get_channel(errorChannel2)
                await channel.send(tracebackMessage)
            except:
                # print('e1-trace')
                await ctx.send(exceptMessage)

@bot.command(name='help', help='help command')
async def help(ctx):
    await ctx.send(str(ctx.message.author.mention) + ", Professor Birch will assist you in your Direct Messages.")
    files = []
    newline = "\n\n"
    halfNewline = "\n"
    embed = discord.Embed(title="PokéNav - Help", description="Hello " + ctx.author.display_name + "," + newline +
                                                           "Professor Birch here! Let's get you the help you need!" + newline +
                                                           "For a full information guide, please see our website:\n[PokéNav website](https://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md)" + newline +
                                                           "If you need support, please join our official PokéNav server!\n[PokéNav official server](https://discord.gg/HwYME4Vwj9)" + newline +
                                                           "[🗳️Vote for PokéNav here!🗳️](https://top.gg/bot/800207357622878229/vote)" + newline +
                                                           "Otherwise, here is a list of commands, although all you need to begin using the bot is `!start`.",
                          color=0x00ff00)
    embed.set_footer(text="------------------------------------\nZetaroid#1391 - PokéNav Developer")
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------Main Commands--------------", value=
                                            "`!start` - begin your adventure, use this each time you want to start a new session" + halfNewline +
                                            "`!fly <location>` - after obtaining 6th badge, use to fly to any visited location" + halfNewline +
                                            "`!endSession` - while in the overworld, will end your current session" + halfNewline +
                                            "`!guide` - tells you where to go next"  + halfNewline +
                                            "`!map` - shows a visual map of the Hoenn region" + halfNewline +
                                            "`!vote` - vote for the bot on top.gg"
                    ,inline=False)
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------Party Management--------------", value=
                                            "`!nickname <party number> <name>` - nickname a Pokemon" + halfNewline +
                                            "`!swapMoves <party number> <moveSlot1> <moveSlot2>` - swap 2 moves" + halfNewline +
                                            "`!evolve <party number> [optional: Pokemon to evolve into]` - evolves a Pokemon capable of evolution" + halfNewline +
                                            "`!unevolve <party number>` - unevolves a Pokemon with a pre-evolution" + halfNewline +
                                            "`!release <party number>` - release a Pokemon from your party" + halfNewline +
                                            "`!changeForm <party number> [optional: form number from !dex command]` - toggle a Pokemon's form" + halfNewline +
                                            "`!moveInfo <move name>` - get information about a move"  + halfNewline +
                                            "`!dex <Pokemon name>` - view a Pokemon's dex entry, add 'shiny' or 'distortion' to end of command to view those sprites, see !guide for examples" + halfNewline +
                                            "`!createTeam <team number between 1 and 10> [optional: team name]` - create new preset team from current party" + halfNewline +
                                            "`!setTeam <team number or name>` - replace party with preset team" + halfNewline +
                                            "`!viewTeams` - view all preset teams" + halfNewline +
                                            "`!deleteTeam <team number>` - delete a team" + halfNewline +
                                            "`!renameTeam <team number>` - rename a team"
                    ,inline=False)
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------Player Management--------------", value=
                                            "`!profile [@user]` - get a trainer's profile" + halfNewline +
                                            "`!trainerCard [@user]` - get a trainer's card" + halfNewline +
                                            "`!enableGlobalSave` - sets the save file from the server you are currently in as your save for ALL servers (will not delete other saves)" + halfNewline +
                                            "`!disableGlobalSave` - disables global save for you, all servers will have separate save files" + halfNewline +
                                            "`!resetSave` - permanently reset your save file on a server" + halfNewline +
                                            "`!setSprite <gender>` - sets player trainer card sprite (options: male, female, default)" + halfNewline +
                                            "`!setAlteringCave <pokemon name>` - trade 10 BP to set the Pokemon in Altering Cave (BP earned at Battle Tower in post-game)" + halfNewline +
                                            "`!secretPower` - create a secret base in the overworld" + halfNewline +
                                            "`!deleteBase` - delete your current secret base" + halfNewline +
                                            "`!shop [category]` - opens the BP shop (League Champions only)" + halfNewline +
                                            "`!buy <amount> <item>` - buy an item from the BP shop (League Champions only)"
                    ,inline=False)
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------PVP / Trading--------------", value=
                                            "`!trade <party number> <@user>` - trade with another user" + halfNewline +
                                            "`!pvp` - get matched with someone else at random to PVP them" + halfNewline +
                                            "`!battle <@user>` - battle another user on the server" + halfNewline +
                                            "`!battleCopy <@user>` - battle an NPC copy of another user on the server" + halfNewline +
                                            "`!raid` - join an active raid if one exists" + halfNewline +
                                            "`!raidInfo` - display status of current raid" + halfNewline +
                                            "`!event` - view active event" + halfNewline +
                                            "`!viewBase <@user>` - view a user's secret base"
                    ,inline=False)
    embed.add_field(name='\u200b', value="Cheers,\nProfessor Birch")
    if str(ctx.author) == 'Zetaroid#1391':
        embed.add_field(name='------------------------------------\nDev Commands:',
                        value="Oh hello there!\nI see you are a dev! Here are some extra commands for you:" + newline +
                        "`!grantFlag <flag> [userName] [server_id]` - grants flag to user" + halfNewline +
                        "`!removeFlag <flag> [userName=self] [server_id]` - removes flag from user" + halfNewline +
                        "`!save [flag=disable]` - disable save and manually save" + halfNewline +
                        "`!saveStatus` - view status of save variables" + halfNewline +
                        "`!test` - test things" + halfNewline +
                        "`!verifyChampion [userName]` - verify elite 4 victory for user" + halfNewline +
                        "`!displaySessionList` - display full active session list" + halfNewline +
                        "`!displayGuildList` - display full guild list" + halfNewline +
                        "`!displayOverworldList` - display full overworld session list" + halfNewline +
                        "`!forceEndSession [user id num]` - remove user id from active session list" + halfNewline +
                        "`!leave [targetServer]` - leave the target server" + halfNewline +
                        "`!viewFlags [userName=self] [server_id]` - views user flags (use '_' for spaces in flag name)"
                        ,
                        inline=False)
        # embed.add_field(name='\u200b',
        embed.add_field(name='Dev Commands 2:',
                        value="`!grantItem <item> <amount> [@user]` - grants a specified item in amount to user (replace space in item name with '\_')" + halfNewline +
                        "`!removeItem <item> <amount> [@user]` - removes a specified item in amount to user (replace space in item name with '\_')" + halfNewline +
                        "`!grantPokemon [pokemon] [level] [shiny] [distortion] [@user]` - grant a Pokemon (replace space in name with '\_')" + halfNewline +
                        "`!startRaid` - starts a raid" + halfNewline +
                        "`!endRaid` - ends a raid" + halfNewline +
                        "`!clearRaidList` - clears raid list" + halfNewline +
                        "`!viewRaidList` - views raid list" + halfNewline +
                        "`!raidEnable <true/false>` - enable/disable raids" + halfNewline +
                        "`!recentUsers` - displays # of recent users" + halfNewline +
                        "`!eventList` - view all events" + halfNewline +
                        "`!startEvent <name or number>` - start an event" + halfNewline +
                        "`!endEvent` - ends current event" + halfNewline +
                        "`!checkAuthor <author id> [server id]` - view user info"
                        ,
                        inline=False)
    thumbnailImage = discord.File("logo.png", filename="thumb.png")
    files.append(thumbnailImage)
    embed.set_thumbnail(url="attachment://thumb.png")
    channel = await ctx.author.create_dm()
    await channel.send(embed=embed,files=files)

@bot.command(name='invite', help='get an invite link to add the bot to your own server')
async def inviteCommand(ctx):
    logging.debug(str(ctx.author.id) + " - !invite")
    embed = discord.Embed(title="PokéNav wants to join your party!", description="Click [HERE](https://discord.com/oauth2/authorize?client_id=800207357622878229&permissions=64576&scope=bot) to invite the bot!\n\nIf you already have a save file on this server, use `!enableGlobalSave` here to make this save your universal save file (otherwise you will have separate saves per Discord server).", color=0x00ff00)
    file = discord.File("logo.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    await ctx.send(embed=embed, file=file)

@bot.command(name='resetSave', help='resets save file, this will wipe all of your data', aliases=['resetsave', 'deletesave', 'deleteSave', 'reset'])
async def resetSave(ctx):
    logging.debug(str(ctx.author.id) + " - !resetSave")
    server_id = ctx.message.guild.id
    user, isNewUser = data.getUser(ctx)
    if not isNewUser:
        if ctx.author.id in data.globalSaveDict.keys():
            await ctx.send("You already currently using a global save. Please disable it with `!disableGlobalSave` before erasing a save file.")
            return

        if data.isUserInSession(ctx, user):
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot reset your save while in an active session. Please end session with `!endSession`.")
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

@bot.command(name='createTeam', help='create a new team', aliases=['createteam', 'newteam', "newTeam"])
async def createTeamCommand(ctx, teamNum, *, teamName=''):
    global bannedFlyAreas
    validTeamNumbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        if 'elite4' not in user.flags:
            await ctx.send("Team creation is only available to trainers who have beaten the elite 4!")
            return
        try:
            teamNum = int(teamNum)
        except:
            await ctx.send("Team number must be an integer between " + str(validTeamNumbers[0]) + " and " + str(validTeamNumbers[len(validTeamNumbers)-1]) + " where the team number follows command as shown below:\n`!createTeam <team number>`.")
            return
        if teamNum not in validTeamNumbers:
            await ctx.send("Team number must be an integer between " + str(validTeamNumbers[0]) + " and " + str(validTeamNumbers[len(validTeamNumbers)-1]) + " where the team number follows command as shown below:\n`!createTeam <team number>`.")
            return
        if not teamName:
            teamName = None
        user.createTeamFromParty(teamNum, teamName)
        teamList = [user.teamDict[teamNum]]
        files, embed = createTeamEmbed(teamList, user, "New Team Created:")
        await ctx.send(files=files, embed=embed)

@bot.command(name='renameTeam', help='renames team', aliases=['renameteam'])
async def renameTeamCommand(ctx, teamNum, *, name):
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        try:
            teamNum = int(teamNum)
        except:
            await ctx.send("Invalid team number.")
            return
        try:
            user.teamDict[teamNum].name = name
            await ctx.send("Team " + str(teamNum) + " renamed to `" + name + "`.")
        except:
            await ctx.send("Invalid team number.")

@bot.command(name='deleteTeam', help='deletes team', aliases=['deleteteam'])
async def deleteTeamCommand(ctx, teamNum):
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        try:
            teamNum = int(teamNum)
        except:
            await ctx.send("Invalid team number.")
            return
        try:
            del user.teamDict[teamNum]
            await ctx.send("Team " + str(teamNum) + " deleted.")
        except:
            await ctx.send("Invalid team number.")

@bot.command(name='setTeam', help='set active team', aliases=['setteam'])
async def setTeamCommand(ctx, *, teamNumOrName=''):
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        if 'elite4' not in user.flags:
            await ctx.send("Team creation is only available to trainers who have beaten the elite 4!")
            return
        if user.location.lower() in [item.lower() for item in bannedFlyAreas]:
            logging.debug(str(ctx.author.id) + " - not switching team, cannot set from this area!")
            await ctx.send("Sorry, cannot set teams from this area!")
        else:
            allowSet = False
            activeSession = data.doesUserHaveActiveSession(ctx.guild.id, user)
            if (user in data.getTradeDict(ctx).keys()):
                await ctx.send("Please finish your current trade before setting a team.")
                return
            if activeSession:
                overworldTuple, isGlobal = data.userInOverworldSession(ctx, user)
                if overworldTuple:
                    allowSet = True
                else:
                    await ctx.send("Must be in the overworld to set your team.")
                    return
            else:
                allowSet = True
            try:
                teamNum = int(teamNumOrName)
            except:
                teamNum = None
            if teamNum:
                success, teamName, errorReason = user.setTeam(teamNum)
            else:
                success, teamName, errorReason = user.setTeam(None, teamNumOrName)
            if success:
                await ctx.send(teamName + " set as active party.")
            else:
                messageStr = "Invalid team name or number selection. Please use `!setTeam <team name or number>`."
                if errorReason:
                    messageStr = errorReason
                await ctx.send(messageStr)

@bot.command(name='viewTeams', help='shop for items', aliases=['viewteams', 'viewteam', 'viewTeam', 'teamlist', 'teamList'])
async def viewTeamCommand(ctx):
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        if 'elite4' not in user.flags:
            await ctx.send("Team creation is only available to trainers who have beaten the elite 4!")
            return
        teamList = []
        for i in sorted(user.teamDict.keys()):
            teamList.append(user.teamDict[i])
        files, embed = createTeamEmbed(teamList, user)
        await ctx.send(files=files, embed=embed)

def createTeamEmbed(teamList, trainer, title=None):
    files = []
    if not title:
        title = "Team Summary"
        desc = "Summary of all preset teams."
    else:
        desc = ''
    embed = discord.Embed(title=title, description=desc,
                          color=0x00ff00)
    for team in teamList:
        nameList = team.getNameList(trainer)
        embed.add_field(name=str(team.number) + ". " + team.name,
                        value=", ".join(nameList), inline=False)
    embed.set_author(name=(trainer.name))
    return files, embed

@bot.command(name='shop', help='shop for items', aliases=['mart', 'store', "bpShop"])
async def shopCommand(ctx, *, input=''):
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        if not 'elite4' in user.flags:
            await ctx.send("The shop may only be used by league champions! Continue your adventure to unlock access.")
            return
        if input:
            category = input.lower()
            if category == "furniture":
                categoryList = list(data.secretBaseItemTypes.keys())
                categoryList.append('custom')
                files, embed = createShopEmbed(ctx, user, categoryList)
                await ctx.send(files=files, embed=embed)
            elif category in data.secretBaseItemTypes.keys() or category == "custom":
                itemList = []
                for name, item in data.secretBaseItems.items():
                    if item.getCategory().lower() == category:
                        itemList.append(Shop_Item(item.name, item.getPrice(), item.getCurrency()))
                files, embed = createShopEmbed(ctx, user, None, category, itemList, True)
                await ctx.send(files=files, embed=embed)
            elif category in data.shopDict.keys():
                itemList = data.shopDict[category]
                files, embed = createShopEmbed(ctx, user, None, category, itemList)
                await ctx.send(files=files, embed=embed)
            else:
                await ctx.send("Invalid category selection '" +  input + "'. Use `!shop` to view categories.")
        else:
            categoryList = list(data.shopDict.keys())
            files, embed = createShopEmbed(ctx, user, categoryList)
            await ctx.send(files=files, embed=embed)

@bot.command(name='buy', help='buy an item', aliases=['buyItem', 'purchase'])
async def buyCommand(ctx, amount, *, input=''):
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("Use `!start` to begin your adventure first!")
    else:
        if not 'elite4' in user.flags:
            await ctx.send("The shop may only be used by league champions! Continue your adventure to unlock access.")
            return
        try:
            amount = int(amount)
            itemName = input.title()
        except:
            itemName = amount
            amount = 1
        if itemName in data.secretBaseItems.keys():
            item = data.secretBaseItems[itemName]
            price = item.getPrice() * amount
            currency = item.getCurrency()
            if currency in user.itemList.keys():
                if user.itemList[currency] >= price:
                    user.useItem(currency, price)
                    user.addSecretBaseItem(itemName, amount)
                    await ctx.send(itemName + " x" + str(amount) + " purchased in exchange for " + str(price) + " " + currency + ".")
                    return
                else:
                    await ctx.send("Not enough " + currency + " to make transaction. " + str(price) + " " + currency + " is required.")
                    return
        for category, itemList in data.shopDict.items():
            for item in itemList:
                if item.itemName == itemName:
                    price = item.price * amount
                    currency = item.currency
                    if user.itemList[currency] >= price:
                        if itemName.lower() == 'shiny charm':
                            if 'Shiny Charm' in user.itemList.keys() and user.itemList['Shiny Charm'] > 0:
                                await ctx.send("Can only have 1 Shiny Charm at a time!")
                                return
                        user.useItem(currency, price)
                        user.addItem(itemName, amount)
                        await ctx.send(itemName + " x" + str(amount) + " purchased in exchange for " + str(price) + " " + currency + ".")
                        return
                    else:
                        await ctx.send("Not enough " + currency + " to make transaction. " + str(price) + " " + currency + " is required.")
                        return
        await ctx.send("Invalid item selection '" + itemName + "'. Please use `!shop` to find a valid item to buy.")

@bot.command(name='preview', help='preview furniture', aliases=['previewFurniture', 'furniturePreview'])
async def previewCommand(ctx, *, input=''):
    itemName = input.title()
    if itemName in data.secretBaseItems.keys():
        item = data.secretBaseItems[itemName]
        await secretBaseUi.sendPreviewMessage(ctx, item)
    else:
        await ctx.send("Invalid item name '" + input + "'. Try `!shop furniture` to see available items.")

@bot.command(name='release', help="release a specified party Pokemon, cannot be undone, '!release [your party number to release]'", aliases=['releasePartyPokemon'])
async def releasePartyPokemon(ctx, partyNum):
    logging.debug(str(ctx.author.id) + " - !releasePartyPokemon")
    partyNum = int(partyNum)-1
    user, isNewUser = data.getUser(ctx)
    if not isNewUser:
        if data.isUserInSession(ctx, user):
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot release Pokemon while in an active session. Please end session with `!endSession`.")
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

@bot.command(name='recentUsers', help='DEV ONLY: get number of recent users', aliases=['ru', 'recentusers'])
async def getRecentUsersCount(ctx):
    if not await verifyDev(ctx):
        return
    numRecentUsers, channelList = data.getNumOfRecentUsersForRaid()
    await ctx.send("Number of recent users who are eligible for raids: " + str(numRecentUsers))

@bot.command(name='leave', help='DEV ONLY: leave a server')
async def leaveCommand(ctx, server_id):
    if not await verifyDev(ctx):
        return
    server_id = int(server_id)
    server = bot.get_guild(server_id)
    await ctx.send("Left server `" + str(server_id) + "`.")
    await server.leave()

@bot.command(name='phonefix', help='phone fix for user', aliases=['phoneFix', 'PhoneFix'])
async def phoneFix(ctx):
    user, isNewUser = data.getUser(ctx)
    if not isNewUser:
        user.iphone = not user.iphone
        await ctx.send("Phone fix applied for " + str(ctx.author) + ".")
    else:
        await ctx.send("User '" + str(ctx.author) + "' not found.")

@bot.command(name='verifyChampion', help='DEV ONLY: verify if user has beaten the elite 4', aliases=['verifychampion'])
async def verifyChampion(ctx, *, userName: str="self"):
    if not await verifyDev(ctx):
        return
    user = await getUserById(ctx, userName)
    if user:
        if 'elite4' in user.flags:
            await ctx.send(user.name + " is a league champion!")
        else:
            await ctx.send(user.name + " has NOT beaten the elite 4.")
    else:
        await ctx.send("User '" + userName + "' not found, cannot verify.")

@bot.command(name='grantFlag', help='DEV ONLY: grants user flag (use "_" for spaces in flag name), usage: "!grantFlag [flag, with _] [user] [server id = None]', aliases=['grantflag'])
async def grantFlag(ctx, flag, userName: str="self", server_id=None):
    if not server_id:
        server_id = ctx.message.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = ctx.message.guild.id
    flag = flag.replace("_", " ")
    if not await verifyDev(ctx):
        return
    user = await getUserById(ctx, userName, server_id)
    if user:
        user.addFlag(flag)
        await ctx.send(user.name + ' has been granted the flag: "' + flag + '".')
    else:
        await ctx.send("User '" + userName + "' not found, cannot grant flag.")

@bot.command(name='viewFlags', help='DEV ONLY: views user flags, usage: "!viewFlags [user] [server id = None]', aliases=['viewflags'])
async def viewFlags(ctx, userName: str="self", server_id=None):
    if not server_id:
        server_id = ctx.message.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = ctx.message.guild.id
    if not await verifyDev(ctx):
        return
    user = await getUserById(ctx, userName, server_id)
    if user:
        await ctx.send(user.name + ' flags:\n' + str(user.flags))
    else:
        await ctx.send("User '" + userName + "' not found, cannot revoke flag.")

@bot.command(name='removeFlag', help='DEV ONLY: grants user flag (use "_" for spaces in flag name), usage: "!removeFlag [flag, with _] [user] [server id = None]', aliases=['removeflag'])
async def removeFlag(ctx, flag, userName: str="self", server_id=None):
    if not server_id:
        server_id = ctx.message.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = ctx.message.guild.id
    flag = flag.replace("_", " ")
    if not await verifyDev(ctx):
        return
    user = await getUserById(ctx, userName, server_id)
    if user:
        if user.removeFlag(flag):
            await ctx.send(user.name + ' has been revoked the flag: "' + flag + '".')
        else:
            await ctx.send(user.name + ' did not have the flag: "' + flag + '". Nothing to revoke.')
    else:
        await ctx.send("User '" + userName + "' not found, cannot revoke flag.")

@bot.command(name='setSprite', help='sets sprite to male or female or default', aliases=['setsprite'])
async def setSpriteCommand(ctx, gender=None):
    if not gender:
        await ctx.send("Must enter a gender. Use `!setSprite male`, `!setSprite female`, `!setSprite default`.")
        return
    gender = gender.lower()
    if gender != 'male' and gender != 'female' and gender != 'default':
        await ctx.send("Must choose a male, female, or default gender option.")
        return
    user, isNewUser = data.getUser(ctx)
    if user:
        if gender == 'male':
            user.sprite = 'trainerSpriteMale.png'
        elif gender == 'female':
            user.sprite = 'trainerSpriteFemale.png'
        else:
            user.sprite = 'trainerSprite.png'
        await ctx.send("Sprite set to " + gender + "!")
    else:
        await ctx.send("You haven't played the game yet! Please do `!start` first.")

@bot.command(name='displayGuildList', help='DEV ONLY: display the overworld list', aliases=['dgl', 'displayguildlist'])
async def displayGuildList(ctx, request="short"):
    if not await verifyDev(ctx):
        return
    guildStr = "Guilds that PokéNav is in:\n\n"
    guildOwnerDict = {}
    for guild in bot.guilds:
        if guild.owner_id in guildOwnerDict:
            guildOwnerDict[guild.owner_id] = guildOwnerDict[guild.owner_id] + 1
        else:
            guildOwnerDict[guild.owner_id] = 1
        guildStr += "guild id: " + str(guild.id) + " | guild owner: " + str(guild.owner_id) + "\n"
    guildStr2 = "Owners with 3 or more servers using bot:\n"
    for owner, numServers in guildOwnerDict.items():
        if numServers >= 10:
            guildStr2 += "`guild owner: " + str(owner) + " | number of servers: " + str(numServers) + "`\n"
        elif numServers >= 3:
            guildStr2 += "guild owner: " + str(owner) + " | number of servers: " + str(numServers) + "\n"
    if request == "short":
        guildStr = guildStr2
    elif request == "long":
        guildStr = guildStr2 + "\n\n" + guildStr
    else:
        guildStr = "Must input 'short' or 'long' as argument."
    n = 1964
    messageList = [guildStr[i:i + n] for i in range(0, len(guildStr), n)]
    for messageText in messageList:
        await ctx.send(messageText)

@bot.command(name='displayOverworldList', help='DEV ONLY: display the overworld list', aliases=['dol', 'displayoverworldlist'])
async def displayOverworldList(ctx):
    if not await verifyDev(ctx):
        return
    messageStr = 'Overworld list:\n\nserver: [user id 1, user id 2, ...]\n\n'
    for key, userDict in data.overworldSessions.items():
        if userDict:
            toAppend = str(key) + ': ['
            toAppendUsers = ''
            first = True
            for identifier in userDict.keys():
                if not first:
                    toAppendUsers += ", "
                first = False
                identifier = str(identifier)
                toAppendUsers += identifier
            toAppend += toAppendUsers + "]\n\n"
            if toAppendUsers:
                messageStr += toAppend
    n = 2000
    messageList = [messageStr[i:i + n] for i in range(0, len(messageStr), n)]
    for messageText in messageList:
        await ctx.send(messageText)

@bot.command(name='displaySessionList', help='DEV ONLY: display the active session list', aliases=['dsl', 'displaysessionlist'])
async def displaySessionList(ctx):
    if not await verifyDev(ctx):
        return
    messageStr = 'Active session list:\n\nserver: [user id 1, user id 2, ...]\n\n'
    globalSaveStr = 'Global saves active:\n['
    globalSaveStrUsers = ''
    for key, userList in data.sessionDict.items():
        if userList:
            toAppend = str(key) + ': ['
            toAppendUsers = ''
            first = True
            for user in userList:
                if not first:
                    toAppendUsers += ", "
                first = False
                identifier = str(user.identifier)
                if identifier == -1:
                    identifier = str(user.author)
                if identifier == str(key):
                    if globalSaveStrUsers:
                        globalSaveStrUsers += ", "
                    globalSaveStrUsers += str(key)
                    continue
                toAppendUsers += identifier
            toAppend += toAppendUsers + "]\n\n"
            if toAppendUsers:
                messageStr += toAppend
    globalSaveStr += globalSaveStrUsers + "]"
    messageStr += globalSaveStr
    n = 2000
    messageList = [messageStr[i:i + n] for i in range(0, len(messageStr), n)]
    for messageText in messageList:
        await ctx.send(messageText)

@bot.command(name='forceEndSession', help='ADMIN ONLY: forcibly removes user from active sessions list, usage: !forceEndSession [user]', aliases=['forceendsession'])
async def forceEndSession(ctx, *, userName: str="self"):
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !forceEndsession for " + userName)

        if await verifyDev(ctx, False):
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

        user = await getUserById(ctx, userName)

        if user:
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

@bot.command(name='grantStamina', help='ADMIN ONLY: grants user stamina in amount specified, usage: !grantStamina [amount] [user]', aliases=['grantstamina'])
async def grantStamina(ctx, amount, *, userName: str="self"):
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !grantStamina for " + userName)

        user = await getUserById(ctx, userName)

        if user:
            user.dailyProgress += amount
            await ctx.send(user.name + ' has been granted ' + str(amount) + ' stamina.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant stamina.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='grantPokemon', help='DEV ONLY: grants user a Pokemon (use "_" for spaces in Pokemon name) in amount specified, usage: !grantPokemon [pokemon] [level] [shiny] [distortion] [@user]', aliases=['grantpokemon'])
async def grantPokemon(ctx, pokemonName, level, shiny, distortion, *, userName: str="self"):
    if not await verifyDev(ctx):
        return
    pokemonName = pokemonName.replace('_', " ")
    level = int(level)
    shiny = (shiny.lower() == "true")
    distortion = (distortion.lower() == "true")
    if distortion:
        shiny = True
    logging.debug(str(ctx.author.id) + " - !grantPokemon " + pokemonName.title() + " for " + userName + " with level=" + str(level) + " and shiny=" + str(shiny) + " and distortion=" + str(distortion))
    user = await getUserById(ctx, userName)
    if user:
        try:
            pokemon = Pokemon(data, pokemonName, level)
            pokemon.shiny = shiny
            pokemon.distortion = distortion
            pokemon.setSpritePath()
            pokemon.OT = "Event"
            user.addPokemon(pokemon, False)
            await ctx.send(user.name + ' has been granted ' + pokemonName.title() + " for " + userName + " with level=" + str(level) + " and shiny=" + str(shiny) + " and distortion=" + str(distortion))
        except:
            await ctx.send("Something went wrong trying to grant Pokemon.")
    else:
        await ctx.send("User '" + userName + "' not found, cannot grant Pokemon.")

@bot.command(name='grantItem', help='DEV ONLY: grants user item (use "_" for spaces in item name) in amount specified, usage: !grantItem [item] [amount] [user]', aliases=['grantitem'])
async def grantItem(ctx, item, amount, *, userName: str="self"):
    if not await verifyDev(ctx):
        return
    item = item.replace('_', " ")
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !grantItem " + item + " for " + userName)
        user = await getUserById(ctx, userName)
        if user:
            user.addItem(item, amount)
            await ctx.send(user.name + ' has been granted ' + str(amount) + ' of ' + item + '.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot grant item.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='removeItem', help='DEV ONLY: removes user item (use "_" for spaces in item name) in amount specified, usage: !removeItem [item] [amount] [user]', aliases=['removeitem'])
async def removeItem(ctx, item, amount, *, userName: str="self"):
    if not await verifyDev(ctx):
        return
    item = item.replace('_', " ")
    amount = int(amount)
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !removeItem " + item + " for " + userName)
        user = await getUserById(ctx, userName)
        if user:
            user.useItem(item, amount)
            await ctx.send(user.name + ' has been revoked ' + str(amount) + ' of ' + item + '.')
        else:
            await ctx.send("User '" + userName + "' not found, cannot remove item.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='disableStamina', help='ADMIN ONLY: disables stamina cost server wide for all users', aliases=['disablestamina'])
async def disableStamina(ctx):
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !disableStamina")
        data.staminaDict[str(ctx.message.guild.id)] = False
        await ctx.send("Stamina has been disabled on this server.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='enableStamina', help='ADMIN ONLY: enables stamina cost server wide for all users', aliases=['enablestamina'])
async def enableStamina(ctx):
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !enableStamina")
        data.staminaDict[str(ctx.message.guild.id)] = True
        await ctx.send("Stamina has been enabled on this server.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='setLocation', help='ADMIN ONLY: sets a players location, usage: !setLocation [user#1234] [location]', aliases=['setlocation'])
async def setLocation(ctx, userName, *, location):
    if ctx.message.author.guild_permissions.administrator:
        logging.debug(str(ctx.author.id) + " - !setLocation to " + location + " for " + userName)
        user = await getUserById(ctx, userName)
        if user:
            if location in user.locationProgressDict.keys():
                user.location = location
                await ctx.send(ctx.message.author.display_name + " was forcibly sent to: " + location + "!")
            else:
                await ctx.send('"' + location + '" has not been visited by user or does not exist.')
        else:
            await ctx.send("User '" + userName + "' not found.")
    else:
        await ctx.send(str(ctx.message.author.display_name) + ' does not have admin rights to use this command.')

@bot.command(name='getStamina', help='trade 2000 Pokedollars for 1 stamina', aliases=['gs', 'getstamina'])
async def getStamina(ctx, amount: str="1"):
    logging.debug(str(ctx.author.id) + " - !getStamina " + str(amount))
    try:
        amount = int(amount)
    except:
        await ctx.send("Invalid stamina amount.")
        return
    user, isNewUser = data.getUser(ctx)
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

@bot.command(name='setAlteringCave', help='trade 10 BP to set the Pokemon in Altering Cave (requirements: must have beaten Elite 4, no legendaries), use: "!sac [Pokemon name]"', aliases=['sac', 'setalteringcave'])
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
        "Deoxys",
        "Crystal Onix",
        "Shadow Lugia",
        "Shadow Ho-Oh",
        "Detective Pikachu",
        "Solar Espeon",
        "Spectre Greninja",
        "Pridetales",
        "Cool Ludicolo",
        "Pure Celebi",
        "Ditto Machoke",
        "Ditto Furret",
        "Missingno"
    ]
    user, isNewUser = data.getUser(ctx)
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

@bot.command(name='setBuyAmount', help='sets amount of item to buy in PokeMarts', aliases=['sba', 'setMartAmount', 'setbuyamount'])
async def setBuyAmount(ctx, amount):
    logging.debug(str(ctx.author.id) + " - !setBuyAmount " + amount)
    try:
        amount = int(amount)
    except:
        await ctx.send("Please use the format `!setBuyAmount 7`.")
        return
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if amount > 0:
            user.storeAmount = amount
            await ctx.send("PokeMart buy quantity set to " + str(amount) + ".")
        else:
            await ctx.send("Specified amount must be greated than 0.")

@bot.command(name='furret', help='furret', aliases=['Furret'])
async def furret(ctx):
    await ctx.send("https://tenor.com/view/furret-pokemon-cute-gif-17963535")

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

@bot.command(name='swapMoves', help="swap two of a Pokemon's moves, use: '!swapMoves [party position] [move slot 1] [move slot 2]'", aliases=['sm', 'swapmoves'])
async def swapMoves(ctx, partyPos, moveSlot1, moveSlot2):
    logging.debug(str(ctx.author.id) + " - !swapMoves " + str(partyPos) + ' ' +  str(moveSlot1) + ' ' + str(moveSlot2))
    partyPos = int(partyPos) - 1
    moveSlot1 = int(moveSlot1) - 1
    moveSlot2 = int(moveSlot2) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
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

@bot.command(name='createShinyCharm', help="creates shiny charm if possible", aliases=['csc', 'createshinycharm', 'shinycharm', 'shinyCharm'])
async def createShinyCharm(ctx):
    logging.debug(str(ctx.author.id) + " - !createShinyCharm")
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
    else:
        if "Shiny Charm Fragment" in user.itemList.keys():
            if user.itemList['Shiny Charm Fragment'] >= 3:
                if 'Shiny Charm' in user.itemList.keys() and user.itemList['Shiny Charm'] > 0:
                    await ctx.send("Already own a Shiny Charm. Can only have 1 at a time. They will break after you find your next shiny Pokemon.")
                    return
                user.useItem('Shiny Charm Fragment', 3)
                user.addItem('Shiny Charm', 1)
                await ctx.send("Shiny Charm created at the cost of 3 fragments. This charm will increase your shiny odds until you find your next shiny (at which point it will break).")
                return
        await ctx.send("Not enough Shiny Charm Fragment(s) in Bag to create Shiny Charm. Requires 3 fragments to create 1 charm.")

@bot.command(name='checkAuthor', help="DEV ONLY: check author by ID", aliases=['ca', 'checkauthor'])
async def checkAuthorCommand(ctx, identifier, server_id=""):
    if not await verifyDev(ctx):
        return
    if server_id:
        server_id = int(server_id)
    else:
        server_id = ctx.guild.id
    identifier = int(identifier)
    user = data.getUserById(server_id, identifier)
    if user:
        await ctx.send("Server: " + str(server_id) + "\nID: " + str(identifier) + "\nAuthor: " + user.author + "\nDisplay name: " + user.name)
    else:
        await ctx.send("User not found.")

@bot.command(name='startRaid', help="DEV ONLY: start a raid", aliases=['startraid'])
async def startRaidCommand(ctx, numRecentUsers=0):
    global raidsEnabled
    if not await verifyDev(ctx):
        return
    if not raidsEnabled:
        await ctx.send("Raids are not enabled.")
        return
    raid = Raid(data, battleTower)
    if numRecentUsers > 0:
        started = await raid.startRaid(True, numRecentUsers)
    else:
        started = await raid.startRaid(True)
    if started:
        await data.setRaid(raid)
    await ctx.send("Raid start command sent.")

@bot.command(name='endRaid', help="DEV ONLY: end a raid", aliases=['endraid'])
async def endRaidCommand(ctx, success="False"):
    if not await verifyDev(ctx):
        return
    if success.lower() == "true":
        success = True
    else:
        success = False
    if data.raid:
        await data.raid.endRaid(success)
    await ctx.send("Raid end command sent.")

@bot.command(name='removeFromRaidList', help="DEV ONLY: remove user from raid list", aliases=['removefromraidlist'])
async def removeFromRaidListCommand(ctx, *, userName='self'):
    if not await verifyDev(ctx):
        return
    logging.debug(str(ctx.author.id) + " - !removeFromRaidList " + userName)
    if data.raid:
        user = await getUserById(ctx, userName)
        if user:
            if data.raid.removeUserFromRaidList(user):
                await ctx.send(user.name + " removed from raid list.")
            else:
                await ctx.send("Failed to remove from raid list.")
        else:
            if userName == 'self':
                userName = str(ctx.author)
            await ctx.send("User '" + userName + "' not found.")
    else:
        await ctx.send("No raid active.")

@bot.command(name='clearRaidList', help="DEV ONLY: clears raid list", aliases=['clearraidlist'])
async def clearRaidListCommand(ctx):
    if not await verifyDev(ctx):
        return
    if data.raid:
        data.raid.clearRaidList()
    await ctx.send("Raid list cleared.")

@bot.command(name='viewRaidList', help="DEV ONLY: view raid list", aliases=['viewraidlist'])
async def viewRaidListCommand(ctx):
    if not await verifyDev(ctx):
        return
    messageStr = 'Raid List:\n\n'
    if data.raid:
        for user in data.raid.inRaidList:
            messageStr += str(user.identifier) + " - " + str(user.author) + '\n'
    n = 2000
    messageList = [messageStr[i:i + n] for i in range(0, len(messageStr), n)]
    for messageText in messageList:
        await ctx.send(messageText)

@bot.command(name='raidInfo', help="join an active raid", aliases=['ri', 'raidinfo'])
async def getRaidInfo(ctx):
    logging.debug(str(ctx.author.id) + " - !raidInfo ")
    raidExpired = True
    if data.raid:
        raidExpired = await data.raid.hasRaidExpired()
    if raidExpired:
        await ctx.send("There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")
        return
    if data.raid:
        data.raid.addChannel(ctx.channel)
        files, embed = data.raid.createRaidInviteEmbed()
        alertMessage = await ctx.send(files=files, embed=embed)
        # data.raid.addAlertMessage(alertMessage)
        user, isNewUser = data.getUser(ctx)
        if user:
            if data.isUserInRaidList(user):
                await ctx.send("You have already joined this raid.")
    else:
        await ctx.send("There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")

@bot.command(name='raidEnable', help="DEV ONLY: enable/disable raids", aliases=['raidenable'])
async def raidEnableCommand(ctx, shouldEnable="true"):
    global raidsEnabled
    if not await verifyDev(ctx):
        return
    if shouldEnable.lower() == 'true':
        raidsEnabled = True
        await ctx.send("Raids are enabled.")
    elif shouldEnable.lower() == "false":
        raidsEnabled = False
        await ctx.send("Raids are disabled.")
    else:
        await ctx.send("Invalid 'shouldEnable' option. Must be true or false.")

@bot.command(name='raid', help="join an active raid", aliases=['r', 'join'])
async def joinRaid(ctx):
    logging.debug(str(ctx.author.id) + " - !raid")
    try:
        user, isNewUser = data.getUser(ctx)
        if isNewUser:
            await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
        else:
            if data.raid and not data.raid.raidEnded:
                identifier = data.raid.identifier
                raidExpired = await data.raid.hasRaidExpired()
                if raidExpired:
                    await ctx.send("There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")
                    return
                if data.isUserInRaidList(user):
                    await ctx.send("You have already joined this raid. Use `!raidInfo` to check on the raid's status.")
                    return
                if not user.checkFlag('elite4'):
                    await ctx.send("Only trainers who have proven their worth against the elite 4 may take on raids.")
                    return
                data.raid.addChannel(ctx.channel)
                data.updateRecentActivityDict(ctx, user)
                data.raid.inRaidList.append(user)
                userCopy = copy(user)
                userCopy.itemList.clear()
                userCopy.pokemonCenterHeal()
                raidBossCopy = copy(data.raid.raidBoss)
                voidTrainer = Trainer(0, "The Void", "The Void", "NPC Battle")
                voidTrainer.addPokemon(raidBossCopy, True)
                userCopy.location = 'Petalburg Gym'
                battle = Battle(data, userCopy, voidTrainer)
                battle.isRaid = True
                battle.startBattle()
                battle.disableExp()
                battle.pokemon2.hp = data.raid.raidBoss.hp
                battle.pokemon2.currentHP = data.raid.raidBoss.currentHP
                startingHP = battle.pokemon2.currentHP
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                       startNewUI, continueUI, startPartyUI, startOverworldUI,
                                       startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(ctx, False, battle, 'BattleCopy', None, False, False, False)
                logging.debug(str(ctx.author.id) + " - !raid - done with battle")
                if data.raid is not None and data.raid.identifier == identifier and not data.raid.raidEnded:
                    logging.debug(str(ctx.author.id) + " - !raid - attempting to end raid")
                    try:
                        logging.debug(str(ctx.author.id) + " - !raid - ending raid")
                        await data.raid.endRaid(True)
                        logging.debug(str(ctx.author.id) + " - !raid - updating alert messages")
                        await data.raid.updateAlertMessages()
                    except:
                        logging.error("Error in !raid command, traceback = " + str(traceback.format_exc()))
                logging.debug(str(ctx.author.id) + " - !raid - sending message = Your raid battle has ended.")
                await ctx.send("Your raid battle has ended.")
            else:
                await ctx.send("There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")
    except:
        logging.error("Error in !raid command, traceback = " + str(traceback.format_exc()))
        # traceback.print_exc()

@bot.command(name='battle', help="battle an another user on the server, use: '!battle [trainer name]'", aliases=['b', 'battleTrainer', 'duel', 'pvp'])
async def battleTrainer(ctx, *, trainerName: str="self"):
    logging.debug(str(ctx.author.id) + " - !battle " + trainerName)
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
    else:
        if data.isUserInSession(ctx, user):
            await ctx.send("Sorry " + str(ctx.message.author.mention) + ", but you cannot battle another player while in an active session. Please end current session with `!endSession` or wait for it to timeout.")
        else:
            if trainerName == 'self':
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
                userToBattle = await getUserById(ctx, trainerName)
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
                            await ctx.send(str(ctx.author.mention) + " has requested a battle against " + trainerName +
                                           ". They have 2 minutes to respond.\n\n" + trainerName +
                                           ", to accept this battle, please type: '!battle " +
                                           str(ctx.author.mention) + "'.\nIt is recommended to do this in a separate channel so your opponent cannot see your move selection.")
                            await sleep(pvpTimeout)
                            if userToBattle in serverPvpDict.keys():
                                if not serverPvpDict[userToBattle][2]:
                                    del serverPvpDict[userToBattle]
                                    await ctx.send(trainerName + " did not respond to battle request. Please try again. If you would instead like to battle an NPC-controlled copy of this user, please use `!battleCopy @user`.")
                    else:
                        await ctx.send("Cannot battle yourself.")
                else:
                    await ctx.send("User '" + trainerName + "' not found.")

@bot.command(name='battleCopy', help="battle an NPC of another trainer, use: '!battleCopy [trainer name]'", aliases=['battlecopy', 'bc'])
async def battleCopy(ctx, *, trainerName: str="self"):
    logging.debug(str(ctx.author.id) + " - !battleCopy " + trainerName)
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
    else:
        if data.isUserInSession(ctx, user):
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot battle another player while in an active session. Please end your session with `!endSession`.")
        else:
            if trainerName == 'self':
                await ctx.send("Please @ a user to battle a copy of.\nExample: `!battleCopy @Zetaroid`")
            else:
                userToBattle = await getUserById(ctx, trainerName)
                if userToBattle:
                    if user.author != userToBattle.author:
                        userToBattle = copy(userToBattle)
                        user = copy(user)
                        user.scaleTeam(None, 100)
                        userToBattle.identifier = 0
                        userToBattle.scaleTeam(None, 100)
                        userToBattle.pokemonCenterHeal()
                        user.pokemonCenterHeal()
                        user.location = 'Petalburg Gym'
                        user.itemList.clear()
                        battle = Battle(data, user, userToBattle)
                        battle.disableExp()
                        battle.startBattle()
                        await startBeforeTrainerBattleUI(ctx, False, battle, "BattleCopy")
                        await ctx.send("Battle ended due to victory/loss or timeout.")
                    else:
                        await ctx.send("Cannot battle yourself.")
                else:
                    await ctx.send("User '" + trainerName + "' not found.")

@bot.command(name='endSession', help="ends the current session", aliases=['e', 'es', 'end', 'quit', 'close', 'endsession'])
async def endSessionCommand(ctx):
    logging.debug(str(ctx.author.id) + " - !endSession - Command")
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        logging.debug(str(ctx.author.id) + " - not ending session, have not started game yet")
        await ctx.send("You have not yet played the game and have no active session! Please start with `!start`.")
    else:
        overworldTuple, isGlobal = data.userInOverworldSession(ctx, user)
        if overworldTuple:
            try:
                message = overworldTuple[0]
                await message.delete()
                data.expiredSessions.append(overworldTuple[1])
                data.removeOverworldSession(ctx, user)
            except:
                logging.error(str(ctx.author.id) + " - end session command had an error\n" + str(traceback.format_exc()))
                await sendDiscordErrorMessage(ctx, traceback, str(str(ctx.message.author.id) + "'s end session command attempt had an error.\n" + str(traceback.format_exc()))[-1999:])
            logging.debug(str(ctx.author.id) + " - calling endSession() from endSessionCommand()")
            await endSession(ctx)
        else:
            logging.debug(str(ctx.author.id) + " - not ending session, not in overworld or not active session")
            await ctx.send("You must be in the overworld in an active session to end a session.")

async def endSession(ctx):
    logging.debug(str(ctx.author.id) + " - endSession() called")
    user, isNewUser = data.getUser(ctx)
    removedSuccessfully = data.removeUserSession(ctx.message.guild.id, user)
    if (removedSuccessfully):
        logging.debug(str(ctx.author.id) + " - endSession() session ended successfully, connection closed")
        await ctx.send(ctx.message.author.display_name + "'s session ended. Please start game again with `!start`.")
    else:
        logging.debug(str(ctx.author.id) + " - endSession() session unable to end, not in session list")
        await sendDiscordErrorMessage(ctx, traceback, "Session unable to end, not in session list: " + str(ctx.message.author.id))

@bot.command(name='viewBase', help="view another trainers base", aliases=['viewbase'])
async def viewBaseCommand(ctx, *, userName: str="self"):
    logging.debug(str(ctx.author.id) + " - !viewBase " + userName)
    user = await getUserById(ctx, userName)
    if userName == 'self':
        userName = str(ctx.author)
    if user:
        if user.secretBase:
            await secretBaseUi.viewSecretBaseUI(ctx, user)
        else:
            await ctx.send(userName + " does not have a secret base.")
    else:
        await ctx.send("User '" + userName + "' not found.")

@bot.command(name='deleteBase', help="delete a secret base", aliases=['removeBase', 'deletebase', 'removebase'])
async def deleteBaseCommand(ctx):
    logging.debug(str(ctx.author.id) + " - !deleteBase")
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        logging.debug(str(ctx.author.id) + " - cannot delete base, have not started game yet")
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
    else:
        if data.isUserInSession(ctx, user):
            await ctx.send("Cannot delete base while in an active session. Please send session with `!endSession`.")
        else:
            if user.secretBase:
                for coords, itemList in user.secretBase.placedItems.items():
                    for item in itemList:
                        user.addSecretBaseItem(item.name, 1)
                user.secretBase = None
                await ctx.send("Base deleted.")
            else:
                await ctx.send("No base to delete.")

@bot.command(name='secretPower', help="create a secret base", aliases=['sp', 'createBase', 'base', 'createbase', 'secretpower', 'secretBase', 'secretbase'])
async def secretPowerCommand(ctx, baseNum=''):
    logging.debug(str(ctx.author.id) + " - !secretPower")
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        logging.debug(str(ctx.author.id) + " - cannot create base, have not started game yet")
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
    else:
        if not data.isUserInSession(ctx, user):
            logging.debug(str(ctx.author.id) + " - not creating base, not in active session")
            await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot create a base without being in an active session. Please start a session with '!start'.")
        else:
            currentLocation = user.location
            locationObj = data.getLocation(currentLocation)
            if locationObj.secretBaseType:
                if user.secretBase:
                    await ctx.send("You already have a secret base. Please delete this secret base with `!deleteBase` before creating a new one.")
                    return
                overworldTuple, isGlobal = data.userInOverworldSession(ctx, user)
                if overworldTuple:
                    try:
                        message = overworldTuple[0]
                        await message.delete()
                        data.expiredSessions.append(overworldTuple[1])
                        data.removeOverworldSession(ctx, user)
                    except:
                        logging.error(str(ctx.author.id) + " - creating a base had an error\n" + str(traceback.format_exc()))
                        await sendDiscordErrorMessage(ctx, traceback, str(str(ctx.message.author.id) + "'s create base attempt had an error.\n" + str(traceback.format_exc()))[-1999:])
                    logging.debug(str(ctx.author.id) + " - creating base successful")
                    baseCreationMessage = await ctx.send(ctx.message.author.display_name + " created a new secret base! Traveling to base now.\n(continuing automatically in 4 seconds...)")
                    await sleep(4)
                    await baseCreationMessage.delete()
                    createNewSecretBase(user, locationObj, baseNum)
                    try:
                        await secretBaseUi.startSecretBaseUI(ctx, user)
                    except discord.errors.Forbidden:
                        await forbiddenErrorHandle(ctx)
                    except:
                        await sessionErrorHandle(ctx, user, traceback)
                else:
                    logging.debug(str(ctx.author.id) + " - not creating base, not in overworld")
                    await ctx.send("Cannot create base while not in the overworld.")
            else:
                await ctx.send("Cannot create a secret base in this location.")

def createNewSecretBase(user, locationObj, baseNum):
    baseType = locationObj.secretBaseType
    if baseNum and (baseNum == '1' or baseNum == '2' or baseNum == '3' or baseNum == '4'):
        randomBaseNum = baseNum
    else:
        randomBaseNum = random.randint(1, 4)
    baseType += "_" + str(randomBaseNum)
    myBase = Secret_Base(data, baseType, user.name + "'s Base", locationObj.name)
    user.secretBase = myBase

@bot.command(name='fly', help="fly to a visited location, use: '!fly [location name]'", aliases=['f'])
async def fly(ctx, *, location: str=""):
    global bannedFlyAreas
    logging.debug(str(ctx.author.id) + " - !fly " + location)
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        logging.debug(str(ctx.author.id) + " - not flying, have not started game yet")
        await ctx.send("You have not yet played the game and have no Pokemon! Please start with `!start`.")
    else:
        if 'fly' in user.flags:
            if not data.isUserInSession(ctx, user):
                logging.debug(str(ctx.author.id) + " - not flying, not in active session")
                await ctx.send("Sorry " + ctx.message.author.display_name + ", but you cannot fly without being in an active session. Please start a session with '!start'.")
            else:
                location = location.title()
                locationLower = location.lower()
                if locationLower in [item.lower() for item in list(user.locationProgressDict.keys())]:
                    if locationLower in [item.lower() for item in bannedFlyAreas]:
                        logging.debug(str(ctx.author.id) + " - not flying, cannot fly to this area!")
                        await ctx.send("Sorry, cannot fly to this area!")
                    elif user.location.lower() in [item.lower() for item in bannedFlyAreas]:
                        logging.debug(str(ctx.author.id) + " - not flying, cannot fly from this area!")
                        await ctx.send("Sorry, cannot fly from this area!")
                    else:
                        overworldTuple, isGlobal = data.userInOverworldSession(ctx, user)
                        if overworldTuple:
                            try:
                                message = overworldTuple[0]
                                await message.delete()
                                data.expiredSessions.append(overworldTuple[1])
                                data.removeOverworldSession(ctx, user)
                            except:
                                #traceback.print_exc()
                                logging.error(str(ctx.author.id) + " - flying had an error\n" + str(traceback.format_exc()))
                                await sendDiscordErrorMessage(ctx, traceback, str(str(ctx.message.author.id) + "'s fly attempt had an error.\n" + str(traceback.format_exc()))[-1999:])
                            logging.debug(str(ctx.author.id) + " - flying successful")
                            user.location = location
                            flyMessage = await ctx.send(ctx.message.author.display_name + " used Fly! Traveled to: " + location + "!\n(continuing automatically in 4 seconds...)")
                            await sleep(4)
                            await flyMessage.delete()
                            try:
                                await startOverworldUI(ctx, user)
                            except discord.errors.Forbidden:
                                await forbiddenErrorHandle(ctx)
                            except:
                                await sessionErrorHandle(ctx, user, traceback)
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
                        if location in bannedFlyAreas:
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
    user = await getUserById(ctx, userName)
    if user:
        embed = createProfileEmbed(ctx, user)
        await ctx.send(embed=embed)
    else:
        if userName == 'self':
            userName = str(ctx.author)
        await ctx.send("User '" + userName + "' not found.")

@bot.command(name='trainerCard', help="get a Trainer's card, use: '!trainerCard [trainer name]'", aliases=['tc', 'trainercard', 'card', 'team'])
async def trainerCard(ctx, *, userName: str="self"):
    logging.debug(str(ctx.author.id) + " - !trainerCard " + userName)
    user = await getUserById(ctx, userName)
    if user:
        filename, filenameBack = createTrainerCard(user)
        await ctx.send(file=discord.File(filename))
        await ctx.send(file=discord.File(filenameBack))
        try:
            os.remove(filename)
            os.remove(filenameBack)
        except:
            pass
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
    userToTradeWith = await getUserById(ctx, userName)
    userTrading = await getUserById(ctx, ctx.author.id)
    try:
        if userToTradeWith is None:
            await ctx.send("User '" + userName + "' not found.")
        elif userTrading is None:
            await ctx.send("You are not yet a trainer! Use '!start' to begin your adventure.")
        elif (len(userTrading.partyPokemon) < partyNum):
            await ctx.send("No Pokemon in that party slot.")
        elif data.isUserInTradeDict(ctx, userTrading):
            await ctx.send("You are already waiting for a trade.")
        elif data.isUserInSession(ctx, userTrading):
            await ctx.send("Please end your session with `!endSession` before trading.")
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
            awaitingMessage = await ctx.send("You are trading: `" + pokemonToTrade.name + "`\n\n" +
                           str(ctx.author.mention) + " has requested a trade with " + userName +
                           ". They have 1 minute to respond.\n\n" + userName +
                           ", to accept this trade, please type: '!trade <party number> " +
                           str(ctx.author.mention) + "'.")
            # awaitingMessage = await ctx.send("Awaiting " + userName + " to initiate trade with you.\nYou are trading: " + pokemonToTrade.name)
            data.getTradeDict(ctx)[userTrading] = (userToTradeWith, pokemonToTrade, partyNum, awaitingMessage)
            def check(m):
                return ('!trade' in m.content.lower()
                        and str(ctx.author.id) in m.content.lower()
                        and str(m.author.id) in userName.lower()
                        )

            async def waitForMessage(ctx):
                try:
                    msg = await bot.wait_for("message", timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    try:
                        await awaitingMessage.delete()
                        expiredMessage = await ctx.send('Trade offer from ' + str(ctx.author.mention) + " timed out.")
                    except:
                        pass
                    try:
                        del data.getTradeDict(ctx)[userTrading]
                    except:
                        pass
                else:
                    pass

            await waitForMessage(ctx)
    except:
        try:
            if userTrading in data.getTradeDict(ctx).keys():
                del data.getTradeDict(ctx)[userTrading]
        except:
            pass
        try:
            if userToTradeWith in data.getTradeDict(ctx).keys():
                del data.getTradeDict(ctx)[userToTradeWith]
        except:
            pass

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
        # payloadAuthor = payload.member.name + "#" + payload.member.discriminator
        payloadIdentifier = str(payload.member.id)
        if payloadIdentifier != str(botId):
            logging.debug(str(ctx.author.id) +
                          " - payloadIdentifier = " +
                          str(payloadIdentifier) +
                          ", payload.emoji.name = " +
                          str(payload.emoji.name) +
                          ", checkEquals = " +
                          str(payload.emoji.name == '☑️') +
                              ", checkX = " +
                          str(payloadIdentifier == str(user2.identifier)))
        returnVal = ((payloadIdentifier == str(user1.identifier) or payloadIdentifier == str(user2.identifier)) and (
                    payload.emoji.name == '☑️' or payload.emoji.name == '🇽'))
        return returnVal

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
            try:
                payloadAuthor = payload.member.name + "#" + payload.member.discriminator
                payloadIdentifier = payload.member.id
                userValidated = False
                if (messageID == payload.message_id):
                    userValidated = True
                if userValidated:
                    if (payload.emoji.name == '☑️'):
                        if payloadIdentifier == user1.identifier and user1.identifier not in confirmedList:
                            confirmedList.append(user1.identifier)
                        elif payloadIdentifier == user2.identifier and user2.identifier not in confirmedList:
                            confirmedList.append(user2.identifier)
                        if (user1.identifier in confirmedList and user2.identifier in confirmedList):
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
                    elif (payload.emoji.name == '🇽'):
                        await message.delete()
                        cancelMessage = await ctx.send(payloadAuthor + " cancelled trade.")
                        if user1 in data.getTradeDict(ctx).keys():
                            del data.getTradeDict(ctx)[user1]
                        if user2 in data.getTradeDict(ctx).keys():
                            del data.getTradeDict(ctx)[user2]
                        return
                    await waitForEmoji(ctx, confirmedList)
            except:
                logging.error("Trading failed.\n" + str(traceback.format_exc()))

    await waitForEmoji(ctx, confirmedList)

@bot.command(name='guide', help='helpful guide', aliases=['g'])
async def getGuide(ctx):
    guideMessage = 'Check out our full guide here:\nhttps://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md#Guide'
    nextMessage = ''
    user = await getUserById(ctx, 'self')
    if user:
        nextMessage += "```Guide:\n"
        if 'elite4' in user.flags:
            nextMessage += 'Congratulations league champion! You can now do the following:\n- Take part in raids (!raid)\n- Shiny hunt (1/200 odds) or look for rare Distortion Shinies (1/10k odds)\n- Catch gen 4-7 Pokemon in Altering Cave (costs 10 BP to alter the Pokemon in the cave with !setAlteringCave)\n- Catch legendaries (hint: see Slateport Harbor, Route 115, Route 127, Route 134, and Route 108)\n- Gym leader rematches (lv70 and lv100)\n- Take on a harder elite 4\n- Take on the battle tower to earn BP (go to Slateport Harbor and head to the Battle Frontier)\n- Create a secret base (!secretPower)\n- Buy Mega Stones and furniture in the !shop\n- And much more!'
        elif 'badge8' in user.flags:
            nextMessage += "You've beaten the gym challenge! Now go to Route 128 and head for Victory Road and the Pokemon League!"
        elif 'rayquaza' in user.flags:
            nextMessage += "You beat Zinnia at Sky Pillar and earned Rayquaza's respect. Rayquaza has quelled the conflict between Groudon and Kyogre, and the region is safe once more. Head back to Sootopolis City and take on the 8th gym!"
        elif "cave of origin" in user.flags:
            nextMessage += "You met Juan in the Cave of Origin. He told you to head to Sky Pillar off of Route 131 to request the help of a deity."
        elif 'seafloor cavern' in user.flags:
            nextMessage += "You took down Team Aqua in Seafloor Cavern, but Groudon and Kyogre rage on! Head to the Cave of Origin in Sootopolis City to learn how to quell the ancient beasts!"
        elif 'badge7' in user.flags:
            nextMessage += "You've beaten the 7th gym in Mossdeep City and obtained HM Dive. Head to Route 128 and take a dive under to battle Team Aqua one last time!"
        elif 'route 124' in user.flags:
            nextMessage += "You have taken down both Team Magma's and Team Aqua's bases. Head to Route 124 and Mossdeep City from Lilycove City to continue your adventure and take on the 7th gym."
        elif 'aqua emblem' in user.flags:
            nextMessage += "Infuriated by their defeat, Team Magma handed you the Aqua Emblem. Head back to Lilycove City to take down Team Aqua's base!"
        elif 'magma emblem' in user.flags:
            nextMessage += "You defeated some Team Aqua grunts at Mt. Pyre and they handed you a Magma Emblem. Head back to Jagged Pass (hint: you can `!fly` there) to take down Team Magma's base!"
        elif 'badge6' in user.flags:
            nextMessage += "You've beaten Winona at the 6th gym in Fortree City. You now have the ability to use the `!fly` command. Head to Route 120->121->122 and to Mt. Pyre to continue your journey."
        elif 'rival3' in user.flags:
            nextMessage += "You have defeated your rival yet again! Continue onto Fortree City for the 6th gym."
        elif 'badge5' in user.flags:
            nextMessage += "You've beaten Norman at the 5th gym in Petalburg City. You have obtained HM Surf, and can now freely explore Routes 105-108 between Petalburg and Slateport City. When you are ready, head back to Mauville City and continue onto Route 118 to continue your adventure."
        elif 'badge4' in user.flags:
            nextMessage += "You've beaten Flannery at the 4th gym in Lavaridge Town. You can now explore the desert off Route 111. When you are ready, go back to Petalburg City to take on the 5th gym!"
        elif 'mt chimney' in user.flags:
            nextMessage += "You defeated Team Magma at Mt. Chimney! Head down the mountain to Lavaridge Town and take on the 4th gym."
        elif 'meteor falls' in user.flags:
            nextMessage += "You encountered Team Magma at Meteor Falls, but they got away! Head back to Route 112 S and follow them to Mt. Chimney!"
        elif 'badge3' in user.flags:
            nextMessage += "You've beaten Wattson at the 3rd gym in Dewford Town. Head north from Mauville City to Route 111 S and make your way to Meteor Falls."
        elif 'badge2' in user.flags:
            nextMessage += "You've beaten Brawly at the 2nd gym in Dewford Town. Ride with Mr. Briney to Slateport City to continue your adventure towards the 3rd gym in Mauville City."
        elif 'badge1' in user.flags and 'briney' in user.flags:
            nextMessage += "You've beaten Roxanne at the 1st gym in Rustboro City and saved Mr. Briney. Head back to Route 104 S to ride with Mr. Briney to Dewford Town for the 2nd gym."
        elif 'badge1' in user.flags:
            nextMessage += "You've beaten Roxanne at the 1st gym in Rustboro City. Head to Rusturf Tunnel off of Route 116 to help Mr. Briney."
        elif 'briney' in user.flags:
            nextMessage += "You've saved Mr. Briney, but have yet to tackle the 1st gym! Head to Rustboro City to start your gym challenge."
        elif 'rival1' in user.flags:
            nextMessage += "You managed to beat your rival! Head back to Oldale Town and continue onto Route 102."
        nextMessage += "```"
    await ctx.send(nextMessage + "\n\n" + guideMessage)

@bot.command(name='moveInfo', help='get information about a move', aliases=['mi', 'moveinfo'])
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
        moveCategory = moveData['category']
        try:
            moveDesc = moveData['pokedex_entries']['Emerald']['en']
        except:
            try:
                moveDesc = moveData['pokedex_entries']['Sun']['en']
            except:
                moveDesc = 'No description'
        result = '```Name: ' + moveName + '\nPower: ' + str(movePower) + '\nPP: ' + str(movePP) + '\nCategory: ' + str(moveCategory).title() + '\nAccuracy: ' + str(moveAcc) + '\nType: ' + moveType + '\nDescription: ' + moveDesc + '```'
        await ctx.send(result)
    else:
        await ctx.send('Invalid move')

@bot.command(name='dex', help='get information about a Pokemon', aliases=['pokedex', 'pokeinfo'])
async def dexCommand(ctx, *, pokeName=""):
    if pokeName:
        formNum = None
        shiny = False
        distortion = False
        if pokeName.lower().endswith(" shiny"):
            shiny = True
            pokeName = pokeName[:-6]
        if pokeName.lower().endswith(" distortion"):
            distortion = True
            pokeName = pokeName[:-11]
        if ' form ' in pokeName.lower():
            strList = pokeName.split(' ')
            formStr = strList[len(strList)-1]
            formNum = int(formStr)
            pokeName = pokeName[:-(len(formStr)+6)]
        pokeName = pokeName.title()
        try:
            pokemon = Pokemon(data, pokeName, 100)
            if formNum:
                if formNum >= 0 and formNum <= len(pokemon.getFullData()['variations']):
                    pokemon.form = formNum
                    pokemon.updateForFormChange()
                else:
                    await ctx.send("Invalid form number.")
                    return
            files, embed = createPokemonDexEmbed(ctx, pokemon, shiny, distortion)
            await ctx.send(files=files, embed=embed)
        except:
            #traceback.print_exc()
            await ctx.send(pokeName + " is not a valid Pokemon species.")
    else:
        await ctx.send("Invalid command input. Use `!dex <Pokemon name>`.")

@bot.command(name='enableGlobalSave', help="enables global save file for current server", aliases=['egs', 'enableglobalsave'])
async def enableGlobalSave(ctx, server_id=''):
    logging.debug(str(ctx.author.id) + " - !enableGlobalSave")
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if ctx.author.id in data.globalSaveDict.keys():
            await ctx.send("You already have a global save. Please disable it with `!disableGlobalSave` before setting a new one.")
            return
        elif data.isUserInSession(ctx, user):
            await ctx.send("Please end your session with `!endSession` before enabling global save.")
            return
        elif data.isUserInAnySession(user):
            await ctx.send("You have an active session in another server. Please end it in that server with `!endSession` before enabling global save.")
            return
        else:
            if server_id:
                try:
                    server_id = int(server_id)
                except:
                    server_id = ctx.guild.id
            else:
                server_id = ctx.guild.id
            data.globalSaveDict[ctx.author.id] = (server_id, str(ctx.author))
            await ctx.send("Global save enabled. The save file from this server will now be used on ALL servers you use the PokéNav bot in. To disable, use `!disableGlobalSave`.")

@bot.command(name='disableGlobalSave', help="disables global save file", aliases=['dgs', 'disableglobalsave'])
async def disableGlobalSave(ctx):
    logging.debug(str(ctx.author.id) + " - !disableGlobalSave")
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if data.isUserInSession(ctx, user):
            await ctx.send("Please end your session with `!endSession` before disabling global save.")
            return
        if ctx.author.id in data.globalSaveDict.keys():
            del data.globalSaveDict[ctx.author.id]
            await ctx.send("Global save disabled. Each server you use the bot in will have a unique save file. To enable again, use `!enableGlobalSave` from the server you want to be your global save file.")
        else:
            await ctx.send("You do not have a global save to disable. Please enable it with `!enableGlobalSave` before attempting to disable.")

@bot.command(name='toggleForm', help="toggles the form of a Pokemon in your party", aliases=['tf', 'changeForm', 'toggleform', 'changeform'])
async def toggleForm(ctx, partyPos, formNum=None):
    logging.debug(str(ctx.author.id) + " - !toggleForm " + str(partyPos))
    partyPos = int(partyPos) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        overworldTuple, isGlobal = data.userInOverworldSession(ctx, user)
        if overworldTuple or not data.isUserInSession(ctx, user):
            if (len(user.partyPokemon) > partyPos):
                if formNum:
                    try:
                        formNum = int(formNum)
                    except:
                        await ctx.send("Invalid form number.")
                    success, reason = user.partyPokemon[partyPos].setForm(formNum, user)
                else:
                    success, reason = user.partyPokemon[partyPos].toggleForm(user)
                if success:
                    await ctx.send("'" + user.partyPokemon[partyPos].nickname + "' changed form to " + user.partyPokemon[partyPos].getFormName() + "!")
                else:
                    await ctx.send("'" + user.partyPokemon[partyPos].name + "' cannot change form. " + reason)
            else:
                await ctx.send("No Pokemon in that party slot.")
        else:
            logging.debug(str(ctx.author.id) + " - not changing forms, not in overworld")
            await ctx.send("Cannot change Pokemon forms while not in the overworld.")

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

@bot.command(name='event', help='display current event')
async def eventCommand(ctx):
    if data.eventActive:
        eventObj = data.eventDict[data.activeEvent]
        files, embed = createEventEmbed(eventObj.name)
        await ctx.send(files=files, embed=embed)
    else:
        await ctx.send("No active event.")

@bot.command(name='startEvent', help='DEV ONLY: starts a specified event', aliases=['startevent'])
async def startEventCommand(ctx, *, event):
    if not await verifyDev(ctx):
        return
    try:
        event = int(event) - 1
        eventList = list(data.eventDict.keys())
        if event < len(eventList):
            await endEvent(ctx)
            data.activeEvent = eventList[event]
            data.eventActive = True
            await ctx.send("Event '" + data.activeEvent + "' started.")
    except:
        if event in data.eventDict.keys():
            await endEvent(ctx)
            data.activeEvent = event
            data.eventActive = True
            await ctx.send("Event '" + data.activeEvent + "' started.")
        else:
            await ctx.send("Invalid event name. Use `!eventList` to see valid events.")

async def eventCheck(ctx, user):
    if data.activeEvent in data.eventDict:
        eventObj = data.eventDict[data.activeEvent]
        if data.eventActive:
            if eventObj.item:
                if eventObj.item in user.itemList.keys() and user.itemList[eventObj.item] > 0:
                    return
                user.itemList[eventObj.item] = 1
            files, embed = createEventEmbed(eventObj.name)
            await ctx.send(files=files, embed=embed)

def createEventEmbed(eventName, ended=False):
    event = data.eventDict[eventName]
    files = []
    if ended:
        title = "'" + event.name + "' has ended!"
        desc = "Event has ended! See you next time!"
        footer = "Thank you for participating!"
    else:
        title = event.name
        desc = event.desc
        if event.footer:
            footer = event.footer
        else:
            footer = "Head to Lilycove Harbor to participate in the event!\nEvents are limited time only!"
    embed = discord.Embed(title=title, description=desc)
    file = discord.File(event.image, filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=footer)
    return files, embed

@bot.command(name='endEvent', help='DEV ONLY: ends current event', aliases=['endevent'])
async def endEventCommand(ctx):
    if not await verifyDev(ctx):
        return
    await endEvent(ctx)

async def endEvent(ctx, suppressMessage=False):
    if data.eventActive:
        eventObj = data.eventDict[data.activeEvent]
        eventItem = eventObj.item
        for server_id in data.userDict.keys():
            for user in data.userDict[server_id]:
                user.itemList[eventItem] = 0
        data.eventActive = False
        await ctx.send("Event ended.")
        if not suppressMessage:
            numRecentUsers, channelList = data.getNumOfRecentUsersForRaid()
            for channel_id in channelList:
                try:
                    channel = data.getChannelById(channel_id)
                    files, embed = createEventEmbed(eventObj.name, True)
                    await channel.send(files=files, embed=embed)
                except:
                    pass
    else:
        await ctx.send("No event to end.")

@bot.command(name='eventList', help='DEV ONLY: lists all events', aliases=['eventlist'])
async def eventListCommand(ctx):
    if not await verifyDev(ctx):
        return
    eventStr = 'Events:\n\n'
    count = 1
    for eventName in data.eventDict.keys():
        eventStr += str(count) + ". " + eventName + "\n"
        count += 1
    await ctx.send(eventStr)

@bot.command(name='save', help='DEV ONLY: saves data, automatically disables bot auto save (add flag "enable" to reenable)')
async def saveCommand(ctx, flag = "disable"):
    global allowSave
    global saveLoopActive
    if not await verifyDev(ctx):
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
        await endEvent(ctx, True)
        allowSave = False
        await sleep(5)
        data.writeUsersToJSON()
    await ctx.send("Data saved.\nautoSave = " + str(allowSave))

@bot.command(name='vote', help='vote for the bot', aliases=['Vote'])
async def voteCommand(ctx):
    await ctx.send("Please support us by voting for PokeNav!\n\nhttps://top.gg/bot/800207357622878229/vote")

@bot.command(name='saveStatus', help='DEV ONLY: check status of autosave', aliases=['savestatus'])
async def getSaveStatus(ctx):
    global allowSave
    global saveLoopActive
    if not await verifyDev(ctx):
        return
    await ctx.send("allowSave = " + str(allowSave) + '\n' + 'saveLoopActive = ' + str(saveLoopActive))

@bot.command(name='bag', help='DEV ONLY: display bag items')
async def bagCommand(ctx, *, userName: str="self"):
    if not await verifyDev(ctx, False):
        return
    user = await getUserById(ctx, userName)
    newItemList = []
    for item, amount in user.itemList.items():
        if amount > 0:
            newItemList.append(item)
    files, embed = createBagEmbed(ctx, user, newItemList)
    await ctx.send(files=files, embed=embed)

@bot.command(name='test', help='DEV ONLY: test various features')
async def testWorldCommand(ctx):
    if not await verifyDev(ctx):
        return
    location = "Test"
    progress = 0
    pokemonPairDict = {
        "Greninja": 100,
        "Charmander": 100,
        "Froakie": 100,
        "Mudkip": 100,
        "Groudon": 100,
        "Arceus": 100,
    }
    movesPokemon1 = [
        "Spore",
        "Toxic",
        "Poison Powder",
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

@bot.command(name='testBase', help='DEV ONLY: test base features', aliases=['testbase'])
async def testBase(ctx):
    if not await verifyDev(ctx):
        return
    user, isNewUser = data.getUser(ctx)

    myBase = Secret_Base(data, "forest_3", "My Awesome Base", "Desert")

    # print('\nattract mat:')
    # attractRug = data.secretBaseItems['rug_attract']
    # placedSuccessfully = myBase.placeItemByLetter("E", 1, attractRug)
    # print('placedSuccessfully = ', placedSuccessfully)
    #
    # print('\nbrick desk large:')
    # desk_brick_large = data.secretBaseItems['desk_brick']
    # placedSuccessfully = myBase.placeItemByLetter("E", 1, desk_brick_large)
    # print('placedSuccessfully = ', placedSuccessfully)
    #
    # print('\nduskull doll:')
    # duskullDoll = data.secretBaseItems['doll_duskull']
    # placedSuccessfully = myBase.placeItemByLetter("F", 1, duskullDoll)
    # print('placedSuccessfully = ', placedSuccessfully)
    #
    # print("\nlapras doll:")
    # laprasDoll = data.secretBaseItems['slide']
    # placedSuccessfully = myBase.placeItemByLetter("C", 4, laprasDoll)
    # print('placedSuccessfully = ', placedSuccessfully)
    #
    # print("\nballoon:")
    # balloon_blue = data.secretBaseItems['balloon_blue']
    # placedSuccessfully = myBase.placeItemByLetter("L", 5, balloon_blue)
    # print('placedSuccessfully = ', placedSuccessfully)
    #
    # print("\nposter_mudkip:")
    # poster_mudkip = data.secretBaseItems['poster_mudkip']
    # placedSuccessfully = myBase.placeItemByLetter("F", 0, poster_mudkip)
    # print('placedSuccessfully = ', placedSuccessfully)

    user.secretBase = myBase
    addAllBaseItems(user)

    await secretBaseUi.startSecretBaseUI(ctx, user)

def addAllBaseItems(trainer):
    for key in data.secretBaseItems.keys():
        trainer.addSecretBaseItem(key, 100)

async def safeDeleteMessgae(message):
    try:
        await message.delete()
    except:
        pass

async def verifyDev(ctx, sendMessage=True):
    if ctx.author.id == 189312357892096000:
        return True
    else:
        if sendMessage:
            await ctx.send(str(ctx.message.author.display_name) + ' does not have developer rights to use this command.')
        return False

async def getUserById(ctx, userName, server_id = None):
    if server_id is None:
        server_id = ctx.guild.id
    if userName == 'self':
        user = data.getUserById(server_id, ctx.author.id)
    else:
        try:
            identifier = convertToId(userName)
            user = data.getUserById(server_id, identifier)
        except:
            await ctx.send("Please @ a user or enter ID.")
            return None
    return user

def updateStamina(user):
    if (datetime.today().date() > user.date):
        if "elite4" in user.flags:
            if user.dailyProgress < 15:
                user.dailyProgress = 15
        else:
            if user.dailyProgress < 10:
                user.dailyProgress = 10
        user.date = datetime.today().date()

def createPokemonDexEmbed(ctx, pokemon, shiny=False, distortion=False):
    pokemon.shiny = False
    pokemon.distortion = False
    if shiny:
        pokemon.shiny = True
    if distortion:
        pokemon.shiny = True
        pokemon.distortion = True
    pokemon.setSpritePath()
    pokeData = pokemon.getFullData()
    firstEntry = ''
    if 'pokedex_entries' in pokeData:
        entries = pokeData['pokedex_entries']
        try:
            firstEntry = list(list(entries.values())[0].values())[0]
        except:
            pass
    if firstEntry:
        firstEntry = "PokeDex Entry: \n" + firstEntry
    dexString = "#" + str(pokemon.getFullData()['national_id'])
    files = []
    title = ''
    title = dexString + ": " + pokemon.name

    typeString = ''
    for pokeType in pokemon.getType():
        if typeString:
            typeString = typeString + ", "
        typeString = typeString + pokeType
    typeString = "\n\nType: \n" + typeString

    forms = []
    formString = ''
    formList = pokemon.getFullData()['variations']
    count = 1
    for formObj in formList:
        formName = formObj['names']['en']
        forms.append("(" + str(count) + ") " + formName)
        count += 1
    if forms:
        formString = '\n\nForms: \n' + ', '.join(forms)

    evolutionString = ''
    if "evolutions" in pokemon.getFullData():
        for evolution in pokemon.getFullData()['evolutions']:
            to = evolution['to']
            level = str(evolution['level'])
            if evolutionString:
                evolutionString += "\n"
            evolutionString += to + " at level " + level
    if evolutionString:
        evolutionString = '\n\nEvolutions: \n' + evolutionString

    evolvesFromString = ''
    try:
        evolvesFrom = pokemon.getFullData()['evolution_from']
        if evolvesFrom:
            evolvesFromString = evolvesFrom
    except:
        pass
    if evolvesFromString:
        evolvesFromString = '\n\nEvolves from: \n' + evolvesFromString

    locationString = ""
    locationList = []
    regionList = ['hoenn', 'event']
    fishTagRequired = False
    for region in regionList:
        for location in data.regionDict[region]["locations"]:
            for locationPokemon in location['pokemon']:
                name = locationPokemon['pokemon']
                encounterType = locationPokemon['location']
                games = locationPokemon['games']
                if 'Emerald' in games and (encounterType == "Walking" or encounterType == "Surfing" or " Rod" in encounterType) and name == pokemon.name:
                    if location["names"]["en"] not in locationList and (location["names"]["en"] + "*") not in locationList:
                        if encounterType == "Surfing" or " Rod" in encounterType:
                            locationList.append(location["names"]["en"] + "*")
                            fishTagRequired = True
                        else:
                            if region == 'event':
                                locationList.append(location["names"]["en"] + " (event)")
                            else:
                                locationList.append(location["names"]["en"])
    if locationList:
        locationString += "\n\nLocation:\n" + ', '.join(locationList)
    else:
        locationString = "\n\nLocation:\nUnknown"
    if fishTagRequired:
        locationString += "\n* = surf required"

    classificationString = "\n\nClassification:\n" + str(pokemon.getFullData()['categories']['en'])
    heightString = "\n\nHeight:\n" + str(pokemon.getFullData()['height_eu'])
    weightString = "\n\nWeight:\n" + str(pokemon.getFullData()['weight_eu'])
    catchrateString = "\n\nCatch Rate: (ranges 3 to 255)\n" + str(pokemon.getFullData()['catch_rate'])
    embed = discord.Embed(title=title,
                          description="```" + firstEntry + classificationString + locationString + heightString + weightString + typeString + formString + evolutionString + evolvesFromString + catchrateString + "```",
                          color=0x00ff00)
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.add_field(name="----Base Stats----", value=("```" + "HP:     " + str(pokemon.baseHP) + "\nATK:    " + str(pokemon.baseAtk) + "\nDEF:    " + str(pokemon.baseDef) + "\nSP ATK: " + str(pokemon.baseSpAtk) + "\nSP DEF: " + str(pokemon.baseSpDef) + "\nSPD:    " + str(pokemon.baseSpd) + "```"), inline=True)
    count = 0
    #embed.add_field(name='\u200b', value = '\u200b')
    return files, embed

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
    # dexString = "Dex #: " + str(pokemon.getFullData()['hoenn_id'])
    natureString = "Nature: " + pokemon.nature.capitalize()
    happinessString = "Happiness: " + str(pokemon.happiness)
    formString = ''
    if pokemon.getFormName():
        formString = "\nForm: " + pokemon.getFormName()
    caughtIn = "pokeball"
    if pokemon.caughtIn:
        caughtIn = pokemon.caughtIn.lower()
    statusText = ''
    for status in pokemon.statusList:
        statusText = statusText + data.getStatusEmoji(status)
    if not statusText:
        statusText = "None"
    caughtInString = "Caught in: " + data.getEmoji(caughtIn)
    embed = discord.Embed(title=title,
                          description="```Type: " + typeString + "\n" + hpString + "\n" + levelString + "\n" + natureString + "\n" + happinessString + "\n" + genderString + "\n" + otString + formString + "\n" + caughtInString + "```" + '\n**---Status---**\n' + statusText + '\n\n**---EXP---**\n' + ("```" + "Total: " + str(pokemon.exp) + "\nTo next level: " + str(pokemon.calculateExpToNextLevel()) + "```"),
                          color=0x00ff00)
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
    #embed.add_field(name='---Level---', value=str(pokemon.level), inline=True)
    #embed.add_field(name='-----OT-----', value=pokemon.OT, inline=True)
    #embed.add_field(name='---Dex Num---', value=pokemon.getFullData()['hoenn_id'], inline=True)
    #embed.add_field(name='---Nature---', value=pokemon.nature.capitalize(), inline=True)
    # embed.add_field(name='---Status---', value=statusText, inline=True)
    # embed.add_field(name='---EXP---', value=("```" + "Total: " + str(pokemon.exp) + "\nTo next level: " + str(pokemon.calculateExpToNextLevel()) + "```"), inline=True)
    embed.add_field(name="----Stats----", value=("```" + "HP:     " + str(pokemon.hp) + "\nATK:    " + str(pokemon.attack) + "\nDEF:    " + str(pokemon.defense) + "\nSP ATK: " + str(pokemon.special_attack) + "\nSP DEF: " + str(pokemon.special_defense) + "\nSPD:    " + str(pokemon.speed) + "```"), inline=True)
    embed.add_field(name="-----IV's-----", value=("```" + "HP:     " + str(pokemon.hpIV) + "\nATK:    " + str(pokemon.atkIV) + "\nDEF:    " + str(pokemon.defIV) + "\nSP ATK: " + str(pokemon.spAtkIV) + "\nSP DEF: " + str(pokemon.spDefIV) + "\nSPD:    " + str(pokemon.spdIV) + "```"), inline=True)
    embed.add_field(name="-----EV's-----", value=("```" + "HP:     " + str(pokemon.hpEV) + "\nATK:    " + str(pokemon.atkEV) + "\nDEF:    " + str(pokemon.defEV) + "\nSP ATK: " + str(pokemon.spAtkEV) + "\nSP DEF: " + str(pokemon.spDefEV) + "\nSPD:    " + str(pokemon.spdEV) + "```"), inline=True)
    count = 0
    for move in pokemon.moves:
        physicalSpecialText = ''
        bp = '\nPow:  '
        acc = '\nAcc:  '
        # if (move['category'].lower() == 'physical'):
        #     physicalSpecialEmoji = data.getEmoji('physical')
        #     bp = bp + str(move['power'])
        #     acc = acc + str(move['accuracy'])
        # elif (move['category'].lower() == 'special'):
        #     physicalSpecialEmoji = data.getEmoji('special')
        #     bp = bp + str(move['power'])
        #     acc = acc + str(move['accuracy'])
        # else:
        #     physicalSpecialEmoji = data.getEmoji('no damage')
        tempPower = move['power']
        if tempPower == 0:
            bp = bp + "N/A"
        else:
            bp = bp + str(move['power'])
        tempAcc = move['accuracy']
        if tempAcc == 0:
            tempAcc = 100
        acc = acc + str(tempAcc)
        # if (bp == '\nPower: 0' or bp == '\nPower: '):
        #         bp = ''
        if count+1 == 3:
            embed.add_field(name='\u200b', value='\u200b')
        embed.add_field(name=('-----Move ' + str(count+1) + '-----'), value=("```" + "Name: " + move['names']['en'] + "\nCat:  " + move['category'].capitalize() + "\nType: " + move['type'] + " " + bp + acc + "\nPP:   " + str(pokemon.pp[count]) + "/" + str(move['pp']) + " pp" + "```"), inline=True)
        count += 1
    embed.add_field(name='\u200b', value = '\u200b')
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
        embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")" + shinyString, value=embedValue, inline=False)
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
                if item not in ballItems and item not in healthItems and item not in statusItems and item != "money" and item != "BP" and "Badge" not in item:
                    items.append(item)
    for item in items:
        if (battle is not None):
            if (item in battle.trainer1.itemList.keys() and battle.trainer1.itemList[item] > 0):
                trainerItems.append(item)
        elif (trainer is not None):
            if (item in trainer.itemList.keys() and trainer.itemList[item] > 0):
                trainerItems.append(item)
    return trainerItems

def createTrainerCard(trainer):
    numberOfBadges = 0
    backgroundPath = 'data/sprites/trainerCard.png'
    backgroundPathBack = 'data/sprites/trainerCardBack.png'
    pokemonPathDict = {}
    for index in range(0, 6):
        if len(trainer.partyPokemon) > index:
            pokemonPathDict[index+1] = (trainer.partyPokemon[index].getSpritePath(), trainer.partyPokemon[index].level)
    background = Image.open(backgroundPath)
    backgroundBack = Image.open(backgroundPathBack)
    background = background.convert('RGBA')
    backgroundBack = backgroundBack.convert('RGBA')
    trainerSpritePath = 'data/sprites/trainers/' + trainer.sprite
    trainerSprite = Image.open(trainerSpritePath)
    badgePath = "data/sprites/badges/badge"
    elite4Image = Image.open("data/sprites/badges/" + 'gold_star.png')
    badgeImage1 = Image.open(badgePath + '1.png')
    badgeImage2 = Image.open(badgePath + '2.png')
    badgeImage3 = Image.open(badgePath + '3.png')
    badgeImage4 = Image.open(badgePath + '4.png')
    badgeImage5 = Image.open(badgePath + '5.png')
    badgeImage6 = Image.open(badgePath + '6.png')
    badgeImage7 = Image.open(badgePath + '7.png')
    badgeImage8 = Image.open(badgePath + '8.png')
    background.paste(trainerSprite, (10, 80), trainerSprite.convert('RGBA'))
    fnt = ImageFont.truetype('data/fonts/pokemonGB.ttf', 10)
    d = ImageDraw.Draw(background)
    if len(pokemonPathDict.keys()) >= 1:
        image1 = Image.open(pokemonPathDict[1][0])
        background.paste(image1, (180, 65), image1.convert('RGBA'))
        level = pokemonPathDict[1][1]
        if level == 100:
            x = 252
        elif level >= 10:
            x = 262
        else:
            x = 272
        d.text((x, 75), str(level), font=fnt, fill=(255, 255, 255))
    if len(pokemonPathDict.keys()) >= 2:
        image2 = Image.open(pokemonPathDict[2][0])
        background.paste(image2, (305, 65), image2.convert('RGBA'))
        level = pokemonPathDict[2][1]
        if level == 100:
            x = 377
        elif level >= 10:
            x = 387
        else:
            x = 397
        d.text((x, 75), str(level), font=fnt, fill=(255, 255, 255))
    if len(pokemonPathDict.keys()) >= 3:
        image3 = Image.open(pokemonPathDict[3][0])
        background.paste(image3, (430, 65), image3.convert('RGBA'))
        level = pokemonPathDict[3][1]
        if level == 100:
            x = 502
        elif level >= 10:
            x = 512
        else:
            x = 522
        d.text((x, 75), str(level), font=fnt, fill=(255, 255, 255))
    if len(pokemonPathDict.keys()) >= 4:
        image4 = Image.open(pokemonPathDict[4][0])
        background.paste(image4, (180, 150), image4.convert('RGBA'))
        level = pokemonPathDict[4][1]
        if level == 100:
            x = 252
        elif level >= 10:
            x = 262
        else:
            x = 272
        d.text((x, 160), str(level), font=fnt, fill=(255, 255, 255))
    if len(pokemonPathDict.keys()) >= 5:
        image5 = Image.open(pokemonPathDict[5][0])
        background.paste(image5, (305, 150), image5.convert('RGBA'))
        level = pokemonPathDict[5][1]
        if level == 100:
            x = 377
        elif level >= 10:
            x = 387
        else:
            x = 397
        d.text((x, 160), str(level), font=fnt, fill=(255, 255, 255))
    if len(pokemonPathDict.keys()) >= 6:
        image6 = Image.open(pokemonPathDict[6][0])
        background.paste(image6, (430, 150), image6.convert('RGBA'))
        level = pokemonPathDict[6][1]
        if level == 100:
            x = 502
        elif level >= 10:
            x = 512
        else:
            x = 522
        d.text((x, 160), str(level), font=fnt, fill=(255, 255, 255))
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
    if 'elite4' in trainer.flags:
        background.paste(elite4Image, (15, 75), elite4Image.convert('RGBA'))
    d.text((310, 40), trainer.name, font=fnt, fill=(0, 0, 0))
    d_back = ImageDraw.Draw(backgroundBack)
    d_back.text((310, 40), trainer.name, font=fnt, fill=(0, 0, 0))
    fnt = ImageFont.truetype('data/fonts/pokemonGB.ttf', 12)
    d_back.text((20, 100), getProfileDescStr(trainer), font=fnt,
                fill=(255, 255, 255))
    # comboPath = 'data/sprites/trainerCardComboBackground2.png'
    # combo = Image.open(comboPath)
    # combo = combo.convert('RGBA')
    # combo.paste(background, (0,0))
    # combo.paste(backgroundBack, (550, 0))
    # combo.paste(backgroundBack, (0, 353))
    temp_uuid = uuid.uuid4()
    filename = "data/temp/trainerCardNew" + str(temp_uuid) + ".png"
    fileNameBack = "data/temp/trainerCardNewBack" + str(temp_uuid) + ".png"
    background.save(filename, "PNG")
    backgroundBack.save(fileNameBack, "PNG")
    return filename, fileNameBack

async def resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining, goToSecretBase):
    embed = newEmbed
    if (reloadArea):
        await safeDeleteMessgae(message)
        await startOverworldUI(ctx, trainer)
    elif (goToBox):
        await safeDeleteMessgae(message)
        await startBoxUI(ctx, trainer, 0, 'startOverworldUI', dataTuple)
    elif (goToBag):
        await safeDeleteMessgae(message)
        await startBagUI(ctx, trainer, 'startOverworldUI', dataTuple)
    elif (goToMart):
        await safeDeleteMessgae(message)
        await startMartUI(ctx, trainer, 'startOverworldUI', dataTuple)
    elif (goToParty):
        await safeDeleteMessgae(message)
        await startPartyUI(ctx, trainer, 'startOverworldUI', None, dataTuple)
    elif (goToTMMoveTutor):
        await safeDeleteMessgae(message)
        await startMoveTutorUI(ctx, trainer, 0, True, 0, 'startOverworldUI', dataTuple)
    elif (goToLevelMoveTutor):
        await safeDeleteMessgae(message)
        await startMoveTutorUI(ctx, trainer, 0, False, 0, 'startOverworldUI', dataTuple)
    elif (goToSuperTraining):
        await safeDeleteMessgae(message)
        await startSuperTrainingUI(ctx, trainer)
    elif (battle is not None):
        battle.startBattle(trainer.location)
        await safeDeleteMessgae(message)
        if not battle.isWildEncounter:
            await startBeforeTrainerBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
        else:
            battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                  startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
            await battle_ui.startBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
    elif (goToBattleTower):
        await safeDeleteMessgae(message)
        await startBattleTowerSelectionUI(ctx, trainer, withRestrictions)
    elif goToSecretBase:
        await safeDeleteMessgae(message)
        await secretBaseUi.startSecretBaseUI(ctx, trainer)

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
    goToSecretBase = True
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
            # trainer.progress(trainer.location) # HERE
            currentProgress = trainer.checkProgress(trainer.location)
            locationDataObj = data.getLocation(trainer.location)
            event = locationDataObj.getEventForProgress(currentProgress+1)
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
    elif (command[0] == "secretBase"):
        goToSecretBase = True
    elif (command[0] == "legendaryPortal"):
        if trainer.dailyProgress > 0 or not data.staminaDict[str(ctx.message.guild.id)]:
            if (data.staminaDict[str(ctx.message.guild.id)]):
                trainer.dailyProgress -= 1
            pokemonName = data.getLegendaryPortalPokemon()
            legendaryPokemon = data.shinyCharmCheck(trainer, Pokemon(data, pokemonName, 70))
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
    return embed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining, goToSecretBase

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
    if locationObj.secretBaseType and trainer.secretBase:
        if trainer.secretBase.location == locationObj.name:
            optionsText = optionsText + "(" + str(count) + ") Enter Secret base\n"
            overWorldCommands[count] = ('secretBase',)
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
             'Southern Island', 'Faraway Island', 'Birth Island', 'Naval Rock 1', 'Naval Rock 2', 'Lake Verity Cavern', "Agate Village Shrine"]
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

def createShopEmbed(ctx, trainer, categoryList=None, category='', itemList=None, isFurniture=False):
    files = []
    furnitureAddition = ''
    if isFurniture:
        furnitureAddition = '\n- To preview furniture, use `!preview [item name]`.'
    if category:
        category = ' - ' + category.title()
    embed = discord.Embed(title="Premium PokeMart" + category, description="- To view a category, use `!shop [category]`.\n- To make a purchase, use `!buy [amount] [item name]`." + furnitureAddition, color=0x00ff00)
    file = discord.File("data/sprites/locations/pokemart.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    if categoryList:
        for category in categoryList:
            embed.add_field(name=category.title(), value='`!shop ' + category + '`', inline=False)
    if itemList:
        for item in itemList:
            prefix = 'Cost: '
            suffix = ' ' + item.currency
            embed.add_field(name=item.itemName, value=prefix + str(item.price) + suffix, inline=False)
    # embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')) + "\nBP: " + str(trainer.getItemAmount('BP')))
    embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP')))
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
    embed = discord.Embed(title="Welcome " + trainer.name + " to the world of Pokemon!", description="[type the name of the desired start into the chat to choose!]", color=0x00ff00)
    file = discord.File("data/sprites/starters.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    # count = 1
    for pokemon in starterList:
        shinyText = '\u200b'
        if (pokemon.shiny):
            shinyText = ' :star2:'
        embed.add_field(name=pokemon.name + shinyText, value='\u200b', inline=True)
        # count += 1
    embed.set_author(name=ctx.message.author.display_name + " is choosing a starter:")
    return files, embed

def createProfileEmbed(ctx, trainer):
    descString = getProfileDescStr(trainer)
    descString = descString + "\n\n**Party:**"
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

def getProfileDescStr(trainer):
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
    descString = "Badges: " + str(numberOfBadges) + "\n"
    if ('elite4' in trainer.flags):
        descString = descString + "Badges Lv70: " + str(numberOfBadges2)
        descString = descString + "\nBadges Lv100: " + str(numberOfBadges3) + "\n"
        descString = descString + "\nElite 4 Cleared: Yes" + "\n"
        if 'elite4-2' in trainer.flags:
            descString = descString + "Elite 4 Lv70 Cleared: Yes"
        else:
            descString = descString + "Elite 4 Lv70 Cleared: No"
        if 'elite4-3' in trainer.flags:
            descString = descString + "\nElite 4 Lv100 Cleared: Yes" + "\n"
        else:
            descString = descString + "\nElite 4 Lv100 Cleared: No" + "\n"
    else:
        descString = descString + "\nElite 4 Cleared: No" + "\n"
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
        # descString = descString + "\nBattle Tower With Restrictions Current Streak: " + str(trainer.withRestrictionStreak)
        # descString = descString + "\nBattle Tower No Restrictions Current Streak: " + str(trainer.noRestrictionsStreak)
    descString = descString + "\nPVP Win/Loss Ratio: " + str(trainer.getPvpWinLossRatio())
    shinyOwned = 0
    for pokemon in trainer.partyPokemon:
        if pokemon.shiny:
            shinyOwned += 1
    for pokemon in trainer.boxPokemon:
        if pokemon.shiny:
            shinyOwned += 1
    descString = descString + "\nShiny Pokemon Owned: " + str(shinyOwned)
    return descString

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

async def safeAddEmoji(message, emojiName):
    try:
        await message.add_reaction(data.getEmoji(emojiName))
    except:
        pass

async def continueUI(ctx, message, emojiNameList, local_timeout=None, ignoreList=None, isOverworld=False, isPVP=False, isRaid=False):
    if message:
        logging.debug(str(ctx.author.id) + " - continueUI(), message.content = " + message.content)
    else:
        logging.debug(str(ctx.author.id) + " - continueUI(), message = None")
    if local_timeout is None:
        local_timeout = timeout
    return await startNewUI(ctx, None, None, emojiNameList, local_timeout, message, ignoreList, isOverworld, isPVP, isRaid)

async def startNewUI(ctx, embed, files, emojiNameList, local_timeout=None, message=None, ignoreList=None, isOverworld=False, isPVP=False, isRaid=False):
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
        await ctx.send("Our apologies, " + str(ctx.message.author.mention) + ", but PokéNav is currently down for maintenance. Please try again later.")
        return None, None
    # print(embed_title, ' - ', temp_uuid)
    if not ignoreList:
        ignoreList = []
    group = None
    if not message:
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - message is None, creating new message")
        message = await ctx.send(files=files, embed=embed)
        group = gather()
        for emojiName in emojiNameList:
            # await message.add_reaction(data.getEmoji(emojiName))
            group = gather(group, safeAddEmoji(message, emojiName))
    messageID = message.id

    if isOverworld:
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - isOverworld=True, removing old from data.overworldSessions and adding new")
        data.addOverworldSession(ctx, None, message, temp_uuid)

    if not emojiNameList:
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - emojiNameList is None or empty, returning [None, message]")
        return None, message

    def check(payload):
        user_id = payload.user_id
        return user_id == ctx.author.id and messageID == payload.message_id

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
                if not isRaid:
                    if not isPVP:
                        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - timeout")
                        # print('attempting to end session: ', embed_title, ' - ', temp_uuid)
                        if isOverworld:
                            overworldTuple, isGlobal = data.userInOverworldSession(ctx)
                            if overworldTuple:
                                uuidToCompare = overworldTuple[1]
                                if uuidToCompare != temp_uuid:
                                    logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - isOverworld=True and uuid's do not match, returning [None, None]")
                                    return None, None
                            if temp_uuid in data.expiredSessions:
                                logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - isOverworld=True and temp_uuid in data.expiredSessions, returning [None, None]")
                                return None, None
                        # print('ending session: ', embed_title, ' - ', temp_uuid, '\n')
                        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - calling endSession()")
                        await endSession(ctx)
                # print("returning none, none from startNewUI")
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
        logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - returning [" + str(commandNum) + ", message]")
        return commandNum, message

    logging.debug(str(ctx.author.id) + " - uuid = " + str(temp_uuid) + " - calling waitForEmoji()")
    if group:
        a, *b = await gather(waitForEmoji(ctx), group)
        return a
    else:
        return await waitForEmoji(ctx)
    # return await waitForEmoji(ctx)

def convertToId(input):
    if isinstance(input, int):
        id = input
    else:
        id = int(input.replace("<", "").replace("@", "").replace(">", "").replace("!", ""))
    return id

async def fetchUserFromServer(ctx, userName):
    try:
        identifier = convertToId(userName)
        fetched_user = await ctx.guild.fetch_member(identifier)
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
    await raidCheck()
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
            goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining, goToSecretBase = \
                executeWorldCommand(ctx, trainer, overWorldCommands[commandNum], embed)
            if (embedNeedsUpdating):
                await message.edit(embed=newEmbed)
            else:
                overworldTuple, isGlobal = data.userInOverworldSession(ctx)
                if overworldTuple:
                    try:
                        data.removeOverworldSession(ctx)
                    except:
                        pass
                await resolveWorldCommand(ctx, message, trainer,
                                          dataTuple, newEmbed, embedNeedsUpdating,
                                          reloadArea, goToBox, goToBag, goToMart, goToParty, battle,
                                          goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower,
                                          withRestrictions, goToSuperTraining, goToSecretBase)
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

    isPVP = False
    isRaid = False
    tempTimeout = timeout
    if battle:
        isPVP = battle.isPVP
        if isPVP:
            tempTimeout = pvpTimeout
        isRaid = battle.isRaid

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList, tempTimeout, None, None, False, isPVP, isRaid)

    while True:
        if (chosenEmoji == None and message == None):
            if isPVP:
                await ctx.send(
                    str(ctx.author.mention) + ", you have timed out - battle has ended. You lose the battle.")
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                       startNewUI, continueUI, startPartyUI, startOverworldUI,
                                       startBattleTowerUI, startCutsceneUI)
                battle_ui.recordPVPWinLoss(False, trainer, ctx)
                return
            elif isRaid:
                pass
            else:
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
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList, tempTimeout, None, False, isPVP, isRaid)

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

    isPVP = False
    isRaid = False
    tempTimeout = timeout
    if battle:
        isPVP = battle.isPVP
        if isPVP:
            tempTimeout = pvpTimeout
        isRaid = battle.isRaid

    chosenEmoji, message = await startNewUI(ctx, embed, files, emojiNameList, tempTimeout, None, None, False, isPVP, isRaid)

    while True:
        if (chosenEmoji == None and message == None):
            if isPVP:
                await ctx.send(
                    str(ctx.author.mention) + ", you have timed out - battle has ended. You lose the battle.")
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                       startNewUI, continueUI, startPartyUI, startOverworldUI,
                                       startBattleTowerUI, startCutsceneUI)
                battle_ui.recordPVPWinLoss(False, trainer, ctx)
                return
            elif isRaid:
                pass
            else:
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
        chosenEmoji, message = await continueUI(ctx, message, emojiNameList, tempTimeout, None, False, isPVP, isRaid)

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
        key = None
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1' and len(itemDict) >= 1):
            key = list(itemDict.keys())[0]
        elif (chosenEmoji == '2' and len(itemDict) >= 2):
            key = list(itemDict.keys())[1]
        elif (chosenEmoji == '3' and len(itemDict) >= 3):
            key = list(itemDict.keys())[2]
        elif (chosenEmoji == '4' and len(itemDict) >= 4):
            key = list(itemDict.keys())[3]
        elif (chosenEmoji == '5' and len(itemDict) >= 5):
            key = list(itemDict.keys())[4]
        elif (chosenEmoji == '6' and len(itemDict) >= 6):
            key = list(itemDict.keys())[5]
        elif (chosenEmoji == '7' and len(itemDict) >= 7):
            key = list(itemDict.keys())[6]
        elif (chosenEmoji == '8' and len(itemDict) >= 8):
            key = list(itemDict.keys())[7]
        elif (chosenEmoji == '9' and len(itemDict) >= 9):
            key = list(itemDict.keys())[8]
        if key:
            if trainer.location == "Battle Frontier":
                if (trainer.getItemAmount('BP') >= itemDict[key]):
                    trainer.addItem('BP', -1 * itemDict[key])
                    trainer.addItem(key, 1)
                    # print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                    embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                          + "\nBought 1x " + key + " for " + str(itemDict[key]) + " BP.")
                    await message.edit(embed=embed)
            else:
                amount = trainer.storeAmount
                if (trainer.getItemAmount("money") >= itemDict[key] * amount):
                    trainer.addItem("money", -1 * itemDict[key] * amount)
                    trainer.addItem(key, amount)
                    # print("mart: " + trainer.name + "bought " + item + " and now has a total of " + str(trainer.getItemAmount(item)))
                    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount("money"))
                                          + "\nBought " + str(amount) + "x " + key + " for $" + str(itemDict[key] * amount) + ".")
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
    starterNameList = []
    starterList.append(Pokemon(data, "Bulbasaur", 5))
    starterNameList.append('bulbasaur')
    starterList.append(Pokemon(data, "Charmander", 5))
    starterNameList.append('charmander')
    starterList.append(Pokemon(data, "Squirtle", 5))
    starterNameList.append('squirtle')
    starterList.append(Pokemon(data, "Chikorita", 5))
    starterNameList.append('chikorita')
    starterList.append(Pokemon(data, "Cyndaquil", 5))
    starterNameList.append('cyndaquil')
    starterList.append(Pokemon(data, "Totodile", 5))
    starterNameList.append('totodile')
    starterList.append(Pokemon(data, "Treecko", 5))
    starterNameList.append('treecko')
    starterList.append(Pokemon(data, "Torchic", 5))
    starterNameList.append('torchic')
    starterList.append(Pokemon(data, "Mudkip", 5))
    starterNameList.append('mudkip')
    starterList.append(Pokemon(data, "Turtwig", 5))
    starterNameList.append('turtwig')
    starterList.append(Pokemon(data, "Chimchar", 5))
    starterNameList.append('chimchar')
    starterList.append(Pokemon(data, "Piplup", 5))
    starterNameList.append('piplup')
    starterList.append(Pokemon(data, "Snivy", 5))
    starterNameList.append('snivy')
    starterList.append(Pokemon(data, "Tepig", 5))
    starterNameList.append('tepig')
    starterList.append(Pokemon(data, "Oshawott", 5))
    starterNameList.append('oshawott')
    starterList.append(Pokemon(data, "Chespin", 5))
    starterNameList.append('chespin')
    starterList.append(Pokemon(data, "Fennekin", 5))
    starterNameList.append('fennekin')
    starterList.append(Pokemon(data, "Froakie", 5))
    starterNameList.append('froakie')
    starterList.append(Pokemon(data, "Rowlet", 5))
    starterNameList.append('rowlet')
    starterList.append(Pokemon(data, "Litten", 5))
    starterNameList.append('litten')
    starterList.append(Pokemon(data, "Popplio", 5))
    starterNameList.append('popplio')
    starterList.append(Pokemon(data, "Grookey", 5))
    starterNameList.append('grookey')
    starterList.append(Pokemon(data, "Scorbunny", 5))
    starterNameList.append('scorbunny')
    starterList.append(Pokemon(data, "Sobble", 5))
    starterNameList.append('sobble')
    files, embed = createNewUserEmbed(ctx, trainer, starterList)
    emojiNameList = []
    for x in range(1, len(starterList) + 1):
        emojiNameList.append(str(x))

    confirmMessage = await ctx.send(embed=embed, files=files)

    def check(m):
        return (m.content.lower() in starterNameList) \
               and m.author.id == ctx.author.id and m.channel == ctx.channel

    try:
        response = await bot.wait_for('message', timeout=timeout, check=check)
    except asyncio.TimeoutError:
        await endSession(ctx)
    else:
        responseContent = response.content
        if responseContent.lower() in starterNameList:
            desiredPokemon = responseContent.lower()
            chosenPokemon = None
            for pokemon in starterList:
                if pokemon.name.lower() == desiredPokemon:
                    chosenPokemon = pokemon
                    break
            if chosenPokemon:
                await startAdventure(ctx, confirmMessage, trainer, chosenPokemon)
        else:
            await ctx.send(str(ctx.author.display_name) + " has provided an invalid starter choice. Please try again.")

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
        moveListTM = pokemon.getAllTmMoves()
        moveListEgg = pokemon.getAllEggMoves()
        moveList = moveListTM + moveListEgg
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
        index = None

        if (chosenEmoji == '1' and len(moveList) >= 1 + (offset*9)):
            index = 0
        elif (chosenEmoji == '2' and len(moveList) >= 2 + (offset*9)):
            index = 1
        elif (chosenEmoji == '3' and len(moveList) >= 3 + (offset*9)):
            index = 2
        elif (chosenEmoji == '4' and len(moveList) >= 4 + (offset*9)):
            index = 3
        elif (chosenEmoji == '5' and len(moveList) >= 5 + (offset*9)):
            index = 4
        elif (chosenEmoji == '6' and len(moveList) >= 6 + (offset*9)):
            index = 5
        elif (chosenEmoji == '7' and len(moveList) >= 7 + (offset*9)):
            index = 6
        elif (chosenEmoji == '8' and len(moveList) >= 8 + (offset*9)):
            index = 7
        elif (chosenEmoji == '9' and len(moveList) >= 9 + (offset*9)):
            index = 8
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
        if index is not None:
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await message.delete()
                await startLearnNewMoveUI(ctx, trainer, pokemon, moveList[(index) + (offset*9)], 'startMoveTutorUI', dataTuple)
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
                        return
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
                    return
                if confirm:
                    totalEV = hpEV + atkEV + defEV + spAtkEV + spDefEV + spdEV
                    if totalEV > 510:
                        await message.delete()
                        message = await ctx.send("Total combined EV's cannot exceed 510, please try again. " + str(ctx.author.display_name) + "'s training session cancelled. BP refunded.")
                        await returnToOverworldFromSuperTraining(ctx, trainer, message)
                        return
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
                    return
                else:
                    await message.delete()
                    message = await ctx.send(str(ctx.author.display_name) + "'s training session cancelled. BP refunded.")
                    await returnToOverworldFromSuperTraining(ctx, trainer, message)
                    return
            else:
                message = await ctx.send("No Pokemon in that party slot.")
                await returnToOverworldFromSuperTraining(ctx, trainer, message)
                return
        await ctx.send("Sorry " + ctx.message.author.display_name + ", but you need at least " + str(bpCost) + " BP to train a Pokemon.")

async def returnToOverworldFromSuperTraining(ctx, trainer, message=None):
    await sleep(6)
    if message is not None:
        try:
            await message.delete()
        except:
            pass
    await startOverworldUI(ctx, trainer)

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

def clearTempFolder():
    folder = 'data/temp/'
    for filename in os.listdir(folder):
        try:
            os.remove(folder + filename)
        except:
            pass

async def saveLoop():
    global allowSave
    global saveLoopActive
    logging.debug("saveLoop()")
    if saveLoopActive:
        try:
            channel = bot.get_channel(errorChannel1)
            logging.debug("Save loop tried to enable but save loop is already active.")
            await channel.send("Save loop tried to enable but save loop is already active.")
        except:
            pass
        return
    saveLoopActive = True
    await sleep(timeBetweenSaves)
    try:
        channel = bot.get_channel(errorChannel1)
        logging.debug("Save loop enabled successfully.")
        await channel.send("Save loop enabled successfully.")
    except:
        pass
    while allowSave:
        try:
            uniqueUsers = []
            for server_id, userList in data.userDict.items():
                for user in userList:
                    if user.identifier not in uniqueUsers:
                        uniqueUsers.append(user.identifier)
            numUniqueUsers = str(len(uniqueUsers))
            await bot.change_presence(activity=discord.Game(name="on " + str(len(bot.guilds)) + " servers with " + numUniqueUsers + " trainers! | !help"))
        except:
            pass
        try:
            logging.debug("Saved.")
            data.writeUsersToJSON()
        except:
            logging.error("Saving failed.\n" + str(traceback.format_exc()))
            try:
                channel = bot.get_channel(errorChannel1)
                await channel.send(("Saving failed.\n" + str(traceback.format_exc()))[-1999:])
            except:
                pass
        await sleep(timeBetweenSaves)
    logging.debug("Save loop disabled successfully.")
    try:
        channel = bot.get_channel(errorChannel1)
        await channel.send("Save loop disabled successfully.")
    except:
        pass
    saveLoopActive = False

pokeDiscordLogger = logging.getLogger()
pokeDiscordLogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='pokeDiscord_log.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s'))
pokeDiscordLogger.addHandler(handler)
discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.ERROR)
imageLogger = logging.getLogger('PIL.PngImagePlugin')
imageLogger.setLevel(logging.ERROR)
clearTempFolder()
timeout = 600
battleTimeout = 900
pvpTimeout = 120
# timeout = 15
# battleTimeout = 15
# pvpTimeout = 15
allowSave = True
saveLoopActive = False
raidsEnabled = True
timeBetweenSaves = 60
errorChannel1 = 831720385878818837
errorChannel2 = 804463066241957981
botId = 800207357622878229
data = pokeData()
data.setBot(bot)
data.readUsersFromJSON()
battleTower = Battle_Tower(data)
secretBaseUi = Secret_Base_UI(bot, timeout, data, startNewUI, continueUI, startOverworldUI, endSession)
bannedFlyAreas = ['Elite 4 Room 1', 'Elite 4 Room 2', 'Elite 4 Room 3', 'Elite 4 Room 4', 'Champion Room',
                           'Elite 4 Room 1 Lv70', 'Elite 4 Room 2 Lv70', 'Elite 4 Room 3 Lv70', 'Elite 4 Room 4 Lv70',
                           'Champion Room Lv70',
                           'Elite 4 Room 1 Lv100', 'Elite 4 Room 2 Lv100', 'Elite 4 Room 3 Lv100',
                           'Elite 4 Room 4 Lv100', 'Champion Room Lv100',
                           "Colosseum Event", "Agate Village Shrine",
                           "Dance Party In Orre Event", "PokeSpot",
                           "Rainbow Mirage Island", "Galarian Lab"]
bot.run(TOKEN)
