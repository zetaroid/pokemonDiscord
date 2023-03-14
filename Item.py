class Item(object):

    def __init__(self, itemName):
        self.name = itemName
        self.price = 0
        self.multiplier = 0
        self.mart_tier = []
        self.bp_price = 0
        self.effects = []
        self.amount = 0
        self.battle_frontier_mart = False

    def perform_effect(self, pokemon, isCheck=False):
        text = ""

        if "Tera Shard" in self.name:
            type_list = ['normal', 'fairy', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost', 'steel',
                         'fire', 'water', 'grass', 'electric', 'psychic', 'ice', 'dragon', 'dark']
            for poketype in type_list:
                if poketype in self.name.lower():
                    pokemon.teraType = poketype.capitalize()
                    return True, "The Pokemon's Tera Type became " + pokemon.teraType.capitalize() + ".", False
            return False, text, False

        if self.name == "Halloween Shiny Candy":
            if not pokemon.shiny and "halloween" in pokemon.name.lower():
                if not isCheck:
                    pokemon.shiny = True
                    pokemon.setSpritePath()
                return True, "The Halloween Pokemon became shiny.", False
            else:
                return False, text, False

        if self.name == "Card Gloss":
            if not pokemon.shiny and pokemon.name.lower() in ["exodia", "blue eyes white dragon", "blue eyes toon dragon", "dark magician",
                                        "dark magician girl", "kuriboh", "obelisk the tormentor", "slifer the sky dragon",
                                        "winged dragon of ra", "time wizard", "relinquished", "red eyes black dragon"]:
                if not isCheck:
                    pokemon.shiny = True
                    pokemon.setSpritePath()
                return True, "The strange monster became shiny.", False
            else:
                return False, text, False

        if "revive_and_heal_full" in self.effects:
            if 'faint' not in pokemon.statusList:
                return False, text, True
            if not isCheck:
                pokemon.clearStatus()
                pokemon.heal(pokemon.hp)
                text += "\nThe Pokemon was revived to max health."

        if "revive" in self.effects:
            if 'faint' not in pokemon.statusList:
                return False, text, True
            if not isCheck:
                pokemon.clearStatus()
                pokemon.heal(round(pokemon.hp / 2))
                text += "\nThe Pokemon was revived."

        if "heal" in self.effects:
            if pokemon.currentHP >= pokemon.hp or 'faint' in pokemon.statusList:
                return False, text, True
            if not isCheck:
                pokemon.heal(self.amount)
                text += "\n" + str(self.amount) + " HP was restored."

        if "heal_full" in self.effects:
            if pokemon.currentHP >= pokemon.hp or 'faint' in pokemon.statusList:
                return False, text, True
            if not isCheck:
                pokemon.heal(pokemon.hp)
                text += "\nHP was fully restored."

        if "status" in self.effects:
            if (not pokemon.statusList) or 'faint' in pokemon.statusList:
                return False, text, True
            if not isCheck:
                pokemon.clearStatus()
                text += "\nStatus conditions removed."

        if "heal_full_and_status" in self.effects:
            if (pokemon.currentHP >= pokemon.hp and len(pokemon.statusList) < 1) or 'faint' in pokemon.statusList:
                return False, text, True
            if not isCheck:
                pokemon.clearStatus()
                pokemon.heal(pokemon.hp)
                text += "\nHP was fully restored and status conditions removed."

        if "pp_full_restore" in self.effects:
            if not isCheck:
                pokemon.resetPP(None)
                text += "\nPP was fully restored."
        return True, text, True
