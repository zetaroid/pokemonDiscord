import asyncio
import math

import disnake
from disnake import SelectOption
from disnake.ui import Select

from Pokemon import Pokemon


class ConfirmView(disnake.ui.View):
    def __init__(self, author, text_confirm, text_nevermind, flip_color=False, disable_first=False):
        super().__init__()
        self.author = author
        self.confirmed = False
        self.children[0].label = text_confirm
        self.children[1].label = text_nevermind
        self.timed_out = False
        if flip_color:
            self.children[0].style = disnake.ButtonStyle.green
            self.children[1].style = disnake.ButtonStyle.red
        if disable_first:
            self.children[0].disabled = True

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

    async def on_timeout(self):
        self.timed_out = True


class OverworldUIView(disnake.ui.View):
    def __init__(self, author, button_list, timeout=600):
        super().__init__(timeout=timeout)
        self.author = author
        for button in button_list:
            self.add_item(button)
        self.timed_out = False

    async def verify_response(self, interaction: disnake.MessageInteraction):
        if interaction.author != self.author:
            return await interaction.send("This session is not yours! Please begin your own with `/start`.")
        await interaction.response.defer()
        self.stop()

    async def on_timeout(self):
        self.timed_out = True


class OverworldUIButton(disnake.ui.Button):
    def __init__(self, label="\u200b", emoji=None, row=None, style=disnake.ButtonStyle.gray, info="", identifier=0):
        super().__init__(label=label, emoji=emoji, row=row, style=style, custom_id=str(identifier))
        self.info = info
        self.identifier = identifier

    async def callback(self, interaction):
        pass


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
                option.label += "🌟"
            option_list.append(option)
        self.select_menu = Select(options=option_list)
        self.add_item(self.select_menu)

    def get_starter(self, name):
        for pokemon in self.starterList:
            if name == pokemon.name:
                return pokemon


def get_box_select(offset, max_boxes):
    current_box = offset + 1
    option_list = []
    remaining = 24
    forward = True
    backward = False
    highest_forward_count = 0
    count = 0
    for x in range(0, max_boxes):
        if remaining <= 0:
            break
        if forward:
            if count >= 12 or (current_box + count) >= max_boxes:
                forward = False
                backward = True
                highest_forward_count = count
                count = 0
            else:
                box_num_str = str(current_box + count + 1)
                option = SelectOption(label="Box " + box_num_str, value="box," + box_num_str)
                option_list.append(option)
                count += 1
        if backward:
            if (current_box - count - 1) <= 0:
                backward = False
                count = highest_forward_count
            else:
                box_num_str = str(current_box - count - 1)
                option = SelectOption(label="Box " + box_num_str, value="box," + box_num_str)
                option_list.insert(0, option)
                count += 1
        if not forward and not backward:
            if (current_box + count) >= max_boxes:
                break
            box_num_str = str(current_box + count + 1)
            option = SelectOption(label="Box " + box_num_str, value="box," + box_num_str)
            option_list.append(option)
            count += 1
        remaining -= 1
    if len(option_list) > 0:
        select = Select(options=option_list, custom_id="box_select")
        select.placeholder = "Box " + str(current_box)
        return select
    return None


def get_mart_select(items=None):
    option_list = []
    if items:
        for x in range(0, len(items)):
            option = SelectOption(label=items[x], value="item," + items[x])
            option_list.append(option)
        select = Select(options=option_list, custom_id="item_select")
        select.placeholder = "Select item"
    else:
        for x in range(0, 20):
            option = SelectOption(label=str(x+1), value="quantity," + str(x+1))
            option_list.append(option)
        select = Select(options=option_list, custom_id="box_select")
        select.placeholder = "Select purchase quantity (default: 1)"
    return select
