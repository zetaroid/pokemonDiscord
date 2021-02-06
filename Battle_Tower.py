from copy import copy
from Pokemon import Pokemon
from Trainer import Trainer
import random

class Battle_Tower(object):

    # The class "constructor"
    def __init__(self, data):
        self.data = data
        self.trainersObj = []
        self.specialTrainersObj = []
        self.specialPokemonObj = []
        self.pokemonObj = []
        self.femaleNames = []
        self.maleNames = []
        self.setTrainers()
        self.setPokemon()
        self.setNames()

    def getBattleTowerTrainer(self, trainer, position1, position2, position3):
        trainerCopy = copy(trainer)
        trainerCopy.pokemonCenterHeal()
        partyPokemon = trainerCopy.partyPokemon
        pokemon1 = partyPokemon[position1]
        pokemon2 = partyPokemon[position2]
        pokemon3 = partyPokemon[position3]
        pokemon1.level = 100
        pokemon1.setStats()
        pokemon2.level = 100
        pokemon2.setStats()
        pokemon3.level = 100
        pokemon3.setStats()
        trainerCopy.partyPokemon = [pokemon1, pokemon2, pokemon3]
        trainerCopy.itemList.clear()
        return trainerCopy

    def setTrainers(self):
        for trainerObj in self.data.battleTowerTrainersJson['trainers']:
            self.trainersObj.append(trainerObj)
        for trainerObj in self.data.battleTowerTrainersJson['specialTrainers']:
            self.specialTrainersObj.append(trainerObj)

    def getTrainer(self, specialTrainer=False, specialPokemon=0):
        if specialTrainer:
            randInt = random.randint(0, len(self.specialTrainersObj) - 1)
            return self.generateTrainer(self.specialTrainersObj[randInt], specialPokemon)
        else:
            randInt = random.randint(0, len(self.trainersObj) - 1)
            return self.generateTrainer(self.trainersObj[randInt], specialPokemon)

    def generateTrainer(self, trainerObj, specialPokemon=0):
        gender = ''
        if 'gender' in trainerObj:
            gender = trainerObj['gender']
        if gender:
            name = trainerObj['name'] + ' ' + self.getRandomName(gender)
        else:
            name = trainerObj['name']
        sprite = trainerObj['image']
        newTrainer = Trainer(name, name, "NPC Battle")
        newTrainer.setSprite(sprite)

        normalPokemonAmount = 3-specialPokemon
        for x in range(0, normalPokemonAmount):
            newTrainer.addPokemon(self.getPokemon())
        for x in range(0, specialPokemon):
            newTrainer.addPokemon(self.getPokemon(True))

        return newTrainer

    def getPokemon(self, special=False):
        if special:
            randInt = random.randint(0, len(self.specialPokemonObj) - 1)
            return self.generatePokemon(self.specialPokemonObj[randInt])
        else:
            randInt = random.randint(0, len(self.pokemonObj)-1)
            return self.generatePokemon(self.pokemonObj[randInt])

    def setPokemon(self):
        for pokemonObj in self.data.battleTowerPokemonJson['pokemon']:
            self.pokemonObj.append(pokemonObj)
        for pokemonObj in self.data.battleTowerPokemonJson['specialPokemon']:
            self.specialPokemonObj.append(pokemonObj)

    def generatePokemon(self, pokemonObj):
        newPokemon = Pokemon(self.data, pokemonObj['species'], 100)

        newPokemon.hpIV = 31
        newPokemon.atkIV = 31
        newPokemon.defIV = 31
        newPokemon.spAtkIV = 31
        newPokemon.spDefIV = 31
        newPokemon.spdIV = 31

        hpEV = 0
        atkEV = 0
        defEV = 0
        spAtkEV = 0
        spDefEV = 0
        spdEV = 0
        if "hpEV" in pokemonObj:
            hpEV = pokemonObj['hpEV']
        if "atkEV" in pokemonObj:
            hpEV = pokemonObj['atkEV']
        if "defEV" in pokemonObj:
            hpEV = pokemonObj['defEV']
        if "spAtkEV" in pokemonObj:
            hpEV = pokemonObj['spAtkEV']
        if "spDefEV" in pokemonObj:
            hpEV = pokemonObj['spDefEV']
        if "spdEV" in pokemonObj:
            hpEV = pokemonObj['spdEV']
        newPokemon.hpEV = hpEV
        newPokemon.atkEV = atkEV
        newPokemon.defEV = defEV
        newPokemon.spAtkEV = spAtkEV
        newPokemon.spDefEV = spDefEV
        newPokemon.spdEV = spdEV
        self.setStats()

        moves = []
        if 'moves' in pokemonObj:
            for moveName in pokemonObj['moves']:
                moves.append(self.data.getMoveData(moveName))
        newPokemon.setMoves(moves)
        newPokemon.resetPP()

        return newPokemon

    def setNames(self):
        for name in self.data.battleTowerTrainersJson['male_names']:
            self.maleNames.append(name)
        for name in self.data.battleTowerTrainersJson['female_names']:
            self.femaleNames.append(name)

    def getRandomName(self, gender):
        nameList = None
        if gender == 'female':
            nameList = self.femaleNames
        else:
            nameList = self.maleNames
        randInt = random.randint(0, len(nameList)-1)
        return nameList[randInt]
