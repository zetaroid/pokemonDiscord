import uuid

import disnake
from datetime import datetime

from disnake import SelectOption
from disnake.ui import Select

from PIL import Image


class Trade(object):

    def __init__(self, author_1, user_1, user_2):
        self.author_1 = author_1
        self.user_1 = user_1
        self.user_2 = user_2
        self.pokemon_id_1 = None
        self.pokemon_id_2 = None
        self.pokemon_pos_1 = None
        self.pokemon_pos_2 = None
        self.author_2 = None
        self.timestamp = datetime.today()
        self.identifier = uuid.uuid4()

    def get_pokemon_1(self):
        for pokemon in self.user_1.partyPokemon:
            if pokemon.identifier == self.pokemon_id_1:
                return pokemon
        return None

    def get_pokemon_2(self):
        for pokemon in self.user_2.partyPokemon:
            if pokemon.identifier == self.pokemon_id_2:
                return pokemon
        return None

    def make_trade(self):
        if not self.pokemon_id_1 or not self.pokemon_id_2:
            return False
        pokemon_1 = None
        pokemon_2 = None
        party_number_1 = 0
        party_number_2 = 0
        for pokemon in self.user_1.partyPokemon:
            party_number_1 += 1
            if pokemon.identifier == self.pokemon_id_1:
                if self.pokemon_pos_1 and self.pokemon_pos_1 != party_number_1:
                    continue
                pokemon_1 = pokemon
                break
        for pokemon in self.user_2.partyPokemon:
            party_number_2 += 1
            if pokemon.identifier == self.pokemon_id_2:
                if self.pokemon_pos_2 and self.pokemon_pos_2 != party_number_2:
                    continue
                pokemon_2 = pokemon
                break
        if pokemon_1 and pokemon_2:
            pokemon_1.setForm(0)
            pokemon_2.setForm(0)
            self.user_1.partyPokemon[party_number_1 - 1] = pokemon_2
            self.user_2.partyPokemon[party_number_2 - 1] = pokemon_1
            self.user_1.update_pokedex(self.user_1.partyPokemon[party_number_1 - 1].name)
            self.user_2.update_pokedex(self.user_2.partyPokemon[party_number_2 - 1].name)
            return True
        return False


class ChooseTradePokemonEmbed(disnake.embeds.Embed):
    def __init__(self, user):
        super().__init__(title=user.name + ", please select the Pokemon you would like to trade below:", description='\u200b')
        self.user = user
        self.init_footer()
        self.init_thumbnail()
        self.color = disnake.Color.blue()

    def init_footer(self):
        self.set_footer(
            text=f"Trade for {self.user}",
            icon_url=self.user.display_avatar,
        )

    def init_thumbnail(self):
        self.set_thumbnail(url="https://styles.redditmedia.com/t5_2rmov/styles/communityIcon_8jj0o28zosp21.png")


class ChooseTradePokemonView(disnake.ui.View):
    def __init__(self, trainer):
        super().__init__()
        self.trainer = trainer
        self.chosen = ""
        self.select_menu = None
        self.init_select()

    def init_select(self):
        option_list = []
        label_dict = {}
        value_dict = {}
        for pokemon in self.trainer.partyPokemon:
            label = pokemon.name
            if label in label_dict.keys():
                label_dict[label] += 1
            else:
                label_dict[label] = 1
            if label_dict[label] != 1:
                label = label + " (" + str(label_dict[label]) + ")"
            value = pokemon.identifier
            if value in value_dict.keys():
                value_dict[value] += 1
            else:
                value_dict[value] = 1
            if value_dict[value] != 1:
                value = value + "_" + str(value_dict[value])
            option = SelectOption(label=label, value=value)
            if pokemon.shiny:
                option.label += "🌟"
            option_list.append(option)
        self.select_menu = Select(options=option_list)
        self.add_item(self.select_menu)


class TradeConfirmSingleEmbed(disnake.embeds.Embed):
    def __init__(self, bot, user, trainer, trade, is_initiator=True):
        if is_initiator:
            title = user.name + ", please confirm the Pokemon you would like to trade:"
        else:
            title = trade.user_2.name + ", would you like to accept trade request from " + trade.author_1.name + "?"
        super().__init__(title=title, description='\u200b')
        self.user = user
        self.bot = bot
        self.trainer = trainer
        self.trade = trade
        self.files = []
        if is_initiator:
            self.init_footer()
        self.init_thumbnail()
        self.init_fields()
        self.color = disnake.Color.blue()

    def init_footer(self):
        self.set_footer(
            text=f"Trade for {self.user}",
            icon_url=self.user.display_avatar,
        )

    def init_thumbnail(self):
        self.set_thumbnail(url="https://styles.redditmedia.com/t5_2rmov/styles/communityIcon_8jj0o28zosp21.png")

    def init_fields(self):
        pokemon = self.trade.get_pokemon_1()
        if pokemon:
            levelString = "Level: " + str(pokemon.level)
            ivString = "IV's: " + str(pokemon.hpIV) + "/" + str(pokemon.atkIV) + "/" + str(pokemon.defIV) + "/" \
                       + str(pokemon.spAtkIV) + "/" + str(pokemon.spDefIV) + "/" + str(pokemon.spdIV)
            evString = "EV's: " + str(pokemon.hpEV) + "/" + str(pokemon.atkEV) + "/" + str(pokemon.defEV) + "/" \
                       + str(pokemon.spAtkEV) + "/" + str(pokemon.spDefEV) + "/" + str(pokemon.spdEV)
            natureString = 'Nature: ' + pokemon.nature.capitalize()
            otString = "OT: " + pokemon.OT
            obtainedString = 'Obtained: ' + pokemon.location
            moveString = ''
            count = 1
            for move in pokemon.moves:
                moveString += 'Move ' + str(count) + ': ' + move['names']['en'] + '\n'
                count += 1
            shinyString = ''
            if pokemon.shiny:
                shinyString = " :star2:"
            file = disnake.File(pokemon.getSpritePath(), filename="image.png")
            self.files.append(file)
            self.set_image(url="attachment://image.png")
            embedValue = levelString + '\n' + otString + '\n' + natureString + '\n' + obtainedString + '\n' + evString + '\n' + ivString + '\n' + moveString
            self.add_field(name=pokemon.nickname + " (" + pokemon.name + ")" + shinyString, value=embedValue,
                           inline=True)


class TradeConfirmDoubleEmbed(disnake.embeds.Embed):
    def __init__(self, bot, user, trainer, trade, trade_complete=False):
        if trade_complete:
            title = "TRADE COMPLETED"
        else:
            title = user.name + ", please confirm if you would like to make this trade:"
        super().__init__(title=title, description='\u200b')
        self.user = user
        self.bot = bot
        self.trainer = trainer
        self.trade = trade
        self.pokemon_sprites = []
        self.files = []
        self.init_footer()
        # self.init_thumbnail()
        self.init_fields()
        self.color = disnake.Color.blue()

    def init_footer(self):
        self.set_footer(
            text=f"Trade for {self.trade.author_1} and {self.trade.author_2}",
        )

    def init_thumbnail(self):
        self.set_thumbnail(url="https://styles.redditmedia.com/t5_2rmov/styles/communityIcon_8jj0o28zosp21.png")

    def init_fields(self):
        self.add_pokemon_field(self.trade.get_pokemon_1())
        self.add_field(name="・ FOR ・", value='\u200b')
        self.add_pokemon_field(self.trade.get_pokemon_2())
        filename = self.merge_images()
        if filename:
            self.add_image(filename)

    def add_pokemon_field(self, pokemon):
        if pokemon:
            levelString = "Level: " + str(pokemon.level)
            ivString = "IV's: " + str(pokemon.hpIV) + "/" + str(pokemon.atkIV) + "/" + str(pokemon.defIV) + "/" \
                       + str(pokemon.spAtkIV) + "/" + str(pokemon.spDefIV) + "/" + str(pokemon.spdIV)
            evString = "EV's: " + str(pokemon.hpEV) + "/" + str(pokemon.atkEV) + "/" + str(pokemon.defEV) + "/" \
                       + str(pokemon.spAtkEV) + "/" + str(pokemon.spDefEV) + "/" + str(pokemon.spdEV)
            natureString = 'Nature: ' + pokemon.nature.capitalize()
            otString = "OT: " + pokemon.OT
            obtainedString = 'Obtained: ' + pokemon.location
            shinyString = ''
            if pokemon.shiny:
                shinyString = " :star2:"
            self.pokemon_sprites.append(pokemon.getSpritePath())
            embedValue = levelString + '\n' + otString + '\n' + natureString + '\n' + obtainedString + '\n' + evString + '\n' + ivString
            self.add_field(name=pokemon.nickname + " (" + pokemon.name + ")" + shinyString, value=embedValue,
                           inline=True)

    def add_image(self, filename):
        file = disnake.File(filename, filename="image.png")
        self.files.append(file)
        self.set_image(url="attachment://image.png")

    def merge_images(self):
        if len(self.pokemon_sprites) < 2:
            return ""
        path1 = self.pokemon_sprites[0]
        path2 = self.pokemon_sprites[1]
        backgroundPath = 'data/sprites/trade_template.png'
        background = Image.open(backgroundPath)
        background = background.convert('RGBA')
        image1 = Image.open(path1)
        image1 = image1.transpose(method=Image.FLIP_LEFT_RIGHT)
        image2 = Image.open(path2)
        background.paste(image1, (0, 0), image1.convert('RGBA'))
        background.paste(image2, (143, 0), image2.convert('RGBA'))
        temp_uuid = uuid.uuid4()
        filename = "data/temp/merged_image" + str(temp_uuid) + ".png"
        background.save(filename, "PNG")
        return filename


class TradeConfirmView(disnake.ui.View):
    def __init__(self, author_id, is_initiator=True, timeout=60):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.confirmed = False
        self.is_initiator = is_initiator
        self.author_2 = None
        self.timed_out = False
        if is_initiator:
            self.children[0].label = "Confirm"
            self.children[1].label = "Cancel"
        else:
            self.children[0].label ="Accept"
            self.children[1].label = "Refuse"

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.green)
    async def option_yes(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.confirmed = True
        await self.verify_response(interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.red)
    async def option_no(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.verify_response(interaction)

    async def verify_response(self, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.author_id:
            await interaction.response.send_message(
                "Sorry, this trade window is not for you.",
                ephemeral=True,
            )
            return
        if not self.is_initiator:
            self.author_2 = interaction.author
        await interaction.response.defer()
        self.stop()

    async def on_timeout(self):
        self.timed_out = True
