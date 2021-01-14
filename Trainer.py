from Data import pokeData
from Pokemon import Pokemon
from datetime import datetime

class Trainer(object):

    def __init__(self, author, name, location, partyPokemon=None, boxPokemon=None):
        self.author = author
        self.name = name
        self.date = datetime.today().date()
        self.location = location
        if partyPokemon is None:
            self.partyPokemon = []
        else:
            self.partyPokemon = partyPokemon
        if boxPokemon is None:
            self.boxPokemon = []
        else:
            self.boxPokemon = boxPokemon    

    def addPokemon(self, pokemon, changeOT):
        if changeOT:
            pokemon.OT = self.author
        if (len(self.partyPokemon) < 6):
            self.partyPokemon.append(pokemon)
        else:
            self.boxPokemon.append(pokemon)

    def swapPartyPokemon(self, pos):
        if (pos != 0):
            self.partyPokemon[0], self.partyPokemon[pos] = self.partyPokemon[pos], self.partyPokemon[0] 

    def movePokemonPartyToBox(self, index):
        if (len(self.partyPokemon) > 1):
            pokemon = self.partyPokemon.pop(index)
            self.boxPokemon.append(pokemon)
            return True
        else:
            return False

    def movePokemonBoxToParty(self, index):
        if (len(self.partyPokemon) < 6):
            pokemon = self.boxPokemon.pop(index)
            self.partyPokemon.append(pokemon)
            return True
        else:
            return False
        
