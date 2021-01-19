import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from Data import pokeData
from Pokemon import Pokemon
from Battle import Battle
from Trainer import Trainer
from PIL import Image
from time import sleep
import math
import traceback
import copy
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    pass
    #print("Pokemon Bot Is Ready And Online!")

@bot.command(name='start', help='starts the game', aliases=['s'])
async def startGame(ctx):
    try:
        user, isNewUser = data.getUser(ctx)
        #print('isNewUser = ', isNewUser)
        sessionSuccess = data.addUserSession(user)
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
        await ctx.send(str(str(ctx.message.author.display_name) + "'s session ended in error.\n" + str(traceback.format_exc()))[:1999])
        await endSession(ctx)

def updateStamina(user):
    if (datetime.today().date() > user.date):
        user.dailyProgress = 10
        user.date = datetime.today().date()

async def endSession(ctx):
    user, isNewUser = data.getUser(ctx)
    removedSuccessfully = data.removeUserSession(user)
    if (removedSuccessfully):
        await ctx.send(ctx.message.author.display_name + 's connection closed. Please start game again.')
    else:
        pass
        #print("Session unable to end, not in session list: " + str(ctx.message.author.display_name))

@bot.command(name='nickname', help='nickname a Pokemon, use: "!nickname [party position] [nickname]"', aliases=['nn'])
async def nickname(ctx, partyPos, nickname):
    partyPos = int(partyPos) - 1
    user, isNewUser = data.getUser(ctx)
    if isNewUser:
        await ctx.send("You have not yet played the game and have no Pokemon!")
    else:
        if (len(user.partyPokemon) > partyPos):
            await ctx.send(user.partyPokemon[partyPos].nickname + " was renamed to '" + nickname + "'!")
            user.partyPokemon[partyPos].nickname = nickname
            data.writeUsersToJSON()
        else:
            await ctx.send("No Pokemon in that party slot.")

@bot.command(name='profile', help="get a Trainer's profile, use: '!profile [trainer name]'", aliases=['p'])
async def profile(ctx, *, userName: str="self"):
    if userName == 'self':
        user, isNewUser = data.getUserByAuthor(ctx.author)
    else:
        user, isNewUser = data.getUserByAuthor(userName)
    if not isNewUser:
        embed = createProfileEmbed(ctx, user)
        await ctx.send(embed=embed)
    else:
        await ctx.send("User '" + userName + "' not found.")


@bot.command(name='guide', help='helpful guide', aliases=['g'])
async def getGuide(ctx):
    await ctx.send('Check out our guide here:\nhttps://github.com/zetaroid/pokeDiscordPublic/blob/main/README.md')

@bot.command(name='moveInfo', help='get information about a move', aliases=['mi'])
async def getMoveInfo(ctx, moveName="Invalid"):
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
            moveDesc = 'No description'
        result = 'Name: ' + moveName + '\nPower: ' + str(movePower) + '\nPP: ' + str(movePP) + '\nAccuracy: ' + str(moveAcc) + '\nType: ' + moveType + '\nDescription: ' + moveDesc
        await ctx.send(result)
    else:
        await ctx.send('Invalid move')

@bot.command(name='testWorld', help='testWorld')
async def testWorldCommand(ctx):
    pokemon = Pokemon(data, "Deoxys", 70)
    pokemon.setNickname('Kippy')
    trainer = Trainer("Zetaroid", "Marcus", "Dewford Gym")
    pokemon2 = Pokemon(data, "Charmander", 2)
    trainer.addFlag("rival1")
    trainer.addFlag("badge1")
    trainer.addFlag("briney")
    trainer.addFlag("rival1")
    trainer.progress('Dewford Gym')
    trainer.progress('Dewford Gym')
    #trainer.progress("Rusturf Tunnel")
    trainer.addPokemon(pokemon, True)
    trainer.addPokemon(pokemon2, True)
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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
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
                        sleep(4)
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
                            sleep(4)
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
    file = discord.File(pokemon.spritePath, filename="image.png")
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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
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
                        sleep(4)
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
                                sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1],otherData[2])
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
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(1, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[1]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        #print(itemCanBeUsed)
                        if (itemCanBeUsed):
                            battle.sendUseItemCommand(itemToUse, pokemonForItem)
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                            else:  # TODO elif return to overworld/bag/whatev
                                await message.remove_reaction(reaction, user)
                                await waitForEmoji(ctx)
                        elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
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
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(2, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[2]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            battle.sendUseItemCommand(itemToUse, pokemonForItem)
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1], otherData[2])
                                return
                            else:  # TODO elif return to overworld/bag/whatev
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
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(3, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[3]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            battle.sendUseItemCommand(itemToUse, pokemonForItem)
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                                return
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1],otherData[2])
                                return
                            else:  # TODO elif return to overworld/bag/whatev
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
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(4, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[4]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            battle.sendUseItemCommand(itemToUse, pokemonForItem)
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1],otherData[2])
                                return
                            else:  # TODO elif return to overworld/bag/whatev
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
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(5, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                        return
                    elif (itemToUse is not None):
                        pokemonForItem = trainer.partyPokemon[5]
                        itemCanBeUsed, uselessText = pokemonForItem.useItemOnPokemon(itemToUse, True)
                        if (itemCanBeUsed):
                            battle.sendUseItemCommand(itemToUse, pokemonForItem)
                            if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                                await message.delete()
                                await startBattleUI(ctx, otherData[0], battle, otherData[2], otherData[3], True)
                            elif (goBackTo == "startBagUI"):
                                itemBool, itemText = pokemonForItem.useItemOnPokemon(itemToUse)
                                trainer.useItem(itemToUse, 1)
                                await message.delete()
                                confirmation = await ctx.send(itemText + "\n(continuing in 4 seconds...)")
                                sleep(4)
                                await confirmation.delete()
                                await startBagUI(ctx, otherData[0], otherData[1],otherData[2])
                                return
                            else:  # TODO elif return to overworld/bag/whatev
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

def createPartyUIEmbed(ctx, trainer, isBoxSwap=False, itemToUse=None):
    files = []
    if isBoxSwap:
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
        embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")", value=embedValue, inline=True)
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
    mergeImages(pokemon1.spritePath, pokemon2.spritePath)
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
                    sleep(2)
                    embed.clear_fields()
                    createBattleEmbedFields(embed, pokemon1, pokemon2)
                    await message.edit(embed=embed)
                    sleep(2)
            goStraightToResolve = False # shadows outer scope?
            battle.clearCommands()
            displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted = battle.endTurn()
            #embed.clear_fields()
            #createBattleEmbedFields(embed, pokemon1, pokemon2)
            #await message.edit(embed=embed)
            if (displayText != ''):
                embed.set_footer(text=createTextFooter(pokemon1, pokemon2, displayText))
                await message.edit(embed=embed)
                sleep(6)
            if shouldBattleEnd: # TODO finish shouldBattleEnd to return to overworld
                pokemonToEvolveList, pokemonToLearnMovesList = battle.endBattle()
                if (isWin):
                    rewardText = ''
                    if (battle.trainer2 is not None):
                        for rewardName, rewardValue in battle.trainer2.rewards.items():
                            if (rewardName == "flag"):
                                battle.trainer1.addFlag(rewardValue)
                            else:
                                rewardText = rewardText + "\n" + rewardName.capitalize() + ": " + str(rewardValue)
                                #print("giving " + battle.trainer1.name + " " + rewardName + "x" + str(rewardValue))
                                battle.trainer1.addItem(rewardName, rewardValue)
                        for flagName in battle.trainer2.rewardFlags:
                            battle.trainer1.addFlag(flagName)
                    if rewardText:
                        rewardText = "Rewards:" + rewardText + "\n\n(returning to overworld in 4 seconds...)"
                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, rewardText))
                        await message.edit(embed=embed)
                        sleep(4)
                    await message.delete()
                else:
                    await message.delete()
                    battle.trainer1.removeProgress(battle.trainer1.location)
                    battle.trainer1.location = battle.trainer1.lastCenter
                    battle.trainer1.pokemonCenterHeal()
                await afterBattleCleanup(ctx, battle, pokemonToEvolveList, pokemonToLearnMovesList)
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
                    sleep(3)
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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
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
                                    sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            sleep(2)
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
                                        sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        sleep(4)
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
                                    sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            sleep(2)
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
                                        sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        sleep(4)
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
                                    sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            sleep(2)
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
                                        sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        sleep(4)
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
                            sleep(4)
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
                                    sleep(3)
                                    caught, shakes, sentToBox = battle.catchPokemon(ball)
                                    failText = ''
                                    if (shakes > 0):
                                        for x in range(0, shakes):
                                            embed.clear_fields()
                                            createBattleEmbedFields(embed, pokemon1, pokemon2, ball, x+1)
                                            await message.edit(embed=embed)
                                            sleep(2)
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
                                        sleep(6)
                                        await message.delete()
                                        battle.battleRefresh()
                                        await startOverworldUI(ctx, battle.trainer1)
                                        return
                                    else:
                                        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, failText))
                                        await message.edit(embed=embed)
                                        sleep(4)
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
    if (category == "Balls"):
        items = ["Pokeball", "Greatball", "Ultraball", "Masterball"]
    elif (category == "Healing Items"):
        items = ["Potion", "Super Potion", "Hyper Potion", "Max Potion"]
    elif (category == "Status Items"):
        items = ["Full Restore", "Full Heal", "Revive", "Max Revive"]
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

async def afterBattleCleanup(ctx, battle, pokemonToEvolveList, pokemonToLearnMovesList):
    trainer = battle.trainer1
    for pokemon in pokemonToEvolveList:
        #print('evolist')
        #print(pokemon.nickname)
        oldName = copy.copy(pokemon.nickname)
        pokemon.evolve()
        embed = discord.Embed(title="Congratulations! " + str(ctx.message.author) + "'s " + oldName + " evolved into " + pokemon.evolveToAfterBattle + "!", description="(continuing automatically in 6 seconds...)", color=0x00ff00)
        file = discord.File(pokemon.spritePath, filename="image.png")
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
        embed.set_author(name=(ctx.message.author.display_name + "'s Pokemon Evolved:"))
        message = await ctx.send(file=file, embed=embed)
        sleep(6)
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
                        reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
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
                                    sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('2')):
                                if (newMoveCount != 2):
                                    oldMoveName = pokemon.moves[1]['names']['en']
                                    pokemon.replaceMove(1, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('3')):
                                if (newMoveCount != 3):
                                    oldMoveName = pokemon.moves[2]['names']['en']
                                    pokemon.replaceMove(2, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('4')):
                                if (newMoveCount != 4):
                                    oldMoveName = pokemon.moves[3]['names']['en']
                                    pokemon.replaceMove(3, move)
                                    await message.delete()
                                    message = await ctx.send(pokemon.nickname + ' forgot ' + oldMoveName + " and learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                                    sleep(4)
                                    await message.delete()
                            elif (str(reaction.emoji) == data.getEmoji('5')):
                                await message.delete()
                                message = await ctx.send("Gave up on learning " + move['names']['en'] + "." + " (continuing automatically in 4 seconds...)")
                                sleep(4)
                                await message.delete()

                await waitForEmoji(ctx, message)
            else:
                pokemon.learnMove(move)
                message = await ctx.send(pokemon.nickname + " learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                sleep(4)
                await message.delete()
    battle.battleRefresh()
    await startOverworldUI(ctx, trainer)

def mergeImages(path1, path2):
    background = Image.open('data/sprites/background.png')
    background = background.convert('RGBA')
    image1 = Image.open(path1)
    image1 = image1.transpose(method=Image.FLIP_LEFT_RIGHT)
    image2 = Image.open(path2)
    background.paste(image1, (12,40), image1.convert('RGBA'))
    background.paste(image2, (130,0), image2.convert('RGBA'))
    background.save("data/temp/merged_image.png","PNG")

async def startOverworldUI(ctx, trainer):
    data.writeUsersToJSON()
    files, embed, overWorldCommands = createOverworldEmbed(ctx, trainer)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    count = 1
    for command in overWorldCommands:
        await message.add_reaction(data.getEmoji(str(count)))
        count += 1

    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('5')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('6'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('7')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('8'))
                or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('9')))

    async def waitForEmoji(ctx):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            dataTuple = (trainer,)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(overWorldCommands) > 0):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[1], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('2') and len(overWorldCommands) > 1):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[2], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('3') and len(overWorldCommands) > 2):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[3], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('4') and len(overWorldCommands) > 3):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[4], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('5') and len(overWorldCommands) > 4):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[5], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('6') and len(overWorldCommands) > 5):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[6], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('7') and len(overWorldCommands) > 6):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[7], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('8') and len(overWorldCommands) > 7):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[8], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
                        return
                elif (str(reaction.emoji) == data.getEmoji('9') and len(overWorldCommands) > 8):
                    newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle = executeWorldCommand(trainer, overWorldCommands[9], embed)
                    if (embedNeedsUpdating):
                        await message.edit(embed=newEmbed)
                    else:
                        await resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle)
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

async def resolveWorldCommand(ctx, message, trainer, dataTuple, newEmbed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle):
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
    elif (battle is not None):
        battle.startBattle()
        await message.delete()
        if not battle.isWildEncounter:
            await startBeforeTrainerBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)
        else:
            await startBattleUI(ctx, battle.isWildEncounter, battle, 'startOverworldUI', dataTuple)

def executeWorldCommand(trainer, command, embed):
    embedNeedsUpdating = False
    reloadArea = False
    goToBox = False
    goToMart = False
    goToParty = False
    goToBag = False
    battle = None
    footerText = '[react to # to do commands]'
    if (command[0] == "party"):
        goToParty = True
    elif (command[0] == "bag"):
        goToBag = True
    elif (command[0] == "progress"):
        if (trainer.dailyProgress > 0):
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
                        battle = Battle(data, trainer, None, locationDataObj.entryType, event.pokemon)
            else:
                if (locationDataObj.hasWildEncounters):
                    battle = Battle(data, trainer, None, locationDataObj.entryType)
        else:
            embed.set_footer(text=footerText + "\n\nOut of stamina for today! Please come again tomorrow!")
            embedNeedsUpdating = True
    elif (command[0] == "wildEncounter"):
        if (trainer.dailyProgress > 0):
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
    elif (command[0] == "travel"):
        trainer.location = command[1]
        reloadArea = True
    return embed, embedNeedsUpdating, reloadArea, goToBox, goToBag, goToMart, goToParty, battle

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
    embed.set_footer(text='[react to # to do commands]')
    embed.set_author(name=(ctx.message.author.display_name + " is exploring the world:\n(remaining stamina: " + str(trainer.dailyProgress) + ")"))

    optionsText = ''
    count = 1
    optionsText = optionsText + "(" + str(count) + ") Party\n"
    overWorldCommands[count] = ('party',)
    count += 1
    optionsText = optionsText + "(" + str(count) + ") Bag\n"
    overWorldCommands[count] = ('bag',)
    count += 1
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
    if (locationObj.hasPokemonCenter):
        optionsText = optionsText + "(" + str(count) + ") Heal at Pokemon Center\n"
        overWorldCommands[count] = ('heal',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Access the Pokemon Storage System\n"
        overWorldCommands[count] = ('box',)
        count += 1
    if (locationObj.hasMart):
        optionsText = optionsText + "(" + str(count) + ") Shop at Pokemart\n"
        overWorldCommands[count] = ('mart',)
        count += 1

    for nextLocationName, nextLocationObj in locationObj.nextLocations.items():
        if (nextLocationObj.checkRequirements(trainer)):
            optionsText = optionsText + "(" + str(count) + ") Travel to " + nextLocationName + "\n"
            overWorldCommands[count] = ('travel', nextLocationName)
            count += 1

    embed.add_field(name='Options:', value=optionsText, inline=True)
    return files, embed, overWorldCommands

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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await endSession(ctx)
        else:
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(itemDict) >= 1):
                    key = list(itemDict.keys())[0]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        #print("mart: " + trainer.name + "bought " + key + " and now has a total of " + str(trainer.getItemAmount(key)))
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('2') and len(itemDict) >= 2):
                    key = list(itemDict.keys())[1]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('3') and len(itemDict) >= 3):
                    key = list(itemDict.keys())[2]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('4') and len(itemDict) >= 4):
                    key = list(itemDict.keys())[3]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('5') and len(itemDict) >= 5):
                    key = list(itemDict.keys())[4]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('6') and len(itemDict) >= 6):
                    key = list(itemDict.keys())[5]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('7') and len(itemDict) >= 7):
                    key = list(itemDict.keys())[6]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('8') and len(itemDict) >= 8):
                    key = list(itemDict.keys())[7]
                    if (trainer.getItemAmount('money') >= itemDict[key]):
                        trainer.addItem('money', -1 * itemDict[key])
                        trainer.addItem(key, 1)
                        embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money'))
                                              + "\nBought 1x " + key + " for $" + str(itemDict[key]) + ".")
                        await message.edit(embed=embed)
                elif (str(reaction.emoji) == data.getEmoji('9') and len(itemDict) >= 9):
                    key = list(itemDict.keys())[8]
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
        embed.add_field(name="(" + str(count) + ") " + item, value="$" + str(price), inline=True)
        count += 1
    embed.set_author(name=ctx.message.author.display_name + " is shopping:")
    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')))
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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
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
                        pass
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
        embed.add_field(name="Pockets:", value="(1) Balls\n(2) Healing Items\n(3) Status Items", inline=True)
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
    embed.set_footer(text="PokeDollars: " + str(trainer.getItemAmount('money')))
    return files, embed

async def startBeforeTrainerBattleUI(ctx, isWildEncounter, battle, goBackTo='', otherData=None):
    files, embed = createBeforeTrainerBattleEmbed(ctx, battle.trainer2)
    message = await ctx.send(files=files, embed=embed)
    sleep(6)
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
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
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
    data.writeUsersToJSON()
    await message.delete()
    confirmationText = "Congratulations! You obtained " + starter.name + "! Get ready for your Pokemon adventure!\n(continuing automatically in 5 seconds...)"
    confirmation = await ctx.send(confirmationText)
    sleep(5)
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
    if ('badge8' in trainer.flags):
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
    descString = "Badges: " + str(numberOfBadges)
    if ('elite4' in trainer.flags):
        descString = descString + "\nElite 4 Cleared: Yes"
    else:
        descString = descString + "\nElite 4 Cleared: No"
    descString = descString + "\nPokemon Caught: " + str(len(trainer.partyPokemon) + len(trainer.boxPokemon))
    descString = descString + "\n\nParty:"
    embed = discord.Embed(title=trainer.name + "'s Profile", description=descString, color=0x00ff00)
    for pokemon in trainer.partyPokemon:
        levelString = "Level: " + str(pokemon.level)
        shinyString = ''
        if pokemon.shiny:
            shinyString = " :star2:"
        embedValue = levelString
        embed.add_field(name=pokemon.nickname + " (" + pokemon.name + ")" + shinyString, value=embedValue,
                        inline=True)
    embed.set_author(name=(ctx.message.author.display_name + " requested this profile."))
    return embed

data = pokeData()
data.readUsersFromJSON()
bot.run(TOKEN)
