from Data import pokeData
from Pokemon import Pokemon
from Trainer import Trainer
from Battle import Battle

data = []

def runTests():
    testFindLevelUpMove()
    print("")
    testEncounterLookup()
    print("")
    testReplaceMove()
    print("")
    testGetFullData()
    print("")
    testStatsLv100()
    print("")
    testStatus()
    print("")
    testTrainerAddRemovePokemon()
    print("")
    testGenerateWildPokemon()
    
def testFindLevelUpMove():
    global data
    errors = 0
    print("testFindLevelUpMove STARTING")
    moves = data.getLevelUpMove("bulbasaur", 15)
    expected = ["Poison Powder", "Sleep Powder"]
    for x in range(len(expected)):
        if (expected[x] != moves[x]):
            errors += 1
            print("ERROR: [" + expected[x] + "] expected but got [" + moves[x] + "]")
        else:
            print("[" + expected[x] + "] expected and got [" + moves[x] + "]")
    print("testFindLevelUpMove DONE, errors = " + str(errors))
    
def testEncounterLookup():
    global data
    errors = 0
    print("testEncounterLookup STARTING")
    encounterList = data.getEncounterTable("Route 101", "Walking")
    expected = ["Wurmple", "Poochyena", "Zigzagoon"]
    index = 0
    for pokemonLocationObj in encounterList:
        print(pokemonLocationObj["pokemon"])
    for x in range(len(expected)):
        if (expected[x] != encounterList[x]["pokemon"]):
            errors += 1
            print("ERROR: [" + expected[x] + "] expected but got [" + encounterList[x]["pokemon"] + "]")
    print("testEncounterLookup DONE, errors = " + str(errors))

def testReplaceMove():
    global data
    errors = 0
    print("testReplaceMove STARTING")
    pokemonTest = Pokemon(data, "bulbasaur", 100)
    count = 0
    for moveName in pokemonTest.moves:
        print(str(count) + ": " + moveName)
        count += 1
    count = 0
    pokemonTest.replaceMove(0, "Return")
    for moveName in pokemonTest.moves:
        if (count == 0):
            if (moveName != "Return"):
                errors += 1
                print("ERROR: [Return] expected but got [" + moveName + "]")
        print(str(count) + ": " + moveName)
        count += 1
    print("testReplaceMove DONE, errors = " + str(errors))

def testGetFullData():
    global data
    errors = 0
    print("testGetFullData STARTING")
    pokemonTest = Pokemon(data, "bulbasaur", 100)
    fullData = pokemonTest.getFullData()
    expected = "Bulbasaur"
    if (expected != fullData["names"]["en"]):
        print("ERROR: " + expected + " expected but got [" + fullData["names"]["en"] + "]")
    else:
        print(fullData["names"]["en"], fullData["types"])
    print("testGetFullData DONE, errors = " + str(errors))

def testStatsLv100():
    global data
    errors = 0
    print("testStatsLv100 STARTING")
    pokemonTest = Pokemon(data, "bulbasaur", 100, [], "hardy", False, 252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31)
    print("HP = " + str(pokemonTest.hp))
    print("ATK = " + str(pokemonTest.attack))
    print("DEF = " + str(pokemonTest.defense))
    print("SP ATK = " + str(pokemonTest.special_attack))
    print("SP DEF = " + str(pokemonTest.special_defense))
    print("SPD = " + str(pokemonTest.speed))
    print("testStatsLv100 DONE")

def testStatus():
    global data
    errors = 0
    print("testStatus STARTING")
    pokemonTest = Pokemon(data, "bulbasaur", 100, [], "hardy", False, 252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31)
    pokemonTest.addStatus("burn")
    print(pokemonTest.statusList)
    pokemonTest.removeStatus("burn")
    print(pokemonTest.statusList)
    print("testStatus DONE")

def testTrainerAddRemovePokemon():
    global data
    print("testTrainerAddPokemon STARTING")
    trainer = Trainer("author", "NAME", "Route 101")
    pokemon = Pokemon(data, "Bulbasaur", 100, "Marcus", [], "hardy", False, 252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31)
    pokemon2 = Pokemon(data, "Ivysaur", 100, "Marcus", [], "hardy", False, 252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31)
    trainer.addPokemon(pokemon)
    trainer.addPokemon(pokemon2)
    print("Party size = " + str(len(trainer.partyPokemon)))
    print("Box size = " + str(len(trainer.boxPokemon)))
    print("In party: " + trainer.partyPokemon[0].name)
    print("In party: " + trainer.partyPokemon[1].name)
    trainer.movePokemonPartyToBox(0)
    print("Party size = " + str(len(trainer.partyPokemon)))
    print("Box size = " + str(len(trainer.boxPokemon)))
    print("In box: " + trainer.boxPokemon[0].name)
    print("In party: " + trainer.partyPokemon[0].name)
    trainer.movePokemonBoxToParty(0)
    print("Party size = " + str(len(trainer.partyPokemon)))
    print("Box size = " + str(len(trainer.boxPokemon)))
    print("In party: " + trainer.partyPokemon[0].name)
    print("In party: " + trainer.partyPokemon[1].name)
    print("testTrainerAddPokemon DONE")

def testGenerateWildPokemon():
    global data
    print("testGenerateWildPokemon STARTING")
    trainerNew = Trainer("Zetaroid", "Marcus", "Route 103")
    print(trainerNew.name)
    print("Party size = " + str(len(trainerNew.partyPokemon)))
    pokemon = Pokemon(data, "Charmander", 100, [], "hardy", False, 252, 252, 252, 252, 252, 252, 31, 31, 31, 31, 31, 31)
    trainerNew.addPokemon(pokemon)
    print("Party size = " + str(len(trainerNew.partyPokemon)))
    battle = Battle(data, trainerNew, None, "Walking")
    battle.startBattle()
    wildPokemon = battle.pokemon2
    print(battle.pokemon1.name)
    print(wildPokemon.name)
    print("testGenerateWildPokemon DONE")
         
if __name__ == '__main__':
    print("TEST SCRIPT BEGINNING...")
    print("")
    print("LOADING DATA FILES")
    data = pokeData()
    print("DONE LOADING DATA FILES")
    print("")
    runTests()
