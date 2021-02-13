from copy import copy
from Pokemon import Pokemon
from Trainer import Trainer
import random
import math

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
        self.restrictedPokemon = [
            "Mewtwo",
            "Mew",
            "Lugia",
            "Hooh",
            "Celebi",
            "Kyogre",
            "Groudon",
            "Rayquaza",
            "Jirachi",
            "Deoxys",
            "Dialga",
            "Palkia",
            "Giratina",
            "Phione",
            "Manaphy",
            "Darkrai",
            "Shaymin",
            "Arceus",
            "Victini",
            "Reshiram",
            "Zekrom",
            "Kyurem",
            "Keldeo",
            "Meloetta",
            "Genesect",
            "Xerneas",
            "Yveltal",
            "Zygarde",
            "Diancie",
            "Hoopa",
            "Volcanion",
            "Cosmog",
            "Cosmoem",
            "Solgaleo",
            "Lunala",
            "Necrozma",
            "Magearna",
            "Marshadow",
            "Zeraora"
        ]

    def getBattleTowerUserCopy(self, trainer, position1, position2, position3, withRestrictions=True):
        trainerCopy = copy(trainer)
        trainerCopy.pokemonCenterHeal()
        partyPokemon = trainerCopy.partyPokemon
        pokemon1 = partyPokemon[position1-1]
        pokemon2 = partyPokemon[position2-1]
        pokemon3 = partyPokemon[position3-1]
        pokemon1.level = 100
        pokemon1.setStats()
        pokemon2.level = 100
        pokemon2.setStats()
        pokemon3.level = 100
        pokemon3.setStats()
        trainerCopy.partyPokemon = [pokemon1, pokemon2, pokemon3]
        trainerCopy.pokemonCenterHeal()
        if withRestrictions:
            for pokemon in trainerCopy.partyPokemon:
                if not self.validateRestrictedPokemon(pokemon):
                    return None, False
        trainerCopy.itemList.clear()
        return trainerCopy, True

    def validateRestrictedPokemon(self, pokemon):
        if pokemon.name in self.restrictedPokemon:
            return False
        return True

    def calculateBP(self, trainer, withRestrictions):
        maxBP = 5
        if withRestrictions:
            streak = trainer.withRestrictionStreak
        else:
            streak = trainer.noRestrictionsStreak
        bp = math.floor(streak/5)
        if bp > maxBP:
            bp = maxBP
        return bp

    def setTrainers(self):
        for trainerObj in self.data.battleTowerTrainersJson['trainers']:
            self.trainersObj.append(trainerObj)
        for trainerObj in self.data.battleTowerTrainersJson['specialTrainers']:
            self.specialTrainersObj.append(trainerObj)

    def getBattleTowerTrainer(self, trainer, withRestrictions):
        specialTrainer = False
        specialPokemonNum = 0
        if withRestrictions:
            streak = trainer.withRestrictionStreak
        else:
            streak = trainer.noRestrictionsStreak
            specialPokemonNum = 1
            if streak > 20:
                specialPokemonNum = 2
            elif streak > 50:
                specialPokemonNum = 3
        bpReward = math.ceil(streak / 10)
        if bpReward < 1:
            bpReward = 1
        elif bpReward > 5:
            bpReward = 5
        if streak % 10 == 0 and streak != 0:
            specialTrainer = True
            bpReward = bpReward * 2

        if specialTrainer:
            randInt = random.randint(0, len(self.specialTrainersObj) - 1)
            return self.generateTrainer(self.specialTrainersObj[randInt], withRestrictions, bpReward)
        else:
            randInt = random.randint(0, len(self.trainersObj) - 1)
            return self.generateTrainer(self.trainersObj[randInt], withRestrictions, bpReward, specialPokemonNum)

    def generateTrainer(self, trainerObj, withRestrictions, bpReward, specialPokemon=0):
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
        rewardDict = {}
        rewardDict['BP'] = bpReward
        newTrainer.setRewards(rewardDict)

        if withRestrictions:
            pokemonStr = 'pokemon'
        else:
            pokemonStr = 'specialPokemon'

        if pokemonStr in trainerObj:
            setPokemon = trainerObj[pokemonStr]
            for pokemonName in setPokemon:
                newTrainer.addPokemon(self.getPokemon(False, pokemonName), True)
        else:
            normalPokemonAmount = 3-specialPokemon
            if normalPokemonAmount < 0:
                normalPokemonAmount = 0
            for x in range(0, normalPokemonAmount):
                newTrainer.addPokemon(self.getPokemon(), True)
            for x in range(0, specialPokemon):
                newTrainer.addPokemon(self.getPokemon(True), True)

        return newTrainer

    def getPokemon(self, special=False, specified=None):
        if specified is not None:
            for pokemonObj in self.specialPokemonObj:
                if specified == pokemonObj['species']:
                    return self.generatePokemon(pokemonObj)
            for pokemonObj in self.pokemonObj:
                if specified == pokemonObj['species']:
                    return self.generatePokemon(pokemonObj)
            try:
                newPokemon = Pokemon(self.data, specified, 100)
                newPokemon.hpIV = 31
                newPokemon.atkIV = 31
                newPokemon.defIV = 31
                newPokemon.spAtkIV = 31
                newPokemon.spDefIV = 31
                newPokemon.spdIV = 31
                newPokemon.atkEV = 252
                newPokemon.spAtkEV = 252
                newPokemon.hpEV = 6
                newPokemon.setStats()
                newPokemon.nickname = "Nosferatu"
                return newPokemon
            except:
                pass
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
            atkEV = pokemonObj['atkEV']
        if "defEV" in pokemonObj:
            defEV = pokemonObj['defEV']
        if "spAtkEV" in pokemonObj:
            spAtkEV = pokemonObj['spAtkEV']
        if "spDefEV" in pokemonObj:
            spDefEV = pokemonObj['spDefEV']
        if "spdEV" in pokemonObj:
            spdEV = pokemonObj['spdEV']
        newPokemon.hpEV = hpEV
        newPokemon.atkEV = atkEV
        newPokemon.defEV = defEV
        newPokemon.spAtkEV = spAtkEV
        newPokemon.spDefEV = spDefEV
        newPokemon.spdEV = spdEV

        if 'nature' in pokemonObj:
            newPokemon.nature = pokemonObj['nature']

        newPokemon.setStats()

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
