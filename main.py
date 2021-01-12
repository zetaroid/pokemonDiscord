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
from PIL import Image

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print("Pokemon Bot Is Ready And Online!")
    
@bot.command(name='testParty', help='testBattle')
async def test3Command(ctx):
    pokemon = Pokemon(data, "Mudkip", 100)
    pokemon.addStatus("burn")
    pokemon.setNickname('Kippy')
    pokemon2 = Pokemon(data, "Blaziken", 100)
    pokemon3 = Pokemon(data, "Rayquaza", 100)
    pokemon4 = Pokemon(data, "Mew", 100)
    pokemon5 = Pokemon(data, "Torchic", 100)
    pokemon6 = Pokemon(data, "Celebi", 100)
    trainer = Trainer("Zetaroid", "Marcus", "Route 103")
    trainer.addPokemon(pokemon)
    trainer.addPokemon(pokemon2)
    trainer.addPokemon(pokemon3)
    trainer.addPokemon(pokemon4)
    trainer.addPokemon(pokemon5)
    trainer.addPokemon(pokemon6)
    await startPartyUI(ctx, False, trainer)
    
@bot.command(name='testSummary', help='testBattle')
async def test2Command(ctx):
    pokemon = Pokemon(data, "Mudkip", 100)
    pokemon.addStatus("burn")
    pokemon.setNickname('Kippy')
    await startPokemonSummaryUI(ctx, pokemon)
    
@bot.command(name='test', help='testBattle')
async def test1Command(ctx):
    trainer = Trainer("Zetaroid", "Marcus", "Route 103")
    pokemon1 = Pokemon(data, "Mudkip", 30)
    pokemon1.addStatus("burn")
    trainer.addPokemon(pokemon1)
    battle = Battle(data, trainer, None, "Walking")
    battle.startBattle()
    await startBattleUI(ctx, True, battle)

async def startPokemonSummaryUI(ctx, pokemon, goBackTo='', otherData=None):
    files, embed = createPokemonSummaryEmbed(ctx, pokemon)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    await message.add_reaction(data.getEmoji('right arrow'))
        
    def check(reaction, user):
        return (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow'))
    
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
        embed.add_field(name=('-----Move ' + str(count+1) + '-----'), value=(move['names']['en'] + "\n" + move['type'] + " " + physicalSpecialEmoji + bp + "\n" + str(move['pp']) + "/" + str(move['pp']) + " pp"), inline=True) #todo fix pp
        count += 1
    embed.set_author(name=(ctx.message.author.display_name + "'s Pokemon Summary:"))
    brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    files.append(brendanImage)
    embed.set_thumbnail(url="attachment://image2.png")
    return files, embed

async def startPartyUI(ctx, isBattle, trainer, goBackTo='', otherData=None):
    files, embed = createPartyUIEmbed(ctx, trainer)
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
    
    async def waitForEmoji(ctx, isBattle):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(ctx.message.author.display_name + 's connection closed. Please start game again.')
        else:
            dataTuple = (isBattle, trainer, goBackTo, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1') and len(trainer.partyPokemon) >= 1):
                    await message.delete()     
                    await startPokemonSummaryUI(ctx, trainer.partyPokemon[0], 'startPartyUI', dataTuple)
                elif (str(reaction.emoji) == data.getEmoji('2') and len(trainer.partyPokemon) >= 2):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer.partyPokemon[1], 'startPartyUI', dataTuple)
                elif (str(reaction.emoji) == data.getEmoji('3') and len(trainer.partyPokemon) >= 3):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer.partyPokemon[2], 'startPartyUI', dataTuple)
                elif (str(reaction.emoji) == data.getEmoji('4') and len(trainer.partyPokemon) >= 4):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer.partyPokemon[3], 'startPartyUI', dataTuple)
                elif (str(reaction.emoji) == data.getEmoji('5') and len(trainer.partyPokemon) >= 5):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer.partyPokemon[4], 'startPartyUI', dataTuple)
                elif (str(reaction.emoji) == data.getEmoji('6') and len(trainer.partyPokemon) >= 6):
                    await message.delete()
                    await startPokemonSummaryUI(ctx, trainer.partyPokemon[5], 'startPartyUI', dataTuple)
                elif (str(reaction.emoji) == data.getEmoji('right arrow')):
                    if (goBackTo == 'startBattleUI'):
                        await message.delete()
                        await startBattleUI(ctx, otherData[0], otherData[1], otherData[2], otherData[3])
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isBattle)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx, isBattle)
            else:
                await message.remove_reaction(reaction, user)
                await reaction.message.remove_reaction(reaction, user)
                await waitForEmoji(ctx, isBattle)
    await waitForEmoji(ctx, isBattle)

def createPartyUIEmbed(ctx, trainer):
    files = []
    embed = discord.Embed(title="Party Summary", description="[react to # to view individual summary]", color=0x00ff00)
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

async def startBattleUI(ctx, isWild, battle, goBackTo='', otherData=None):
    pokemon1 = battle.pokemon1
    pokemon2 = battle.pokemon2
    isMoveUI = False
    mergeImages(pokemon1.spritePath, pokemon2.spritePath)
    files, embed = createBattleEmbed(ctx, isWild, pokemon1, pokemon2)
    message = await ctx.send(files=files, embed=embed)
    messageID = message.id
    await message.add_reaction(data.getEmoji('1'))
    await message.add_reaction(data.getEmoji('2'))
    await message.add_reaction(data.getEmoji('3'))
    await message.add_reaction(data.getEmoji('4'))
    
    def check(reaction, user):
        return ((user == ctx.message.author and str(reaction.emoji) == data.getEmoji('1')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('2'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('3')) or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('4'))
            or (user == ctx.message.author and str(reaction.emoji) == data.getEmoji('right arrow')))

    async def waitForEmoji(ctx, isMoveUI, isWild):
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send('The wild ' + pokemon2.name + ' fled!')
        else:
            dataTuple = (isWild, battle, goBackTo, otherData)
            userValidated = False
            if (messageID == reaction.message.id):
                userValidated = True
            if userValidated:
                if (str(reaction.emoji) == data.getEmoji('1')):
                    if not isMoveUI:
                        isMoveUI = True
                        response = 'Fight'
                        embed.set_footer(text=createMoveFooter(pokemon1, pokemon2))
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                        await message.add_reaction(data.getEmoji('right arrow'))
                        await waitForEmoji(ctx, isMoveUI, isWild)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild)
                elif (str(reaction.emoji) == data.getEmoji('2')):
                    if not isMoveUI:
                        response = 'Bag'
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild)
                elif (str(reaction.emoji) == data.getEmoji('3')):
                    if not isMoveUI:
                        response = 'Pokemon'
                        await message.delete()
                        await startPartyUI(ctx, True, battle.trainer1, 'startBattleUI', dataTuple)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild)
                elif (isMoveUI and str(reaction.emoji) == data.getEmoji('right arrow')):
                    isMoveUI = False
                    embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
                    await message.edit(embed=embed)
                    await message.clear_reaction(reaction)
                    await waitForEmoji(ctx, isMoveUI, isWild)
                elif (str(reaction.emoji) == data.getEmoji('4')):
                    if not isMoveUI:
                        response = 'Run'
                        await ctx.send('Got away safely!')
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                        await waitForEmoji(ctx, isMoveUI, isWild)
                else:
                    await message.remove_reaction(reaction, user)
                    await waitForEmoji(ctx, isMoveUI, isWild)
            else:
                await message.remove_reaction(reaction, user)
                await reaction.message.remove_reaction(reaction, user)
                await waitForEmoji(ctx, isMoveUI, isWild)

    await waitForEmoji(ctx, isMoveUI, isWild)

def createBattleEmbed(ctx, isWild, pokemon1, pokemon2):
    files = []
    if (isWild):
        embed = discord.Embed(title="A wild " + pokemon2.name + " appeared!", description="[react to # to do commands]", color=0x00ff00)
    else:
        embed = discord.Embed(title=pokemon2.OT + " sent out " + pokemon2.name + "!", description="[react to # to do commands]", color=0x00ff00)
    file = discord.File("data/temp/merged_image.png", filename="image.png")
    files.append(file)
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=createBattleFooter(pokemon1, pokemon2))
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
    embed.set_author(name=(ctx.message.author.display_name + "'s Battle:"))
    #brendanImage = discord.File("data/sprites/Brendan.png", filename="image2.png")
    #files.append(brendanImage)
    #embed.set_thumbnail(url="attachment://image2.png")
    return files, embed

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

###HERE
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
            movePP = str(99)
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
            
def mergeImages(path1, path2):
    background = Image.open('data/sprites/background.png')
    background = background.convert('RGBA')
    image1 = Image.open(path1)
    image1 = image1.transpose(method=Image.FLIP_LEFT_RIGHT)
    image2 = Image.open(path2)
    background.paste(image1, (12,40), image1.convert('RGBA'))
    background.paste(image2, (130,0), image2.convert('RGBA'))
    background.save("data/temp/merged_image.png","PNG")

data = pokeData()
bot.run(TOKEN)
