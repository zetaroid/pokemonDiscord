import random
import uuid

import disnake
from PIL import Image


class SlotOptions:
    red_7 = 'red_7'
    blue_7 = 'blue_7'
    bolt = 'bolt'
    lotad = 'lotad'
    cherry = 'cherry'
    replay = 'replay'
    azurill = 'azurill'


class Slots(object):
    path = 'data/sprites/game_corner/'
    background_path = path + 'game_corner_template.png'
    game_corner_image_path = path + 'game_corner.png'
    slots_image_path = path + 'game_corner_slots.png'
    image_paths = {
        'red_7': 'game_corner_red_7.png',
        'blue_7': 'game_corner_blue_7.png',
        'azurill': 'game_corner_azurill.png',
        'bolt': 'game_corner_bolt.png',
        'cherry': 'game_corner_cherry.png',
        'lotad': 'game_corner_lotad.png',
        'replay': 'game_corner_replay.png'
    }
    gif = 'https://i.imgur.com/Ti6TJaD.gif'
    #gif = 'https://i.imgur.com/qhd0PS7.gif' #small
    payouts = { # does not include 2 cherries or 1 cherry or triple replay
        'red_7,red_7,red_7': 300,
        'blue_7,blue_7,blue_7': 300,
        'blue_7,blue_7,red_7': 90,
        #'blue_7,red_7,blue_7': 90,
        #'blue_7,red_7,red_7': 90,
        'red_7,red_7,blue_7': 90,
        #'red_7,blue_7,red_7': 90,
        #'red_7,blue_7,blue_7': 90,
        'azurill,azurill,azurill': 12,
        'lotad,lotad,lotad': 6,
        'cherry,cherry,cherry': 6,
        'bolt,bolt,bolt': 8
    }
    roulette_1_list = [SlotOptions.bolt, SlotOptions.lotad, SlotOptions.replay, SlotOptions.red_7, SlotOptions.cherry,
                       SlotOptions.azurill, SlotOptions.replay, SlotOptions.bolt, SlotOptions.lotad, SlotOptions.blue_7,
                       SlotOptions.lotad, SlotOptions.cherry, SlotOptions.bolt, SlotOptions.replay, SlotOptions.azurill,
                       SlotOptions.red_7, SlotOptions.bolt, SlotOptions.lotad, SlotOptions.replay, SlotOptions.azurill,
                       SlotOptions.blue_7]
    roulette_2_list = [SlotOptions.bolt, SlotOptions.bolt, SlotOptions.lotad, SlotOptions.blue_7, SlotOptions.lotad,
                       SlotOptions.replay, SlotOptions.cherry, SlotOptions.azurill, SlotOptions.lotad, SlotOptions.replay,
                       SlotOptions.cherry, SlotOptions.lotad, SlotOptions.replay, SlotOptions.cherry, SlotOptions.red_7,
                       SlotOptions.cherry, SlotOptions.replay, SlotOptions.lotad, SlotOptions.azurill, SlotOptions.cherry,
                       SlotOptions.replay]
    roulette_3_list = [SlotOptions.bolt, SlotOptions.replay, SlotOptions.lotad, SlotOptions.cherry, SlotOptions.red_7,
                       SlotOptions.bolt, SlotOptions.blue_7, SlotOptions.replay, SlotOptions.lotad, SlotOptions.azurill,
                       SlotOptions.replay, SlotOptions.lotad, SlotOptions.bolt, SlotOptions.azurill, SlotOptions.replay,
                       SlotOptions.lotad, SlotOptions.azurill, SlotOptions.bolt, SlotOptions.replay, SlotOptions.lotad,
                       SlotOptions.azurill]

    def roll(self):
        min_roll = 0
        max_roll = 20
        roll_1 = random.randint(min_roll, max_roll)
        roll_2 = random.randint(min_roll, max_roll)
        roll_3 = random.randint(min_roll, max_roll)
        if roll_1 == min_roll:
            r1_c1 = self.roulette_1_list[max_roll]
        else:
            r1_c1 = self.roulette_1_list[roll_1 - 1]
        r2_c1 = self.roulette_1_list[roll_1]
        if roll_1 == max_roll:
            r3_c1 = self.roulette_1_list[min_roll]
        else:
            r3_c1 = self.roulette_1_list[roll_1 + 1]

        if roll_2 == min_roll:
            r1_c2 = self.roulette_2_list[max_roll]
        else:
            r1_c2 = self.roulette_2_list[roll_2 - 1]
        r2_c2 = self.roulette_2_list[roll_2]
        if roll_2 == max_roll:
            r3_c2 = self.roulette_2_list[min_roll]
        else:
            r3_c2 = self.roulette_2_list[roll_2 + 1]

        if roll_3 == min_roll:
            r1_c3 = self.roulette_3_list[max_roll]
        else:
            r1_c3 = self.roulette_3_list[roll_3 - 1]
        r2_c3 = self.roulette_3_list[roll_3]
        if roll_3 == max_roll:
            r3_c3 = self.roulette_3_list[min_roll]
        else:
            r3_c3 = self.roulette_3_list[roll_3 + 1]

        result = [
            [r1_c1, r1_c2, r1_c3],
            [r2_c1, r2_c2, r2_c3],
            [r3_c1, r3_c2, r3_c3]
        ]

        return result

    def check_result(self, result, coins):
        payout = 0
        replay = False
        center_row = result[1][0] + ',' + result[1][1] + ',' + result[1][2]
        top_row = result[0][0] + ',' + result[0][1] + ',' + result[0][2]
        bottom_row = result[2][0] + ',' + result[2][1] + ',' + result[2][2]
        diagonal_top_left = result[0][0] + ',' + result[1][1] + ',' + result[2][2]
        diagonal_bottom_right = result[2][0] + ',' + result[1][1] + ',' + result[0][2]
        rows = []
        if coins == 1:
            rows = [center_row]
        elif coins == 2:
            rows = [center_row, top_row, bottom_row]
        elif coins == 3:
            rows = [center_row, top_row, bottom_row, diagonal_bottom_right, diagonal_top_left]
        print('')
        print('winning rows:')
        single_cherry_won = False
        for row in rows:
            if row in self.payouts.keys():
                print(row, self.payouts[row])
                payout += self.payouts[row]
            if row.startswith('cherry,cherry'):
                print(row, 4)
                payout += 4
            elif row.startswith('cherry') and not single_cherry_won:
                print(row, 2)
                payout += 2
                single_cherry_won = True
            if 'replay,replay,replay' in row:
                print(row, 'replay')
                replay = True
        return payout, replay

    def create_slot_result_image(self, result):
        background = Image.open(self.background_path)
        background = background.convert('RGBA')
        image1_path = self.path + self.image_paths[result[0][0]]
        image2_path = self.path + self.image_paths[result[0][1]]
        image3_path = self.path + self.image_paths[result[0][2]]
        image4_path = self.path + self.image_paths[result[1][0]]
        image5_path = self.path + self.image_paths[result[1][1]]
        image6_path = self.path + self.image_paths[result[1][2]]
        image7_path = self.path + self.image_paths[result[2][0]]
        image8_path = self.path + self.image_paths[result[2][1]]
        image9_path = self.path + self.image_paths[result[2][2]]
        image1 = Image.open(image1_path)
        image2 = Image.open(image2_path)
        image3 = Image.open(image3_path)
        image4 = Image.open(image4_path)
        image5 = Image.open(image5_path)
        image6 = Image.open(image6_path)
        image7 = Image.open(image7_path)
        image8 = Image.open(image8_path)
        image9 = Image.open(image9_path)
        background.paste(image1, (69, 78), image1.convert('RGBA'))
        background.paste(image2, (155, 78), image2.convert('RGBA'))
        background.paste(image3, (242, 78), image3.convert('RGBA'))
        background.paste(image4, (69, 130), image4.convert('RGBA'))
        background.paste(image5, (155, 130), image5.convert('RGBA'))
        background.paste(image6, (242, 130), image6.convert('RGBA'))
        background.paste(image7, (69, 181), image7.convert('RGBA'))
        background.paste(image8, (155, 181), image8.convert('RGBA'))
        background.paste(image9, (242, 181), image9.convert('RGBA'))
        # background.paste(image1, (32, 36), image1.convert('RGBA'))
        # background.paste(image2, (72, 36), image2.convert('RGBA'))
        # background.paste(image3, (112, 36), image3.convert('RGBA'))
        # background.paste(image4, (32, 60), image4.convert('RGBA'))
        # background.paste(image5, (72, 60), image5.convert('RGBA'))
        # background.paste(image6, (112, 60), image6.convert('RGBA'))
        # background.paste(image7, (32, 84), image7.convert('RGBA'))
        # background.paste(image8, (72, 84), image8.convert('RGBA'))
        # background.paste(image9, (112, 84), image9.convert('RGBA'))
        temp_uuid = uuid.uuid4()
        filename = "data/temp/merged_image" + str(temp_uuid) + ".png"
        background.save(filename, "PNG")
        return filename

    def get_slot_roll_embed(self, author_name, result):
        embed = disnake.Embed(title='Game Corner - Slots', description=author_name + ' is playing slots.\n')
        embed.set_image(url=self.gif)
        result_filename = self.create_slot_result_image(result)
        file = disnake.File(result_filename, filename="image.png")
        embed.set_footer(text='Press STOP below!')
        return embed, file

    def get_game_corner_embed(self, author_name):
        embed = disnake.Embed(title='Game Corner', description='Welcome!')
        file = disnake.File(self.game_corner_image_path, filename="image.png")
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=author_name + ' is visiting the Game Corner.')
        return embed, file

    def get_slot_embed(self, author_name):
        embed = disnake.Embed(title='Game Corner - Slots', description=author_name + 'is playing slots.')
        file = disnake.File(self.slots_image_path, filename="image.png")
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text='Choose number of coins below!\n' + self.get_footer_for_trainer(None))
        return embed, file

    def get_footer_for_trainer(self, trainer):
        footer = ''
        footer += 'Credit: ' + str(1234)
        footer += '\nReplays: ' + str(2)
        return footer


class GameCornerView(disnake.ui.View):
    def __init__(self, author_id, timeout=600):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.slots = True
        self.timed_out = False

    @disnake.ui.button(label="Slots", style=disnake.ButtonStyle.blurple)
    async def option_stop(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if await self.verify_response(interaction):
            self.slots = True

    async def verify_response(self, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.author_id:
            await interaction.response.send_message(
                "Sorry, this slots session is not for you.",
                ephemeral=True,
            )
            return False
        await interaction.response.defer()
        self.stop()
        return True

    async def on_timeout(self):
        self.timed_out = True


class RollingView(disnake.ui.View):
    def __init__(self, author_id, timeout=600):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.stopped = True
        self.timed_out = False

    @disnake.ui.button(label="STOP", style=disnake.ButtonStyle.red)
    async def option_stop(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if await self.verify_response(interaction):
            self.stopped = True

    async def verify_response(self, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.author_id:
            await interaction.response.send_message(
                "Sorry, this slots session is not for you.",
                ephemeral=True,
            )
            return False
        await interaction.response.defer()
        self.stop()
        return True

    async def on_timeout(self):
        self.timed_out = True


class RolledView(disnake.ui.View):
    def __init__(self, author_id, timeout=600):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.coins = 0
        self.timed_out = False
        self.replay = False

    @disnake.ui.button(label="1", style=disnake.ButtonStyle.blurple, emoji='🪙')
    async def option_coin1(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if await self.verify_response(interaction):
            self.coins = 1

    @disnake.ui.button(label="2", style=disnake.ButtonStyle.blurple, emoji='🪙')
    async def option_coin2(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if await self.verify_response(interaction):
            self.coins = 2

    @disnake.ui.button(label="3", style=disnake.ButtonStyle.blurple, emoji='🪙')
    async def option_coin3(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if await self.verify_response(interaction):
            self.coins = 3

    @disnake.ui.button(label="Free Replay", style=disnake.ButtonStyle.green, disabled=True)
    async def option_replay(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if await self.verify_response(interaction):
            self.replay = True

    async def verify_response(self, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.author_id:
            await interaction.response.send_message(
                "Sorry, this slots session is not for you.",
                ephemeral=True,
            )
            return False
        await interaction.response.defer()
        self.stop()
        return True

    async def on_timeout(self):
        self.timed_out = True
