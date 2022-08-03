import disnake as discord
import requests
from disnake import OptionType, MessageInteraction
from disnake.ext import commands
from disnake.ext.commands.slash_core import Option
from dotenv import load_dotenv
import os
import asyncio

import Game_Corner
import PokeNavComponents
import Quests
import Trade
import TrainerIcons
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
TOPGG_TOKEN = os.getenv('TOPGG_TOKEN')
bot = commands.Bot(command_prefix='!',
                   sync_permissions=True,
                   reconnect=True)  # , test_guilds=[303282588901179394, 805976403140542476, 804463066241957978])
bot.remove_command('help')


@bot.event
async def on_ready():
    try:
        channel = bot.get_channel(errorChannel1)
        await channel.send('NOTICE: PokéNav is online and ready for use.')
    except:
        pass
    # print("PokéNav is online and ready for use.")
    logging.debug("PokéNav is online and ready for use.")
    await saveLoop()


@bot.command(name='start', help='starts the game', aliases=['s', 'begin'])
async def old_start(ctx):
    newline = "\n\n"
    embed = discord.Embed(title="PokéNav - Migrating to Slash Commands",
                          description="Hello " + ctx.author.display_name + "," + newline +
                                      "Professor Birch here! Let's get you the help you need!" + newline +
                                      "At the end of April, Discord is making slash commands mandatory for all bots.\nFor example, you will now use `/start` to begin." + newline +
                                      "To continue enjoying this bot, please re-authorize the bot with the link below so it can use slash commands:" + newline +
                                      "[✅ Re-authorize PokéNav here! ✅](https://discord.com/api/oauth2/authorize?client_id=800207357622878229&permissions=137439275072&scope=applications.commands%20bot)" + newline,
                          # "[✅ Re-authorize PokéNav here! ✅](https://discord.com/api/oauth2/authorize?client_id=944317982274899969&permissions=137439275072&scope=bot%20applications.commands)" + newline,
                          color=0x00ff00)
    await ctx.send(embed=embed)


@bot.slash_command(name='start', description='starts the game')
async def startGame(inter):
    global allowSave
    logging.debug(str(inter.author.id) + " - /start - in server: " + str(inter.guild.id))
    await inter.send("Session starting...")
    message = await inter.original_message()
    await message.delete()
    if not allowSave:
        logging.debug(str(inter.author.id) + " - not starting session, bot is down for maintenance")
        await inter.send("Our apologies, but PokéNav is currently down for maintenance. Please try again later.")
        return
    user, isNewUser = data.getUser(inter)
    try:
        if user.current_trade_id != 0:
            logging.debug(str(inter.author.id) + " - not starting session, user is waiting for a trade")
            await inter.send(
                "You are waiting for a trade, please finish the trade, wait for it to timeout, or cancel it before starting a session.",
                ephemeral=True)
            return
        if user.closed:
            logging.debug(str(inter.author.id) + " - not starting session, user account is closed")
            await inter.send(
                "This account has been closed. Please use the community server for help.",
                ephemeral=True)
            return
        sessionSuccess = data.addUserSession(inter.guild.id, user)
        updateStamina(user)
        # print('sessionSuccess = ', sessionSuccess)
        if (sessionSuccess):
            data.updateRecentActivityDict(inter, user)
            await eventCheck(inter, user)
            if (isNewUser or (len(user.partyPokemon) == 0 and len(user.boxPokemon) == 0)):
                logging.debug(str(inter.author.id) + " - is new user, picking starter Pokemon UI starting")
                await startNewUserUI(inter, user)
            else:
                logging.debug(str(inter.author.id) + " - is returning user, starting overworld UI")
                await startOverworldUI(inter, user)
        else:
            logging.debug(
                str(inter.author.id) + " - session failed to start, reason unknown but likely already has active session")
            # print('Unable to start session for: ' + str(inter.author.display_name))
            await inter.send('Unable to start session for: ' + str(
                inter.author.display_name) + '. If you already have an active session, please end it before starting another one.')
    except discord.errors.Forbidden:
        await forbiddenErrorHandle(inter)
    except:
        await sessionErrorHandle(inter, user, traceback)


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


async def forbiddenErrorHandle(inter):
    logging.error(str(inter.author.id) + " - session ended in discord.errors.Forbidden error.\n" + str(
        traceback.format_exc()) + "\n")
    logging.error(str(inter.author.id) + " - calling endSession() due to error")
    # traceback.print_exc()
    try:
        await endSession(inter)
    except:
        pass
    forbiddenMessage = "Hello! Professor Birch here! It appears you revoked some required bot permissions that are required for PokéNav to function! The bot will not work without these."
    try:
        await inter.channel.send(forbiddenMessage)
    except:
        channel = await inter.author.create_dm()
        await channel.send(forbiddenMessage)
    disregardStr = "Error for '" + str(inter.author.id) + "' was due to missing permissions. You can safely disregard."
    logging.error(str(inter.author.id) + " - " + disregardStr)
    # await sendDiscordErrorMessage(inter, traceback, disregardStr)


async def sessionErrorHandle(inter, user, traceback):
    logging.error(str(inter.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()) + "\n")
    logging.error(str(inter.author.id) + " - calling endSession() due to error")
    removedSuccessfully = await endSession(inter)
    logging.error(str(inter.author.id) + " - endSession() complete, removedSuccessfully = " + str(removedSuccessfully))
    #traceback.print_exc()
    # user.dailyProgress += 1
    # user.removeProgress(user.location)
    logging.error(str(inter.author.id) + " - sending error message for traceback")
    await sendDiscordErrorMessage(inter, traceback)


async def sendDiscordErrorMessage(inter, traceback, message=None):
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
                await inter.channel.send(exceptMessage)
    else:
        tracebackMessage = str(
            str(inter.author.id) + "'s session ended in error.\n" + str(traceback.format_exc()))[-1999:]
        try:
            channel = bot.get_channel(errorChannel1)
            await channel.send(tracebackMessage)
        except:
            try:
                channel = bot.get_channel(errorChannel2)
                await channel.send(tracebackMessage)
            except:
                # print('e1-trace')
                await inter.channel.send(exceptMessage)


@bot.slash_command(name='help', description='DM you with a help message.')
async def help(inter):
    await inter.send(str(inter.author.mention) + ", Professor Birch will assist you in your Direct Messages.")
    files = []
    newline = "\n\n"
    halfNewline = "\n"
    embed = discord.Embed(title="PokéNav - Help", description="Hello " + inter.author.display_name + "," + newline +
                                                              "Professor Birch here! Let's get you the help you need!" + newline +
                                                              "For a full information guide, please see our website:\n[PokéNav website](https://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md)" + newline +
                                                              "If you need support, please join our official PokéNav server!\n[PokéNav official server](https://discord.gg/HwYME4Vwj9)" + newline +
                                                              "[🗳️Vote for PokéNav here!🗳️](https://top.gg/bot/800207357622878229/vote)" + newline +
                                                              "Otherwise, here is a list of commands, although all you need to begin using the bot is `/start`.",
                          color=0x00ff00)
    embed.set_footer(text="------------------------------------\nZetaroid#1391 - PokéNav Developer")
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------Main Commands--------------", value=
    "`/start` - begin your adventure, use this each time you want to start a new session" + halfNewline +
    "`/fly <location>` - after obtaining 6th badge, use to fly to any visited location" + halfNewline +
    "`/end_session` - while in the overworld, will end your current session" + halfNewline +
    "`/guide` - tells you where to go next" + halfNewline +
    "`/map` - shows a visual map of the Hoenn region" + halfNewline +
    "`/vote` - vote for the bot on top.gg" + halfNewline +
    "`/game_corner` - visit the iconic Mauville Game Corner to win prizes"
                    , inline=False)
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------Party Management--------------", value=
    "`/nickname <party number> <name>` - nickname a Pokemon" + halfNewline +
    "`/swap_moves <party number> <moveSlot1> <moveSlot2>` - swap 2 moves" + halfNewline +
    "`/evolve <party number> [optional: Pokemon to evolve into]` - evolves a Pokemon capable of evolution" + halfNewline +
    "`/unevolve <party number>` - unevolves a Pokemon with a pre-evolution" + halfNewline +
    "`/release <party number>` - release a Pokemon from your party" + halfNewline +
    "`/change_form <party number> [optional: form number from /dex command]` - toggle a Pokemon's form" + halfNewline +
    "`/move_info <move name>` - get information about a move" + halfNewline +
    "`/dex <Pokemon name>` - view a Pokemon's dex entry, add 'shiny' or 'distortion' to end of command to view those sprites, see /guide for examples" + halfNewline +
    "`/create_team <team number between 1 and 10> [optional: team name]` - create new preset team from current party" + halfNewline +
    "`/set_team <team number or name>` - replace party with preset team" + halfNewline +
    "`/teams` - view all preset teams" + halfNewline +
    "`/delete_team <team number>` - delete a team" + halfNewline +
    "`/rename_team <team number>` - rename a team" + halfNewline +
    "`/super_train` - at the cost of 20BP, train a Pokemon"
                    , inline=False)
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------Player Management--------------", value=
    "`/profile [@user]` - get a trainer's profile" + halfNewline +
    "`/trainer_card [@user]` - get a trainer's card" + halfNewline +
    "`/quests` - view your quest inventory" + halfNewline +
    "`/enable_global_save` - sets the save file from the server you are currently in as your save for ALL servers (will not delete other saves)" + halfNewline +
    "`/disable_global_save` - disables global save for you, all servers will have separate save files" + halfNewline +
    "`/reset_save` - permanently reset your save file on a server" + halfNewline +
    "`/set_sprite <gender>` - sets player trainer card sprite (options: male, female, default)" + halfNewline +
    "`/set_altering_cave <pokemon name>` - trade 10 BP to set the Pokemon in Altering Cave (BP earned at Battle Tower in post-game)" + halfNewline +
    "`/secret_power` - create a secret base in the overworld" + halfNewline +
    "`/delete_base` - delete your current secret base" + halfNewline +
    "`/shop [category]` - opens the BP shop (League Champions only)" + halfNewline +
    "`/buy <item> <amount>` - buy an item from the BP shop (League Champions only)"
                    , inline=False)
    embed.add_field(name='\u200b', value='\u200b')
    embed.add_field(name="--------------PVP / Trading--------------", value=
    "`/trade <@user>` - trade with another user" + halfNewline +
    "`/battle <@user>` - battle another user on the server" + halfNewline +
    "`/battle_copy <@user>` - battle an NPC copy of another user on the server" + halfNewline +
    "`/raid` - join an active raid if one exists" + halfNewline +
    "`/raid_info` - display status of current raid" + halfNewline +
    "`/event` - view active event" + halfNewline +
    "`/view_base <@user>` - view a user's secret base"
                    , inline=False)
    embed.add_field(name='\u200b', value="Cheers,\nProfessor Birch")
    if str(inter.author) == 'Zetaroid#1391':
        embed.add_field(name='------------------------------------\nDev Commands:',
                        value="Oh hello there!\nI see you are a dev! Here are some extra commands for you (prefixed by `zzz_`):" + newline +
                              "`/grant_flag <flag> [userName] [server_id]` - grants flag to user" + halfNewline +
                              "`/remove_flag <flag> [userName=self] [server_id]` - removes flag from user" + halfNewline +
                              "`/save [flag=disable]` - disable save and manually save" + halfNewline +
                              "`/save_status` - view status of save variables" + halfNewline +
                              "`/test` - test things" + halfNewline +
                              "`/verify_champion [userName]` - verify elite 4 victory for user" + halfNewline +
                              "`/display_session_list` - display full active session list" + halfNewline +
                              "`/display_guild_list` - display full guild list" + halfNewline +
                              "`/display_overworld_list` - display full overworld session list" + halfNewline +
                              "`/force_end_session [user id num]` - remove user id from active session list" + halfNewline +
                              "`/leave [targetServer]` - leave the target server" + halfNewline +
                              "`/view_flags [userName=self] [server_id]` - views user flags (use '_' for spaces in flag name)"
                        ,
                        inline=False)
        # embed.add_field(name='\u200b',
        embed.add_field(name='Dev Commands 2:',
                        value="`/grant_item <item> <amount> [@user]` - grants a specified item in amount to user (replace space in item name with '\_')" + halfNewline +
                              "`/remove_item <item> <amount> [@user]` - removes a specified item in amount to user (replace space in item name with '\_')" + halfNewline +
                              "`/grant_pokemon [pokemon] [level] [shiny] [distortion] [@user]` - grant a Pokemon (replace space in name with '\_')" + halfNewline +
                              "`/start_raid` - starts a raid" + halfNewline +
                              "`/end_raid` - ends a raid" + halfNewline +
                              "`/clear_raid_list` - clears raid list" + halfNewline +
                              "`/view_raid_list` - views raid list" + halfNewline +
                              "`/raid_enable <true/false>` - enable/disable raids" + halfNewline +
                              "`/recent_users` - displays # of recent users" + halfNewline +
                              "`/event_list` - view all events" + halfNewline +
                              "`/start_event <name or number>` - start an event" + halfNewline +
                              "`/end_event` - ends current event" + halfNewline +
                              "`/check_author <author id> [server id]` - view user info"
                        ,
                        inline=False)
    thumbnailImage = discord.File("logo.png", filename="thumb.png")
    files.append(thumbnailImage)
    embed.set_thumbnail(url="attachment://thumb.png")
    channel = await inter.author.create_dm()
    await channel.send(embed=embed, files=files)


@bot.slash_command(name='invite', description='get an invite link to add the bot to your own server')
async def inviteCommand(inter):
    logging.debug(str(inter.author.id) + " - /invite")
    embed = discord.Embed(title="PokéNav wants to join your party!",
                          description="Click [HERE](https://discord.com/api/oauth2/authorize?client_id=800207357622878229&permissions=137439275072&scope=applications.commands%20bot) to invite the bot!\n\nYour save file from this server will be used as default for all servers. If you want a separate save file per server, use `!disableGlobalSave`.",
                          color=0x00ff00)
    file = discord.File("logo.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    await inter.send(embed=embed, file=file)


@bot.slash_command(name='reset_save', description='resets save file, this will wipe all of your data')
async def resetSave(inter):
    logging.debug(str(inter.author.id) + " - /resetSave")
    server_id = inter.guild.id
    user, isNewUser = data.getUser(inter)
    if not isNewUser:
        if inter.author.id in data.globalSaveDict.keys():
            await inter.send(
                "You already currently using a global save. Please disable it with `/disable_global_save` before erasing a save file.")
            return

        if data.isUserInSession(inter, user):
            await inter.send(
                "Sorry " + inter.author.display_name + ", but you cannot reset your save while in an active session. Please end session with `/end_session`.")
            return

        embed = discord.Embed(title=str(inter.author) + " is resetting their save data.",
                              description='WARNING: This command will reset your save data PERMANENTLY. Please choose carefully below.')
        view = PokeNavComponents.ConfirmView(inter.author, "I understand, reset my save.",
                                             "Nevermind! I want to keep it.")
        await inter.send(embed=embed, view=view)
        message = await inter.original_message()
        await view.wait()
        await message.delete()
        if view.confirmed:
            success = data.deleteUser(server_id, user)
            if success:
                await inter.send(str(inter.author.display_name) + "'s save file has been deleted. Poof.")
            else:
                await inter.send("There was an error deleting the save file.")
        else:
            await inter.send(str(inter.author.display_name) + "'s reset request cancelled.")
    else:
        await inter.send("User '" + str(inter.author) + "' not found, no save to reset...")


@bot.slash_command(name='create_team', description='create a team',
                   options=[Option("team_number", description="Number of team to create.", required=True,
                                   type=OptionType.integer),
                            Option("team_name", description="The new name of the team.", required=True)])
async def createTeamCommand(inter, team_number, *, team_name=''):
    maxTeams = 30
    validTeamNumbers = list(range(1, maxTeams + 1))
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        if 'elite4' not in user.flags:
            await inter.send("Team creation is only available to trainers who have beaten the elite 4!")
            return
        try:
            team_number = int(team_number)
        except:
            await inter.send("Team number must be an integer between " + str(validTeamNumbers[0]) + " and " + str(
                validTeamNumbers[
                    len(validTeamNumbers) - 1]) + " where the team number follows command as shown below:\n`/create_team <team number>`.")
            return
        if team_number not in validTeamNumbers:
            await inter.send("Team number must be an integer between " + str(validTeamNumbers[0]) + " and " + str(
                validTeamNumbers[
                    len(validTeamNumbers) - 1]) + " where the team number follows command as shown below:\n`/create_team <team number>`.")
            return
        if not team_name:
            teamName = None
        user.createTeamFromParty(team_number, team_name)
        teamList = [user.teamDict[team_number]]
        files, embed = createTeamEmbed(teamList, user, "New Team Created:")
        await inter.send(files=files, embed=embed)


@bot.slash_command(name='rename_team', description='rename a team',
                   options=[Option("team_number", description="Number of team to rename.", required=True,
                                   type=OptionType.integer),
                            Option("team_name", description="The new name of the team.", required=True)])
async def renameTeamCommand(inter, team_number, *, team_name):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        try:
            team_number = int(team_number)
        except:
            await inter.send("Invalid team number.")
            return
        try:
            user.teamDict[team_number].name = team_name
            await inter.send("Team " + str(team_number) + " renamed to `" + team_name + "`.")
        except:
            await inter.send("Invalid team number.")


@bot.slash_command(name='delete_team', description='delete a team',
                   options=[Option("team_number", description="# of team to delete.", required=True,
                                   type=OptionType.integer)])
async def deleteTeamCommand(inter, team_number):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        try:
            team_number = int(team_number)
        except:
            await inter.send("Invalid team number.")
            return
        try:
            del user.teamDict[team_number]
            await inter.send("Team " + str(team_number) + " deleted.")
        except:
            await inter.send("Invalid team number.")


@bot.slash_command(name='set_team', description='set active team',
                   options=[Option("team_number_or_name", description="Number of team to create.", required=True)])
async def setTeamCommand(inter, *, team_number_or_name=''):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        if 'elite4' not in user.flags:
            await inter.send("Team creation is only available to trainers who have beaten the elite 4!")
            return
        if user.location.lower() in [item.lower() for item in data.flyRestrictions['both']]:
            logging.debug(str(inter.author.id) + " - not switching team, cannot set from this area!")
            await inter.send("Sorry, cannot set teams from this area!")
        else:
            allowSet = False
            activeSession = data.doesUserHaveActiveSession(inter.guild.id, user)
            if user.current_trade_id != 0:
                await inter.send("Please finish your current trade before setting a team.")
                return
            if activeSession:
                overworldTuple, isGlobal = data.userInOverworldSession(inter, user)
                if overworldTuple:
                    allowSet = True
                else:
                    await inter.send("Must be in the overworld to set your team.")
                    return
            else:
                allowSet = True
            try:
                teamNum = int(team_number_or_name)
            except:
                teamNum = None
            if teamNum:
                success, teamName, errorReason = user.setTeam(teamNum)
            else:
                success, teamName, errorReason = user.setTeam(None, team_number_or_name)
            if success:
                await inter.send(teamName + " set as active party.")
            else:
                messageStr = "Invalid team name or number selection. Please use `/set_team <team name or number>`."
                if errorReason:
                    messageStr = errorReason
                await inter.send(messageStr)


@bot.slash_command(name='teams', description='view list of teams')
async def viewTeamCommand(inter):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        if 'elite4' not in user.flags:
            await inter.send("Team creation is only available to trainers who have beaten the elite 4!")
            return
        teamList = []
        for i in sorted(user.teamDict.keys()):
            teamList.append(user.teamDict[i])
        files, embed = createTeamEmbed(teamList, user)
        await inter.send(files=files, embed=embed)


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


@bot.slash_command(name='shop', description='shop for post-game items with BP',
                   options=[Option("category", description="category to view, leave blank to view category list")])
async def shopCommand(inter, *, category=''):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        if not 'elite4' in user.flags:
            await inter.send("The shop may only be used by league champions! Continue your adventure to unlock access.")
            return
        if category:
            category_lower = category.lower()
            if category_lower == "trainer icons":
                embed = TrainerIcons.TrainerIconPurchaseEmbed(data, inter.author, user)
                view = TrainerIcons.TrainerIconPurchaseView(data, inter.author, user)
                await inter.send(view=view, embed=embed)
                message = await inter.original_message()
                await view.wait()
                await message.delete()
                while view.chosen:
                    icon = view.chosen
                    file = discord.File(icon.filename, filename="image.png")
                    already_owned = icon.name in user.trainer_icons
                    if already_owned:
                        title = 'Would you like to set ' + icon.name + ' as your trainer card icon?'
                        description = '\u200b'
                    else:
                        title = 'Would you like to purchase ' + icon.name + ' icon?'
                        description = 'Price: ' + str(icon.price) + 'BP'
                    embed = discord.Embed(title=title,
                                          description=description)
                    embed.set_image(url="attachment://image.png")
                    if not already_owned:
                        embed.set_footer(text='BP: ' + str(user.getItemAmount('BP')))
                    enough_bp = user.getItemAmount('BP') >= icon.price
                    disable_confirm = not already_owned and not enough_bp
                    confirmed_text = 'PURCHASE'
                    if already_owned:
                        confirmed_text = 'SET AS SPRITE'
                    elif not enough_bp:
                        confirmed_text = "Not enough BP"
                    view = PokeNavComponents.ConfirmView(inter.author, confirmed_text, "CANCEL", True, disable_confirm)
                    message = await inter.channel.send(embed=embed, view=view, file=file)
                    await view.wait()
                    await message.delete()
                    if view.confirmed:
                        if already_owned:
                            user.sprite = icon.filename
                            file = discord.File(icon.filename, filename="image.png")
                            embed = discord.Embed(title=icon.name + ' set as trainer card sprite!',
                                                  description='\u200b')
                            embed.set_image(url="attachment://image.png")
                            await inter.channel.send(embed=embed, file=file)
                        else:
                            if user.useItem('BP', icon.price):
                                user.sprite = icon.filename
                                user.trainer_icons.append(icon.name)
                                file = discord.File(icon.filename, filename="image.png")
                                embed = discord.Embed(title='Congrats! You purchased ' + icon.name + ' icon!',
                                                      description='It has been set as your trainer card sprite.')
                                embed.set_image(url="attachment://image.png")
                                await inter.channel.send(embed=embed, file=file)
                        break
                    else:
                        embed = TrainerIcons.TrainerIconPurchaseEmbed(data, inter.author, user)
                        view = TrainerIcons.TrainerIconPurchaseView(data, inter.author, user)
                        message = await inter.channel.send(embed=embed, view=view)
                        await view.wait()
                        await message.delete()
                return
            elif category_lower == "furniture":
                categoryList = list(data.secretBaseItemTypes.keys())
                categoryList.append('custom')
                files, embed = createShopEmbed(inter, user, categoryList)
                await inter.send(files=files, embed=embed)
            elif category_lower in data.secretBaseItemTypes.keys() or category_lower == "custom":
                itemList = []
                for name, item in data.secretBaseItems.items():
                    if item.getCategory().lower() == category_lower:
                        itemList.append(Shop_Item(item.name, item.getPrice(), item.getCurrency()))
                files, embed = createShopEmbed(inter, user, None, category_lower, itemList, True)
                await inter.send(files=files, embed=embed)
            elif category_lower in data.shopDict.keys():
                itemList = data.shopDict[category_lower]
                files, embed = createShopEmbed(inter, user, None, category_lower, itemList)
                await inter.send(files=files, embed=embed)
            else:
                await inter.send("Invalid category selection '" + category + "'. Use `/shop` to view categories.")
        else:
            categoryList = list(data.shopDict.keys())
            files, embed = createShopEmbed(inter, user, categoryList, includeTrainerIcons=True)
            await inter.send(files=files, embed=embed)


@bot.slash_command(name='buy', description='buy post-game items with BP',
                   options=[Option("item_name", description="name of item to buy", required=True),
                            Option("amount", description="leave blank for buying 1", type=OptionType.integer)])
async def buyCommand(inter, item_name='', amount=1):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("Use `/start` to begin your adventure first!")
    else:
        if not 'elite4' in user.flags:
            await inter.send("The shop may only be used by league champions! Continue your adventure to unlock access.")
            return
        try:
            amount = int(amount)
            itemName = item_name.title()
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
                    await inter.send(itemName + " x" + str(amount) + " purchased in exchange for " + str(
                        price) + " " + currency + ".")
                    return
                else:
                    await inter.send("Not enough " + currency + " to make transaction. " + str(
                        price) + " " + currency + " is required.")
                    return
        matching_items = []
        for category, itemList in data.shopDict.items():
            for item in itemList:
                if item.itemName.lower() == itemName.lower():
                    matching_items.append(item)
        if len(matching_items) > 1:
            view = PokeNavComponents.ConfirmView(inter.author, str(matching_items[1].currency), str(matching_items[0].currency), True)
            embed = discord.Embed(title="Which currency would you like to use to purchase " + str(amount) + " " + matching_items[0].itemName + "?", description="Choose below.")
            footer_text = ""
            footer_text += "BP: " + str(user.getItemAmount('BP')) + '\n'
            footer_text += "Coins: " + str(user.getItemAmount('Coins'))
            if matching_items[0].currency == "Shiny Charm Fragment" or matching_items[1].currency == "Shiny Charm Fragment":
                footer_text += "\nShiny Charm Fragments: " + str(user.getItemAmount('Shiny Charm Fragment'))
            embed.set_footer(text=footer_text)
            await inter.send(view=view, embed=embed)
            message = await inter.original_message()
            await view.wait()
            if view.timed_out:
                await message.delete()
                return
            if view.confirmed:
                item = matching_items[1]
            else:
                item = matching_items[0]
            await message.delete()
        elif len(matching_items) > 0:
            item = matching_items[0]
        else:
            await inter.send(
                "Invalid item selection '" + itemName + "'. Please use `/shop` to find a valid item to buy.")
            return
        price = item.price * amount
        currency = item.currency
        if user.itemList[currency] >= price:
            if itemName.lower() == 'shiny charm':
                if 'Shiny Charm' in user.itemList.keys() and user.itemList['Shiny Charm'] > 0:
                    await inter.send("Can only have 1 Shiny Charm at a time!")
                    return
            user.useItem(currency, price)
            if itemName.lower() == "shiny magikarp":
                shinyKarp = Pokemon(data, "Shiny Magikarp", 5)
                user.addPokemon(shinyKarp, True, True)
            elif itemName.lower() == "retro porygon":
                new_pokemon = Pokemon(data, "Retro Porygon", 5)
                user.addPokemon(new_pokemon, True, True)
            elif itemName.lower() == "retro charizard":
                new_pokemon = Pokemon(data, "Retro Charizard", 5)
                user.addPokemon(new_pokemon, True, True)
            elif itemName.lower() == "retro venasaur":
                new_pokemon = Pokemon(data, "Retro Venasaur", 5)
                user.addPokemon(new_pokemon, True, True)
            elif itemName.lower() == "retro blastoise":
                new_pokemon = Pokemon(data, "Retro Blastoise", 5)
                user.addPokemon(new_pokemon, True, True)
            else:
                user.addItem(item.itemName, amount)
            await inter.send(item.itemName + " x" + str(amount) + " purchased in exchange for " + str(
                price) + " " + currency + ".")
            return
        else:
            await inter.send("Not enough " + currency + " to make transaction. " + str(
                price) + " " + currency + " is required.")
            return


@bot.slash_command(name='preview', description='preview a furniture item from the /shop',
                   options=[Option("item_name", description="item name to preview", required=True)])
async def previewCommand(inter, *, item_name=''):
    itemName = item_name.title()
    if itemName in data.secretBaseItems.keys():
        item = data.secretBaseItems[itemName]
        await secretBaseUi.sendPreviewMessage(inter, item)
    else:
        await inter.send("Invalid item name '" + item_name + "'. Try `/shop furniture` to see available items.")


@bot.slash_command(name='release',
                   description='release a specified party Pokemon, cannot be undone',
                   options=[Option("party_number", description="number of pokemon in party to release",
                                   type=OptionType.integer, required=True)])
async def releasePartyPokemon(inter, party_number):
    logging.debug(str(inter.author.id) + " - /releasePartyPokemon")
    partyNum = int(party_number) - 1
    user, isNewUser = data.getUser(inter)
    if not isNewUser:
        if data.isUserInSession(inter, user):
            await inter.send(
                "Sorry " + inter.author.display_name + ", but you cannot release Pokemon while in an active session. Please end session with `/end_session`.")
            return

        if len(user.partyPokemon) <= 1:
            await inter.send(
                "Sorry " + inter.author.display_name + ", but you cannot release Pokemon when you only have 1 in your party.")
            return

        if partyNum >= len(user.partyPokemon) or partyNum < 0:
            await inter.send("Sorry " + inter.author.display_name + ", but you do not have a Pokemon in that slot.")
            return

        name = user.partyPokemon[partyNum].name
        embed = discord.Embed(title=str(inter.author) + " is releasing: " + name,
                              description='WARNING: This command will release your selected Pokemon PERMANENTLY. Please choose carefully below.')
        file = discord.File(user.partyPokemon[partyNum].getSpritePath(), filename="image.png")
        files = [file]
        embed.set_image(url="attachment://image.png")
        view = PokeNavComponents.ConfirmView(inter.author, "I understand, release my Pokemon.",
                                             "Nevermind! I want to keep it.")
        await inter.send(embed=embed, view=view, files=files)
        message = await inter.original_message()
        await view.wait()
        await message.delete()
        if view.confirmed:
            try:
                del user.partyPokemon[partyNum]
                await inter.send(str(inter.author.display_name) + "'s Pokemon was released. Bye bye " + name + "!")
            except:
                await inter.send("There was an error releasing the Pokemon.")
        else:
            await inter.send(str(inter.author.display_name) + "'s release request cancelled.")
    else:
        await inter.send("User '" + str(inter.author) + "' not found, no Pokemon to release...")


@bot.slash_command(name='zzz_recent_users', description='DEV ONLY: get number of recent users',
                   default_permission=False)
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def getRecentUsersCount(inter):
    if not await verifyDev(inter):
        return
    numRecentUsers, channelList = data.getNumOfRecentUsersForRaid()
    await inter.send("Number of recent users who are eligible for raids: " + str(numRecentUsers))


@bot.slash_command(name='zzz_leave', description='DEV ONLY: leave a server',
                   options=[Option("server_id", description="id of server to leave",
                                   required=True)],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def leaveCommand(inter, server_id):
    if not await verifyDev(inter):
        return
    server_id = int(server_id)
    server = bot.get_guild(server_id)
    await inter.send("Left server `" + str(server_id) + "`.")
    await server.leave()


@bot.slash_command(name='phonefix', description='phone fix for user')
async def phoneFix(inter):
    user, isNewUser = data.getUser(inter)
    if not isNewUser:
        user.iphone = not user.iphone
        await inter.send("Phone fix applied for " + str(inter.author) + ".")
    else:
        await inter.send("User '" + str(inter.author) + "' not found.")


@bot.slash_command(name='zzz_verify_champion', description='DEV ONLY: verify if user has beaten the elite 4',
                   options=[Option("username", description="username of person to verify")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def verifyChampion(inter, *, username: str = "self"):
    if not await verifyDev(inter):
        return
    user = await getUserById(inter, username)
    if user:
        if 'elite4' in user.flags:
            await inter.send(user.name + " is a league champion!")
        else:
            await inter.send(user.name + " has NOT beaten the elite 4.")
    else:
        await inter.send("User '" + username + "' not found, cannot verify.")


@bot.slash_command(name='zzz_set_location_progress', description='DEV ONLY: sets location progress',
                   options=[Option("location", description="flag to grant", required=True),
                            Option("progress_amount", description="progress to set to", required=True,
                                   type=OptionType.integer),
                            Option("username", description="username of person to grant flag for"),
                            Option("server_id", description="server_id person is on")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def set_location_progress(inter, location, progress_amount, username: str = "self", server_id=None):
    if not server_id:
        server_id = inter.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = inter.guild.id
    if not await verifyDev(inter):
        return
    user = await getUserById(inter, username, server_id)
    if user:
        user.locationProgressDict[location] = progress_amount
        await inter.send(user.name + ' has been set to ' + str(progress_amount) + ' for location ' + location + '.')
    else:
        await inter.send("User '" + username + "' not found, cannot set location progress.")


@bot.slash_command(name='zzz_grant_flag', description='DEV ONLY: grants user flag',
                   options=[Option("flag", description="flag to grant", required=True),
                            Option("username", description="username of person to grant flag for", required=True),
                            Option("server_id", description="server_id person is on")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def grantFlag(inter, flag, username: str = "self", server_id=None):
    if not server_id:
        server_id = inter.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = inter.guild.id
    flag = flag.replace("_", " ")
    if not await verifyDev(inter):
        return
    user = await getUserById(inter, username, server_id)
    if user:
        user.addFlag(flag)
        await inter.send(user.name + ' has been granted the flag: "' + flag + '".')
    else:
        await inter.send("User '" + username + "' not found, cannot grant flag.")


@bot.slash_command(name='zzz_view_flags', description='DEV ONLY: views user flags',
                   options=[Option("username", description="username of person to grant flag for", required=True),
                            Option("server_id", description="server_id person is on")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def viewFlags(inter, username: str = "self", server_id=None):
    if not server_id:
        server_id = inter.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = inter.guild.id
    if not await verifyDev(inter):
        return
    user = await getUserById(inter, username, server_id)
    if user:
        await inter.send(user.name + ' flags:\n' + str(user.flags))
    else:
        await inter.send("User '" + username + "' not found, cannot revoke flag.")


@bot.slash_command(name='zzz_remove_flag', description='DEV ONLY: grants user flag',
                   options=[Option("flag", description="flag to grant", required=True),
                            Option("username", description="username of person to grant flag for", required=True),
                            Option("server_id", description="server_id person is on")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def removeFlag(inter, flag, username: str = "self", server_id=None):
    if not server_id:
        server_id = inter.guild.id
    else:
        try:
            server_id = int(server_id)
        except:
            server_id = inter.guild.id
    flag = flag.replace("_", " ")
    if not await verifyDev(inter):
        return
    user = await getUserById(inter, username, server_id)
    if user:
        if user.removeFlag(flag):
            await inter.send(user.name + ' has been revoked the flag: "' + flag + '".')
        else:
            await inter.send(user.name + ' did not have the flag: "' + flag + '". Nothing to revoke.')
    else:
        await inter.send("User '" + username + "' not found, cannot revoke flag.")


@bot.slash_command(name='zzz_stats', description='DEV ONLY: stats',
                   default_permission=False)
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def statsCommand(inter):
    if not await verifyDev(inter):
        return
    totalAccounts = 0
    elite4 = 0
    badge1 = 0
    badge2 = 0
    badge3 = 0
    badge4 = 0
    badge5 = 0
    badge6 = 0
    badge7 = 0
    badge8 = 0
    shinyFound = 0
    shinyPokemon = 0
    distortionFound = 0
    distortionPokemon = 0
    uniqueUsers = []
    uniqueUserIds = []
    allUsers = []
    uniqueUsersDict = {}
    highestWithRestrictionsStreak = 0
    highestNoRestrictionsStreak = 0
    battleTowerAttempted = 0
    mostPokemonCaught = 0
    secretBases = 0
    magikarpBought = 0
    for server_id, userList in data.userDict.items():
        allUsers = userList
        for user in userList:
            totalAccounts += 1
            if user.identifier in uniqueUsersDict.keys():
                uniqueUsersDict[user.identifier].append(user)
            else:
                uniqueUsersDict[user.identifier] = [user]
            if user.identifier not in uniqueUserIds:
                uniqueUsers.append(user)
                uniqueUserIds.append(user.identifier)
    for userId, userList in uniqueUsersDict.items():
        elite4Found = False
        badge1Found = False
        badge2Found = False
        badge3Found = False
        badge4Found = False
        badge5Found = False
        badge6Found = False
        badge7Found = False
        badge8Found = False
        userHasShiny = False
        userHasDistortion = False
        userTriedBattleTower = False
        userHasSecretBase = False
        pokemonCaught = 0
        for user in userList:
            if user.secretBase:
                userHasSecretBase = True
            if user.withRestrictionsRecord > 0 or user.noRestrictionsRecord > 0:
                userTriedBattleTower = True
            if user.withRestrictionsRecord > highestWithRestrictionsStreak:
                highestWithRestrictionsStreak = user.withRestrictionsRecord
            if user.noRestrictionsRecord > highestNoRestrictionsStreak:
                highestNoRestrictionsStreak = user.noRestrictionsRecord
            if user.checkFlag('elite4'):
                elite4Found = True
            if user.checkFlag('badge1'):
                badge1Found = True
            if user.checkFlag('badge2'):
                badge2Found = True
            if user.checkFlag('badge3'):
                badge3Found = True
            if user.checkFlag('badge4'):
                badge4Found = True
            if user.checkFlag('badge5'):
                badge5Found = True
            if user.checkFlag('badge6'):
                badge6Found = True
            if user.checkFlag('badge7'):
                badge7Found = True
            if user.checkFlag('badge8'):
                badge8Found = True
            pokemonCaught += len(user.partyPokemon) + len(user.boxPokemon)
            for pokemon in user.partyPokemon:
                if pokemon.shiny and not pokemon.distortion:
                    userHasShiny = True
                    shinyPokemon += 1
                if pokemon.distortion:
                    userHasDistortion = True
                    distortionPokemon += 1
                if pokemon.name == "Shiny Magikarp":
                    magikarpBought += 1
            for pokemon in user.boxPokemon:
                if pokemon.shiny and not pokemon.distortion:
                    userHasShiny = True
                    shinyPokemon += 1
                if pokemon.distortion:
                    userHasDistortion = True
                    distortionPokemon += 1
                if pokemon.name == "Shiny Magikarp":
                    magikarpBought += 1
        if userHasSecretBase:
            secretBases += 1
        if userHasShiny:
            shinyFound += 1
        if userHasDistortion:
            distortionFound += 1
        if elite4Found:
            elite4 += 1
        if badge1Found:
            badge1 += 1
        if badge2Found:
            badge2 += 1
        if badge3Found:
            badge3 += 1
        if badge4Found:
            badge4 += 1
        if badge5Found:
            badge5 += 1
        if badge6Found:
            badge6 += 1
        if badge7Found:
            badge7 += 1
        if badge8Found:
            badge8 += 1
        if userTriedBattleTower:
            battleTowerAttempted += 1
        if pokemonCaught > mostPokemonCaught:
            mostPokemonCaught = pokemonCaught
    message = "```"
    message += "# Total Number of Servers: " + str(len(bot.guilds)) + "\n"
    message += "# Total Number of Accounts: " + str(totalAccounts) + "\n"
    message += "# Total Number of Unique Trainers: " + str(len(uniqueUsers)) + "\n"
    message += "# Trainers Who Have Beaten Elite 4: " + str(elite4) + "\n"
    message += "# Trainers Who Have Caught a Shiny: " + str(shinyFound) + "\n"
    message += "# of Shiny Pokemon Caught: " + str(shinyPokemon) + "\n"
    message += "# Trainers Who Have Caught a Distortion: " + str(distortionFound) + "\n"
    message += "# of Distortion Pokemon Caught: " + str(distortionPokemon) + "\n"
    message += "# of Trainers with at least 1 Battle Tower win: " + str(battleTowerAttempted) + "\n"
    message += "# of Trainers with a secret base: " + str(secretBases) + "\n"
    message += "Most Pokemon Caught by a single user: " + str(mostPokemonCaught) + "\n"
    message += "'Shiny Magikarp' bought: " + str(magikarpBought) + "\n"
    message += "Highest Battle Tower w/ Restrictions Streak: " + str(highestWithRestrictionsStreak) + "\n"
    message += "Highest Battle Tower no Restrictions Streak: " + str(highestNoRestrictionsStreak) + "\n"
    message += "Percent beaten elite 4 that beat badge1: " + str(round(elite4 / badge1 * 100, 2)) + "%\n"
    message += "Percent beaten elite 4: " + str(round(elite4 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge8: " + str(round(badge8 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge7: " + str(round(badge7 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge6: " + str(round(badge6 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge5: " + str(round(badge5 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge4: " + str(round(badge4 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge3: " + str(round(badge3 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge2: " + str(round(badge2 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += "Percent beaten badge1: " + str(round(badge1 / len(uniqueUsers) * 100, 2)) + "%\n"
    message += '```'
    await inter.send(message)


@bot.slash_command(name='zzz_display_guild_list', description='DEV ONLY: display the overworld list',
                   options=[Option("request", description="short, long")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def displayGuildList(inter, request="short"):
    if not await verifyDev(inter):
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
        await inter.send(messageText)


@bot.slash_command(name='zzz_display_overworld_list', description='DEV ONLY: display the overworld list',
                   default_permission=False)
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def displayOverworldList(inter):
    if not await verifyDev(inter):
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
        await inter.send(messageText)


@bot.slash_command(name='zzz_display_session_list', description='DEV ONLY: display the active session list',
                   default_permission=False)
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def displaySessionList(inter):
    if not await verifyDev(inter):
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
        await inter.send(messageText)


@bot.slash_command(name='zzz_force_end_session',
                   description='DEV ONLY: forcibly removes user from active sessions list',
                   options=[Option("username", description="username of person to remove")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def forceEndSession(inter, *, username: str = "self"):
    if inter.author.guild_permissions.administrator:
        logging.debug(str(inter.author.id) + " - /force_end_session for " + username)

        if await verifyDev(inter, False):
            try:
                username = int(username)
                logging.debug("Trying to find user by number.")
                found = False
                selectedServer = ''
                for key, userList in data.sessionDict.items():
                    for user in userList:
                        if user.identifier == username:
                            userList.remove(user)
                            found = True
                            selectedServer = key
                if found:
                    logging.debug(str(inter.author.id) + " - user " + str(
                        username) + " has been removed from active session list from server '" + str(
                        selectedServer) + "'")
                    await inter.send(
                        "User '" + str(username) + "' has been removed from active session list from server '" + str(
                            selectedServer) + "'")
                    return
                else:
                    logging.debug(str(inter.author.id) + " - user " + str(username) + " not found")
                    await inter.send("User '" + str(username) + "' not found.")
                    return
            except:
                logging.debug("forceEndSession input is not a number, continuing as normal")

        user = await getUserById(inter, username)

        if user:
            success = data.removeUserSession(inter.guild.id, user)
            if success:
                logging.debug(
                    str(inter.author.id) + " - user " + str(username) + " has been removed from active session list")
                await inter.send("User '" + str(username) + "' has been removed from the active session list.")
            else:
                logging.debug(str(inter.author.id) + " - user " + str(username) + " not in active session list")
                await inter.send("User '" + str(username) + "' not in active session list.")
        else:
            logging.debug(str(inter.author.id) + " - user " + str(username) + " not found")
            await inter.send("User '" + str(username) + "' not found.")
    else:
        await inter.send(str(inter.author.display_name) + ' does not have admin rights to use this command.')


@bot.slash_command(name='zzz_set_battle_tower_streak',
                   description='DEV ONLY: forcibly removes user from active sessions list',
                   options=[Option("with_restrictions", description="true or false"),
                            Option("number", description="number to set streak to"),
                            Option("username", description="username of person to set streak for")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def setBattleTowerStreakCommand(inter, with_restrictions, num, *, username: str = "self"):
    if not await verifyDev(inter):
        return
    with_restrictions = (with_restrictions.lower() == "true")
    num = int(num)
    user = await getUserById(inter, username)
    if user:
        try:
            streak = ''
            if with_restrictions:
                streak = 'withRestrictions'
                user.withRestrictionStreak = num
            else:
                streak = 'noRestrictions'
                user.noRestrictionsStreak = num
            await inter.send(user.name + ' ' + streak + ' streak has been set to ' + str(num) + '.')
        except:
            await inter.send("Something went wrong trying to set the streak.")
    else:
        await inter.send("User '" + username + "' not found, cannot set streak.")


@bot.slash_command(name='zzz_refresh', description='DEV ONLY: refresh components',
                   options=[Option("component", description="component to refresh", required=True)
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def refresh_command(inter, component):
    component = component.lower()
    await inter.response.defer()
    try:
        if component == "pokemon":
            data.loadPokemonDataFromJSON()
            data.loadAlteringCaveRestrictionsFromJSON()
            data.loadBattleTowerRestrictionsFromJSON()
            data.loadAltShiniesFromJSON()
            data.loadDexSegementsFromJSON()
        elif component == "event":
            data.loadPokemonDataFromJSON()
            data.loadAlteringCaveRestrictionsFromJSON()
            data.loadBattleTowerRestrictionsFromJSON()
            data.loadAltShiniesFromJSON()
            data.loadEventDataFromJSON()
            data.loadLocationDataFromJSON()
            data.loadRegionDataFromJSON()
            data.loadFlyRestrictionsFromJSON()
        elif component == "moves":
            data.loadMoveDataFromJSON()
            for server_id, userList in data.userDict.items():
                for user in userList:
                    for pokemon in user.partyPokemon + user.boxPokemon:
                        moveNameList = []
                        for move in pokemon.moves:
                            moveNameList.append(move['names']['en'])
                        pokemon.moves.clear()
                        for move_name in moveNameList:
                            pokemon.moves.append(data.getMoveData(move_name))
        elif component == "location":
            data.loadLocationDataFromJSON()
            data.loadFlyRestrictionsFromJSON()
        elif component == "shop":
            data.loadShopDataFromJSON()
        elif component == "trainer icons":
            data.loadTrainerIconDataFromJSON()
        elif component == "cutscene":
            data.loadCutsceneDataFromJSON()
        elif component == "spawns":
            data.loadRegionDataFromJSON()
        elif component == "fly":
            data.loadFlyRestrictionsFromJSON()
        else:
            await inter.send("Unknown component. Try one of the following:\n"
                       "pokemon\nevent\nmoves\nlocation\nshop\ntrainer icons\ncutscene\nspawns\nfly")
            return
    except:
        await inter.send("An error occurred while refreshing data.")
        return
    await inter.send("Done! Refreshed " + component + ".")


@bot.slash_command(name='zzz_toggle_account_active', description='DEV ONLY: close or open an account',
                   options=[Option("user_id", description="id of the user to clone", required=True),
                            Option("server_id", description="id of the server to get user from")
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def toggle_account_active(inter, user_id, server_id=None):
    if not await verifyDev(inter):
        return
    logging.debug(
        str(inter.author.id) + " - /zzz_toggle_account_active " + user_id)
    user_id = int(user_id)
    skip_global = False
    if server_id:
        skip_global = True
    user = await getUserById(inter, user_id, server_id, skip_global)
    if user:
        if user.closed:
            user.closed = False
            await inter.send("User '" + str(user_id) + "' account OPENED.")
        else:
            user.closed = True
            await inter.send("User '" + str(user_id) + "' account CLOSED.")
    else:
        await inter.send("User '" + str(user_id) + "' not found, cannot toggle active.")


@bot.slash_command(name='zzz_clone_user', description='DEV ONLY: clone a user',
                   options=[Option("user_id_to_clone", description="id of the user to clone", required=True),
                            Option("new_id", description="new_id for cloned user", required=True),
                            Option("server_id_to_pull_user", description="server id to pull user to clone from")
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def clone_user_command(inter, user_id_to_clone, new_id, server_id_to_pull_user=None):
    if not await verifyDev(inter):
        return
    logging.debug(
        str(inter.author.id) + " - /zzz_clone_user " + user_id_to_clone + " to " + new_id)
    user_id_to_clone = int(user_id_to_clone)
    new_id = int(new_id)
    if server_id_to_pull_user:
        server_id_to_pull_user = int(server_id_to_pull_user)
    user_to_clone = await getUserById(inter, user_id_to_clone, server_id_to_pull_user)
    if user_to_clone:
        try:
            data.clone_user(user_to_clone, new_id)
            await inter.send("User " + str(user_id_to_clone) + " successfully cloned to " + str(new_id) + ".")
        except:
            await inter.send("Something went wrong trying to clone user.")
    else:
        await inter.send("User '" + str(user_id_to_clone) + "' not found, cannot clone.")


@bot.slash_command(name='zzz_grant_pokemon', description='DEV ONLY: grants user a Pokemon',
                   options=[Option("pokemon_name", description="name of the pokemon to grant", required=True),
                            Option("level", description="level of the pokemon", type=OptionType.integer),
                            Option("username", description="user to grant pokemon to"),
                            Option("shiny", description="true or false"),
                            Option("distortion", description="true or false"),
                            Option("alt_shiny", description="true or false"),
                            Option("shadow", description="true or false"),
                            Option("was_caught", description="true or false"),
                            Option("location", description="location where the Pokemon was caught"),
                            Option("ot", description="who the Pokemon is owned by")
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def grantPokemon(inter, pokemon_name, level=5, username: str = "self", shiny="false", distortion="false",
                       alt_shiny="false", shadow="false", was_caught="false", location="", ot="Event"):
    if not await verifyDev(inter):
        return
    pokemon_name = pokemon_name.replace('_', " ")
    level = int(level)
    shiny = (shiny.lower() == "true")
    distortion = (distortion.lower() == "true")
    alt_shiny = (alt_shiny.lower() == "true")
    shadow = (shadow.lower() == "true")
    was_caught = (was_caught.lower() == "true")
    if distortion:
        shiny = True
    if alt_shiny:
        shiny = True
    logging.debug(
        str(inter.author.id) + " - /grant_pokemon " + pokemon_name.title() + " for " + username + " with level=" + str(
            level) + " and shiny=" + str(shiny) + " and distortion=" + str(distortion))
    user = await getUserById(inter, username)
    if user:
        try:
            pokemon = Pokemon(data, pokemon_name, level)
            pokemon.shiny = shiny
            pokemon.distortion = distortion
            if pokemon.name.lower() in data.alternative_shinies['all']:
                pokemon.altShiny = alt_shiny
            else:
                alt_shiny = False
                pokemon.altShiny = False
            pokemon.shadow = shadow
            if pokemon.shadow:
                pokemon.setShadowMoves()
            pokemon.setSpritePath()
            pokemon.OT = ot
            user.addPokemon(pokemon, False, was_caught, location)
            await inter.send(
                user.name + ' has been granted: ' + pokemon_name.title() + "\nlevel=" + str(level)
                + "\nshiny=" + str(shiny) + "\ndistortion=" + str(distortion) + "\naltShiny=" + str(alt_shiny)
                + "\nshadow=" + str(shadow) + "\nwas_caught=" + str(was_caught) + "\nlocation=" + str(location)
                + "\nOT=" + str(ot)
            )
        except:
            await inter.send("Something went wrong trying to grant Pokemon.")
    else:
        await inter.send("User '" + username + "' not found, cannot grant Pokemon.")


@bot.slash_command(name='zzz_grant_item', description='DEV ONLY: grants user an item',
                   options=[Option("item", description="name of the item to grant", required=True),
                            Option("amount", description="amount of the item", type=OptionType.integer),
                            Option("username", description="user to grant item to"),
                            Option("trainer_icon", description="true or false")
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def grantItem(inter, item, amount=1, username: str = "self", trainer_icon="false"):
    if not await verifyDev(inter):
        return
    item = item.replace('_', " ")
    amount = int(amount)
    trainer_icon = trainer_icon.lower() == "true"
    if inter.author.guild_permissions.administrator:
        logging.debug(str(inter.author.id) + " - /grant_item " + item + " for " + username)
        user = await getUserById(inter, username)
        if user:
            if trainer_icon:
                user.trainer_icons.append(item)
            else:
                user.addItem(item, amount)
            await inter.send(user.name + ' has been granted ' + str(amount) + ' of ' + item + '.')
        else:
            await inter.send("User '" + username + "' not found, cannot grant item.")
    else:
        await inter.send(str(inter.author.display_name) + ' does not have admin rights to use this command.')


@bot.slash_command(name='zzz_remove_item', description='DEV ONLY: removes user item',
                   options=[Option("item", description="name of the item to remove", required=True),
                            Option("amount", description="amount of the item", type=OptionType.integer),
                            Option("username", description="user to remove item from")
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def removeItem(inter, item, amount=1, *, username: str = "self"):
    if not await verifyDev(inter):
        return
    item = item.replace('_', " ")
    amount = int(amount)
    if inter.author.guild_permissions.administrator:
        logging.debug(str(inter.author.id) + " - /remove_item " + item + " for " + username)
        user = await getUserById(inter, username)
        if user:
            user.useItem(item, amount)
            await inter.send(user.name + ' has been revoked ' + str(amount) + ' of ' + item + '.')
        else:
            await inter.send("User '" + username + "' not found, cannot remove item.")
    else:
        await inter.send(str(inter.author.display_name) + ' does not have admin rights to use this command.')


@bot.slash_command(name='zzz_set_location', description='DEV ONLY: set a players location',
                   options=[Option("location", description="location to set user to", required=True),
                            Option("username", description="user to set location")
                            ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def setLocation(inter, location, username='self'):
    if inter.author.guild_permissions.administrator:
        logging.debug(str(inter.author.id) + " - /set_location to " + location + " for " + username)
        user = await getUserById(inter, username)
        if user:
            if location in user.locationProgressDict.keys():
                user.location = location
                await inter.send(inter.author.display_name + " was forcibly sent to: " + location + "!")
            else:
                await inter.send('"' + location + '" has not been visited by user or does not exist.')
        else:
            await inter.send("User '" + username + "' not found.")
    else:
        await inter.send(str(inter.author.display_name) + ' does not have admin rights to use this command.')


@bot.slash_command(name='set_altering_cave', description='trade 10 BP to set the Pokemon in Altering Cave',
                   options=[Option("pokemon_name", description="pokemon to set", required=True)]
                   )
async def setAlteringCave(inter, *, pokemon_name):
    logging.debug(str(inter.author.id) + " - /set_altering_cave " + pokemon_name)
    bpCost = 10
    bannedList = data.alteringCaveRestrictions
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        pokemon = None
        try:
            pokemon = data.getPokemonData(pokemon_name)
        except:
            pass
        if pokemon is not None:
            if pokemon['names']['en'] not in bannedList:
                if 'BP' in user.itemList.keys():
                    totalBp = user.itemList['BP']
                    if totalBp >= bpCost:
                        user.useItem('BP', bpCost)
                        user.alteringPokemon = pokemon['names']['en']
                        await inter.send(
                            "Congratulations " + inter.author.display_name + "! You set the Altering Cave Pokemon to be " +
                            pokemon['names']['en'] + "! (at the cost of " + str(bpCost) + " BP mwahahaha).")
                    else:
                        await inter.send("Sorry " + inter.author.display_name + ", but you need at least " + str(
                            bpCost) + " to trade for setting the Altering Cave Pokemon.")
                else:
                    await inter.send("Sorry " + inter.author.display_name + ", but you need at least " + str(
                        bpCost) + " to trade for setting the Altering Cave Pokemon.")
            else:
                await inter.send("Pokemon '" + pokemon_name + "' cannot be set for Altering Cave.")
        else:
            await inter.send("Pokemon '" + pokemon_name + "' not found.")


# @bot.slash_command(name='set_buy_amount', description='sets amount of item to buy in PokeMarts',
#                    options=[Option("amount", description="amount per purchase in PokeMarts", required=True,
#                                    type=OptionType.integer)]
#                    )
# async def setBuyAmount(inter, amount):
#     logging.debug(str(inter.author.id) + " - /set_buy_amount " + str(amount))
#     try:
#         amount = int(amount)
#     except:
#         await inter.send("Please use the format `/set_buy_amount 7`.")
#         return
#     user, isNewUser = data.getUser(inter)
#     if isNewUser:
#         await inter.send("You have not yet played the game and have no Pokemon!")
#     else:
#         if amount > 0:
#             user.storeAmount = amount
#             await inter.send("PokeMart buy quantity set to " + str(amount) + ".")
#         else:
#             await inter.send("Specified amount must be greated than 0.")


@bot.slash_command(name='furret', description='furret')
async def furret(inter):
    await inter.send("https://tenor.com/view/furret-pokemon-cute-gif-17963535")


@bot.slash_command(name='nickname', description='nickname a Pokemon',
                   options=[Option("party_number", description="number of Pokemon in party to rename", required=True,
                                   type=OptionType.integer),
                            Option("nickname", description="new nicknme for Pokemon", required=True)]
                   )
async def nickname(inter, party_number, *, nickname):
    logging.debug(str(inter.author.id) + " - /nickname " + str(party_number) + ' ' + nickname)
    party_number = int(party_number) - 1
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > party_number):
            await inter.send(user.partyPokemon[party_number].nickname + " was renamed to '" + nickname + "'!")
            user.partyPokemon[party_number].nickname = nickname
        else:
            await inter.send("No Pokemon in that party slot.")


@bot.slash_command(name='swap_moves', description="swap two of a Pokemon's moves",
                   options=[Option("party_number", description="number of Pokemon in party to rename", required=True,
                                   type=OptionType.integer),
                            Option("move_slot_1", description="first move to swap", required=True,
                                   type=OptionType.integer),
                            Option("move_slot_2", description="second move to swap", required=True,
                                   type=OptionType.integer)]
                   )
async def swapMoves(inter, party_number, move_slot_1, move_slot_2):
    logging.debug(
        str(inter.author.id) + " - /swap_moves " + str(party_number) + ' ' + str(move_slot_1) + ' ' + str(move_slot_2))
    party_number = int(party_number) - 1
    move_slot_1 = int(move_slot_1) - 1
    move_slot_2 = int(move_slot_2) - 1
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if (len(user.partyPokemon) > party_number):
            pokemon = user.partyPokemon[party_number]
            if (len(pokemon.moves) > move_slot_1 and len(pokemon.moves) > move_slot_2):
                await inter.send(
                    pokemon.nickname + " had '" + pokemon.moves[move_slot_1]['names']['en'] + "' swapped with '" +
                    pokemon.moves[move_slot_2]['names']['en'] + "'!")
                move1 = pokemon.moves[move_slot_1]
                move2 = pokemon.moves[move_slot_2]
                pp1 = pokemon.pp[move_slot_1]
                pp2 = pokemon.pp[move_slot_2]
                pokemon.moves[move_slot_1] = move2
                pokemon.moves[move_slot_2] = move1
                pokemon.pp[move_slot_1] = pp2
                pokemon.pp[move_slot_2] = pp1
            else:
                await inter.send("Invalid move slots.")
        else:
            await inter.send("No Pokemon in that party slot.")


@bot.slash_command(name='create_shiny_charm', description="creates shiny charm if possibles")
async def createShinyCharm(inter):
    logging.debug(str(inter.author.id) + " - /create_shiny_charm")
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if "Shiny Charm Fragment" in user.itemList.keys():
            if user.itemList['Shiny Charm Fragment'] >= 3:
                if 'Shiny Charm' in user.itemList.keys() and user.itemList['Shiny Charm'] > 0:
                    await inter.send(
                        "Already own a Shiny Charm. Can only have 1 at a time. They will break after you find your next shiny Pokemon.")
                    return
                user.useItem('Shiny Charm Fragment', 3)
                user.addItem('Shiny Charm', 1)
                await inter.send(
                    "Shiny Charm created at the cost of 3 fragments. This charm will increase your shiny odds until you find your next shiny (at which point it will break).")
                return
        await inter.send(
            "Not enough Shiny Charm Fragment(s) in Bag to create Shiny Charm. Requires 3 fragments to create 1 charm.")


@bot.slash_command(name='zzz_check_author', description='DEV ONLY: check author by ID',
                   options=[
                       Option("identifier", description="user id to check", required=True),
                       Option("server_id", description="optional server id"),
                   ],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def checkAuthorCommand(inter, identifier, server_id=""):
    if not await verifyDev(inter):
        return
    if server_id:
        server_id = int(server_id)
    else:
        server_id = inter.guild.id
    identifier = int(identifier)
    user = data.getUserById(server_id, identifier)
    if user:
        await inter.send("Server: " + str(server_id) + "\nID: " + str(
            identifier) + "\nAuthor: " + user.author + "\nDisplay name: " + user.name)
    else:
        await inter.send("User not found.")

@bot.slash_command(name='zzz_game_corner_simulation', description='simulates many runs of the game corner',
                   options=[
                       Option("starting_coins", description="number of coins to start with", type=OptionType.integer),
                       Option("number_of_simulations", description="number of simulatins to run", type=OptionType.integer),
                       Option("max_rolls", description="maximum number of rolls per simulation", type=OptionType.integer),
                   ],
                   default_permission=False)
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def game_corner_simulation(inter, starting_coins=100, number_of_simulations=1000, max_rolls=1000):
    await inter.send('Launching Game Corner Simulation...')
    message = await inter.original_message()
    await message.delete()
    final_coins_dict = {}
    slots = Game_Corner.Slots()
    number_to_max_rolls = 0
    for x in range(0, number_of_simulations):
        coins = starting_coins
        replays = 0
        rolls_complete = 0
        while coins > 0:
            if rolls_complete >= max_rolls:
                number_to_max_rolls += 1
                break
            result = slots.roll()
            if coins > 2 or replays > 0:
                tier = 3
            elif coins == 2:
                tier = 2
            elif coins == 1:
                tier = 1
            else:
                break
            if replays > 0:
                replays -= 1
            else:
                coins -= tier
            payout, replay, winning_string = slots.check_result(result, tier)
            coins += payout
            if replay:
                replays += 1
            rolls_complete += 1
        if coins in final_coins_dict.keys():
            final_coins_dict[coins] += 1
        else:
            final_coins_dict[coins] = 1
    result_str = "RESULTS:\n\n"
    result_str += "Total Simulations: " + str(number_of_simulations) + '\n'
    result_str += "Starting Coins: " + str(starting_coins) + '\n'
    result_str += "Max Rolls / Simulation: " + str(max_rolls) + '\n\n'
    less_than_100 = 0
    bw_100_500 = 0
    bw_500_1000 = 0
    greater_than_1000 = 0
    max_result = 0
    for final_amount, count in final_coins_dict.items():
        if final_amount > max_result:
            max_result = final_amount
        if final_amount < 100:
            less_than_100 += count
        elif 100 <= final_amount < 500:
            bw_100_500 += count
        elif 500 <= final_amount < 1000:
            bw_500_1000 += count
        elif final_amount > 1000:
            greater_than_1000 += count
    result_str += "< 100: " + str(less_than_100) + ' (' + str(less_than_100/number_of_simulations * 100) + '%)' + '\n'
    result_str += "100-499: " + str(bw_100_500) + ' (' + str(bw_100_500/number_of_simulations * 100) + '%)' + '\n'
    result_str += "500-999: " + str(bw_500_1000) + ' (' + str(bw_500_1000/number_of_simulations * 100) + '%)' + '\n'
    result_str += "\> 1000: " + str(greater_than_1000) + ' (' + str(greater_than_1000/number_of_simulations * 100) + '%)' + '\n\n'

    result_str += "Number reached max rolls: " + str(number_to_max_rolls) + '\n'
    result_str += "Max reached: " + str(max_result) + '\n'
    await inter.channel.send(result_str)


@bot.slash_command(name='game_corner', description='play slots at the game corner')
async def game_corner_command(inter):
    channel = inter.channel
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
        return
    else:
        await inter.send('Launching Game Corner...')
        message = await inter.original_message()
        await message.delete()

    if not 'Coins' in user.itemList.keys():
        await inter.send("Welcome to the Game Corner! To commemorate your arrival, you have been granted 100 Coins!", ephemeral=True)
        user.itemList['Coins'] = 100
        user.itemList['Game Corner Replay Tokens'] = 0
    elif user.getItemAmount('Coins') == 0:
        if user.getItemAmount('BP') >= 10:
                embed = discord.Embed(title='Would you like to buy 100 Coins for 10BP?', description='You have run out of coins!\nYou can buy more now, or try the game corner again later.')
                embed.set_footer(text="BP: " + str(user.getItemAmount('BP')))
                view = PokeNavComponents.ConfirmView(inter.author, "Buy 100 Coins for 10BP",
                                                     "Nevermind!", True)
                message = await channel.send(embed=embed, view=view)
                await view.wait()
                await message.delete()
                if view.confirmed:
                    if user.getItemAmount('BP') >= 10:
                        user.itemList['Coins'] += 100
                        user.itemList['BP'] -= 10
                    await inter.send("100 Coins purchased! Enjoy your time at the Game Corner!", ephemeral=True)
                else:
                    return
        else:
            await channel.send("You are out of Game Corner coins and do not have enough BP (10) to purchase more!")

    slots = Game_Corner.Slots()
    embed, file = slots.get_game_corner_embed(inter.author.name)
    view = Game_Corner.GameCornerView(inter.author.id)

    image_channel = bot.get_channel(slots.main_server_image_channel)
    #image_channel = bot.get_channel(slots.beta_server_image_channel)
    message = await channel.send(embed=embed, file=file, view=view)
    await view.wait()
    await message.delete()

    if view.slots and image_channel:
        # Chose slots as game
        embed, file = slots.get_slot_embed(inter.author.name, user)
        view = Game_Corner.RolledView(inter.author.id)
        if user.getItemAmount('Game Corner Replay Tokens') > 0:
            view.enable_replay_button()
        message = await channel.send(embed=embed, file=file, view=view)
        await view.wait()
        await message.delete()
        coins = view.coins
        while True:
            if coins > 0 or view.replay:
                # Chose to roll the slots, displaying gif
                if user.getItemAmount('Coins') < coins:
                    await channel.send("Sorry, you have run out of coins! Use `/game_corner` again to purchase more for 10BP.")
                    return
                if view.replay:
                    coins = 3
                    user.itemList['Game Corner Replay Tokens'] -= 1
                else:
                    user.itemList['Coins'] -= coins
                result = slots.roll()
                embed, file = slots.get_slot_roll_embed(inter.author.name, result)
                image_message = await image_channel.send(file=file)
                result_url = image_message.attachments[0]
                view = Game_Corner.RollingView(inter.author.id)
                message = await channel.send(embed=embed, view=view)
                await view.wait()

                if view.stopped:
                    # Stopped the spinning, switching to result
                    payout, replay, winning_string = slots.check_result(result, coins)
                    result_str = ''
                    if payout > 0:
                        result_str = 'WINNINGS (tier ' + str(coins) + '):\nCoins: ' + str(payout)
                        user.itemList['Coins'] += payout
                    else:
                        result_str = 'Sorry, please try again!'
                    if replay:
                        result_str += "\nREPLAY: 1"
                        user.itemList['Game Corner Replay Tokens'] += 1
                    if winning_string:
                        result_str += "\n\nBreakdown:\n" + winning_string
                    embed.set_image(url=result_url)
                    embed.set_footer(text=slots.get_footer_for_trainer(user) + '\n\n' + result_str)
                    view = Game_Corner.RolledView(inter.author.id)
                    if user.itemList['Game Corner Replay Tokens'] > 0:
                        view.enable_replay_button()
                    await message.edit(embed=embed, view=view)
                    await view.wait()
                    coins = view.coins
                    await message.delete()
                else:
                    break
            else:
                break


@bot.slash_command(name='zzz_start_raid', description='DEV ONLY: start a raid',
                   options=[Option("num_recent_users", description="optional, default = 0", type=OptionType.integer)],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def startRaidCommand(inter, numRecentUsers=0):
    global raidsEnabled
    if not await verifyDev(inter):
        return
    if not raidsEnabled:
        await inter.send("Raids are not enabled.")
        return
    raid = Raid(data, battleTower)
    if numRecentUsers > 0:
        started = await raid.startRaid(True, numRecentUsers)
    else:
        started = await raid.startRaid(True)
    if started:
        await data.setRaid(raid)
    await inter.send("Raid start command sent.")


@bot.slash_command(name='zzz_end_raid', description='DEV ONLY: end a raid',
                   options=[Option("success", description="optional, default = False")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def endRaidCommand(inter, success="False"):
    if not await verifyDev(inter):
        return
    if success.lower() == "true":
        success = True
    else:
        success = False
    if data.raid:
        await data.raid.endRaid(success)
    await inter.send("Raid end command sent.")


@bot.slash_command(name='zzz_remove_from_raid_list', description='DEV ONLY: remove user from raid list',
                   options=[Option("username", description="optional, default = self")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def removeFromRaidListCommand(inter, *, username='self'):
    if not await verifyDev(inter):
        return
    logging.debug(str(inter.author.id) + " - /remove_from_raid_list " + username)
    if data.raid:
        user = await getUserById(inter, username)
        if user:
            if data.raid.removeUserFromRaidList(user):
                await inter.send(user.name + " removed from raid list.")
            else:
                await inter.send("Failed to remove from raid list.")
        else:
            if username == 'self':
                username = str(inter.author)
            await inter.send("User '" + username + "' not found.")
    else:
        await inter.send("No raid active.")


@bot.slash_command(name='zzz_clear_raid_list', description='DEV ONLY: clears raid list',
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def clearRaidListCommand(inter):
    if not await verifyDev(inter):
        return
    if data.raid:
        data.raid.clearRaidList()
    await inter.send("Raid list cleared.")


@bot.slash_command(name='zzz_view_raid_list', description='DEV ONLY: view raid list',
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def viewRaidListCommand(inter):
    if not await verifyDev(inter):
        return
    messageStr = 'Raid List:\n\n'
    if data.raid:
        for user in data.raid.inRaidList:
            messageStr += str(user.identifier) + " - " + str(user.author) + '\n'
    n = 2000
    messageList = [messageStr[i:i + n] for i in range(0, len(messageStr), n)]
    for messageText in messageList:
        await inter.send(messageText)


@bot.slash_command(name='raid_info', description='see active raid information')
async def getRaidInfo(inter):
    logging.debug(str(inter.author.id) + " - /raid_info ")
    raidExpired = True
    if data.raid:
        raidExpired = await data.raid.hasRaidExpired()
    if raidExpired:
        await inter.send(
            "There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")
        return
    if data.raid:
        data.raid.addChannel(inter)
        files, embed = data.raid.createRaidInviteEmbed()
        await inter.send(files=files, embed=embed)
        # data.raid.addAlertMessage(alertMessage)
        user, isNewUser = data.getUser(inter)
        if user:
            if data.isUserInRaidList(user):
                await inter.send("You have already joined this raid.")
    else:
        await inter.send(
            "There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")


@bot.slash_command(name='zzz_raid_enable', description='DEV ONLY: enable/disable raids',
                   options=[Option("should_enable", description="optional, default = true")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def raidEnableCommand(inter, should_enable="true"):
    global raidsEnabled
    if not await verifyDev(inter):
        return
    if should_enable.lower() == 'true':
        raidsEnabled = True
        await inter.send("Raids are enabled.")
    elif should_enable.lower() == "false":
        raidsEnabled = False
        await inter.send("Raids are disabled.")
    else:
        await inter.send("Invalid 'should_enable' option. Must be true or false.")


@bot.slash_command(name='raid', description='join an active raid')
async def joinRaid(inter):
    logging.debug(str(inter.author.id) + " - /raid")
    await inter.send("Raid starting...")
    message = await inter.original_message()
    await message.delete()
    try:
        user, isNewUser = data.getUser(inter)
        if isNewUser:
            await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
        elif user.closed:
            await inter.send("Your account is closed, please contact support in the community server.")
        else:
            if data.raid and not data.raid.raidEnded:
                identifier = data.raid.identifier
                raidExpired = await data.raid.hasRaidExpired()
                if raidExpired:
                    await inter.send(
                        "There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")
                    return
                if data.isUserInRaidList(user):
                    await inter.send(
                        "You have already joined this raid. Use `/raid_info` to check on the raid's status.")
                    return
                if not user.checkFlag('elite4'):
                    await inter.send("Only trainers who have proven their worth against the elite 4 may take on raids.")
                    return
                data.raid.addChannel(inter.channel)
                data.updateRecentActivityDict(inter, user)
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
                await battle_ui.startBattleUI(inter, False, battle, 'BattleCopy', None, False, False, False)
                logging.debug(str(inter.author.id) + " - /raid - done with battle")
                if data.raid is not None and data.raid.identifier == identifier and not data.raid.raidEnded:
                    logging.debug(str(inter.author.id) + " - /raid - attempting to end raid")
                    try:
                        logging.debug(str(inter.author.id) + " - /raid - ending raid")
                        await data.raid.endRaid(True)
                        logging.debug(str(inter.author.id) + " - /raid - updating alert messages")
                        await data.raid.updateAlertMessages()
                    except:
                        logging.error("Error in /raid command, traceback = " + str(traceback.format_exc()))
                logging.debug(str(inter.author.id) + " - /raid - sending message = Your raid battle has ended.")
                await inter.send("Your raid battle has ended.")
            else:
                await inter.send(
                    "There is no raid currently active. Continue playing the game for a chance at a raid to spawn.")
    except:
        logging.error("Error in /raid command, traceback = " + str(traceback.format_exc()))
        # traceback.print_exc()


# @bot.command(name='stuck', help="fuck this")
# async def stuckCommand(inter, *, message=''):
#     global stuckList
#     if inter.author.id not in stuckList.keys():
#         stuckList[inter.author.id] = str(datetime.today()) + ' - ' + message
#         await inter.channel.send("Feedback received.")
#     else:
#         await inter.channel.send("You have already submitted a ticket.")
#
#
# @bot.command(name='stuckList', help="fuck this")
# async def stuckListCommand(inter):
#     global stuckList
#     if not await verifyDev(inter):
#         return
#     await inter.channel.send("Stuck List:")
#     await inter.channel.send(stuckList)
#
#
# @bot.command(name='clearStuckList', help="fuck this")
# async def clearStuckListCommand(inter):
#     global stuckList
#     if not await verifyDev(inter):
#         return
#     stuckList.clear()
#     await inter.channel.send("Stuck list cleared.")


@bot.slash_command(name='battle', description='battle an another user on the server',
                   options=[Option("username", description="leave blank to matchmake")],
                   )
async def battleTrainer(inter, *, username: str = "self"):
    logging.debug(str(inter.author.id) + " - /battle " + username)
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if data.isUserInSession(inter, user):
            await inter.send("Sorry " + str(
                inter.author.mention) + ", but you cannot battle another player while in an active session. Please end current session with `/end_session` or wait for it to timeout.")
        else:
            if username == 'self':
                if user in data.matchmakingDict:
                    await inter.send("You are already in a PVP battle.")
                    return
                await inter.send("Looking for match...")
                if len(data.matchmakingDict.keys()) == 0:
                    data.matchmakingDict[user] = (inter, False)
                    count = 0
                    while count < pvpTimeout:
                        if user in data.matchmakingDict:
                            matchStarted = data.matchmakingDict[user][1]
                            if matchStarted:
                                break
                        else:
                            break
                        if count == pvpTimeout / 2:
                            await inter.send("Still looking for match...")
                        await sleep(5)
                        count += 5
                    if count >= pvpTimeout:
                        try:
                            del data.matchmakingDict[user]
                        except:
                            pass
                        await inter.send("Matchmaking timed out. No opponent found.")
                else:
                    userToBattle = None
                    userToBattleCopy = None
                    inter2 = None
                    for tempUser, matchmakingTuple in data.matchmakingDict.items():
                        matchFoundAlready = matchmakingTuple[1]
                        if not matchFoundAlready:
                            data.matchmakingDict[tempUser] = (matchmakingTuple[0], True)
                            userToBattle = tempUser
                            userToBattleCopy = copy(tempUser)
                            inter2 = matchmakingTuple[0]
                            break
                    if userToBattleCopy is None or inter2 is None:
                        await inter.send("Matchmaking timed out. No opponent found.")
                        return
                    else:
                        await inter.send("Match found.")
                        await inter2.send("Match found.")
                        data.matchmakingDict[user] = (inter, True)
                    userCopy = copy(user)
                    userCopy.scaleTeam(None, 100)
                    userToBattleCopy.scaleTeam(None, 100)
                    userCopy.pokemonCenterHeal()
                    userToBattleCopy.pokemonCenterHeal()
                    userCopy.location = 'Petalburg Gym'
                    userToBattleCopy.location = 'Petalburg Gym'
                    inter1 = inter
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
                    ui1 = battle_ui1.startBattleUI(inter1, False, battle, '', None, False, True)
                    ui2 = battle_ui2.startBattleUI(inter2, False, battle, '', None, False, False)
                    await gather(ui1, ui2)
                    await inter1.send("Battle has ended.")
                    await inter2.send("Battle has ended.")
                    try:
                        del data.matchmakingDict[userToBattle]
                        del data.matchmakingDict[user]
                    except:
                        pass
            else:
                userToBattle = await getUserById(inter, username)
                if userToBattle:
                    if user.author != userToBattle.author:
                        serverPvpDict = data.getServerPVPDict(inter)
                        matchFound = False
                        for tempUser in list(serverPvpDict.keys()):
                            if tempUser.identifier == user.identifier:
                                if userToBattle.identifier == serverPvpDict[tempUser][0].identifier:
                                    matchFound = True
                                    await inter.send("Battle has been accepted. Starting battle...")
                                    await serverPvpDict[tempUser][1].send(
                                        "Battle has been accepted. Starting battle...")
                                    userCopy = copy(user)
                                    userToBattleCopy = copy(serverPvpDict[tempUser][0])
                                    userCopy.scaleTeam(None, 100)
                                    userToBattleCopy.scaleTeam(None, 100)
                                    userCopy.pokemonCenterHeal()
                                    userToBattleCopy.pokemonCenterHeal()
                                    userCopy.location = 'Petalburg Gym'
                                    userToBattleCopy.location = 'Petalburg Gym'
                                    inter1 = inter
                                    inter2 = serverPvpDict[tempUser][1]
                                    battle = Battle(data, userToBattleCopy, userCopy)
                                    battle.startBattle()
                                    battle.disableExp()
                                    battle.isPVP = True
                                    serverPvpDict[tempUser] = (
                                        serverPvpDict[tempUser][0], serverPvpDict[tempUser][1], True)
                                    battle_ui1 = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                                           startNewUI, continueUI, startPartyUI, startOverworldUI,
                                                           startBattleTowerUI, startCutsceneUI)
                                    battle_ui2 = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                                           startNewUI, continueUI, startPartyUI, startOverworldUI,
                                                           startBattleTowerUI, startCutsceneUI)
                                    ui1 = battle_ui1.startBattleUI(inter1, False, battle, '', None, False, True)
                                    ui2 = battle_ui2.startBattleUI(inter2, False, battle, '', None, False, False)
                                    await gather(ui1, ui2)
                                    await inter.send("Battle has ended.")
                                    await serverPvpDict[tempUser][1].send("Battle has ended.")
                                    if tempUser in serverPvpDict.keys():
                                        del serverPvpDict[tempUser]
                        if not matchFound:
                            match_started = False
                            serverPvpDict[userToBattle] = (user, inter, match_started)
                            await inter.send(
                                str(inter.author.mention) + " has requested a battle against " + username +
                                ". They have 2 minutes to respond.\n\n" + username +
                                ", to accept this battle, please type: '/battle " +
                                str(inter.author.mention) + "'.\nIt is recommended to do this in a separate channel so your opponent cannot see your move selection.")
                            await sleep(pvpTimeout)
                            if userToBattle in serverPvpDict.keys():
                                if not serverPvpDict[userToBattle][2]:
                                    del serverPvpDict[userToBattle]
                                    await inter.send(
                                        username + " did not respond to battle request. Please try again. If you would instead like to battle an NPC-controlled copy of this user, please use `!battleCopy @user`.")
                    else:
                        await inter.send("Cannot battle yourself.")
                else:
                    await inter.send("User '" + username + "' not found.")


@bot.slash_command(name='battle_copy', description='battle an NPC copy of another trainer',
                   options=[Option("username", description="person to battle a copy of", required=True)],
                   )
async def battleCopy(inter, *, username: str = "self"):
    logging.debug(str(inter.author.id) + " - /battle_copy " + username)
    await inter.send("Battle starting...")
    message = await inter.original_message()
    await message.delete()
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if data.isUserInSession(inter, user):
            await inter.send(
                "Sorry " + inter.author.display_name + ", but you cannot battle another player while in an active session. Please end your session with `/end_session`.")
        else:
            if username == 'self':
                await inter.send("Please @ a user to battle a copy of.\nExample: `!battleCopy @Zetaroid`")
            else:
                userToBattle = await getUserById(inter, username)
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
                        await startBeforeTrainerBattleUI(inter, False, battle, "BattleCopy")
                        await inter.send("Battle ended due to victory/loss or timeout.")
                    else:
                        await inter.send("Cannot battle yourself.")
                else:
                    await inter.send("User '" + username + "' not found.")


@bot.slash_command(name='end_session', description='ends the current session')
async def endSessionCommand(inter):
    logging.debug(str(inter.author.id) + " - !endSession - Command")
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        logging.debug(str(inter.author.id) + " - not ending session, have not started game yet")
        await inter.send("You have not yet played the game and have no active session! Please start with `/start`.")
    else:
        overworldTuple, isGlobal = data.userInOverworldSession(inter, user)
        if overworldTuple:
            try:
                message = overworldTuple[0]
                await message.delete()
                data.expiredSessions.append(overworldTuple[1])
                data.removeOverworldSession(inter, user)
            except:
                logging.error(
                    str(inter.author.id) + " - end session command had an error\n" + str(traceback.format_exc()))
                await sendDiscordErrorMessage(inter, traceback, str(str(
                    inter.author.id) + "'s end session command attempt had an error.\n" + str(
                    traceback.format_exc()))[-1999:])
            logging.debug(str(inter.author.id) + " - calling endSession() from endSessionCommand()")
            success = await endSession(inter)
            await inter.send("Session ending...")
            if not success:
                message = await inter.original_message()
                await message.delete()
        else:
            logging.debug(str(inter.author.id) + " - not ending session, not in overworld or not active session")
            await inter.send("You must be in the overworld in an active session to end a session.")


async def endSession(inter):
    logging.debug(str(inter.author.id) + " - endSession() called")
    user, isNewUser = data.getUser(inter)
    removedSuccessfully = data.removeUserSession(inter.guild.id, user)
    if (removedSuccessfully):
        logging.debug(str(inter.author.id) + " - endSession() session ended successfully, connection closed")
        await inter.channel.send(inter.author.display_name + "'s session ended. Please start game again with `/start`.")
    else:
        logging.debug(str(inter.author.id) + " - endSession() session unable to end, not in session list")
        await sendDiscordErrorMessage(inter, traceback,
                                      "Session unable to end, not in session list: " + str(inter.author.id))
    return removedSuccessfully


@bot.slash_command(name='view_base', description='view a trainers base',
                   options=[Option("username", description="person to view base, leave blank for personal")],
                   )
async def viewBaseCommand(inter, *, username: str = "self"):
    logging.debug(str(inter.author.id) + " - !viewBase " + username)
    user = await getUserById(inter, username)
    if username == 'self':
        username = str(inter.author)
    if user:
        if user.secretBase:
            await secretBaseUi.viewSecretBaseUI(inter, user)
        else:
            await inter.send(username + " does not have a secret base.")
    else:
        await inter.send("User '" + username + "' not found.")


@bot.slash_command(name='delete_base', description='delete a secret base')
async def deleteBaseCommand(inter):
    logging.debug(str(inter.author.id) + " - !deleteBase")
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        logging.debug(str(inter.author.id) + " - cannot delete base, have not started game yet")
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if data.isUserInSession(inter, user):
            await inter.send("Cannot delete base while in an active session. Please send session with `!endSession`.")
        else:
            if user.secretBase:
                for coords, itemList in user.secretBase.placedItems.items():
                    for item in itemList:
                        user.addSecretBaseItem(item.name, 1)
                user.secretBase = None
                await inter.send("Base deleted.")
            else:
                await inter.send("No base to delete.")


@bot.slash_command(name='secret_power', description='create a secret base',
                   options=[
                       Option("layout", description="choose the layout: enter 1, 2, 3, or 4", type=OptionType.integer)],
                   )
async def secretPowerCommand(inter, layout=''):
    logging.debug(str(inter.author.id) + " - !secretPower")
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        logging.debug(str(inter.author.id) + " - cannot create base, have not started game yet")
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if not data.isUserInSession(inter, user):
            logging.debug(str(inter.author.id) + " - not creating base, not in active session")
            await inter.send(
                "Sorry " + inter.author.display_name + ", but you cannot create a base without being in an active session. Please start a session with '/start'.")
        else:
            currentLocation = user.location
            locationObj = data.getLocation(currentLocation)
            if locationObj.secretBaseType:
                if user.secretBase:
                    await inter.send(
                        "You already have a secret base. Please delete this secret base with `!deleteBase` before creating a new one.")
                    return
                overworldTuple, isGlobal = data.userInOverworldSession(inter, user)
                if overworldTuple:
                    try:
                        message = overworldTuple[0]
                        await message.delete()
                        data.expiredSessions.append(overworldTuple[1])
                        data.removeOverworldSession(inter, user)
                    except:
                        logging.error(
                            str(inter.author.id) + " - creating a base had an error\n" + str(traceback.format_exc()))
                        await sendDiscordErrorMessage(inter, traceback, str(str(
                            inter.author.id) + "'s create base attempt had an error.\n" + str(
                            traceback.format_exc()))[-1999:])
                    logging.debug(str(inter.author.id) + " - creating base successful")
                    await inter.send(
                        inter.author.display_name + " created a new secret base! Traveling to base now.\n(continuing automatically in 4 seconds...)")
                    baseCreationMessage = await inter.original_message()
                    await sleep(4)
                    await baseCreationMessage.delete()
                    createNewSecretBase(user, locationObj, layout)
                    try:
                        await secretBaseUi.startSecretBaseUI(inter, user)
                    except discord.errors.Forbidden:
                        await forbiddenErrorHandle(inter)
                    except:
                        await sessionErrorHandle(inter, user, traceback)
                else:
                    logging.debug(str(inter.author.id) + " - not creating base, not in overworld")
                    await inter.send("Cannot create base while not in the overworld.")
            else:
                await inter.send("Cannot create a secret base in this location.")


def createNewSecretBase(user, locationObj, baseNum):
    baseType = locationObj.secretBaseType
    if baseNum and (baseNum == '1' or baseNum == '2' or baseNum == '3' or baseNum == '4'):
        randomBaseNum = baseNum
    else:
        randomBaseNum = random.randint(1, 4)
    baseType += "_" + str(randomBaseNum)
    myBase = Secret_Base(data, baseType, user.name + "'s Base", locationObj.name)
    user.secretBase = myBase


@bot.slash_command(name='fly', description='fly to a visited location',
                   options=[Option("location", description="name of location, leave blank to view list")],
                   )
async def fly(inter, *, location: str = ""):
    logging.debug(str(inter.author.id) + " - !fly " + location)
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        logging.debug(str(inter.author.id) + " - not flying, have not started game yet")
        await inter.send("You have not yet played the game and have no Pokemon! Please start with `/start`.")
    else:
        if 'fly' in user.flags:
            if not data.isUserInSession(inter, user):
                logging.debug(str(inter.author.id) + " - not flying, not in active session")
                await inter.send(
                    "Sorry " + inter.author.display_name + ", but you cannot fly without being in an active session. Please start a session with '/start'.")
            else:
                location = location.title()
                locationLower = location.lower()
                if locationLower in [item.lower() for item in list(user.locationProgressDict.keys())]:
                    if locationLower in [item.lower() for item in data.flyRestrictions['both']] or locationLower in [item.lower() for item in data.flyRestrictions['to']]:
                        logging.debug(str(inter.author.id) + " - not flying, cannot fly to this area!")
                        await inter.send("Sorry, cannot fly to this area!")
                    elif user.location.lower() in [item.lower() for item in data.flyRestrictions['both']]:
                        logging.debug(str(inter.author.id) + " - not flying, cannot fly from this area!")
                        await inter.send("Sorry, cannot fly from this area!")
                    else:
                        overworldTuple, isGlobal = data.userInOverworldSession(inter, user)
                        if overworldTuple:
                            try:
                                message = overworldTuple[0]
                                await message.delete()
                                data.expiredSessions.append(overworldTuple[1])
                                data.removeOverworldSession(inter, user)
                            except:
                                # traceback.print_exc()
                                logging.debug(
                                    str(inter.author.id) + " - flying had an error\n" + str(traceback.format_exc()))
                                await sendDiscordErrorMessage(inter, traceback, str(str(
                                    inter.author.id) + "'s fly attempt had an error.\n" + str(
                                    traceback.format_exc()))[-1999:])
                            logging.debug(str(inter.author.id) + " - flying starting")
                            try:
                                user.location = location
                                embed = discord.Embed(
                                    title=inter.author.display_name + " used Fly!\nTraveled to: " + location + '!',
                                    description='(continuing automatically in 4 seconds...)')
                                embed.set_thumbnail(url='https://i.imgur.com/0HLefSo.gif')
                                await inter.send(embed=embed)
                                # await inter.send(
                                #    inter.author.display_name + " used Fly! Traveled to: " + location + "!\n(continuing automatically in 4 seconds...)")
                                flyMessage = await inter.original_message()
                                await sleep(4)
                                await flyMessage.delete()
                                logging.debug(str(inter.author.id) + " - flying - calling startOverworldUI()")
                                await startOverworldUI(inter, user)
                            except discord.errors.Forbidden:
                                await forbiddenErrorHandle(inter)
                            except:
                                logging.debug(
                                    str(inter.author.id) + " - flying had an error (2)\n" + str(traceback.format_exc()))
                                await sessionErrorHandle(inter, user, traceback)
                                await inter.send("Sorry there was an error while flying. Please report this in the support channel of the community server. Use `/start` to continue playing.")
                        else:
                            logging.debug(str(inter.author.id) + " - not flying, not in overworld")
                            await inter.send("Cannot fly while not in the overworld.")
                else:
                    logging.debug(str(inter.author.id) + " - not flying, invalid location")
                    embed = discord.Embed(
                        title="Invalid location. Please try again with one of the following (exactly as spelled and capitalized):\n\n" + user.name + "'s Available Locations",
                        description="\n(try !fly again with '!fly [location]' from this list)", color=0x00ff00)
                    totalLength = 0
                    locationString = ''
                    for location in user.locationProgressDict.keys():
                        if location in data.flyRestrictions['both'] or location in data.flyRestrictions['to']:
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
                    await inter.send(embed=embed)
        else:
            logging.debug(str(inter.author.id) + " - not flying, have not earned 6th badge")
            await inter.send("Sorry, " + inter.author.display_name + ", but you have not learned how to Fly yet!")


@bot.slash_command(name='profile', description="get a Trainer's profile",
                   options=[Option("username", description="leave blank for self")],
                   )
async def profile(inter, *, username: str = "self"):
    logging.debug(str(inter.author.id) + " - !profile " + username)
    user = await getUserById(inter, username)
    if user:
        embed = createProfileEmbed(inter, user)
        await inter.send(embed=embed)
    else:
        if username == 'self':
            username = str(inter.author)
        await inter.send("User '" + username + "' not found.")


@bot.slash_command(name='trainer_card', description="get a Trainer's card",
                   options=[Option("username", description="leave blank for self")],
                   )
async def trainerCard(inter, *, username: str = "self"):
    logging.debug(str(inter.author.id) + " - !trainerCard " + username)
    user = await getUserById(inter, username)
    if user:
        filename, filenameBack = createTrainerCard(user)
        await inter.send(file=discord.File(filename))
        await inter.send(file=discord.File(filenameBack))
        try:
            os.remove(filename)
            os.remove(filenameBack)
        except:
            pass
    else:
        if username == 'self':
            username = str(inter.author)
        await inter.send("User '" + username + "' not found.")


@bot.slash_command(name='map', description="view the region map")
async def showMap(inter, region='hoenn'):
    logging.debug(str(inter.author.id) + " - !map")
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
    await inter.send(embed=embed, files=files)


@bot.slash_command(name='trade', description="trade with another user",
                   options=[Option("username", description="user to trade with", required=True)]
                   )
async def trade_command(inter, *, username):
    logging.debug(str(inter.author.id) + " - /trade " + username)
    userToTradeWith = await getUserById(inter, username)
    userTrading = await getUserById(inter, inter.author.id)
    trade = None

    try:
        if userToTradeWith is None:
            await inter.send("User '" + username + "' not found.")
        elif userTrading is None:
            await inter.send("You are not yet a trainer! Use '/start' to begin your adventure.")
        elif userTrading.closed:
            await inter.send("This account is closed, you cannot trade. Please contact support in the community server.")
        elif userToTradeWith.closed:
            await inter.send("The user you are trying to trade with has their account closed, you cannot trade.")
        elif userTrading.current_trade_id != 0 or userTrading.trade_requested_to:
            await inter.send("You are already waiting for a trade.")
        elif userToTradeWith.trade_requested_to:
            await inter.send("Trade partner is already involved in a trade.")
        elif data.isUserInSession(inter, userTrading):
            await inter.send("Please end your session with `/end_session` before trading.")
        elif (userTrading == userToTradeWith):
            await inter.send("You cannot trade with yourself!")
        else:
            await inter.send("Trade starting...")
            message = await inter.original_message()
            await message.delete()

            trade = Trade.Trade(inter.author, userTrading, userToTradeWith)
            userTrading.current_trade_id = trade.identifier
            userToTradeWith.trade_requested_to = True

            # User 1 Chooses Pokemon to Trade
            embed = Trade.ChooseTradePokemonEmbed(inter.author)
            view = Trade.ChooseTradePokemonView(userTrading)
            message = await inter.channel.send(embed=embed, view=view)
            try:
                res: MessageInteraction = await bot.wait_for(
                    "dropdown",
                    check=lambda m: m.author.id == inter.author.id,
                    timeout=60,
                )
                await res.response.defer()
            except asyncio.TimeoutError:
                trade_end(trade)
                return await inter.channel.send(
                    f"<@!{inter.author.id}> you didn't respond on time for selecting the Pokemon to trade!"
                )
            chosen_pokemon_id = view.select_menu.values[0]
            trade.pokemon_id_1 = chosen_pokemon_id

            await message.delete()

            # User 1 Confirms Pokemon to Trade
            embed = Trade.TradeConfirmSingleEmbed(bot, inter.author, userTrading, trade, True)
            view = Trade.TradeConfirmView(inter.author.id, True)
            message = await inter.channel.send(embed=embed, view=view, files=embed.files)
            await view.wait()
            await message.delete()

            if view.confirmed and not view.timed_out:

                # User 2 Confirms They Want to Trade
                embed = Trade.TradeConfirmSingleEmbed(bot, inter.author, userTrading, trade, False)
                view = Trade.TradeConfirmView(userToTradeWith.identifier, False)
                message = await inter.channel.send(embed=embed, view=view, files=embed.files)
                await view.wait()
                await message.delete()

                if data.isUserInSession(inter, userToTradeWith):
                    trade_end(trade)
                    return await inter.channel.send(f"<@!{view.author_2.id}> please end your session before trading!")

                if view.confirmed and not view.timed_out:
                    trade.author_2 = view.author_2
                    userToTradeWith.current_trade_id = trade.identifier

                    # User 2 Chooses the Pokemon to Trade
                    embed = Trade.ChooseTradePokemonEmbed(trade.author_2)
                    view = Trade.ChooseTradePokemonView(trade.user_2)
                    message = await inter.channel.send(embed=embed, view=view)
                    try:
                        res: MessageInteraction = await bot.wait_for(
                            "dropdown",
                            check=lambda m: m.author.id == trade.author_2.id,
                            timeout=60,
                        )
                        await res.response.defer()
                    except asyncio.TimeoutError:
                        trade_end(trade)
                        return await inter.channel.send(
                            f"<@!{trade.author_2.id}> you didn't respond on time for selecting the Pokemon to trade!"
                        )
                    chosen_pokemon_id = view.select_menu.values[0]
                    trade.pokemon_id_2 = chosen_pokemon_id
                    await message.delete()

                    # User 2 confirm trade
                    embed = Trade.TradeConfirmDoubleEmbed(bot, trade.author_2, trade.user_2, trade, False)
                    view = Trade.TradeConfirmView(trade.author_2.id, True)
                    message = await inter.channel.send(embed=embed, view=view, files=embed.files)
                    await view.wait()
                    await message.delete()

                    if view.confirmed and not view.timed_out:

                        # User 1 confirm trade
                        embed = Trade.TradeConfirmDoubleEmbed(bot, trade.author_1, trade.user_1, trade, False)
                        view = Trade.TradeConfirmView(trade.author_1.id, True)
                        message = await inter.channel.send(embed=embed, view=view, files=embed.files)
                        await view.wait()
                        await message.delete()

                        if view.confirmed:

                            # Trade complete
                            embed = Trade.TradeConfirmDoubleEmbed(bot, trade.author_1, trade.user_1, trade, True)
                            message = await inter.channel.send(embed=embed, files=embed.files)
                            success = trade.make_trade()
                            if not success:
                                await message.delete()
                                await inter.channel.send("There was an error while trading. ")
                        else:
                            await inter.channel.send("Trade cancelled.")
                    else:
                        await inter.channel.send("Trade cancelled.")
                else:
                    await inter.channel.send("Trade cancelled.")
            else:
                await inter.channel.send("Trade cancelled.")
    except:
        pass
    trade_end(trade)


def trade_end(trade):
    if trade:
        if trade.author_1:
            trade.user_1.current_trade_id = 0
            trade.user_2.trade_requested_to = False
        if trade.author_2:
            trade.user_2.current_trade_id = 0


@bot.slash_command(name='guide', description="view the game's guide")
async def getGuide(inter):
    guideMessage = 'Check out our full guide [HERE](https://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md#Guide)!'
    nextMessage = ''
    user = await getUserById(inter, 'self')
    if user:
        nextMessage += "```Guide:\n"
        if 'elite4' in user.flags:
            nextMessage += 'Congratulations league champion! You can now do the following:\n- Take part in raids (/raid)\n- Shiny hunt (1/200 odds) or look for rare Distortion Shinies (1/10k odds)\n- Catch gen 4-7 Pokemon in Altering Cave (costs 10 BP to alter the Pokemon in the cave with /set_altering_cave)\n- Catch legendaries (hint: see Slateport Harbor, Route 115, Route 127, Route 134, and Route 108)\n- Gym leader rematches (lv70 and lv100)\n- Take on a harder elite 4\n- Take on the battle tower to earn BP (go to Slateport Harbor and head to the Battle Frontier)\n- Create a secret base (/secret_power)\n- Buy Mega Stones and furniture in the /shop\n- And much more!'
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
    await inter.send(nextMessage + "\n\n" + guideMessage)


@bot.slash_command(name='move_info', description="get information about a move",
                   options=[Option("move_name", description="name of the move")],
                   )
async def getMoveInfo(inter, *, move_name="Invalid"):
    logging.debug(str(inter.author.id) + " - !getMoveInfo " + move_name)
    try:
        moveData = data.getMoveData(move_name.lower())
    except:
        moveData = None
    if moveData is not None:
        move_name = moveData['names']['en']
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
        result = '```Name: ' + move_name + '\nPower: ' + str(movePower) + '\nPP: ' + str(movePP) + '\nCategory: ' + str(
            moveCategory).title() + '\nAccuracy: ' + str(
            moveAcc) + '\nType: ' + moveType + '\nDescription: ' + moveDesc + '```'
        await inter.send(result)
    else:
        await inter.send('Invalid move')


@bot.slash_command(
    name="quests", description="View your active quests and claim rewards.")
async def quests_command(inter):
    trainer = await getUserById(inter, 'self')
    if trainer:
        embed = Quests.QuestListEmbed(bot, inter.author, trainer, 0)
        view = Quests.QuestListView(bot, inter.author, trainer, 0)
        await inter.send(embed=embed, view=view)
    else:
        await inter.send(
            "Sorry, you need to start the bot first! Use `/start` to begin."
        )
        return


@bot.slash_command(name='dex', description="get information about a Pokemon, leave blank for dex summary",
                   options=[Option("pokemon_name", description="name of the Pokemon"),
                            Option("form_number", description="number of desired form", type=OptionType.integer),
                            Option("shiny_or_distortion", description="enter 'shiny' or 'distortion' or 'altshiny'")],
                   )
async def dexCommand(inter, *, pokemon_name="", form_number="", shiny_or_distortion=""):
    user = await getUserById(inter, 'self')
    if pokemon_name:
        formNum = None
        shiny = False
        distortion = False
        altShiny = False
        if pokemon_name.lower().endswith(" shiny"):
            shiny = True
            pokemon_name = pokemon_name[:-6]
        if pokemon_name.lower().endswith(" distortion"):
            distortion = True
            pokemon_name = pokemon_name[:-11]
        if pokemon_name.lower().endswith(" altshiny"):
            altShiny = True
            pokemon_name = pokemon_name[:-9]
        if ' form ' in pokemon_name.lower():
            strList = pokemon_name.split(' ')
            formStr = strList[len(strList) - 1]
            formNum = int(formStr)
            pokemon_name = pokemon_name[:-(len(formStr) + 6)]
        if form_number:
            formNum = int(form_number)
        if shiny_or_distortion.lower() == 'shiny':
            shiny = True
        if shiny_or_distortion.lower() == 'distortion':
            distortion = True
        if shiny_or_distortion.lower() == 'altshiny':
            altShiny = True
        pokemon_name = pokemon_name.title()
        try:
            pokemon = Pokemon(data, pokemon_name, 100)
            if formNum:
                if formNum >= 0 and formNum <= len(pokemon.getFullData()['variations']):
                    pokemon.form = formNum
                    pokemon.updateForFormChange()
                else:
                    await inter.send("Invalid form number.")
                    return
            if altShiny and pokemon.name.lower() not in data.alternative_shinies['all']:
                await inter.send("This Pokemon does not have an alernative shiny form.")
                return
            files, embed = createPokemonDexEmbed(inter, pokemon, shiny, distortion, user, altShiny)
            embed.set_footer(
                text=f"Dex for {inter.author}\n" +
                     "Main: " + str(user.get_number_caught(data, "non-event")) + " / " + str(data.getNumberOfPokemon("non-event")) +
                     "\nEvent: " + str(user.get_number_caught(data, "event")) + " / " + str(data.getNumberOfPokemon("event")),
                icon_url=inter.author.display_avatar,
            )
            await inter.send(files=files, embed=embed)
        except:
            # traceback.print_exc()
            await inter.send(pokemon_name + " is not a valid Pokemon species.")
    else:
        completionStar = " ⭐"
        mainDex = "Main Dex: " + str(user.get_number_caught(data, "non-event")) + " / " + str(data.getNumberOfPokemon("non-event"))
        extraDex = "\nEvent Dex: " + str(user.get_number_caught(data, "event")) + " / " + str(data.getNumberOfPokemon("event"))
        gen1Caught = user.get_number_caught(data, "gen1")
        gen1Total = data.getNumberOfPokemonInGen(1)
        gen1Str = "Gen 1: " + str(gen1Caught) + " / " + str(gen1Total)
        if gen1Caught == gen1Total:
            gen1Str += completionStar
        gen2Caught = user.get_number_caught(data, "gen2")
        gen2Total = data.getNumberOfPokemonInGen(2)
        gen2Str = "\nGen 2: " + str(gen2Caught) + " / " + str(gen2Total)
        if gen2Caught == gen2Total:
            gen2Str += completionStar
        gen3Caught = user.get_number_caught(data, "gen3")
        gen3Total = data.getNumberOfPokemonInGen(3)
        gen3Str = "\nGen 3: " + str(gen3Caught) + " / " + str(gen3Total)
        if gen3Caught == gen3Total:
            gen3Str += completionStar
        gen4Caught = user.get_number_caught(data, "gen4")
        gen4Total = data.getNumberOfPokemonInGen(4)
        gen4Str = "\nGen 4: " + str(gen4Caught) + " / " + str(gen4Total)
        if gen4Caught == gen4Total:
            gen4Str += completionStar
        gen5Caught = user.get_number_caught(data, "gen5")
        gen5Total = data.getNumberOfPokemonInGen(5)
        gen5Str = "\nGen 5: " + str(gen5Caught) + " / " + str(gen5Total)
        if gen5Caught == gen5Total:
            gen5Str += completionStar
        gen6Caught = user.get_number_caught(data, "gen6")
        gen6Total = data.getNumberOfPokemonInGen(6)
        gen6Str = "\nGen 6: " + str(gen6Caught) + " / " + str(gen6Total)
        if gen6Caught == gen6Total:
            gen6Str += completionStar
        gen7Caught = user.get_number_caught(data, "gen7")
        gen7Total = data.getNumberOfPokemonInGen(7)
        gen7Str = "\nGen 7: " + str(gen7Caught) + " / " + str(gen7Total)
        if gen7Caught == gen7Total:
            gen7Str += completionStar
        gen8Caught = user.get_number_caught(data, "gen8")
        gen8Total = data.getNumberOfPokemonInGen(8)
        gen8Str = "\nGen 8: " + str(gen8Caught) + " / " + str(gen8Total)
        if gen8Caught == gen8Total:
            gen8Str += completionStar
        embed = discord.Embed(title="PokéDex Summary - " + str(inter.author),
                              description="```" + mainDex + extraDex + "```" + "\n```" + gen1Str + gen2Str + gen3Str + gen4Str + gen5Str + gen6Str + gen7Str + gen8Str +"```",
                              color=0x00ff00)
        file = discord.File("data/sprites/pokedex.png", filename="image.png")
        embed.set_image(url="attachment://image.png")
        embed.set_footer(
            text=f"Dex for {inter.author}\n",
            icon_url=inter.author.display_avatar,
        )
        await inter.send(embed=embed, file=file)


@bot.slash_command(name='enable_global_save', description='enables global save file for current server',
                   options=[Option("server_id", description="ID of server to enable for")])
async def enableGlobalSave(inter, server_id=''):
    logging.debug(str(inter.author.id) + " - !enableGlobalSave")
    user, isNewUser = data.getUser(inter)
    # if isNewUser:
    #     await inter.send("You have not yet played the game and have no Pokemon!")
    # else:
    if inter.author.id in data.globalSaveDict.keys():
        await inter.send(
            "You already have a global save. Please disable it with `!disableGlobalSave` before setting a new one.")
        return
    elif data.isUserInSession(inter, user):
        await inter.send("Please end your session with `!endSession` before enabling global save.")
        return
    elif user.current_trade_id != 0:
        await inter.send("Please end your trade before enabling global save.")
        return
    elif data.isUserInAnySession(user):
        await inter.send(
            "You have an active session in another server. Please end it in that server with `/end_session` before enabling global save.")
        return
    else:
        if server_id:
            try:
                server_id = int(server_id)
            except:
                server_id = inter.guild.id
        else:
            server_id = inter.guild.id
        data.globalSaveDict[inter.author.id] = (server_id, str(inter.author))
        await inter.send(
            "Global save enabled. The save file from this server will now be used on ALL servers you use the PokéNav bot in. To disable, use `!disableGlobalSave`.")


@bot.slash_command(name='disable_global_save', description='disables global save file')
async def disableGlobalSave(inter):
    logging.debug(str(inter.author.id) + " - !disableGlobalSave")
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        if data.isUserInSession(inter, user):
            await inter.send("Please end your session with `/end_session` before disabling global save.")
            return
        elif user.current_trade_id != 0:
            await inter.send("Please end your trade before disabling global save.")
            return
        if inter.author.id in data.globalSaveDict.keys():
            del data.globalSaveDict[inter.author.id]
            await inter.send(
                "Global save disabled. Each server you use the bot in will have a unique save file. To enable again, use `!enableGlobalSave` from the server you want to be your global save file.")
        else:
            await inter.send(
                "You do not have a global save to disable. Please enable it with `!enableGlobalSave` before attempting to disable.")


@bot.slash_command(name='change_form', description='changes the form of a Pokemon in your party',
                   options=[Option("party_number", description="# of Pokemon in your party", type=OptionType.integer,
                                   required=True),
                            Option("form_number", description="optional, form number to change to from /dex",
                                   type=OptionType.integer)])
async def toggleForm(inter, party_number, form_number=None):
    logging.debug(str(inter.author.id) + " - !toggleForm " + str(party_number))
    party_number = int(party_number) - 1
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        overworldTuple, isGlobal = data.userInOverworldSession(inter, user)
        if overworldTuple or not data.isUserInSession(inter, user):
            if (len(user.partyPokemon) > party_number):
                if form_number:
                    try:
                        form_number = int(form_number)
                    except:
                        await inter.send("Invalid form number.")
                    success, reason = user.partyPokemon[party_number].setForm(form_number, user)
                else:
                    success, reason = user.partyPokemon[party_number].toggleForm(user)
                if success:
                    await inter.send(
                        "'" + user.partyPokemon[party_number].nickname + "' changed form to " + user.partyPokemon[
                            party_number].getFormName() + "!")
                else:
                    await inter.send("'" + user.partyPokemon[party_number].name + "' cannot change form. " + reason)
            else:
                await inter.send("No Pokemon in that party slot.")
        else:
            logging.debug(str(inter.author.id) + " - not changing forms, not in overworld")
            await inter.send("Cannot change Pokemon forms while not in the overworld.")


@bot.slash_command(name='evolve', description='evolves a Pokemon capable of evolution',
                   options=[Option("party_number", description="# of Pokemon in your party", type=OptionType.integer,
                                   required=True),
                            Option("target_pokemon", description="optional, target Pokemon to evolve into")])
async def forceEvolve(inter, party_number, target_pokemon=None):
    logging.debug(str(inter.author.id) + " - !evolve " + str(party_number))
    party_number = int(party_number) - 1
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > party_number):
            oldName = user.partyPokemon[party_number].nickname
            success = user.partyPokemon[party_number].forceEvolve(target_pokemon)
            if success:
                await inter.send(oldName + " evolved into '" + user.partyPokemon[party_number].name + "'!")
            else:
                await inter.send("'" + user.partyPokemon[party_number].name + "' cannot evolve.")
        else:
            await inter.send("No Pokemon in that party slot.")


@bot.slash_command(name='unevolve', description='unevolves a Pokemon',
                   options=[Option("party_number", description="# of Pokemon in your party", type=OptionType.integer,
                                   required=True)])
async def unevolve(inter, party_number):
    logging.debug(str(inter.author.id) + " - !unevolve " + str(party_number))
    party_number = int(party_number) - 1
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > party_number):
            oldName = user.partyPokemon[party_number].nickname
            success = user.partyPokemon[party_number].unevolve()
            if success:
                await inter.send(oldName + " was reverted to '" + user.partyPokemon[party_number].name + "'!")
            else:
                await inter.send("'" + user.partyPokemon[party_number].name + "' cannot unevolve.")
        else:
            await inter.send("No Pokemon in that party slot.")


@bot.slash_command(name='search', description='search for box pokemon',
                   options=[Option("pokemon_name", description="name of Pokemon to search for", required=True)])
async def searchCommand(inter, *, pokemon_name=""):
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
    else:
        if pokemon_name:
            pokemon_name = pokemon_name.title()
            try:
                pokemon = Pokemon(data, pokemon_name, 100)
                files, embed = createSearchEmbed(inter, user, pokemon.name)
                await inter.send(files=files, embed=embed)
            except:
                # traceback.print_exc()
                await inter.send(pokemon_name + " is not a valid Pokemon species.")
        else:
            await inter.send("Invalid command input. Use `!search <Pokemon name>`.")


@bot.slash_command(name='super_train', description='super train a pokemon',
                   options=[Option("party_number", description="# of pokemon in party to train", required=True),
                            Option("level_100", description="Set to level 100? Enter: Yes or No", required=True),
                            Option("nature", description="Enter: Adamant, Modest, etc...", required=True),
                            Option("set_ivs", description="Set IV's to 31? Enter: Yes or No", required=True),
                            Option("hp_ev", description="HP EV? Enter: 0 to 252", required=True,
                                   type=OptionType.integer),
                            Option("atk_ev", description="ATK EV? Enter: 0 to 252", required=True,
                                   type=OptionType.integer),
                            Option("def_ev", description="DEF EV? Enter: 0 to 252", required=True,
                                   type=OptionType.integer),
                            Option("sp_atk_ev", description="SP ATK EV? Enter: 0 to 252", required=True,
                                   type=OptionType.integer),
                            Option("sp_def_ev", description="SP DEF EV? Enter: 0 to 252", required=True,
                                   type=OptionType.integer),
                            Option("speed_ev", description="SPEED EV? Enter: 0 to 252", required=True,
                                   type=OptionType.integer),
                            ]
                   )
async def super_train_command(inter, party_number, level_100, nature, set_ivs, hp_ev, atk_ev, def_ev, sp_atk_ev,
                              sp_def_ev, speed_ev):
    logging.debug(str(inter.author.id) + " - super_train_command()")
    user, isNewUser = data.getUser(inter)
    if isNewUser:
        await inter.send("You have not yet played the game and have no Pokemon!")
        return
    else:
        if not user.checkFlag('elite4'):
            await inter.send("You must beat the elite 4 to use super training!")
            return
        bpCost = 20
        possibleNatureList = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy",
                              "hasty",
                              "impish", "jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet",
                              "quirky",
                              "rash", "relaxed",
                              "sassy", "serious", "timid"]
        if 'BP' in user.itemList.keys():
            totalBp = user.itemList['BP']
            if totalBp >= bpCost:
                if level_100.lower() != "yes" and level_100.lower() != "no":
                    await inter.send('`level_100` argument must be `yes` or `no`.')
                    return
                if nature.lower() not in possibleNatureList:
                    await inter.send('`nature` argument must be from the following list of nature:\n' + '\n'.join(
                        possibleNatureList))
                    return
                if set_ivs.lower() != "yes" and set_ivs.lower() != "no":
                    await inter.send('`set_ivs` argument must be `yes` or `no`.')
                    return
                if hp_ev < 0 or hp_ev > 252:
                    await inter.send('`hp_ev` argument must be between 0 and 252.')
                    return
                if atk_ev < 0 or atk_ev > 252:
                    await inter.send('`atk_ev` argument must be between 0 and 252.')
                    return
                if def_ev < 0 or def_ev > 252:
                    await inter.send('`def_ev` argument must be between 0 and 252.')
                    return
                if sp_atk_ev < 0 or sp_atk_ev > 252:
                    await inter.send('`sp_atk_ev` argument must be between 0 and 252.')
                    return
                if sp_def_ev < 0 or sp_def_ev > 252:
                    await inter.send('`sp_def_ev` argument must be between 0 and 252.')
                    return
                if speed_ev < 0 or speed_ev > 252:
                    await inter.send('`speed_ev` argument must be between 0 and 252.')
                    return
                totalEV = hp_ev + atk_ev + def_ev + sp_atk_ev + sp_def_ev + speed_ev
                if totalEV > 510:
                    await inter.send("Total combined EV's cannot exceed 510, please try again. " + str(
                        inter.author.display_name) + "'s training session cancelled. BP refunded.")
                    return
                partyPos = int(party_number) - 1
                level100Prompt = "Advance to level 100?"
                naturePrompt = "Desired Nature:"
                ivPrompt = "Max all IV's?"
                hpEVPrompt = "Desired HP EV:"
                atkEVPrompt = "Desired ATK EV:"
                defEVPrompt = "Desired DEF EV:"
                spAtkEVPrompt = "Desired SP ATK EV:"
                spDefEVPrompt = "Desired SP DEF EV:"
                spdEVPrompt = "Desired SPD EV:"
                confirmPrompt = "Would you like to pay " + str(bpCost) + " BP and commit these changes?"
                promptList = {
                    level100Prompt: level_100,
                    naturePrompt: nature,
                    ivPrompt: set_ivs,
                    hpEVPrompt: hp_ev,
                    atkEVPrompt: atk_ev,
                    defEVPrompt: def_ev,
                    spAtkEVPrompt: sp_atk_ev,
                    spDefEVPrompt: sp_def_ev,
                    spdEVPrompt: speed_ev
                }
                pokemon = user.partyPokemon[partyPos]
                files, embed = createTrainEmbed(inter, pokemon)
                for key, value in promptList.items():
                    embed.add_field(name=key, value=str(value).upper())
                view = PokeNavComponents.ConfirmView(inter.author, "Commit Training for 20 BP", "Cancel", True)
                await inter.send(files=files, embed=embed, view=view)
                message = await inter.original_message()
                await view.wait()
                if view.confirmed:
                    if level_100.lower() == "yes":
                        pokemon.level = 100
                        pokemon.exp = pokemon.calculateExpFromLevel(100)
                    if set_ivs.lower() == "yes":
                        pokemon.hpIV = 31
                        pokemon.atkIV = 31
                        pokemon.defIV = 31
                        pokemon.spAtkIV = 31
                        pokemon.spDefIV = 31
                        pokemon.spdIV = 31
                    pokemon.hpEV = hp_ev
                    pokemon.atkEV = atk_ev
                    pokemon.defEV = def_ev
                    pokemon.spAtkEV = sp_atk_ev
                    pokemon.spDefEV = sp_def_ev
                    pokemon.spdEV = speed_ev
                    pokemon.nature = nature.lower()
                    pokemon.setStats()
                    if pokemon.currentHP > pokemon.hp:
                        pokemon.currentHP = pokemon.hp
                    user.useItem('BP', bpCost)
                    embed.set_footer(text="SUPER TRAINING SUCCESSFUL!")
                    await message.edit(embed=embed, view=None)
                else:
                    await inter.send("Super Training cancelled. BP refunded.")
            else:
                await inter.send("Not enough BP to Super Train. 20BP required.")
        else:
            await inter.send("Not enough BP to Super Train. 20BP required.")


@bot.slash_command(name='event', description='display current event')
async def eventCommand(inter):
    if data.eventActive:
        eventObj = data.eventDict[data.activeEvent]
        files, embed = createEventEmbed(eventObj.name)
        await inter.send(files=files, embed=embed)
    else:
        await inter.send("No active event.")


@bot.slash_command(name='zzz_start_event', description='DEV ONLY: starts a specified event',
                   options=[Option("event", description="name of event to start", required=True)],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def startEventCommand(inter, *, event):
    if not await verifyDev(inter):
        return
    try:
        event = int(event) - 1
        eventList = list(data.eventDict.keys())
        if event < len(eventList):
            await endEvent(inter)
            data.activeEvent = eventList[event]
            data.eventActive = True
            await inter.send("Event '" + data.activeEvent + "' started.")
    except:
        if event in data.eventDict.keys():
            await endEvent(inter)
            data.activeEvent = event
            data.eventActive = True
            await inter.send("Event '" + data.activeEvent + "' started.")
        else:
            await inter.send("Invalid event name. Use `!eventList` to see valid events.")


async def eventCheck(inter, user):
    if data.activeEvent in data.eventDict:
        eventObj = data.eventDict[data.activeEvent]
        if data.eventActive:
            if eventObj.item:
                if eventObj.item in user.itemList.keys() and user.itemList[eventObj.item] > 0:
                    return
                user.itemList[eventObj.item] = 1
            for quest in eventObj.quest_list:
                valid = True
                for user_quest in user.questList:
                    if quest.title == user_quest.title:
                        valid = False
                        break
                if quest.title in user.completedQuestList:
                    valid = False
                if valid:
                    quest_copy = copy(quest)
                    quest_copy.start()
                    user.questList.append(quest_copy)
            files, embed = createEventEmbed(eventObj.name)
            await inter.channel.send(files=files, embed=embed)


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


@bot.slash_command(name='zzz_end_event', description='DEV ONLY: ends current event',
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def endEventCommand(inter):
    if not await verifyDev(inter):
        return
    await endEvent(inter)


async def endEvent(inter, suppressMessage=False):
    if data.eventActive:
        eventObj = data.eventDict[data.activeEvent]
        eventItem = eventObj.item
        for server_id in data.userDict.keys():
            for user in data.userDict[server_id]:
                user.itemList[eventItem] = 0
        data.eventActive = False
        await inter.send("Event ended.")
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
        await inter.send("No event to end.")


@bot.slash_command(name='zzz_event_list', description='DEV ONLY: lists all events',
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def eventListCommand(inter):
    if not await verifyDev(inter):
        return
    eventStr = 'Events:\n\n'
    count = 1
    for eventName in data.eventDict.keys():
        eventStr += str(count) + ". " + eventName + "\n"
        count += 1
    await inter.send(eventStr)


@bot.slash_command(name='zzz_save', description='DEV ONLY: saves data, automatically disables bot auto save',
                   options=[Option("flag", description="enable/disable autosave, default = disable")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def saveCommand(inter, flag="disable"):
    global allowSave
    global saveLoopActive
    if not await verifyDev(inter):
        return
    logging.debug(str(inter.author.id) + " - !save " + flag)
    if flag == 'enable':
        if allowSave:
            await inter.send("Not saving data. Auto save is currently enabled, please disable to manually save.")
            return
        else:
            data.writeUsersToJSON()
            await sleep(5)
            if saveLoopActive:
                count = 0
                while count <= 120:
                    await inter.send(
                        "Save loop already active but autoSave=False edge case...waiting for 30 seconds and trying again...")
                    await sleep(30)
                    count += 30
                    if not saveLoopActive:
                        break
                if saveLoopActive:
                    await inter.send("Unable to start autosave.")
                    return
                else:
                    allowSave = True
                    await inter.send("Data saved.\nautoSave = " + str(allowSave))
                    await saveLoop()
            else:
                allowSave = True
                await inter.send("Data saved.\nautoSave = " + str(allowSave))
                await saveLoop()
            return
    elif flag == 'disable':
        await endEvent(inter, True)
        allowSave = False
        await sleep(5)
        data.writeUsersToJSON()
    await inter.send("Data saved.\nautoSave = " + str(allowSave))


@bot.slash_command(name='vote', description='vote for the bot')
async def voteCommand(inter):
    r = requests.get("https://top.gg/api/bots/800207357622878229/check", params={'userId': inter.author.id},
                     headers={'Authorization': TOPGG_TOKEN})
    user_voted = (r.json()["voted"] == 1)
    user, isNewUser = data.getUser(inter)
    if user_voted:
        if user.vote_reward_claimed:
            await inter.send("Thank you for voting!\nPlease come back again tomorrow for another reward!")
        else:
            user.last_vote = datetime.today().date()
            user.vote_reward_claimed = True
            user.addItem("BP", 1)
            await inter.send("Congratulations! You earned `1 BP` for voting!\nThank you for voting and please come back again tomorrow for another reward!")
    else:
        if user.ready_for_daily_vote():
            await inter.send(
                "Please support us by voting for PokeNav!\nUse `/vote` again after voting to claim your reward!\n\nhttps://top.gg/bot/800207357622878229/vote")
        else:
            await inter.send("Thank you for supporting PokeNav!\nYou cannot earn anymore rewards for voting today, but you can vote every 12 hours regardless. We appreciate the support!\n\nhttps://top.gg/bot/800207357622878229/vote")


@bot.slash_command(name='zzz_save_status', description='DEV ONLY: check status of autosave',
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def getSaveStatus(inter):
    global allowSave
    global saveLoopActive
    if not await verifyDev(inter):
        return
    await inter.send("allowSave = " + str(allowSave) + '\n' + 'saveLoopActive = ' + str(saveLoopActive))


@bot.slash_command(name='zzz_bag', description='DEV ONLY: display bag items',
                   options=[Option("username", description="user whos bag to view, default=self")],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def bagCommand(inter, *, username: str = "self"):
    if not await verifyDev(inter, False):
        return
    user = await getUserById(inter, username)
    newItemList = []
    for item, amount in user.itemList.items():
        if amount > 0:
            newItemList.append(item)
    files, embed = createBagEmbed(inter, user, newItemList)
    await inter.send(files=files, embed=embed)


@bot.slash_command(name='view_saves', description='view save files',
                   options=[Option("identifier", description="DEV ONLY INPUT")])
async def viewSavesCommand(inter, identifier="self"):
    saveList = []
    if identifier == 'self':
        identifier = inter.author.id
    else:
        if not await verifyDev(inter):
            return
        else:
            identifier = int(identifier)
    for server_id in data.userDict.keys():
        for user in data.userDict[server_id]:
            if user.identifier == identifier:
                partyString = "Party: "
                for pokemon in user.partyPokemon:
                    partyString += pokemon.name + ", "
                if partyString.endswith(", "):
                    partyString = partyString[:-2]
                elite4String = "Elite 4 Clear: "
                if user.checkFlag('elite4'):
                    elite4String += "Yes"
                else:
                    elite4String += "No"
                saveList.append('Server ID: ' + server_id + "\n" +
                                'Num Pokemon: ' + str(len(user.partyPokemon) + len(user.boxPokemon)) + "\n" +
                                partyString + "\n" +
                                elite4String +
                                '\n\n'
                                )
    saveString = "Saves for " + str(identifier) + ":\n\n" + ''.join(saveList)
    strList = splitStringForMaxLimit(saveString)
    for messageText in strList:
        await inter.send(messageText)


@bot.slash_command(name='zzz_test', description='DEV ONLY: test various features',
                   options=[Option("location", description="DEV ONLY INPUT"),
                            Option("progress", description="DEV ONLY INPUT", type=OptionType.integer)],
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def testWorldCommand(inter, location='Test', progress=0):
    if not await verifyDev(inter):
        return
    await inter.send("Starting test...")
    message = await inter.original_message()
    await message.delete()
    pokemonPairDict = {
        "Articuno": 65,
        "Zapdos": 100,
        "Moltres": 100,
        "Salamence": 100,
        "Lapras": 100,
        "Celebi": 100,
    }
    movesPokemon1 = [
        "Dragon Rage",
        "Hyper Beam",
        "Shadow Claw",
        "Toxic"
    ]
    flagList = ["rival1", "badge1", "badge2", "badge4", "briney"]
    trainer = Trainer(123, "Zetaroid", "Marcus", location)
    trainer.addItem("Masterball", 50)
    for pokemon, level in pokemonPairDict.items():
        pokemon = Pokemon(data, pokemon, level)
        pokemon.shadow = True
        pokemon.setSpritePath()
        trainer.addPokemon(pokemon, True)
    if len(movesPokemon1) > 0 and len(trainer.partyPokemon) > 0:
        moves = data.convertMoveList(movesPokemon1)
        trainer.partyPokemon[0].setMoves(moves)
    for flag in flagList:
        trainer.addFlag(flag)
    for x in range(0, progress):
        trainer.progress(location)
    await startOverworldUI(inter, trainer)


@bot.slash_command(name='zzz_test_base', description='DEV ONLY: test base features',
                   default_permission=False
                   )
@discord.ext.commands.guild_permissions(guild_id=805976403140542476, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=303282588901179394, users={189312357892096000: True})
@discord.ext.commands.guild_permissions(guild_id=951579318495113266, users={189312357892096000: True})
async def testBase(inter):
    if not await verifyDev(inter):
        return
    user, isNewUser = data.getUser(inter)

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

    await secretBaseUi.startSecretBaseUI(inter, user)


def splitStringForMaxLimit(str, n=2000):
    strList = [str[i:i + n] for i in range(0, len(str), n)]
    return strList


def addAllBaseItems(trainer):
    for key in data.secretBaseItems.keys():
        trainer.addSecretBaseItem(key, 100)


async def safeDeleteMessgae(message):
    try:
        await message.delete()
    except:
        pass


async def verifyDev(inter, sendMessage=True):
    if inter.author.id == 189312357892096000:
        return True
    else:
        user = await getUserById(inter, inter.author.id)
        if user:
            if 'developer' in user.flags:
                return True
        if sendMessage:
            await inter.send(
                str(inter.author.display_name) + ' does not have developer rights to use this command.')
        return False


async def getUserById(inter, userName, server_id=None, skip_global=False):
    if server_id is None:
        server_id = inter.guild.id
    if userName == 'self':
        user = data.getUserById(server_id, inter.author.id, skip_global)
    else:
        try:
            identifier = convertToId(userName)
            user = data.getUserById(server_id, identifier, skip_global)
        except:
            await inter.send("Please @ a user or enter ID.")
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


def createPokemonDexEmbed(inter, pokemon, shiny=False, distortion=False, trainer=None, altShiny=False):
    pokemon.shiny = False
    pokemon.distortion = False
    if shiny:
        pokemon.shiny = True
    if distortion:
        pokemon.shiny = True
        pokemon.distortion = True
    if altShiny and pokemon.name.lower() in data.alternative_shinies['all']:
        pokemon.altShiny = True
        pokemon.shiny = True
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
    if trainer:
        if pokemon.name in trainer.pokedex:
            title += " 📒"

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
                if 'Emerald' in games and (
                        encounterType == "Walking" or encounterType == "Surfing" or " Rod" in encounterType) and name == pokemon.name:
                    if location["names"]["en"] not in locationList and (
                            location["names"]["en"] + "*") not in locationList:
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
    heightWeightString = "\n\nHeight / Weight:\n" + str(pokemon.getFullData()['height_eu']) + " / " + str(
        pokemon.getFullData()['weight_eu'])
    catchrateString = "\n\nCatch Rate: (ranges 3 to 255)\n" + str(pokemon.getFullData()['catch_rate'])
    embed = discord.Embed(title=title,
                          description="```" + firstEntry + classificationString + locationString + heightWeightString + typeString + formString + evolutionString + evolvesFromString + catchrateString + "```",
                          color=0x00ff00)
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.add_field(name="----Base Stats----", value=(
            "```" + "HP:     " + str(pokemon.baseHP) + "\nATK:    " + str(pokemon.baseAtk) + "\nDEF:    " + str(
        pokemon.baseDef) + "\nSP ATK: " + str(pokemon.baseSpAtk) + "\nSP DEF: " + str(
        pokemon.baseSpDef) + "\nSPD:    " + str(pokemon.baseSpd) + "```"), inline=True)
    count = 0
    # embed.add_field(name='\u200b', value = '\u200b')
    # if trainer:
    #     if pokemon.name in trainer.pokedex:
    #         embed.set_footer(text=pokemon.name + " is registered in " + trainer.author + "'s Pokédex.")
    #     else:
    #         embed.set_footer(text=pokemon.name + " is not yet registered in " + trainer.author + "'s Pokédex.")
    return files, embed


def createPokemonSummaryEmbed(inter, pokemon):
    files = []
    title = ''
    if (pokemon.name == pokemon.nickname):
        title = pokemon.name
    else:
        title = pokemon.nickname + " (" + pokemon.name + ")"
    if pokemon.altShiny:
        title = title + ' :sparkles:'
    elif pokemon.distortion:
        title = title + ' :nazar_amulet:'
    elif pokemon.shiny:
        title = title + ' :star2:'
    if pokemon.shadow:
        title = title + ' :waxing_crescent_moon:'
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
                          description="```Type: " + typeString + "\n" + hpString + "\n" + levelString + "\n" + natureString + "\n" + happinessString + "\n" + genderString + "\n" + otString + formString + "\n" + caughtInString + "```" + '\n**---Status---**\n' + statusText + '\n\n**---EXP---**\n' + (
                                  "```" + "Total: " + str(pokemon.exp) + "\nTo next level: " + str(
                              pokemon.calculateExpToNextLevel()) + "```"),
                          color=0x00ff00)
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
    # embed.add_field(name='---Level---', value=str(pokemon.level), inline=True)
    # embed.add_field(name='-----OT-----', value=pokemon.OT, inline=True)
    # embed.add_field(name='---Dex Num---', value=pokemon.getFullData()['hoenn_id'], inline=True)
    # embed.add_field(name='---Nature---', value=pokemon.nature.capitalize(), inline=True)
    # embed.add_field(name='---Status---', value=statusText, inline=True)
    # embed.add_field(name='---EXP---', value=("```" + "Total: " + str(pokemon.exp) + "\nTo next level: " + str(pokemon.calculateExpToNextLevel()) + "```"), inline=True)
    embed.add_field(name="----Stats----", value=(
            "```" + "HP:     " + str(pokemon.hp) + "\nATK:    " + str(pokemon.attack) + "\nDEF:    " + str(
        pokemon.defense) + "\nSP ATK: " + str(pokemon.special_attack) + "\nSP DEF: " + str(
        pokemon.special_defense) + "\nSPD:    " + str(pokemon.speed) + "```"), inline=True)
    embed.add_field(name="-----IV's-----", value=(
            "```" + "HP:     " + str(pokemon.hpIV) + "\nATK:    " + str(pokemon.atkIV) + "\nDEF:    " + str(
        pokemon.defIV) + "\nSP ATK: " + str(pokemon.spAtkIV) + "\nSP DEF: " + str(
        pokemon.spDefIV) + "\nSPD:    " + str(pokemon.spdIV) + "```"), inline=True)
    embed.add_field(name="-----EV's-----", value=(
            "```" + "HP:     " + str(pokemon.hpEV) + "\nATK:    " + str(pokemon.atkEV) + "\nDEF:    " + str(
        pokemon.defEV) + "\nSP ATK: " + str(pokemon.spAtkEV) + "\nSP DEF: " + str(
        pokemon.spDefEV) + "\nSPD:    " + str(pokemon.spdEV) + "```"), inline=True)
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
        if count + 1 == 3:
            embed.add_field(name='\u200b', value='\u200b')
        embed.add_field(name=('-----Move ' + str(count + 1) + '-----'), value=(
                "```" + "Name: " + move['names']['en'] + "\nCat:  " + move['category'].capitalize() + "\nType: " +
                move['type'] + " " + bp + acc + "\nPP:   " + str(pokemon.pp[count]) + "/" + str(
            move['pp']) + " pp" + "```"), inline=True)
        count += 1
    embed.add_field(name='\u200b', value='\u200b')
    embed.set_author(name=(inter.author.display_name + "'s Pokemon Summary:"))
    # brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    # files.append(brendanImage)
    # embed.set_thumbnail(url="attachment://image2.png")
    return files, embed


def createPartyUIEmbed(inter, trainer, isBoxSwap=False, itemToUse=None, replacementTitle=None, replacementDesc=None):
    files = []
    if replacementDesc is not None and replacementTitle is not None:
        embed = discord.Embed(title=replacementTitle, description=replacementDesc, color=0x00ff00)
    elif isBoxSwap:
        embed = discord.Embed(title="CHOOSE POKEMON TO SEND TO BOX:",
                              description="[react to # to choose Pokemon to send to box]", color=0x00ff00)
    elif (itemToUse is not None):
        embed = discord.Embed(title="CHOOSE POKEMON TO USE " + itemToUse.upper() + " ON:",
                              description="[react to # to use item on Pokemon]", color=0x00ff00)
    else:
        embed = discord.Embed(title="Party Summary", description="[react to # to view individual summary]",
                              color=0x00ff00)
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
        if pokemon.altShiny:
            shinyString = ' :sparkles:'
        elif pokemon.distortion:
            shinyString = ' :nazar_amulet:'
        elif pokemon.shiny:
            shinyString = ' :star2:'
        shadowString = ""
        if pokemon.shadow:
            shadowString = ' :waxing_crescent_moon:'
        embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")" + shinyString + shadowString,
                        value=embedValue, inline=False)
        count += 1
    embed.set_author(name=(inter.author.display_name))
    # brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    # files.append(brendanImage)
    # embed.set_thumbnail(url="attachment://image.png")
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
    elif (category == "Badges"):
        if trainer is not None:
            for item in trainer.itemList.keys():
                if "Badge" in item and item not in ballItems and item not in healthItems and item not in statusItems and item != "money" and item != "BP":
                    items.append(item)
    elif (category == "HM's"):
        if trainer is not None:
            for item in trainer.itemList.keys():
                if "HM " in item and item not in ballItems and item not in healthItems and item not in statusItems and item != "money" and item != "BP" and "Badge" not in item:
                    items.append(item)
    elif (category == "Mega Stones"):
        if trainer is not None:
            for item in trainer.itemList.keys():
                if "Stone" in item and item not in ballItems and item not in healthItems and item not in statusItems and item != "money" and item != "BP" and "Badge" not in item:
                    items.append(item)
    elif (category == "Dynamax Crystals"):
        if trainer is not None:
            for item in trainer.itemList.keys():
                if "Crystal" in item and item not in ballItems and item not in healthItems and item not in statusItems and item != "money" and item != "BP" and "Badge" not in item:
                    items.append(item)
    elif (category == "Other Items"):
        if trainer is not None:
            for item in trainer.itemList.keys():
                # print(item)
                if "HM " not in item and "Stone" not in item and "Crystal" not in item and item not in ballItems and item not in healthItems and item not in statusItems and item != "money" and item != "BP" and "Badge" not in item:
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
            pokemonPathDict[index + 1] = (
                trainer.partyPokemon[index].getSpritePath(), trainer.partyPokemon[index].level)
    background = Image.open(backgroundPath)
    backgroundBack = Image.open(backgroundPathBack)
    background = background.convert('RGBA')
    backgroundBack = backgroundBack.convert('RGBA')
    trainerSpritePath = trainer.sprite
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
    dex_overlay = Image.open('data/sprites/dex_overlay.png')
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
    d.text((310, 40), trainer.author, font=fnt, fill=(0, 0, 0))
    d_back = ImageDraw.Draw(backgroundBack)
    d_back.text((310, 40), trainer.author, font=fnt, fill=(0, 0, 0))
    fnt = ImageFont.truetype('data/fonts/pokemonGB.ttf', 12)
    d_back.text((20, 80), getProfileDescStr(trainer), font=fnt,
                fill=(255, 255, 255))
    if trainer.get_number_caught(data, "non-event") == data.getNumberOfPokemon("non-event"):
        background.paste(dex_overlay, (0, 0), dex_overlay.convert('RGBA'))
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


async def resolveWorldCommand(inter, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox,
                              goToBag, goToMart, goToParty, battle, goToTMMoveTutor, goToLevelMoveTutor,
                              goToBattleTower, withRestrictions, goToSuperTraining, goToSecretBase):
    embed = newEmbed
    if (reloadArea):
        await safeDeleteMessgae(message)
        await startOverworldUI(inter, trainer)
    elif (goToBox):
        await safeDeleteMessgae(message)
        await startBoxUI(inter, trainer, trainer.lastBoxNum, 'startOverworldUI', dataTuple)
    elif (goToBag):
        await safeDeleteMessgae(message)
        await startBagUI(inter, trainer, 'startOverworldUI', dataTuple)
    elif (goToMart):
        await safeDeleteMessgae(message)
        await startMartUI(inter, trainer, 'startOverworldUI', dataTuple)
    elif (goToParty):
        await safeDeleteMessgae(message)
        await startPartyUI(inter, trainer, 'startOverworldUI', None, dataTuple)
    elif (goToTMMoveTutor):
        await safeDeleteMessgae(message)
        await startMoveTutorUI(inter, trainer, 0, True, 0, 'startOverworldUI', dataTuple)
    elif (goToLevelMoveTutor):
        await safeDeleteMessgae(message)
        await startMoveTutorUI(inter, trainer, 0, False, 0, 'startOverworldUI', dataTuple)
    elif (goToSuperTraining):
        pass
    elif (battle is not None):
        battle.startBattle(trainer.location)
        await safeDeleteMessgae(message)
        if not battle.isWildEncounter:
            await startBeforeTrainerBattleUI(inter, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
        else:
            battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                  startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
            await battle_ui.startBattleUI(inter, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
    elif (goToBattleTower):
        await safeDeleteMessgae(message)
        await startBattleTowerSelectionUI(inter, trainer, withRestrictions)
    elif goToSecretBase:
        await safeDeleteMessgae(message)
        await secretBaseUi.startSecretBaseUI(inter, trainer)


def executeWorldCommand(inter, trainer, command, embed):
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
        logging.debug(str(inter.author.id) + " - executeWorldCommand(), command[0] = " + str(command[0]))
    except:
        pass
    if (command[0] == "party"):
        goToParty = True
    elif (command[0] == "bag"):
        goToBag = True
    elif (command[0] == "progress"):
        if (trainer.dailyProgress > 0 or not data.staminaDict[str(inter.guild.id)]):
            # if (data.staminaDict[str(inter.guild.id)]):
            #     trainer.dailyProgress -= 1
            # trainer.progress(trainer.location) # HERE
            currentProgress = trainer.checkProgress(trainer.location)
            locationDataObj = data.getLocation(trainer.location)
            event = locationDataObj.getEventForProgress(currentProgress + 1)
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
                            if (data.staminaDict[str(inter.guild.id)]):
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
        if (trainer.dailyProgress > 0 or not data.staminaDict[str(inter.guild.id)]):
            if (data.staminaDict[str(inter.guild.id)]):
                trainer.dailyProgress -= 1
            locationDataObj = data.getLocation(trainer.location)
            if (locationDataObj.hasWildEncounters):
                battle = Battle(data, trainer, None, locationDataObj.entryType)
        else:
            embed.set_footer(text=footerText + "\n\nOut of stamina for today! Please come again tomorrow!")
            embedNeedsUpdating = True
    elif (command[0] == "heal"):
        trainer.pokemonCenterHeal()
        embed.set_footer(text=footerText + "\n\nNURSE JOY:\nYour Pokemon were healed! We hope to see you again!")
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
        pass
    elif (command[0] == "travel"):
        trainer.location = command[1]
        reloadArea = True
    elif (command[0] == "secretBase"):
        goToSecretBase = True
    elif (command[0] == "legendaryPortal"):
        if trainer.dailyProgress > 0 or not data.staminaDict[str(inter.guild.id)]:
            if (data.staminaDict[str(inter.guild.id)]):
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
                if data.staminaDict[str(inter.guild.id)]:
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


def createOverworldEmbed(inter, trainer):
    overWorldCommands = {}
    files = []
    locationName = trainer.location
    locationObj = data.getLocation(locationName)
    progressRequired = locationObj.progressRequired
    progressText = ''
    if (progressRequired > 0 and trainer.checkProgress(locationName) < progressRequired):
        progressText = progressText + 'Progress: ' + str(trainer.checkProgress(locationName)) + ' / ' + str(
            progressRequired)
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
    footerText = '[use the buttons below to play]'
    if locationObj.desc is not None:
        footerText += '\n' + locationObj.desc
    embed.set_footer(text=footerText)
    # if data.staminaDict[str(inter.guild.id)]:
    #     embed.set_author(name=(inter.author.display_name + " is exploring the world:\n(remaining stamina: " + str(
    #         trainer.dailyProgress) + ")"))
    # else:
    embed.set_author(name=(inter.author.display_name + " is exploring the world:"))

    optionsText = ''
    buttonList = []
    count = 1
    optionsText = optionsText + "(" + str(count) + ") Party\n"
    buttonList.append(PokeNavComponents.OverworldUIButton(label="Party", style=discord.ButtonStyle.green, row=0,
                                                          info='party', identifier=count))
    overWorldCommands[count] = ('party',)
    count += 1
    optionsText = optionsText + "(" + str(count) + ") Bag\n"
    buttonList.append(PokeNavComponents.OverworldUIButton(label="Bag", style=discord.ButtonStyle.green, row=0,
                                                          info='bag', identifier=count))
    overWorldCommands[count] = ('bag',)
    count += 1
    if (locationObj.hasPokemonCenter):
        optionsText = optionsText + "(" + str(count) + ") Heal at Pokemon Center\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Heal at Pokémon Center", style=discord.ButtonStyle.green, row=0,
                                                info='heal', identifier=count))
        overWorldCommands[count] = ('heal',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Access the Pokemon Storage System\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Pokémon Storage", style=discord.ButtonStyle.green, row=0,
                                                info='box', identifier=count))
        overWorldCommands[count] = ('box',)
        count += 1
    if (locationObj.hasMart):
        if locationName == "Battle Frontier":
            optionsText = optionsText + "(" + str(count) + ") Shop at Battle Frontier Mart\n"
            buttonList.append(
                PokeNavComponents.OverworldUIButton(label="Battle Frontier Mart", style=discord.ButtonStyle.green,
                                                    row=0,
                                                    info='mart', identifier=count))
        else:
            optionsText = optionsText + "(" + str(count) + ") Shop at Pokemart\n"
            buttonList.append(
                PokeNavComponents.OverworldUIButton(label="Poké Mart", style=discord.ButtonStyle.green, row=0,
                                                    info='mart', identifier=count))
        overWorldCommands[count] = ('mart',)
        count += 1
    if (locationObj.hasSuperTraining):
        pass
    if (locationObj.hasMoveTutor):
        optionsText = optionsText + "(" + str(count) + ") Use Move Tutor (TM's)\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Move Tutor (TM)", style=discord.ButtonStyle.grey, row=1,
                                                info='tmMoveTutor', identifier=count))
        overWorldCommands[count] = ('tmMoveTutor',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Use Move Tutor (Level Up Moves)\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Move Tutor (Lv Up)", style=discord.ButtonStyle.grey, row=1,
                                                info='levelMoveTutor', identifier=count))
        overWorldCommands[count] = ('levelMoveTutor',)
        count += 1
    if (trainer.checkProgress(locationName) < progressRequired):
        optionsText = optionsText + "(" + str(count) + ") Make progress\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Make Progress", style=discord.ButtonStyle.green, row=1,
                                                info='progress', identifier=count))
        overWorldCommands[count] = ('progress',)
        count += 1
    else:
        locationDataObj = data.getLocation(trainer.location)
        if (locationDataObj.hasWildEncounters):
            optionsText = optionsText + "(" + str(count) + ") Wild Encounter\n"
            buttonList.append(
                PokeNavComponents.OverworldUIButton(label="Wild Encounter", style=discord.ButtonStyle.green, row=1,
                                                    info='wildEncounter', identifier=count))
            overWorldCommands[count] = ('wildEncounter',)
            count += 1
    if (locationObj.isBattleTower):
        optionsText = optionsText + "(" + str(count) + ") Normal Challenge (with Restrictions)\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Normal Challenge", style=discord.ButtonStyle.grey, row=1,
                                                info='battleTowerR', identifier=count))
        overWorldCommands[count] = ('battleTowerR',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Legendary Challenge (no Restrictions)\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Legendary Challenge", style=discord.ButtonStyle.grey, row=1,
                                                info='battleTowerNoR', identifier=count))
        overWorldCommands[count] = ('battleTowerNoR',)
        count += 1
    if (locationObj.hasLegendaryPortal):
        optionsText = optionsText + "(" + str(count) + ") Explore Mysterious Portal\n"
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="Explore Mysterious Portal", style=discord.ButtonStyle.grey,
                                                row=1,
                                                info='legendaryPortal', identifier=count))
        overWorldCommands[count] = ('legendaryPortal',)
        count += 1
    row = 2
    number_in_row_2 = 0
    if locationObj.secretBaseType and trainer.secretBase:
        if trainer.secretBase.location == locationObj.name:
            optionsText = optionsText + "(" + str(count) + ") Enter Secret base\n"
            buttonList.append(
                PokeNavComponents.OverworldUIButton(label="Enter Secret Base", style=discord.ButtonStyle.grey, row=row,
                                                    info='secretBase', identifier=count))
            number_in_row_2 += 1
            overWorldCommands[count] = ('secretBase',)
            count += 1
    for nextLocationName, nextLocationObj in locationObj.nextLocations.items():
        if number_in_row_2 >= 5:
            row = 3
        if (nextLocationObj.checkRequirements(trainer)):
            optionsText = optionsText + "(" + str(count) + ") Travel to " + nextLocationName + "\n"
            buttonList.append(PokeNavComponents.OverworldUIButton(label="Travel to: " + nextLocationName,
                                                                  style=discord.ButtonStyle.blurple, row=row,
                                                                  info='travel,' + nextLocationName, identifier=count))
            number_in_row_2 += 1
            overWorldCommands[count] = ('travel', nextLocationName)
            count += 1

    # embed.add_field(name='Options:', value=optionsText, inline=True)
    return files, embed, overWorldCommands, buttonList


def resetAreas(trainer):
    currentLocation = trainer.location
    areas = ['Sky Pillar Top 2', 'Forest Ruins', 'Desert Ruins', 'Island Ruins', 'Marine Cave', 'Terra Cave',
             'Northern Island',
             'Southern Island', 'Faraway Island', 'Birth Island', 'Naval Rock 1', 'Naval Rock 2', 'Lake Verity Cavern',
             "Agate Village Shrine",
             "Galar Slumbering Weald Inner 1", "Galar Slumbering Weald Inner 2",
             "Dragon Split Decision Ruins", "Electric Split Decision Ruins", "Energy Plant", "Ghost Crown Shrine",
             "Ice Crown Shrine", "King Crown Shrine", "Jungle", "Master Dojo", "Ancient Retreat Grove",
             "Viridian Gym Secret Room Event", "Pokemon Mansion Event"]
    elite4Areas = ['Elite 4 Room 1', 'Elite 4 Room 2', 'Elite 4 Room 3', 'Elite 4 Room 4', 'Champion Room',
                   'Elite 4 Room 1 Lv70', 'Elite 4 Room 2 Lv70', 'Elite 4 Room 3 Lv70', 'Elite 4 Room 4 Lv70',
                   'Champion Room Lv70',
                   'Elite 4 Room 1 Lv100', 'Elite 4 Room 2 Lv100', 'Elite 4 Room 3 Lv100', 'Elite 4 Room 4 Lv100',
                   'Champion Room Lv100']
    for area in areas:
        if area in trainer.locationProgressDict.keys():
            trainer.locationProgressDict[area] = 0
    if currentLocation not in elite4Areas:
        for area in elite4Areas:
            if area in trainer.locationProgressDict.keys():
                trainer.locationProgressDict[area] = 0


def createSearchEmbed(inter, trainer, pokemonName):
    files = []
    embed = discord.Embed(title="Search Results", description="for '" + pokemonName + "'", color=0x00ff00)
    boxCount = 1
    count = 1
    for pokemon in trainer.partyPokemon:
        if count > 24:
            break
        if pokemon.name.lower() == pokemonName.lower():
            hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
            levelString = "Level: " + str(pokemon.level)
            shinyString = ""
            if pokemon.altShiny:
                shinyString = ' :sparkles:'
            elif pokemon.distortion:
                shinyString = ' :nazar_amulet:'
            elif pokemon.shiny:
                shinyString = ' :star2:'
            shadowString = ""
            if pokemon.shadow:
                shadowString = ' :waxing_crescent_moon:'
            embed.add_field(name="[Party] " + pokemon.nickname + " (" + pokemon.name + ")" + shinyString + shadowString,
                            value=levelString + "\n" + hpString, inline=True)
            count += 1
    for pokemon in trainer.boxPokemon:
        if count > 24:
            break
        if pokemon.name.lower() == pokemonName.lower():
            hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
            levelString = "Level: " + str(pokemon.level)
            shinyString = ""
            if pokemon.altShiny:
                shinyString = ' :sparkles:'
            elif pokemon.distortion:
                shinyString = ' :nazar_amulet:'
            elif pokemon.shiny:
                shinyString = ' :star2:'
            shadowString = ""
            if pokemon.shadow:
                shadowString = ' :waxing_crescent_moon:'
            embed.add_field(name="[Box " + str(
                math.ceil(boxCount / 9)) + "] " + pokemon.nickname + " (" + pokemon.name + ")" + shinyString + shadowString,
                            value=levelString + "\n" + hpString, inline=True)
            count += 1
        boxCount += 1
    if count > 24:
        embed.add_field(name="NOTE:", value="Search exceeded limits.", inline=True)
    embed.set_author(name=(inter.author.display_name))
    return files, embed


def createBoxEmbed(inter, trainer, offset):
    files = []
    embed = discord.Embed(title="Box " + str(offset + 1), description="[react to # to view individual summary]",
                          color=0x00ff00)
    count = 1
    for x in range(offset * 9, offset * 9 + 9):
        try:
            pokemon = trainer.boxPokemon[x]
            hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
            levelString = "Level: " + str(pokemon.level)
            shinyString = ""
            if pokemon.altShiny:
                shinyString = ' :sparkles:'
            elif pokemon.distortion:
                shinyString = ' :nazar_amulet:'
            elif pokemon.shiny:
                shinyString = ' :star2:'
            shadowString = ""
            if pokemon.shadow:
                shadowString = ' :waxing_crescent_moon:'
            embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")" + shinyString + shadowString,
                            value=levelString + "\n" + hpString, inline=True)
            count += 1
        except:
            embed.add_field(name="----Empty Slot----", value="\u200b", inline=True)
    embed.set_author(name=(inter.author.display_name))
    embed.set_footer(text="(dropdown menu shows nearest 24 boxes)")
    # brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    # files.append(brendanImage)
    # embed.set_thumbnail(url="attachment://image.png")
    return files, embed


def createMartEmbed(inter, trainer, itemDict):
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
            embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')) + "\nCurrent Buy Quantity: 1")
        embed.add_field(name="(" + str(count) + ") " + item, value=prefix + str(price) + suffix, inline=True)
        count += 1
    embed.set_author(name=inter.author.display_name + " is shopping:")
    return files, embed


def createShopEmbed(inter, trainer, categoryList=None, category='', itemList=None, isFurniture=False, includeTrainerIcons=False):
    files = []
    furnitureAddition = ''
    if isFurniture:
        furnitureAddition = '\n- To preview furniture, use `!preview [item name]`.'
    if category:
        category = ' - ' + category.title()
    embed = discord.Embed(title="Premium PokeMart" + category,
                          description="- To view a category, use `/shop [category]`.\n- To make a purchase, use `/buy [item name] [amount]`." + furnitureAddition,
                          color=0x00ff00)
    file = discord.File("data/sprites/locations/pokemart.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    if includeTrainerIcons:
        embed.add_field(name='Trainer Icons', value='`/shop ' + 'trainer icons' + '`', inline=False)
    if categoryList:
        for category in categoryList:
            embed.add_field(name=category.title(), value='`/shop ' + category + '`', inline=False)
    if itemList:
        for item in itemList:
            prefix = 'Cost: '
            suffix = ' ' + item.currency
            embed.add_field(name=item.itemName, value=prefix + str(item.price) + suffix, inline=False)
    # embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')) + "\nBP: " + str(trainer.getItemAmount('BP')))
    footer_text = ""
    footer_text += "BP: " + str(trainer.getItemAmount('BP')) + '\n'
    footer_text += "Coins: " + str(trainer.getItemAmount('Coins'))
    embed.set_footer(text=footer_text)
    embed.set_author(name=inter.author.display_name + " is shopping:")
    return files, embed


def createBagEmbed(inter, trainer, items=None, offset=0):
    files = []
    if items is None:
        embed = discord.Embed(title="Bag", description="[react to # to choose category]", color=0x00ff00)
    else:
        embed = discord.Embed(title="Bag (Page " + str(offset + 1) + ")", description="[react to # to use item]",
                              color=0x00ff00)
    file = discord.File("data/sprites/bag.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    if (items is None):
        embed.add_field(name="Pockets:", value="(1) Balls\n(2) Healing Items\n(3) Status Items\n(4) Badges\n(5) HM's"
                                               "\n(6) Mega Stones\n(7) Dynamax Crystals\n(8) Other Items\n(9) [Empty]",
                        inline=True)
    else:
        count = 1
        fieldString = ''
        for x in range(offset * 9, offset * 9 + 9):
            try:
                fieldString = fieldString + "(" + str(count) + ") " + items[x] + ": " + str(
                    trainer.itemList[items[x]]) + " owned\n"
                count += 1
            except:
                fieldString = fieldString + "----Empty Slot----\n"
        if not fieldString:
            fieldString = 'None'
        embed.add_field(name="Items:", value=fieldString, inline=True)
    embed.set_author(name=inter.author.display_name + " is looking at their items:")
    bpText = ''
    if 'BP' in trainer.itemList.keys():
        bpText = "\nBP: " + str(trainer.itemList['BP'])
    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')) + bpText)
    return files, embed


def createBeforeTrainerBattleEmbed(inter, trainer):
    files = []
    beforeBattleText = ''
    if (trainer.beforeBattleText):
        beforeBattleText = trainer.name.upper() + ': ' + '"' + trainer.beforeBattleText + '"\n\n'
    embed = discord.Embed(title=trainer.name + " wants to fight!",
                          description=beforeBattleText + "(battle starting in 6 seconds...)", color=0x00ff00)
    if 'data' in trainer.sprite:
        file = discord.File(trainer.sprite, filename="image.png")
    else:
        file = discord.File("data/sprites/trainers/" + trainer.sprite, filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_author(name=inter.author.display_name + " is about to battle:")
    return files, embed


def createNewUserEmbed(inter, trainer):
    files = []
    embed = discord.Embed(title="Welcome " + trainer.name + " to the world of Pokemon!",
                          description="Choose a starter from the drop down below!", color=0x00ff00)
    file = discord.File("data/sprites/starters.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_author(name=inter.author.display_name + " is choosing a starter:")
    return files, embed


def createProfileEmbed(inter, trainer):
    descString = getProfileDescStr(trainer)
    descString = descString + "\n\n**Party:**"
    embed = discord.Embed(title=trainer.name + "'s Profile", description=descString, color=0x00ff00)
    for pokemon in trainer.partyPokemon:
        levelString = "Level: " + str(pokemon.level)
        ivString = "IV's: " + str(pokemon.hpIV) + "/" + str(pokemon.atkIV) + "/" + str(pokemon.defIV) + "/" \
                   + str(pokemon.spAtkIV) + "/" + str(pokemon.spDefIV) + "/" + str(pokemon.spdIV)
        evString = "EV's: " + str(pokemon.hpEV) + "/" + str(pokemon.atkEV) + "/" + str(pokemon.defEV) + "/" \
                   + str(pokemon.spAtkEV) + "/" + str(pokemon.spDefEV) + "/" + str(pokemon.spdEV)
        natureString = 'Nature: ' + pokemon.nature.capitalize()
        otString = "OT: " + pokemon.OT
        obtainedString = 'Obtained: ' + pokemon.location
        moveString = ''
        count = 1
        for move in pokemon.moves:
            moveString += 'Move ' + str(count) + ': ' + move['names']['en'] + '\n'
            count += 1
        shinyString = ''
        if pokemon.altShiny:
            shinyString = ' :sparkles:'
        elif pokemon.distortion:
            shinyString = ' :nazar_amulet:'
        elif pokemon.shiny:
            shinyString = ' :star2:'
        shadowString = ""
        if pokemon.shadow:
            shadowString = ' :waxing_crescent_moon:'
        embedValue = levelString + '\n' + otString + '\n' + natureString + '\n' + obtainedString + '\n' + evString + '\n' + ivString + '\n' + moveString
        embed.add_field(name=pokemon.nickname + " (" + pokemon.name + ")" + shinyString + shadowString, value=embedValue,
                        inline=True)
    embed.set_author(name=(inter.author.display_name + " requested this profile."))
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
    #descString = descString + "\nCurrent Location: " + trainer.location
    #descString = descString + "\nPokemon Owned: " + str(len(trainer.partyPokemon) + len(trainer.boxPokemon))
    #dexList = []
    #for pokemon in trainer.partyPokemon:
    #    if pokemon.name not in dexList:
    #        dexList.append(pokemon.name)
    #for pokemon in trainer.boxPokemon:
    #    if pokemon.name not in dexList:
    #        dexList.append(pokemon.name)
    #dexNum = len(dexList)
    #descString = descString + "\nDex: " + str(dexNum)
    descString = descString + "\nMain Dex: " + str(trainer.get_number_caught(data, "non-event")) + " / " + str(data.getNumberOfPokemon("non-event"))
    descString = descString + "\nEvent Dex: " + str(trainer.get_number_caught(data, "event")) + " / " + str(data.getNumberOfPokemon("event"))
    descString = descString + "\nMoney: " + str(trainer.getItemAmount('money'))
    if 'BP' in trainer.itemList.keys():
        descString = descString + "\nBP: " + str(trainer.getItemAmount('BP'))
        descString = descString + "\nBattle Tower With Restrictions Record: " + str(trainer.withRestrictionsRecord)
        descString = descString + "\nBattle Tower No Restrictions Record: " + str(trainer.noRestrictionsRecord)
        # descString = descString + "\nBattle Tower With Restrictions Current Streak: " + str(trainer.withRestrictionStreak)
        # descString = descString + "\nBattle Tower No Restrictions Current Streak: " + str(trainer.noRestrictionsStreak)
    #descString = descString + "\nPVP Win/Loss Ratio: " + str(trainer.getPvpWinLossRatio())
    shinyOwned = 0
    distortionOwned = 0
    for pokemon in trainer.partyPokemon:
        if pokemon.shiny:
            shinyOwned += 1
        if pokemon.distortion:
            distortionOwned += 1
    for pokemon in trainer.boxPokemon:
        if pokemon.shiny:
            shinyOwned += 1
        if pokemon.distortion:
            distortionOwned += 1
    descString = descString + "\nShiny Pokemon Owned: " + str(shinyOwned)
    descString = descString + "\nDistortion Pokemon Owned: " + str(distortionOwned)
    return descString


def createMoveTutorEmbed(inter, trainer, pokemon, moveList, offset, isTM):
    files = []
    extraTitleText = ''
    if isTM:
        extraTitleText += " (TM's)"
    else:
        extraTitleText += " (Level Up Moves)"
    embed = discord.Embed(title="Move Tutor" + extraTitleText,
                          description="Cost: $3000\n-> select move to teach to " + pokemon.nickname + " <-\n\nPage: " + str(
                              offset + 1),
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
                    move['names']['en'] + "\n" + move['type'] + " " + physicalSpecialEmoji + bp + "\nPP: " + str(
                move['pp']) + " pp"), inline=True)
            count += 1
        except:
            embed.add_field(name="----Empty Slot----", value="\u200b", inline=True)
    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')))
    return files, embed


def createCutsceneEmbed(inter, cutsceneStr):
    files = []
    cutsceneObj = data.cutsceneDict[cutsceneStr]
    embed = discord.Embed(title=cutsceneObj['title'], description=cutsceneObj['caption'])
    file = discord.File('data/sprites/cutscenes/' + cutsceneStr + '.png', filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text="(continuing automatically in 10 seconds...)")
    embed.set_author(name=(inter.author.display_name + "'s Cutscene:"))
    return files, embed


def createTrainEmbed(inter, pokemon):
    files = []
    embed = discord.Embed(title="Super Training: " + pokemon.nickname,
                          description="Confirm below to finish Super Training!")
    file = discord.File(pokemon.getSpritePath(), filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_author(name=(inter.author.display_name + " is super training their Pokemon:"))
    return files, embed


def createBattleTowerUI(inter, trainer, withRestrictions):
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
    if data.staminaDict[str(inter.guild.id)]:
        embed.set_author(name=(
                inter.author.display_name + "'s Battle Tower Challenge:\n(remaining stamina: " + str(
            trainer.dailyProgress) + ")"))
    else:
        embed.set_author(name=(inter.author.display_name + "'s Battle Tower Challenge:"))

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


async def continueUI(inter, message, buttonList, local_timeout=None, ignoreList=None, isOverworld=False, isPVP=False,
                     isRaid=False):
    if message:
        logging.debug(str(inter.author.id) + " - continueUI(), message.content = " + message.content)
    else:
        logging.debug(str(inter.author.id) + " - continueUI(), message = None")
    if local_timeout is None:
        local_timeout = timeout
    return await startNewUI(inter, None, None, buttonList, local_timeout, message, ignoreList, isOverworld, isPVP,
                            isRaid)


async def startNewUI(inter, embed, files, buttonList, local_timeout=None, message=None, ignoreList=None,
                     isOverworld=False, isPVP=False, isRaid=False):
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
    logging.debug(
        str(inter.author.id) + " - startNewUI() called, uuid = " + str(temp_uuid) + ", title = " + embed_title)
    if not allowSave:
        logging.debug(
            str(inter.author.id) + " - not starting new UI, bot is down for maintenance, calling endSession()")
        await endSession(inter)
        await inter.channel.send("Our apologies, " + str(
            inter.author.mention) + ", but PokéNav is currently down for maintenance. Please try again later.")
        return None, None
    # print(embed_title, ' - ', temp_uuid)
    if not ignoreList:
        ignoreList = []
    group = None
    if not message:
        logging.debug(str(inter.author.id) + " - uuid = " + str(temp_uuid) + " - message is None, creating new message")
        # if inter.response.is_done():
        #     message = await inter.channel.send(embed=embed, files=files)
        # else:
        #     await inter.channel.send(embed=embed, files=files)
        #     message = await inter.original_message()
        view = PokeNavComponents.OverworldUIView(inter.author, buttonList)
        message = await inter.channel.send(embed=embed, files=files, view=view)
        # group = gather()
        # for emojiName in emojiNameList:
        #     # await message.add_reaction(data.getEmoji(emojiName))
        #     group = gather(group, safeAddEmoji(message, emojiName))
    messageID = message.id

    if isOverworld:
        logging.debug(str(inter.author.id) + " - uuid = " + str(
            temp_uuid) + " - isOverworld=True, removing old from data.overworldSessions and adding new")
        data.addOverworldSession(inter, None, message, temp_uuid)

    if not buttonList:
        logging.debug(str(inter.author.id) + " - uuid = " + str(
            temp_uuid) + " - emojiNameList is None or empty, returning [None, message]")
        return None, message

    try:
        res: MessageInteraction = await bot.wait_for(
            "message_interaction",
            check=lambda m: m.author.id == inter.author.id
                            and m.message == message,
            timeout=timeout,
        )
        try:
            await res.response.defer()
        except:
            pass
    except asyncio.TimeoutError:
        if not isRaid:
            if not isPVP:
                logging.debug(str(inter.author.id) + " - uuid = " + str(temp_uuid) + " - timeout")
                # print('attempting to end session: ', embed_title, ' - ', temp_uuid)
                if isOverworld:
                    overworldTuple, isGlobal = data.userInOverworldSession(inter)
                    if overworldTuple:
                        uuidToCompare = overworldTuple[1]
                        if uuidToCompare != temp_uuid:
                            logging.debug(str(inter.author.id) + " - uuid = " + str(
                                temp_uuid) + " - isOverworld=True and uuid's do not match, returning [None, None]")
                            return None, None
                    if temp_uuid in data.expiredSessions:
                        logging.debug(str(inter.author.id) + " - uuid = " + str(
                            temp_uuid) + " - isOverworld=True and temp_uuid in data.expiredSessions, returning [None, None]")
                        return None, None
                # print('ending session: ', embed_title, ' - ', temp_uuid, '\n')
                logging.debug(str(inter.author.id) + " - uuid = " + str(temp_uuid) + " - calling endSession()")
                await endSession(inter)
        # print("returning none, none from startNewUI")
        return None, None

    commandNum = None

    try:
        component = res.component
        if isinstance(component, discord.Button):
            commandNum = component.custom_id
        elif isinstance(component, discord.SelectMenu):
            commandNum = res.data.values[0]
    except:
        # traceback.print_exc()
        pass

    logging.debug(
        str(inter.author.id) + " - uuid = " + str(temp_uuid) + " - returning [" + str(commandNum) + ", message]")
    return commandNum, message


def convertToId(input):
    if isinstance(input, int):
        id = input
    else:
        id = int(input.replace("<", "").replace("@", "").replace(">", "").replace("!", ""))
    return id


async def fetchUserFromServer(inter, userName):
    try:
        identifier = convertToId(userName)
        fetched_user = await inter.guild.fetch_member(identifier)
        return fetched_user
    except:
        return None


async def fetchMessageFromServerByPayload(inter, payload):
    try:
        guild = inter.guild
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        return message
    except:
        return None


async def fetchMessageFromServerByInter(inter, msg_id):
    try:
        channel = inter.channel
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


async def startOverworldUI(inter, trainer):
    logging.debug(str(inter.author.id) + " - startOverworldUI()")
    await raidCheck()
    resetAreas(trainer)
    dataTuple = (trainer,)
    files, embed, overWorldCommands, buttonList = createOverworldEmbed(inter, trainer)
    emojiNameList = []
    count = 1
    for command in overWorldCommands:
        if count >= 10:
            continue
        emojiNameList.append(str(count))
        count += 1
    if len(overWorldCommands) >= 10:
        emojiNameList.append(str(0))

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList, timeout, None, None, True)
    if chosenEmoji == '0':
        chosenEmoji = '10'
    commandNum = strToInt(chosenEmoji)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if commandNum is not None:
            newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle, \
            goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower, withRestrictions, goToSuperTraining, goToSecretBase = \
                executeWorldCommand(inter, trainer, overWorldCommands[commandNum], embed)
            if (embedNeedsUpdating):
                await message.edit(embed=newEmbed)
            else:
                overworldTuple, isGlobal = data.userInOverworldSession(inter)
                if overworldTuple:
                    try:
                        data.removeOverworldSession(inter)
                    except:
                        pass
                await resolveWorldCommand(inter, message, trainer,
                                          dataTuple, newEmbed, embedNeedsUpdating,
                                          reloadArea, goToBox, goToBag, goToMart, goToParty, battle,
                                          goToTMMoveTutor, goToLevelMoveTutor, goToBattleTower,
                                          withRestrictions, goToSuperTraining, goToSecretBase)
                break
        chosenEmoji, message = await continueUI(inter, message, emojiNameList, timeout, None, True)
        if chosenEmoji == '0':
            chosenEmoji = '10'
        commandNum = strToInt(chosenEmoji)


async def startPartyUI(inter, trainer, goBackTo='', battle=None, otherData=None, goStraightToBattle=False,
                       isBoxSwap=False,
                       boxIndexToSwap=None, swapToBox=False, itemToUse=None, isFromFaint=False):
    logging.debug(str(inter.author.id) + " - startPartyUI()")
    dataTuple = (trainer, goBackTo, battle, otherData)
    if (goStraightToBattle):
        if (goBackTo == 'startBattleUI'):
            if isFromFaint:
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                      startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], False,
                                              otherData[4], isFromFaint)
            else:
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                      startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], True,
                                              otherData[4], isFromFaint)
            return
    files, embed = createPartyUIEmbed(inter, trainer, isBoxSwap, itemToUse)
    emojiNameList = []
    count = 1
    buttonList = []
    for pokemon in trainer.partyPokemon:
        emojiNameList.append(str(count))
        if count > 3:
            row = 1
        else:
            row = 0
        color = discord.ButtonStyle.blurple
        if 'faint' in pokemon.statusList:
            color = discord.ButtonStyle.red
        elif pokemon.currentHP < pokemon.hp:
            color = discord.ButtonStyle.grey
        buttonList.append(
            PokeNavComponents.OverworldUIButton(label="(" + str(count) + ") " + pokemon.name, style=color, row=row,
                                                info=pokemon.name, identifier=str(count)))
        count += 1
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='right arrow'))
    emojiNameList.append('right arrow')

    isPVP = False
    isRaid = False
    tempTimeout = timeout
    if battle:
        isPVP = battle.isPVP
        if isPVP:
            tempTimeout = pvpTimeout
        isRaid = battle.isRaid

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList, tempTimeout, None, None, False, isPVP,
                                            isRaid)

    while True:
        if (chosenEmoji == None and message == None):
            if isPVP:
                await inter.channel.send(
                    str(inter.author.mention) + ", you have timed out - battle has ended. You lose the battle.")
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                      startNewUI, continueUI, startPartyUI, startOverworldUI,
                                      startBattleTowerUI, startCutsceneUI)
                battle_ui.recordPVPWinLoss(False, trainer, inter)
                return
            elif isRaid:
                pass
            else:
                break
        if (chosenEmoji == '1' and len(trainer.partyPokemon) >= 1):
            if isBoxSwap:
                await message.delete()
                filename = merge_send_to_box_images(trainer.partyPokemon[0], trainer.boxPokemon[boxIndexToSwap])
                embed = discord.Embed(title=trainer.partyPokemon[0].nickname + " sent to box!\n" + trainer.boxPokemon[
                    boxIndexToSwap].nickname + " added to party!",
                                      description='(continuing in 6 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                # confirmation = await inter.channel.send(
                #     trainer.partyPokemon[0].nickname + " sent to box and " + trainer.boxPokemon[
                #         boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(6)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(0, boxIndexToSwap)
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
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
                        await battle_ui.startBattleUI(inter, otherData[0], battle, otherData[2], otherData[3], True,
                                                      otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await inter.channel.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(inter)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(inter)
            else:
                await message.delete()
                await startPokemonSummaryUI(inter, trainer, 0, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '2' and len(trainer.partyPokemon) >= 2):
            if isBoxSwap:
                await message.delete()
                filename = merge_send_to_box_images(trainer.partyPokemon[1], trainer.boxPokemon[boxIndexToSwap])
                embed = discord.Embed(title=trainer.partyPokemon[1].nickname + " sent to box!\n" + trainer.boxPokemon[
                    boxIndexToSwap].nickname + " added to party!",
                                      description='(continuing in 6 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                # confirmation = await inter.channel.send(
                #     trainer.partyPokemon[1].nickname + " sent to box and " + trainer.boxPokemon[
                #         boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(6)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(1, boxIndexToSwap)
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
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
                        await battle_ui.startBattleUI(inter, otherData[0], battle, otherData[2], otherData[3], True,
                                                      otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await inter.channel.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(inter)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(inter)
            else:
                await message.delete()
                await startPokemonSummaryUI(inter, trainer, 1, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '3' and len(trainer.partyPokemon) >= 3):
            if isBoxSwap:
                await message.delete()
                filename = merge_send_to_box_images(trainer.partyPokemon[2], trainer.boxPokemon[boxIndexToSwap])
                embed = discord.Embed(title=trainer.partyPokemon[2].nickname + " sent to box!\n" + trainer.boxPokemon[
                    boxIndexToSwap].nickname + " added to party!",
                                      description='(continuing in 6 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                # confirmation = await inter.channel.send(
                #     trainer.partyPokemon[2].nickname + " sent to box and " + trainer.boxPokemon[
                #         boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(6)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(2, boxIndexToSwap)
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
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
                        await battle_ui.startBattleUI(inter, otherData[0], battle, otherData[2], otherData[3], True,
                                                      otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await inter.channel.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(inter)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(inter)
            else:
                await message.delete()
                await startPokemonSummaryUI(inter, trainer, 2, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '4' and len(trainer.partyPokemon) >= 4):
            if isBoxSwap:
                await message.delete()
                filename = merge_send_to_box_images(trainer.partyPokemon[3], trainer.boxPokemon[boxIndexToSwap])
                embed = discord.Embed(title=trainer.partyPokemon[3].nickname + " sent to box!\n" + trainer.boxPokemon[
                    boxIndexToSwap].nickname + " added to party!",
                                      description='(continuing in 6 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                # confirmation = await inter.channel.send(
                #     trainer.partyPokemon[3].nickname + " sent to box and " + trainer.boxPokemon[
                #         boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(6)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(3, boxIndexToSwap)
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
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
                        await battle_ui.startBattleUI(inter, otherData[0], battle, otherData[2], otherData[3], True,
                                                      otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await inter.channel.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(inter)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(inter)
            else:
                await message.delete()
                await startPokemonSummaryUI(inter, trainer, 3, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '5' and len(trainer.partyPokemon) >= 5):
            if isBoxSwap:
                await message.delete()
                filename = merge_send_to_box_images(trainer.partyPokemon[4], trainer.boxPokemon[boxIndexToSwap])
                embed = discord.Embed(title=trainer.partyPokemon[4].nickname + " sent to box!\n" + trainer.boxPokemon[
                    boxIndexToSwap].nickname + " added to party!",
                                      description='(continuing in 6 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                # confirmation = await inter.channel.send(
                #     trainer.partyPokemon[4].nickname + " sent to box and " + trainer.boxPokemon[
                #         boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(6)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(4, boxIndexToSwap)
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
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
                        await battle_ui.startBattleUI(inter, otherData[0], battle, otherData[2], otherData[3], True,
                                                      otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await inter.channel.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(inter)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(inter)
            else:
                await message.delete()
                await startPokemonSummaryUI(inter, trainer, 4, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == '6' and len(trainer.partyPokemon) >= 6):
            if isBoxSwap:
                await message.delete()
                filename = merge_send_to_box_images(trainer.partyPokemon[5], trainer.boxPokemon[boxIndexToSwap])
                embed = discord.Embed(title=trainer.partyPokemon[5].nickname + " sent to box!\n" + trainer.boxPokemon[
                        boxIndexToSwap].nickname + " added to party!",
                                      description='(continuing in 6 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                #confirmation = await inter.channel.send(
                #    trainer.partyPokemon[5].nickname + " sent to box and " + trainer.boxPokemon[
                #        boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                await sleep(6)
                await confirmation.delete()
                trainer.swapPartyAndBoxPokemon(5, boxIndexToSwap)
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
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
                        await battle_ui.startBattleUI(inter, otherData[0], battle, otherData[2], otherData[3], True,
                                                      otherData[4])
                        break
                    elif (goBackTo == "startBagUI"):
                        itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                        trainer.useItem(itemToUse, 1)
                        await message.delete()
                        confirmation = await inter.channel.send(itemText + "\n(continuing in 4 seconds...)")
                        await sleep(4)
                        await confirmation.delete()
                        await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    elif (goBackTo == "startBattleTowerUI"):
                        await message.delete()
                        await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                        break
                    # else:
                    #     await message.remove_reaction(reaction, user)
                    #     await waitForEmoji(inter)
                else:
                    embed.set_footer(text="\nIt would have no effect on " + pokemonForItem.nickname + ".")
                    await message.edit(embed=embed)
                    # await message.remove_reaction(reaction, user)
                    # await waitForEmoji(inter)
            else:
                await message.delete()
                await startPokemonSummaryUI(inter, trainer, 5, 'startPartyUI', battle, dataTuple, False,
                                            swapToBox)
                break
        elif (chosenEmoji == 'right arrow'):
            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                await message.delete()
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                                      startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
                await battle_ui.startBattleUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], False,
                                              otherData[4])
                break
            elif (goBackTo == 'startBoxUI'):
                await message.delete()
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
                break
            elif (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(inter, otherData[0])
                break
            elif (goBackTo == 'startBagUI'):
                await message.delete()
                await startBagUI(inter, otherData[0], otherData[1], otherData[2])
                break
            elif (goBackTo == "startBattleTowerUI"):
                await message.delete()
                await startBattleTowerUI(inter, otherData[0], otherData[1], otherData[2])
                break
            # else:
            #     await message.remove_reaction(reaction, user)
            #     await waitForEmoji(inter)
        # else:
        #     await message.remove_reaction(reaction, user)
        #     await waitForEmoji(inter)
        chosenEmoji, message = await continueUI(inter, message, emojiNameList, tempTimeout, None, False, isPVP, isRaid)


async def startPokemonSummaryUI(inter, trainer, partyPos, goBackTo='', battle=None, otherData=None, isFromBox=False,
                                swapToBox=False):
    logging.debug(str(inter.author.id) + " - startPokemonSummaryUI()")
    if not isFromBox:
        pokemon = trainer.partyPokemon[partyPos]
    else:
        pokemon = trainer.boxPokemon[partyPos]
    files, embed = createPokemonSummaryEmbed(inter, pokemon)
    emojiNameList = []
    buttonList = []
    if (swapToBox):
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('box'), style=discord.ButtonStyle.grey, row=0,
                                                identifier='box'))
        emojiNameList.append('box')
    else:
        emojiNameList.append('swap')
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('swap'), style=discord.ButtonStyle.grey, row=0,
                                                identifier='swap'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=0,
                                            identifier='right arrow'))
    emojiNameList.append('right arrow')

    isPVP = False
    isRaid = False
    tempTimeout = timeout
    if battle:
        isPVP = battle.isPVP
        if isPVP:
            tempTimeout = pvpTimeout
        isRaid = battle.isRaid

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList, tempTimeout, None, None, False, isPVP,
                                            isRaid)

    while True:
        if (chosenEmoji == None and message == None):
            if isPVP:
                await inter.channel.send(
                    str(inter.author.mention) + ", you have timed out - battle has ended. You lose the battle.")
                battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems,
                                      startNewUI, continueUI, startPartyUI, startOverworldUI,
                                      startBattleTowerUI, startCutsceneUI)
                battle_ui.recordPVPWinLoss(False, trainer, inter)
                return
            elif isRaid:
                pass
            else:
                break
        if (chosenEmoji == 'right arrow'):
            await message.delete()
            if (goBackTo == 'startPartyUI'):
                await startPartyUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], False, False, None,
                                   swapToBox)
                break
            elif (goBackTo == 'startBoxUI'):
                await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
                break
        elif (chosenEmoji == 'box' and swapToBox):
            if (len(trainer.partyPokemon) > 1):
                await message.delete()
                filename = merge_send_to_box_images(pokemon)
                embed = discord.Embed(title=pokemon.nickname + ' sent to box!',
                                      description='(continuing in 4 seconds...)')
                file = discord.File(filename, filename="image.png")
                embed.set_image(url="attachment://image.png")
                confirmation = await inter.channel.send(embed=embed, file=file)
                #confirmation = await inter.channel.send(
                #    pokemon.nickname + " sent to box! (continuing in 4 seconds...)")
                await sleep(4)
                await confirmation.delete()
                trainer.movePokemonPartyToBox(partyPos)
                await startPartyUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], False, False,
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
                    filename = merge_send_to_box_images(None, trainer.boxPokemon[partyPos])
                    embed = discord.Embed(
                        title=trainer.boxPokemon[partyPos].nickname + " added to party!\n",
                        description='(continuing in 4 seconds...)')
                    file = discord.File(filename, filename="image.png")
                    embed.set_image(url="attachment://image.png")
                    confirmation = await inter.channel.send(embed=embed, file=file)
                    # confirmation = await inter.channel.send(
                    #     trainer.boxPokemon[partyPos].nickname + " added to party! (continuing in 4 seconds...)")
                    await sleep(4)
                    await confirmation.delete()
                    trainer.movePokemonBoxToParty(partyPos)
                    await startBoxUI(inter, otherData[0], otherData[1], otherData[2], otherData[3])
                    break
                else:
                    await startPartyUI(inter, trainer, 'startBoxUI', None, otherData, False, True, partyPos)
                    break
            elif ('faint' not in pokemon.statusList and not alreadyInBattle):
                await message.delete()
                if (goBackTo == 'startPartyUI'):
                    if (battle is not None):
                        # swappingFromFaint = ('faint' in battle.pokemon1.statusList)
                        swappingFromFaint = battle.swapCommand(trainer, partyPos)
                        if swappingFromFaint:
                            await startPartyUI(inter, otherData[0], otherData[1], otherData[2], otherData[3],
                                               True, False, None, False, None, True)
                            break
                        else:
                            await startPartyUI(inter, otherData[0], otherData[1], otherData[2], otherData[3],
                                               True)
                            break
                    else:
                        trainer.swapPartyPokemon(partyPos)
                        await startPartyUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], False)
                        break
        chosenEmoji, message = await continueUI(inter, message, emojiNameList, tempTimeout, None, False, isPVP, isRaid)


def merge_send_to_box_images(pokemonToBox=None, pokemonFromBox=None):
    location = (0, 0)
    if not pokemonToBox and not pokemonFromBox:
        return None
    background = None
    background1 = None
    background2 = None
    if pokemonToBox:
        path1 = pokemonToBox.getSpritePath()
        backgroundPath1 = 'data/sprites/to_pc.png'
        background1 = Image.open(backgroundPath1)
        background1 = background1.convert('RGBA')
        image1 = Image.open(path1)
        image1 = image1.transpose(method=Image.FLIP_LEFT_RIGHT)
        background1.paste(image1, location, image1.convert('RGBA'))
        background = background1
    if pokemonFromBox:
        path2 = pokemonFromBox.getSpritePath()
        backgroundPath2 = 'data/sprites/from_pc.png'
        background2 = Image.open(backgroundPath2)
        background2 = background2.convert('RGBA')
        image2 = Image.open(path2)
        image2 = image2.transpose(method=Image.FLIP_LEFT_RIGHT)
        background2.paste(image2, location, image2.convert('RGBA'))
        background = background2
    if pokemonToBox and pokemonFromBox:
        backgroundPath = 'data/sprites/pc_combined_background.png'
        background = Image.open(backgroundPath)
        background = background.convert('RGBA')
        background.paste(background1, (0,0))
        background.paste(background2, (0,96))
    temp_uuid = uuid.uuid4()
    filename = "data/temp/merged_image" + str(temp_uuid) + ".png"
    background.save(filename, "PNG")
    return filename


async def startBoxUI(inter, trainer, offset=0, goBackTo='', otherData=None):
    logging.debug(str(inter.author.id) + " - startBoxUI()")
    dataTuple = (trainer, offset, goBackTo, otherData)
    maxBoxes = math.ceil(len(trainer.boxPokemon) / 9)
    if (maxBoxes < 1):
        maxBoxes = 1
    files, embed = createBoxEmbed(inter, trainer, offset)  # is box number
    emojiNameList = []
    buttonList = []
    for x in range(1, 10):
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji(str(x)), style=discord.ButtonStyle.grey,
                                                identifier=str(x)))
        emojiNameList.append(str(x))
    emojiNameList.append('party')
    emojiNameList.append('left arrow')
    emojiNameList.append('right arrow')
    emojiNameList.append('down arrow')
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('party'), style=discord.ButtonStyle.grey,
                                            identifier='party'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('left arrow'), style=discord.ButtonStyle.grey, row=3,
                                            identifier='left arrow'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('right arrow'), style=discord.ButtonStyle.grey, row=3,
                                            identifier='right arrow'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=3,
                                            identifier='down arrow'))

    select = PokeNavComponents.get_box_select(offset, maxBoxes)
    if select:
        buttonList.insert(0, select)

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1' and len(trainer.boxPokemon) >= 1 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 0 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '2' and len(trainer.boxPokemon) >= 2 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 1 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '3' and len(trainer.boxPokemon) >= 3 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 2 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '4' and len(trainer.boxPokemon) >= 4 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 3 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '5' and len(trainer.boxPokemon) >= 5 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 4 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '6' and len(trainer.boxPokemon) >= 6 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 5 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '7' and len(trainer.boxPokemon) >= 7 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 6 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '8' and len(trainer.boxPokemon) >= 8 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 7 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == '9' and len(trainer.boxPokemon) >= 9 + (offset * 9)):
            await message.delete()
            await startPokemonSummaryUI(inter, trainer, 8 + (offset * 9), 'startBoxUI', None, dataTuple, True)
            break
        elif (chosenEmoji == 'left arrow'):
            if (offset == 0 and maxBoxes != 1):
                offset = maxBoxes - 1
                files, embed = createBoxEmbed(inter, trainer, offset)
                view = discord.ui.View.from_message(message)
                select = PokeNavComponents.get_box_select(offset, maxBoxes)
                view.children[0] = select
                await message.edit(embed=embed, view=view)
            elif (offset > 0):
                offset -= 1
                files, embed = createBoxEmbed(inter, trainer, offset)
                view = discord.ui.View.from_message(message)
                select = PokeNavComponents.get_box_select(offset, maxBoxes)
                view.children[0] = select
                await message.edit(embed=embed, view=view)
            trainer.lastBoxNum = offset
            dataTuple = (trainer, offset, goBackTo, otherData)
        elif (chosenEmoji == 'right arrow'):
            if (offset + 1 < maxBoxes):
                offset += 1
                files, embed = createBoxEmbed(inter, trainer, offset)
                view = discord.ui.View.from_message(message)
                select = PokeNavComponents.get_box_select(offset, maxBoxes)
                view.children[0] = select
                await message.edit(embed=embed, view=view)
            elif (offset + 1 == maxBoxes and maxBoxes != 1):
                offset = 0
                files, embed = createBoxEmbed(inter, trainer, offset)
                view = discord.ui.View.from_message(message)
                select = PokeNavComponents.get_box_select(offset, maxBoxes)
                view.children[0] = select
                await message.edit(embed=embed, view=view)
            trainer.lastBoxNum = offset
            dataTuple = (trainer, offset, goBackTo, otherData)
        elif (chosenEmoji == 'party'):
            await message.delete()
            await startPartyUI(inter, trainer, 'startBoxUI', None, dataTuple, False, False, None, True)
            break
        elif (chosenEmoji == 'down arrow'):
            if (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(inter, otherData[0])
                break
        else:
            if 'box' in chosenEmoji:
                box_number = int(chosenEmoji.split(",")[1])
                offset = box_number - 1
                files, embed = createBoxEmbed(inter, trainer, offset)
                view = discord.ui.View.from_message(message)
                select = PokeNavComponents.get_box_select(offset, maxBoxes)
                view.children[0] = select
                await message.edit(embed=embed, view=view)
                trainer.lastBoxNum = offset
                dataTuple = (trainer, offset, goBackTo, otherData)
        chosenEmoji, message = await continueUI(inter, message, emojiNameList)


async def startMartUI(inter, trainer, goBackTo='', otherData=None):
    logging.debug(str(inter.author.id) + " - startMartUI()")
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
    files, embed = createMartEmbed(inter, trainer, itemDict)
    emojiNameList = []
    buttonList = []
    for x in range(1, len(itemDict) + 1):
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji(str(x)), style=discord.ButtonStyle.grey,
                                                identifier=str(x)))
        emojiNameList.append(str(x))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='right arrow'))
    emojiNameList.append('right arrow')

    amount = 1
    if trainer.location != "Battle Frontier":
        select = PokeNavComponents.get_mart_select(amount)
        buttonList.insert(0, select)

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList)

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
        else:
            if 'quantity' in chosenEmoji:
                amount = int(chosenEmoji.split(",")[1])
                embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount("money"))
                                      + "\nCurrent Buy Quantity: " + str(amount))
                await message.edit(embed=embed)
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
                    embed.set_footer(text="BP: " + str(trainer.getItemAmount('BP'))
                                          + "\nNot enough currency to make purchase!")
                    await message.edit(embed=embed)
            else:
                if (trainer.getItemAmount("money") >= itemDict[key] * amount):
                    trainer.addItem("money", -1 * itemDict[key] * amount)
                    trainer.addItem(key, amount)
                    # print("mart: " + trainer.name + "bought " + item + " and now has a total of " + str(trainer.getItemAmount(item)))
                    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount("money"))
                                          + "\nCurrent Buy Quantity: " + str(amount)
                                          + "\nBought " + str(amount) + "x " + key + " for $" + str(
                        itemDict[key] * amount) + ".")
                    await message.edit(embed=embed)
                else:
                    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount("money"))
                                          + "\nCurrent Buy Quantity: " + str(amount)
                                          + "\nNot enough currency to make purchase!")
                    await message.edit(embed=embed)
        elif (chosenEmoji == 'right arrow'):
            if (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(inter, otherData[0])
                break
        chosenEmoji, message = await continueUI(inter, message, buttonList)


async def startBagUI(inter, trainer, goBackTo='', otherData=None, offset=0):
    logging.debug(str(inter.author.id) + " - startBagUI()")
    dataTuple = (trainer, goBackTo, otherData, offset)
    files, embed = createBagEmbed(inter, trainer, None, offset)
    maxPages = math.ceil(len(trainer.itemList) / 9)
    if (maxPages < 1):
        maxPages = 1
    emojiNameList = []
    buttonList = []
    for x in range(1, 10):
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji(str(x)), style=discord.ButtonStyle.blurple,
                                                identifier=str(x)))
        emojiNameList.append(str(x))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('left arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='left arrow'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('right arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='right arrow'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='down arrow'))
    emojiNameList.append('left arrow')
    emojiNameList.append('right arrow')
    emojiNameList.append('down arrow')

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList)

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
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
            else:
                items = getBattleItems(category, None, trainer)
                if (len(items) > 0):
                    item = items[0]
                    if (category == "Healing Items" or category == "Status Items"):
                        await message.delete()
                        await startPartyUI(inter, trainer, 'startBagUI', None, dataTuple, False, False, None, False,
                                           item)
                        break
        elif (chosenEmoji == '2'):
            if (isCategory):
                isCategory = False
                category = "Healing Items"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
            else:
                items = getBattleItems(category, None, trainer)
                if (len(items) > 1):
                    item = items[1]
                    if (category == "Healing Items" or category == "Status Items"):
                        await message.delete()
                        await startPartyUI(inter, trainer, 'startBagUI', None, dataTuple, False, False, None, False,
                                           item)
                        break
        elif (chosenEmoji == '3'):
            if (isCategory):
                isCategory = False
                category = "Status Items"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
            else:
                items = getBattleItems(category, None, trainer)
                if (len(items) > 2):
                    item = items[2]
                    if (category == "Healing Items" or category == "Status Items"):
                        await message.delete()
                        await startPartyUI(inter, trainer, 'startBagUI', None, dataTuple, False, False, None, False,
                                           item)
                        break
        elif (chosenEmoji == '4'):
            if (isCategory):
                isCategory = False
                category = "Badges"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
            else:
                items = getBattleItems(category, None, trainer)
                if (len(items) > 3):
                    item = items[3]
                    if (category == "Healing Items" or category == "Status Items"):
                        await message.delete()
                        await startPartyUI(inter, trainer, 'startBagUI', None, dataTuple, False, False, None, False,
                                           item)
                        break
        elif (chosenEmoji == '5'):
            if (isCategory):
                isCategory = False
                category = "HM's"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
        elif (chosenEmoji == '6'):
            if (isCategory):
                isCategory = False
                category = "Mega Stones"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
        elif (chosenEmoji == '7'):
            if (isCategory):
                isCategory = False
                category = "Dynamax Crystals"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
        elif (chosenEmoji == '8'):
            if (isCategory):
                isCategory = False
                category = "Other Items"
                items = getBattleItems(category, None, trainer)
                maxPages = math.ceil(len(items) / 9)
                if (maxPages < 1):
                    maxPages = 1
                files, embed = createBagEmbed(inter, trainer, items)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'left arrow'):
            if not isCategory:
                if (offset == 0 and maxPages != 1):
                    offset = maxPages - 1
                    files, embed = createBagEmbed(inter, trainer, items, offset)
                    await message.edit(embed=embed)
                elif (offset > 0):
                    offset -= 1
                    files, embed = createBagEmbed(inter, trainer, items, offset)
                    await message.edit(embed=embed)
                dataTuple = (trainer, goBackTo, otherData, offset)
        elif (chosenEmoji == 'right arrow'):
            if not isCategory:
                if (offset + 1 < maxPages):
                    offset += 1
                    files, embed = createBagEmbed(inter, trainer, items, offset)
                    await message.edit(embed=embed)
                elif (offset + 1 == maxPages and maxPages != 1):
                    offset = 0
                    files, embed = createBagEmbed(inter, trainer, items, offset)
                    await message.edit(embed=embed)
                dataTuple = (trainer, goBackTo, otherData, offset)
        elif (chosenEmoji == 'down arrow'):
            if (isCategory):
                if (goBackTo == 'startOverworldUI'):
                    await message.delete()
                    await startOverworldUI(inter, trainer)
                    break
            else:
                isCategory = True
                category = ''
                files, embed = createBagEmbed(inter, trainer)
                await message.edit(embed=embed)
        chosenEmoji, message = await continueUI(inter, message, emojiNameList)


async def startBeforeTrainerBattleUI(inter, isWildEncounter, battle, goBackTo='', otherData=None):
    logging.debug(str(inter.author.id) + " - startBeforeTrainerBattleUI()")
    files, embed = createBeforeTrainerBattleEmbed(inter, battle.trainer2)
    if inter.response.is_done():
        message = await inter.channel.send(embed=embed, files=files)
    else:
        message = await inter.channel.send(embed=embed, files=files)
    await sleep(6)
    await message.delete()
    battle_ui = Battle_UI(data, timeout, battleTimeout, pvpTimeout, getBattleItems, startNewUI, continueUI,
                          startPartyUI, startOverworldUI, startBattleTowerUI, startCutsceneUI)
    await battle_ui.startBattleUI(inter, isWildEncounter, battle, goBackTo, otherData)


async def startNewUserUI(inter, trainer):
    logging.debug(str(inter.author.id) + " - startNewUserUI()")
    # starterList = []
    # starterNameList = []
    # starterList.append(Pokemon(data, "Bulbasaur", 5))
    # starterNameList.append('bulbasaur')
    # starterList.append(Pokemon(data, "Charmander", 5))
    # starterNameList.append('charmander')
    # starterList.append(Pokemon(data, "Squirtle", 5))
    # starterNameList.append('squirtle')
    # starterList.append(Pokemon(data, "Chikorita", 5))
    # starterNameList.append('chikorita')
    # starterList.append(Pokemon(data, "Cyndaquil", 5))
    # starterNameList.append('cyndaquil')
    # starterList.append(Pokemon(data, "Totodile", 5))
    # starterNameList.append('totodile')
    # starterList.append(Pokemon(data, "Treecko", 5))
    # starterNameList.append('treecko')
    # starterList.append(Pokemon(data, "Torchic", 5))
    # starterNameList.append('torchic')
    # starterList.append(Pokemon(data, "Mudkip", 5))
    # starterNameList.append('mudkip')
    # starterList.append(Pokemon(data, "Turtwig", 5))
    # starterNameList.append('turtwig')
    # starterList.append(Pokemon(data, "Chimchar", 5))
    # starterNameList.append('chimchar')
    # starterList.append(Pokemon(data, "Piplup", 5))
    # starterNameList.append('piplup')
    # starterList.append(Pokemon(data, "Snivy", 5))
    # starterNameList.append('snivy')
    # starterList.append(Pokemon(data, "Tepig", 5))
    # starterNameList.append('tepig')
    # starterList.append(Pokemon(data, "Oshawott", 5))
    # starterNameList.append('oshawott')
    # starterList.append(Pokemon(data, "Chespin", 5))
    # starterNameList.append('chespin')
    # starterList.append(Pokemon(data, "Fennekin", 5))
    # starterNameList.append('fennekin')
    # starterList.append(Pokemon(data, "Froakie", 5))
    # starterNameList.append('froakie')
    # starterList.append(Pokemon(data, "Rowlet", 5))
    # starterNameList.append('rowlet')
    # starterList.append(Pokemon(data, "Litten", 5))
    # starterNameList.append('litten')
    # starterList.append(Pokemon(data, "Popplio", 5))
    # starterNameList.append('popplio')
    # starterList.append(Pokemon(data, "Grookey", 5))
    # starterNameList.append('grookey')
    # starterList.append(Pokemon(data, "Scorbunny", 5))
    # starterNameList.append('scorbunny')
    # starterList.append(Pokemon(data, "Sobble", 5))
    # starterNameList.append('sobble')
    view = PokeNavComponents.ChooseStarterView(inter.author, data)
    files, embed = createNewUserEmbed(inter, trainer)
    message = await inter.channel.send(embed=embed, view=view, files=files)
    try:
        res: MessageInteraction = await bot.wait_for(
            "dropdown",
            check=lambda m: m.author.id == inter.author.id,
            timeout=300,
        )
        await res.response.defer()
    except asyncio.TimeoutError:
        await endSession(inter)
        return await inter.channel.send(
            f"<@!{inter.author.id}> you didn't choose a starter on time!"
        )
    chosenPokemon = view.get_starter(view.select_menu.values[0])
    await startAdventure(inter, message, trainer, chosenPokemon)


async def startAdventure(inter, message, trainer, starter):
    trainer.addPokemon(starter, True, True)
    await message.delete()
    confirmationText = "Congratulations! You obtained " + starter.name + "! Get ready for your Pokemon adventure!\n(continuing automatically in 5 seconds...)"
    confirmation = await inter.channel.send(confirmationText)
    await sleep(5)
    await confirmation.delete()
    await startOverworldUI(inter, trainer)


async def startMoveTutorUI(inter, trainer, partySlot, isTM, offset=0, goBackTo='', otherData=None):
    logging.debug(str(inter.author.id) + " - startMoveTutorUI()")
    dataTuple = (trainer, partySlot, isTM, offset, goBackTo, otherData)
    pokemon = trainer.partyPokemon[partySlot]
    if isTM:
        moveListTM = pokemon.getAllTmMoves()
        moveListEgg = pokemon.getAllEggMoves()
        moveList = moveListTM + moveListEgg
    else:
        moveList = pokemon.getAllLevelUpMoves()
    maxPages = math.ceil(len(moveList) / 9)
    if (maxPages < 1):
        maxPages = 1
    files, embed = createMoveTutorEmbed(inter, trainer, pokemon, moveList, offset, isTM)  # is page number
    emojiNameList = []
    buttonList = []
    for x in range(1, 10):
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji(str(x)), style=discord.ButtonStyle.grey,
                                                identifier=str(x)))
        emojiNameList.append(str(x))
    emojiNameList.append('left arrow')
    emojiNameList.append('right arrow')
    emojiNameList.append('down arrow')
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('left arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='left arrow'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('right arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='right arrow'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='down arrow'))

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        index = None

        if (chosenEmoji == '1' and len(moveList) >= 1 + (offset * 9)):
            index = 0
        elif (chosenEmoji == '2' and len(moveList) >= 2 + (offset * 9)):
            index = 1
        elif (chosenEmoji == '3' and len(moveList) >= 3 + (offset * 9)):
            index = 2
        elif (chosenEmoji == '4' and len(moveList) >= 4 + (offset * 9)):
            index = 3
        elif (chosenEmoji == '5' and len(moveList) >= 5 + (offset * 9)):
            index = 4
        elif (chosenEmoji == '6' and len(moveList) >= 6 + (offset * 9)):
            index = 5
        elif (chosenEmoji == '7' and len(moveList) >= 7 + (offset * 9)):
            index = 6
        elif (chosenEmoji == '8' and len(moveList) >= 8 + (offset * 9)):
            index = 7
        elif (chosenEmoji == '9' and len(moveList) >= 9 + (offset * 9)):
            index = 8
        elif (chosenEmoji == 'left arrow'):
            if (offset == 0 and maxPages != 1):
                offset = maxPages - 1
                files, embed = createMoveTutorEmbed(inter, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
            elif (offset > 0):
                offset -= 1
                files, embed = createMoveTutorEmbed(inter, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'right arrow'):
            if (offset + 1 < maxPages):
                offset += 1
                files, embed = createMoveTutorEmbed(inter, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
            elif (offset + 1 == maxPages and maxPages != 1):
                offset = 0
                files, embed = createMoveTutorEmbed(inter, trainer, pokemon, moveList, offset, isTM)
                await message.edit(embed=embed)
        elif (chosenEmoji == 'down arrow'):
            if (goBackTo == 'startOverworldUI'):
                await message.delete()
                await startOverworldUI(inter, otherData[0])
                break
        if index is not None:
            if (trainer.getItemAmount('money') < 3000):
                embed.set_footer(text="Not enough PokeDollars! Need $3000.")
                await message.edit(embed=embed)
            else:
                await message.delete()
                await startLearnNewMoveUI(inter, trainer, pokemon, moveList[(index) + (offset * 9)], 'startMoveTutorUI',
                                          dataTuple)
                break
        chosenEmoji, message = await continueUI(inter, message, emojiNameList)


async def startLearnNewMoveUI(inter, trainer, pokemon, move, goBackTo='', otherData=None):
    logging.debug(str(inter.author.id) + " - startLearnNewMoveUI()")
    alreadyLearned = False
    for learnedMove in pokemon.moves:
        if learnedMove['names']['en'] == move['names']['en']:
            alreadyLearned = True
            message = await inter.channel.send(pokemon.nickname + " already knows " + move['names'][
                'en'] + "!" + " (continuing automatically in 4 seconds...)")
            await sleep(4)
            await message.delete()
    if not alreadyLearned:
        if (len(pokemon.moves) >= 4):
            text = str(inter.author) + "'s " + pokemon.nickname + " would like to learn " + move['names'][
                'en'] + ". Please select move to replace."
            count = 1
            newMoveCount = count
            for learnedMove in pokemon.moves:
                text = text + "\n(" + str(count) + ") " + learnedMove['names']['en']
                count += 1
            newMoveCount = count
            text = text + "\n(" + str(count) + ") " + move['names']['en']
            emojiNameList = []
            buttonList = []
            for x in range(1, count + 1):
                emojiNameList.append(str(x))
                buttonList.append(
                    PokeNavComponents.OverworldUIButton(emoji=data.getEmoji(str(x)), style=discord.ButtonStyle.grey,
                                                        row=0,
                                                        identifier=str(x)))
                # await message.add_reaction(data.getEmoji(str(x)))

            view = PokeNavComponents.OverworldUIView(inter, buttonList)
            message = await inter.channel.send(text, view=view)
            chosenEmoji, message = await startNewUI(inter, None, None, buttonList, timeout, message=message)

            if (chosenEmoji == '1'):
                if (newMoveCount != 1):
                    oldMoveName = pokemon.moves[0]['names']['en']
                    pokemon.replaceMove(0, move)
                    await message.delete()
                    trainer.useItem('money', 3000)
                    message = await inter.channel.send(
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
                    message = await inter.channel.send(
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
                    message = await inter.channel.send(
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
                    message = await inter.channel.send(
                        pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names'][
                            'en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
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
            trainer.useItem('money', 3000)
            message = await inter.channel.send(
                pokemon.nickname + " learned " + move['names'][
                    'en'] + "!" + "\nGave the move tutor $3000.\n(continuing automatically in 4 seconds...)")
            await sleep(4)
            await message.delete()
    if goBackTo == 'startMoveTutorUI':
        await startMoveTutorUI(inter, otherData[0], otherData[1], otherData[2], otherData[3], otherData[4],
                               otherData[5])
        return


async def startCutsceneUI(inter, cutsceneStr, trainer, goBackTo='', otherData=None):
    logging.debug(str(inter.author.id) + " - startCutsceneUI()")
    files, embed = createCutsceneEmbed(inter, cutsceneStr)
    message = await inter.channel.send(files=files, embed=embed)
    await sleep(10)
    await message.delete()
    await startOverworldUI(inter, trainer)


async def startBattleTowerSelectionUI(inter, trainer, withRestrictions):
    logging.debug(str(inter.author.id) + " - startBattleTowerSelectionUI()")
    dataTuple = (trainer, withRestrictions)
    trainer.pokemonCenterHeal()
    files, embed = createPartyUIEmbed(inter, trainer, False, None, "Battle Tower Selection",
                                      "[react to #'s to select 3 Pokemon then hit the check mark]")
    emojiNameList = []
    count = 1
    buttonList = []
    for pokemon in trainer.partyPokemon:
        emojiNameList.append(str(count))
        row = 0
        if count > 3:
            row = 1
        buttonList.append(
            PokeNavComponents.OverworldUIButton(emoji=data.getEmoji(str(count)), style=discord.ButtonStyle.grey,
                                                row=row,
                                                identifier=str(count)))
        count += 1
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('confirm'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='confirm'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(emoji=data.getEmoji('down arrow'), style=discord.ButtonStyle.grey, row=2,
                                            identifier='down arrow'))
    emojiNameList.append('confirm')
    emojiNameList.append('down arrow')

    ignoreList = ['1', '2', '3', '4', '5', '6']
    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList, timeout, None, ignoreList)
    messageID = message.id

    chosenPokemonNums = []

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (
                chosenEmoji == '1' or chosenEmoji == '2' or chosenEmoji == '3' or chosenEmoji == '4' or chosenEmoji == '5' or chosenEmoji == '6'):
            index = int(chosenEmoji) - 1
            button = buttonList[index]
            if button.style == discord.ButtonStyle.green:
                button.style = discord.ButtonStyle.grey
                chosenPokemonNums.remove(index + 1)
            else:
                button.style = discord.ButtonStyle.green
                chosenPokemonNums.append(index + 1)
            view = PokeNavComponents.OverworldUIView(inter.author, buttonList)
            await message.edit(view=view)
        elif (chosenEmoji == 'confirm'):
            if len(chosenPokemonNums) > 3:
                embed.set_footer(text="Too many Pokemon selected.")
                await message.edit(embed=embed)
            elif len(chosenPokemonNums) < 3:
                embed.set_footer(text="Not enough Pokemon selected.")
                await message.edit(embed=embed)
            else:
                trainerCopy, valid = battleTower.getBattleTowerUserCopy(trainer, chosenPokemonNums[0],
                                                                        chosenPokemonNums[1], chosenPokemonNums[2],
                                                                        withRestrictions)
                if valid:
                    await message.delete()
                    await startBattleTowerUI(inter, trainer, trainerCopy, withRestrictions)
                    break
                else:
                    embed.set_footer(text="Restricted Pokemon may not be used.")
                    await message.edit(embed=embed)
        elif (chosenEmoji == 'down arrow'):
            await message.delete()
            await startOverworldUI(inter, trainer)
            break
        chosenEmoji, message = await continueUI(inter, message, emojiNameList, timeout, ignoreList)


async def startBattleTowerUI(inter, trainer, trainerCopy, withRestrictions, bpToEarn=0):
    logging.debug(str(inter.author.id) + " - startBattleTowerUI()")
    if bpToEarn > 0:
        trainer.addItem('BP', bpToEarn)
    trainer.pokemonCenterHeal()
    trainerCopy.pokemonCenterHeal()
    dataTuple = (trainer, trainerCopy, withRestrictions)
    files, embed = createBattleTowerUI(inter, trainer, withRestrictions)
    emojiNameList = []
    buttonList = []
    emojiNameList.append('1')
    emojiNameList.append('2')
    emojiNameList.append('3')
    buttonList.append(PokeNavComponents.OverworldUIButton(label='Battle', style=discord.ButtonStyle.green, row=0,
                                                          identifier='1'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(label='Party', style=discord.ButtonStyle.green, row=0,
                                            identifier='2'))
    buttonList.append(
        PokeNavComponents.OverworldUIButton(label='Retire (progress will be saved)', style=discord.ButtonStyle.red,
                                            row=1,
                                            identifier='3'))

    chosenEmoji, message = await startNewUI(inter, embed, files, buttonList)

    while True:
        if (chosenEmoji == None and message == None):
            break
        if (chosenEmoji == '1'):
            if (trainer.dailyProgress > 0 or not data.staminaDict[str(inter.guild.id)]):
                if (data.staminaDict[str(inter.guild.id)]):
                    trainer.dailyProgress -= 1
                await message.delete()
                battle = Battle(data, trainerCopy, battleTower.getBattleTowerTrainer(trainer, withRestrictions))
                battle.disableExp()
                battle.startBattle()
                await startBeforeTrainerBattleUI(inter, False, battle, 'startBattleTowerUI', dataTuple)
                break
            else:
                embed.set_footer(text="Out of stamina for today! Please come again tomorrow!")
                await message.edit(embed=embed)
        elif (chosenEmoji == '2'):
            await message.delete()
            await startPartyUI(inter, trainerCopy, 'startBattleTowerUI', None, dataTuple)
            break
        elif (chosenEmoji == '3'):
            await message.delete()
            await startOverworldUI(inter, trainer)
            break
        chosenEmoji, message = await continueUI(inter, message, emojiNameList)


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
            await bot.change_presence(activity=discord.Game(
                name="on " + str(len(bot.guilds)) + " servers with " + numUniqueUsers + " trainers! | /help"))
        except:
            pass
        try:
            logging.debug("Saving...")
            data.writeUsersToJSON()
            logging.debug("Save complete.")
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
logging.getLogger('disnake').setLevel(logging.WARNING)
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
timeBetweenSaves = 600
errorChannel1 = 831720385878818837
errorChannel2 = 804463066241957981
botId = 800207357622878229
stuckList = {}
data = pokeData()
data.setBot(bot)
data.readUsersFromJSON()
battleTower = Battle_Tower(data)
secretBaseUi = Secret_Base_UI(bot, timeout, data, startNewUI, continueUI, startOverworldUI, endSession)
bot.run(TOKEN)
