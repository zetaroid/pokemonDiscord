from Data import pokeData
from Pokemon import Pokemon
import random

class Battle(object):

    def __init__(self, data, trainer1, trainer2=None, entryType="Walking"):
        self.trainer1 = trainer1
        self.trainer2 = trainer2
        self.data = data
        self.entryType = entryType
        self.isWildEncounter = False

    def startBattle(self):
        self.pokemon1 = self.getTrainer1FirstPokemon()
        self.pokemon2 = self.getTrainer2FirstPokemon()
        
    def getTrainer1FirstPokemon(self):
        return self.trainer1.partyPokemon[0]

    def getTrainer2FirstPokemon(self):
        if (self.trainer2 is None):
            self.isWildEncounter = True
            return self.generateWildPokemon()
        else:
            return self.trainer2.partyPokemon[0]

    def generateWildPokemon(self):
        encounterList = self.data.getEncounterTable(self.trainer1.location, self.entryType)
        commonList = []
        uncommonList = []
        rareList = []
        for pokemonLocationObj in encounterList:
            if (pokemonLocationObj["rarity"] == "rare"):
                rareList.append(pokemonLocationObj)
            elif (pokemonLocationObj["rarity"] == "uncommon"):
                uncommonList.append(pokemonLocationObj)
            else:
                commonList.append(pokemonLocationObj)
        roll = random.randint(0,99)
        pokemonObj = None
        if not rareList and not uncommonList and not commonList:
            pokemonObj = None
        elif not rareList and not uncommonList and commonList:
            randInt = random.randint(0,len(commonList)-1)
            pokemonObj = commonList[randInt]
        elif not rareList and uncommonList and not commonList:
            randInt = random.randint(0,len(uncommmonList)-1)
            pokemonObj = uncommonList[randInt]
        elif rareList and not uncommonList and not commonList:
            randInt = random.randint(0,len(rareList)-1)
            pokemonObj = rareList[randInt]
        elif not rareList and uncommonList and commonList:
            if (roll >= 60):
                randInt = random.randint(0,len(uncommonList)-1)
                pokemonObj = uncommonList[randInt]
            else:
                randInt = random.randint(0,len(commonList)-1)
                pokemonObj = commonList[randInt]
        elif rareList and not uncommonList and commonList:
            if (roll >= 90):
                randInt = random.randint(0,len(rareList)-1)
                pokemonObj = rareList[randInt]
            else:
                randInt = random.randint(0,len(commonList)-1)
                pokemonObj = commonList[randInt]
        elif rareList and uncommonList and not commonList:
            if (roll >= 90):
                randInt = random.randint(0,len(rareList)-1)
                pokemonObj = rareList[randInt]
            else:
                randInt = random.randint(0,len(uncommonList)-1)
                pokemonObj = uncommonList[randInt]
        else:
            if (roll >= 90):
                randInt = random.randint(0,len(rareList)-1)
                pokemonObj = rareList[randInt]
            elif (roll >= 60):
                randInt = random.randint(0,len(uncommonList)-1)
                pokemonObj = uncommonList[randInt]
            else:
                randInt = random.randint(0,len(commonList)-1)
                pokemonObj = commonList[randInt]
        if (pokemonObj is not None):
            level = random.randint(pokemonObj["min_level"],pokemonObj["max_level"])
            return Pokemon(self.data, pokemonObj["pokemon"], level)
        else:
            return Pokemon(self.data, "Rayquaza", 100, [], "adamant", True)
            
                
