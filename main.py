import praw
import random
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import pokebase as pb
from Data import pokeData
from Pokemon import Pokemon
from Battle import Battle
from Trainer import Trainer
from Location import Location
from PIL import Image
from time import sleep
import math

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print("Pokemon Bot Is Ready And Online!")

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

@bot.command(name='testMart', help='testMart')
async def testMartCommand(ctx):
    pokemon = Pokemon(data, "Pidgeot", 15)
    pokemon.setNickname('Pidgster')
    trainer = Trainer("Zetaroid", "Marcus", "Route 101")
    trainer.addPokemon(pokemon, True)
    trainer.addItem('money', 100000)
    trainer.addFlag('rival1')
    await startMartUI(ctx, trainer)

@bot.command(name='testWorld', help='testWorld')
async def testWorldCommand(ctx):
    pokemon = Pokemon(data, "Pidgeot", 15)
    pokemon.setNickname('Pidgster')
    trainer = Trainer("Zetaroid", "Marcus", "Route 101")
    trainer.addPokemon(pokemon, True)
    trainer.addFlag('rival1')
    await startOverworldUI(ctx, trainer)

@bot.command(name='testBox', help='testBox')
async def testBoxCommand(ctx):
    pokemon = Pokemon(data, "Pidgeot", 15)
    pokemon.setNickname('Pidgster')
    pokemon2 = Pokemon(data, "Blaziken", 100)
    pokemon3 = Pokemon(data, "Rayquaza", 100)
    pokemon4 = Pokemon(data, "Mew", 100)
    pokemon5 = Pokemon(data, "Entei", 62)
    pokemon6 = Pokemon(data, "Celebi", 100)
    pokemon7 = Pokemon(data, "Hariyama", 100)
    pokemon8 = Pokemon(data, "Swampert", 100)
    pokemon9 = Pokemon(data, "Sceptile", 100)
    pokemon10 = Pokemon(data, "Zigzagoon", 100)
    pokemon11 = Pokemon(data, "Oddish", 100)
    pokemon12 = Pokemon(data, "Gloom", 100)
    pokemon13 = Pokemon(data, "Muk", 100)
    pokemon14 = Pokemon(data, "Grimer", 100)
    pokemon15 = Pokemon(data, "Voltorb", 100)
    pokemon16 = Pokemon(data, "Hitmonchan", 100)
    trainer = Trainer("Zetaroid", "Marcus", "Route 101")
    trainer.addPokemon(pokemon, True)
    trainer.addPokemon(pokemon2, True)
    trainer.addPokemon(pokemon3, True)
    trainer.addPokemon(pokemon4, True)
    trainer.addPokemon(pokemon5, True)
    trainer.addPokemon(pokemon6, True)
    trainer.addPokemon(pokemon7, True)
    trainer.addPokemon(pokemon8, True)
    trainer.addPokemon(pokemon9, True)
    trainer.addPokemon(pokemon10, True)
    trainer.addPokemon(pokemon11, True)
    trainer.addPokemon(pokemon12, True)
    trainer.addPokemon(pokemon13, True)
    trainer.addPokemon(pokemon14, True)
    trainer.addPokemon(pokemon15, True)
    trainer.addPokemon(pokemon16, True)
    await startBoxUI(ctx, trainer)

@bot.command(name='testParty', help='testBattle')
async def test3Command(ctx):
    pokemon = Pokemon(data, "Mudkip", 15)
    pokemon.addStatus("burn")
    pokemon.setNickname('Kippy')
    pokemon2 = Pokemon(data, "Blaziken", 100)
    pokemon3 = Pokemon(data, "Rayquaza", 100)
    pokemon4 = Pokemon(data, "Mew", 100)
    pokemon5 = Pokemon(data, "Torchic", 100)
    pokemon6 = Pokemon(data, "Celebi", 100)
    trainer = Trainer("Zetaroid", "Marcus", "Route 101")
    trainer.addPokemon(pokemon)
    trainer.addPokemon(pokemon2, True)
    trainer.addPokemon(pokemon3, True)
    trainer.addPokemon(pokemon4, True)
    trainer.addPokemon(pokemon5, True)
    trainer.addPokemon(pokemon6, True)
    await startPartyUI(ctx, trainer)
    
@bot.command(name='testSummary', help='testBattle')
async def test2Command(ctx):
    pokemon = Pokemon(data, "Mudkip", 100)
    pokemon.evolveToAfterBattle = 'Swampert'
    pokemon.evolve()
    pokemon.addStatus("burn")
    pokemon.setNickname('Kippy')
    trainer = Trainer("Zetaroid", "Marcus", "Route 103")
    trainer.addPokemon(pokemon, True)
    await startPokemonSummaryUI(ctx, trainer, 0)

@bot.command(name='testTrainer', help='testTrainerBattle')
async def testTrainerCommand(ctx):
    pokemon = Pokemon(data, "Arceus", 100)
    pokemon.setNickname('God')
    pokemon2 = Pokemon(data, "Blaziken", 100)
    pokemon3 = Pokemon(data, "Rayquaza", 100)
    pokemon4 = Pokemon(data, "Mew", 100)
    pokemon5 = Pokemon(data, "Entei", 62)
    pokemon6 = Pokemon(data, "Celebi", 100)
    trainer = Trainer("Zetaroid", "Marcus", "Route 101")
    trainer.addPokemon(pokemon, True)
    trainer.addPokemon(pokemon2, True)
    trainer.addPokemon(pokemon3, True)
    trainer.addPokemon(pokemon4, True)
    trainer.addPokemon(pokemon5, True)
    trainer.addPokemon(pokemon6, True)
    pokemon7 = Pokemon(data, "Mudkip", 15)
    pokemon7.setNickname('Kippy2')
    pokemon8 = Pokemon(data, "Blaziken", 100)
    pokemon9 = Pokemon(data, "Rayquaza", 100)
    pokemon10 = Pokemon(data, "Mew", 100)
    pokemon11 = Pokemon(data, "Entei", 62)
    pokemon12 = Pokemon(data, "Celebi", 100)
    trainer2 = Trainer("Mai-san", "Marcus2", "Route 101")
    trainer2.addPokemon(pokemon9, True)
    trainer2.addPokemon(pokemon8, True)
    trainer2.addPokemon(pokemon7, True)
    trainer2.addPokemon(pokemon10, True)
    trainer2.addPokemon(pokemon11, True)
    trainer2.addPokemon(pokemon12, True)
    battle = Battle(data, trainer, trainer2, "Walking")
    battle.startBattle()
    await startBattleUI(ctx, False, battle)
    
@bot.command(name='test', help='testBattle')
async def test1Command(ctx):
    pokemon = Pokemon(data, "Mudkip", 15)
    #pokemon.addStatus("paralysis")
    #pokemon.addStatus("confusion")
    pokemon.setNickname('Kippy')
    pokemon2 = Pokemon(data, "Blaziken", 100)
    pokemon3 = Pokemon(data, "Rayquaza", 100)
    pokemon4 = Pokemon(data, "Mew", 100)
    pokemon5 = Pokemon(data, "Entei", 62)
    pokemon6 = Pokemon(data, "Celebi", 100)
    trainer = Trainer("Zetaroid", "Marcus", "Route 101")
    trainer.addPokemon(pokemon, True)
    trainer.addPokemon(pokemon2, True)
    trainer.addPokemon(pokemon3, True)
    trainer.addPokemon(pokemon4, True)
    trainer.addPokemon(pokemon5, True)
    trainer.addPokemon(pokemon6, True)
    battle = Battle(data, trainer, None, "Walking")
    battle.startBattle()
    await startBattleUI(ctx, True, battle)

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
            await ctx.send(ctx.message.author.display_name + 's connection closed. Please start game again.')
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
                elif (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('box') and swapToBox):
                    if (len(trainer.partyPokemon) > 1):
                        await message.delete()
                        confirmation = await ctx.send(pokemon.nickname + " sent to box! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.movePokemonPartyToBox(partyPos)
                        await startPartyUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
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
                                battle.swapCommand(trainer, partyPos)
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
                await reaction.message.remove_reaction(reaction, user)
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
    embed = discord.Embed(title=title, description="Type: " + typeString + "\n" + hpString + "\n" + levelString + "\n" + genderString + "\n" + otString + "\n" + dexString, color=0x00ff00)
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
    embed.add_field(name="----Stats----", value=("ATK: " + str(pokemon.attack) + "\nDEF: " + str(pokemon.defense) + "\nSP ATK: " + str(pokemon.special_attack) + "\nSP DEF: " + str(pokemon.special_defense) + "\nSPD: " + str(pokemon.speed)), inline=True)
    embed.add_field(name="-----IV's-----", value=("ATK: " + str(pokemon.atkIV) + "\nDEF: " + str(pokemon.defIV) + "\nSP ATK: " + str(pokemon.spAtkIV) + "\nSP DEF: " + str(pokemon.spDefIV) + "\nSPD: " + str(pokemon.spdIV)), inline=True)
    embed.add_field(name="-----EV's-----", value=("ATK: " + str(pokemon.atkEV) + "\nDEF: " + str(pokemon.defEV) + "\nSP ATK: " + str(pokemon.spAtkEV) + "\nSP DEF: " + str(pokemon.spDefEV) + "\nSPD: " + str(pokemon.spdEV)), inline=True)
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
        embed.add_field(name=('-----Move ' + str(count+1) + '-----'), value=(move['names']['en'] + "\n" + move['type'] + " " + physicalSpecialEmoji + bp + "\n" + str(pokemon.pp[count]) + "/" + str(move['pp']) + " pp"), inline=True) #todo fix pp
        count += 1
    embed.set_author(name=(ctx.message.author.display_name + "'s Pokemon Summary:"))
    brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    files.append(brendanImage)
    embed.set_thumbnail(url="attachment://image2.png")
    return files, embed

async def startPartyUI(ctx, trainer, goBackTo='', battle=None, otherData=None, goStraightToBattle=False, isBoxSwap=False, boxIndexToSwap=None, swapToBox=False):
    if (goStraightToBattle):
        if (goBackTo == 'startBattleUI'):
            await startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3], True)
            return
    files, embed = createPartyUIEmbed(ctx, trainer, isBoxSwap)
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
            await ctx.send(ctx.message.author.display_name + "'s connection closed. Please start game again.")
        else:
            dataTuple = (trainer, goBackTo, battle, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(trainer.partyPokemon) >= 1):
                    await message.delete()
                    if isBoxSwap:
                        confirmation = await ctx.send(trainer.partyPokemon[0].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(0, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await startPokemonSummaryUI(ctx, trainer, 0, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('2') and len(trainer.partyPokemon) >= 2):
                    await message.delete()
                    if isBoxSwap:
                        confirmation = await ctx.send(trainer.partyPokemon[1].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(1, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await startPokemonSummaryUI(ctx, trainer, 1, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('3') and len(trainer.partyPokemon) >= 3):
                    await message.delete()
                    if isBoxSwap:
                        confirmation = await ctx.send(trainer.partyPokemon[2].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(2, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await startPokemonSummaryUI(ctx, trainer, 2, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('4') and len(trainer.partyPokemon) >= 4):
                    await message.delete()
                    if isBoxSwap:
                        confirmation = await ctx.send(trainer.partyPokemon[3].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(3, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await startPokemonSummaryUI(ctx, trainer, 3, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('5') and len(trainer.partyPokemon) >= 5):
                    await message.delete()
                    if isBoxSwap:
                        confirmation = await ctx.send(trainer.partyPokemon[4].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(4, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await startPokemonSummaryUI(ctx, trainer, 4, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('6') and len(trainer.partyPokemon) >= 6):
                    await message.delete()
                    if isBoxSwap:
                        confirmation = await ctx.send(trainer.partyPokemon[5].nickname + " sent to box and " + trainer.boxPokemon[boxIndexToSwap].nickname + " added to party! (continuing in 4 seconds...)")
                        sleep(4)
                        await confirmation.delete()
                        trainer.swapPartyAndBoxPokemon(5, boxIndexToSwap)
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await startPokemonSummaryUI(ctx, trainer, 5, 'startPartyUI', battle, dataTuple, False, swapToBox)
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    if (goBackTo == 'startBattleUI' and ('faint' not in battle.pokemon1.statusList)):
                        await message.delete()
                        await startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    elif (goBackTo == 'startBoxUI'):
                        await message.delete()
                        await startBoxUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx)
            else:
                await message.remove_reaction(reaction, user)
                await reaction.message.remove_reaction(reaction, user)
                await waitForEmoji(ctx)
    await waitForEmoji(ctx)

def createPartyUIEmbed(ctx, trainer, isBoxSwap=False):
    files = []
    if not isBoxSwap:
        embed = discord.Embed(title="Party Summary", description="[react to # to view individual summary]", color=0x00ff00)
    else:
        embed = discord.Embed(title="CHOOSE POKEMON TO SEND TO BOX:", description="[react to # to choose Pokemon to send to box]", color=0x00ff00)
    count = 1
    for pokemon in trainer.partyPokemon:
        hpString = "HP: " + str(pokemon.currentHP) + " / " + str(pokemon.hp)
        levelString = "Level: " + str(pokemon.level)
        embed.add_field(name="[" + str(count) + "] " + pokemon.nickname + " (" + pokemon.name + ")", value=levelString + "\n" + hpString, inline=True)
        count += 1
    embed.set_author(name=(ctx.message.author.display_name))
    brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    files.append(brendanImage)
    embed.set_thumbnail(url="attachment://image.png")
    return files, embed

async def startBattleUI(ctx, isWild, battle, goBackTo='', otherData=None, goStraightToResolve=False):
    pokemon1 = battle.pokemon1
    pokemon2 = battle.pokemon2
    print('pokemon1 speed = ', pokemon1.speed)
    print('pokemon2 speed = ', pokemon2.speed)
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
        items = []
        if (category == "Balls"):
            items = ["Pokeball", "Greatball", "Ultraball", "Masterball"]
        elif (category == "Healing Items"):
            items = ["Potion", "Super Potion", "Hyper Potion", "Max Potion"]
        elif (category == "Status Items"):
            items = ["Full Restore", "Full Heal", "Revive", "Max Revive"]
        for item in items:
            if (item not in battle.trainer1.itemList.keys() or battle.trainer1.itemList[item] < 1):
                items.remove(item)
        if (goStraightToResolve):
            await message.clear_reactions()
            battle.addEndOfTurnCommands()
            battle.createCommandsList()
            for command in battle.commands:
                battleText = battle.resolveCommand(command)
                print(battleText)
                if (battleText != ''):
                    embed.set_footer(text=createTextFooter(pokemon1, pokemon2, battleText))
                    await message.edit(embed=embed)
                    sleep(4)
            goStraightToResolve = False # shadows outer scope?
            battle.clearCommands()
            displayText, shouldBattleEnd, isWin, isUserFainted, isOpponentFainted = battle.endTurn()
            embed.clear_fields()
            createBattleEmbedFields(embed, pokemon1, pokemon2)
            await message.edit(embed=embed)
            if (displayText != ''):
                embed.set_footer(text=createTextFooter(pokemon1, pokemon2, displayText))
                await message.edit(embed=embed)
                sleep(6)
            if shouldBattleEnd: # TODO
                pokemonToEvolveList, pokemonToLearnMovesList = battle.endBattle()
                if (isWin):
                    pass # return to overworld
                else:
                    pass # return to last pokemon center town
                await message.delete()
                await afterBattleCleanup(ctx, battle, pokemonToEvolveList, pokemonToLearnMovesList)
                return
            elif isUserFainted:
                dataTuple = (isWild, battle, goBackTo, otherData)
                await message.delete()
                await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple)
                return
            elif isOpponentFainted:
                await message.delete()
                await startBattleUI(ctx, isWild, battle, goBackTo, otherData, goStraightToResolve)
                return
            embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
            await message.edit(embed=embed)
            await message.add_reaction(data.getEmoji('1'))
            await message.add_reaction(data.getEmoji('2'))
            await message.add_reaction(data.getEmoji('3'))
            await message.add_reaction(data.getEmoji('4'))
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(ctx.message.author.display_name + "'s connection closed. Please start game again.")
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
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 0):
                            if(pokemon1.pp[0] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(0)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[0])
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    elif isItemUI1:
                        category = "Balls"
                        isItemUI1 = False
                        isItemUI2 = True
                        embed.set_footer(text=createItemFooter(pokemon1, pokemon2, category, items, battle.trainer1))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                elif (str(reaction.emoji) == data.getEmoji('2')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        isItemUI1 = True
                        response = 'Bag'
                        embed.set_footer(text=createItemCategoryFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await message.add_reaction(data.getEmoji('right arrow'))
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 1):
                            if(pokemon1.pp[1] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(1)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[1])
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    elif isItemUI1:
                        category = "Healing Items"
                        isItemUI1 = False
                        isItemUI2 = True
                        embed.set_footer(text=createItemFooter(pokemon1, pokemon2, category, items, battle.trainer1))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                elif (str(reaction.emoji) == data.getEmoji('3')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        response = 'Pokemon'
                        await message.delete()
                        await startPartyUI(ctx, battle.trainer1, 'startBattleUI', battle, dataTuple)
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 2):
                            if(pokemon1.pp[2] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(2)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[2])
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    elif isItemUI1:
                        category = "Status Items"
                        isItemUI1 = False
                        isItemUI2 = True
                        embed.set_footer(text=createItemFooter(pokemon1, pokemon2, category, items, battle.trainer1))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                elif (str(reaction.emoji) == data.getEmoji('4')):
                    if not isMoveUI and not isItemUI1 and not isItemUI2:
                        response = 'Run'
                        await message.remove_reaction(reaction, user)
                        canRun = battle.run()
                        if canRun:
                            await ctx.send('Got away safely!')
                            return
                        else:
                            await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    elif isMoveUI:
                        if (len(pokemon1.moves) > 3):
                            if(pokemon1.pp[3] > 0):
                                goStraightToResolve = True
                                isMoveUI = False
                                pokemon1.usePP(3)
                                battle.sendAttackCommand(pokemon1, pokemon2, pokemon1.moves[3])
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                elif ((isMoveUI or isItemUI1 or isItemUI2) and str(reaction.emoji) == data.getEmoji('right arrow')):
                    if not isItemUI2:
                        isMoveUI = False
                        isItemUI1 = False
                        embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.clear_reaction(reaction)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                    else:
                        isItemUI2 = False
                        isItemUI1 = True
                        embed.set_footer(text=createItemCategoryFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)
            else:
                await message.remove_reaction(reaction, user)
                await reaction.message.remove_reaction(reaction, user)
                await waitForEmoji(ctx, isMoveUI, isWild, goStraightToResolve, isItemUI1, isItemUI2)

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
        embed.set_footer(text=createTextFooter(pokemon1, pokemon2, '‎'))
    createBattleEmbedFields(embed, pokemon1, pokemon2)
    embed.set_author(name=(ctx.message.author.display_name + "'s Battle:"))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image2.png")
    return files, embed

def createBattleEmbedFields(embed, pokemon1, pokemon2):
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
        itemFooter = itemFooter + "\n(" + str(count) + ") " + item + "   Owned: " + trainer.itemList[item]
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
        print('evolist')
        print(pokemon.nickname)
        pokemon.evolve()
        embed = discord.Embed(title="Congratulations! " + str(ctx.message.author) + "'s " + pokemon.nickname + " evolved into " + pokemon.evolveToAfterBattle + "!", description="(continuing automatically in 6 seconds...)", color=0x00ff00)
        file = discord.File(pokemon.spritePath, filename="image.png")
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=('Pokemon obtained on ' + pokemon.location))
        embed.set_author(name=(ctx.message.author.display_name + "'s Pokemon Evolved:"))
        message = await ctx.send(file=file, embed=embed)
        sleep(6)
        await message.delete()
    for pokemon in pokemonToLearnMovesList:
        print('movelist')
        print(pokemon.nickname)
        for move in pokemon.newMovesToLearn:
            print(move['names']['en'])
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
                        await ctx.send(ctx.message.author.display_name + "'s connection closed. Please start game again.")
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
            else:
                await message.delete()
                pokemon.learnMove(move)
                message = await ctx.send(pokemon.nickname + " learned " + move['names']['en'] + "!" + " (continuing automatically in 4 seconds...)")
                sleep(4)
                await message.delete()
            await waitForEmoji(ctx, message)
    battle.battleRefresh()

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
    files, embed, commands = createOverworldEmbed(ctx, trainer)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id

def createOverworldEmbed(ctx, trainer):
    commands = {}
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
    embed.set_author(name=(ctx.message.author.display_name + " is exploring the world:"))

    optionsText = ''
    count = 1
    if (trainer.checkProgress(locationName) < progressRequired):
        optionsText = optionsText + "(" + str(count) + ") Make progress\n"
        commands[count] = ('progress',)
        count += 1
    if (locationObj.hasPokemonCenter):
        optionsText = optionsText + "(" + str(count) + ") Heal at Pokemon Center\n"
        commands[count] = ('heal',)
        count += 1
        optionsText = optionsText + "(" + str(count) + ") Access the Pokemon Storage System\n"
        commands[count] = ('box',)
        count += 1
    if (locationObj.hasMart):
        optionsText = optionsText + "(" + str(count) + ") Shop at Pokemart\n"
        commands[count] = ('mart',)
        count += 1

    for nextLocationName, nextLocationObj in locationObj.nextLocations.items():
        if (nextLocationObj.checkRequirements(trainer)):
            optionsText = optionsText + "(" + str(count) + ") Travel to " + nextLocationName + "\n"
            commands[count] = ('travel', nextLocationName)
            count += 1

    embed.add_field(name='Options:',value=optionsText, inline=True)
    return files, embed, commands

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
            await ctx.send(ctx.message.author.display_name + "'s connection closed. Please start game again.")
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
                elif (str(reaction.emoji) == data.getEmoji('6') and len(trainer.boxPokemon) >= 6 + (offset*9)): #TODO make 7-9
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
                    print(offset)
                    print(maxBoxes)
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
                await reaction.message.remove_reaction(reaction, user)
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
    brendanImage = discord.File("data/sprites/Brendan.png", filename="image.png")
    files.append(brendanImage)
    embed.set_thumbnail(url="attachment://image.png")
    return files, embed

async def startMartUI(ctx, trainer, goBackTo='', otherData=None):
    itemsForPurchase1 = {
        "PokeBall": 200,
        "Potion": 300,
        "Super Potion": 700,
        "Full Heal": 600,
        "Revive": 1500
    }
    itemsForPurchase2 = {
        "PokeBall": 200,
        "GreatBall": 600,
        "Potion": 300,
        "Super Potion": 700,
        "Hyper Potion": 1200,
        "Max Potion": 3000,
        "Full Heal": 600,
        "Revive": 1500
    }
    itemsForPurchase3 = {
        "PokeBall": 200,
        "GreatBall": 600,
        "UltraBall": 1200,
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
            await ctx.send(ctx.message.author.display_name + "'s connection closed. Please start game again.")
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
                await reaction.message.remove_reaction(reaction, user)
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

data = pokeData()
bot.run(TOKEN)
