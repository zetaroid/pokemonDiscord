import asyncio

import disnake
from disnake import SelectOption
from disnake.ui import Select

from Pokemon import Pokemon


class ConfirmView(disnake.ui.View):
    def __init__(self, author, text_confirm, text_nevermind, flip_color=False):
        super().__init__()
        self.author = author
        self.confirmed = False
        self.children[0].label = text_confirm
        self.children[1].label = text_nevermind
        if flip_color:
            self.children[0].style = disnake.ButtonStyle.green
            self.children[1].style = disnake.ButtonStyle.red

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.red)
    async def option_yes(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.confirmed = True
        await self.verify_response(interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.green)
    async def option_no(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.verify_response(interaction)

    async def verify_response(self, interaction: disnake.MessageInteraction):
        if interaction.author != self.author:
            return
        await interaction.response.defer()
        self.stop()


class ChooseStarterView(disnake.ui.View):
    def __init__(self, author, data):
        super().__init__()
        self.author = author
        self.chosen = ""
        self.starterList = [Pokemon(data, "Bulbasaur", 5), Pokemon(data, "Charmander", 5), Pokemon(data, "Squirtle", 5),
                            Pokemon(data, "Chikorita", 5), Pokemon(data, "Cyndaquil", 5), Pokemon(data, "Totodile", 5),
                            Pokemon(data, "Treecko", 5), Pokemon(data, "Torchic", 5), Pokemon(data, "Mudkip", 5),
                            Pokemon(data, "Turtwig", 5), Pokemon(data, "Chimchar", 5), Pokemon(data, "Piplup", 5),
                            Pokemon(data, "Snivy", 5), Pokemon(data, "Tepig", 5), Pokemon(data, "Oshawott", 5),
                            Pokemon(data, "Chespin", 5), Pokemon(data, "Fennekin", 5), Pokemon(data, "Froakie", 5),
                            Pokemon(data, "Rowlet", 5), Pokemon(data, "Litten", 5), Pokemon(data, "Popplio", 5),
                            Pokemon(data, "Grookey", 5), Pokemon(data, "Scorbunny", 5), Pokemon(data, "Sobble", 5)]
        self.natures = ["adamant", "bashful", "bold", "brave", "calm", "careful", "docile", "gentle", "hardy",
                        "hasty",
                        "impish", "jolly", "lax", "lonely", "mild", "modest", "naive", "naughty", "quiet",
                        "quirky",
                        "rash", "relaxed",
                        "sassy", "serious", "timid"]
        self.select_menu = None
        self.init_select()

    def init_select(self):
        option_list = []
        for pokemon in self.starterList:
            option = SelectOption(label=pokemon.name)
            if pokemon.shiny:
                option.emoji = "🌟"
            option_list.append(option)
        self.select_menu = Select(options=option_list)
        self.add_item(self.select_menu)

    def get_starter(self, name):
        for pokemon in self.starterList:
            if name == pokemon.name:
                return pokemon