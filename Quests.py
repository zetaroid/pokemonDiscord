import math
from copy import copy

from Pokemon import Pokemon
import disnake


class Quest(object):

    def __init__(self):
        self.title = ""
        self.location_requirement = ""
        self.task = ""

        self.defeat_specific_pokemon = {}
        self.defeat_specific_pokemon_original = {}

        self.defeat_specific_trainer = []
        self.defeat_specific_trainer_original = []

        self.catch_specific_pokemon = {}
        self.catch_specific_pokemon_original = {}

        self.catch_level_pokemon = {}
        self.catch_level_pokemon_original = {}

        self.pokemon_caught = 0
        self.pokemon_caught_original = 0

        self.pokemon_defeated = 0
        self.pokemon_defeated_original = 0

        self.trainers_defeated = 0
        self.trainers_defeated_original = 0

        self.raids_defeated = 0
        self.raids_defeated_original = 0

        self.item_rewards = {}
        self.pokemon_rewards = []

        self.complete = False
        self.started = False
        self.can_abandon = True

    def __copy__(self):
        questCopy = type(self)()
        questCopy.title = self.title
        questCopy.location_requirement = self.location_requirement
        questCopy.task = self.task

        questCopy.defeat_specific_pokemon = self.defeat_specific_pokemon.copy()
        questCopy.defeat_specific_pokemon_original = self.defeat_specific_pokemon_original.copy()

        questCopy.defeat_specific_trainer = self.defeat_specific_trainer.copy()
        questCopy.defeat_specific_trainer_original = self.defeat_specific_trainer_original.copy()

        questCopy.catch_specific_pokemon = self.catch_specific_pokemon.copy()
        questCopy.catch_specific_pokemon_original = self.catch_specific_pokemon_original.copy()

        questCopy.catch_level_pokemon = self.catch_level_pokemon.copy()
        questCopy.catch_level_pokemon_original = self.catch_level_pokemon_original.copy()

        questCopy.pokemon_caught = self.pokemon_caught
        questCopy.pokemon_defeated = self.pokemon_defeated
        questCopy.trainers_defeated = self.trainers_defeated
        questCopy.raids_defeated = self.raids_defeated

        questCopy.pokemon_caught_original = self.pokemon_caught_original
        questCopy.pokemon_defeated_original = self.pokemon_defeated_original
        questCopy.trainers_defeated_original = self.trainers_defeated_original
        questCopy.raids_defeated_original = self.raids_defeated_original

        copiedRewardPokemon = []
        for pokemon in self.pokemon_rewards:
            copiedRewardPokemon.append(copy(pokemon))
        questCopy.pokemon_rewards = copiedRewardPokemon

        questCopy.item_rewards = self.item_rewards.copy()
        questCopy.can_abandon = self.can_abandon
        return questCopy

    def start(self):
        self.started = True

    def get_task_string(self):
        return self.task.replace("_", " ").title()

    def redeem_rewards(self, trainer):
        for item_name, amount in self.item_rewards.items():
            trainer.addItem(item_name, amount)
        for pokemon in self.pokemon_rewards:
            trainer.addPokemon(pokemon, True, True)
        trainer.completedQuestList.append(self.title)

    def get_rewards_string(self, trainer=None):
        item_reward_string = ""
        pokemon_rewards_string = ""
        for item_name, amount in self.item_rewards.items():
            item_reward_string += '・ ' + item_name + ' x ' + str(amount) + '\n'
        for pokemon in self.pokemon_rewards:
            pokemon_rewards_string = '・ ' + pokemon.name
            if pokemon.altShiny:
                pokemon_rewards_string += '✨'
            elif pokemon.distortion:
                pokemon_rewards_string += '🧿'
            elif pokemon.shiny:
                pokemon_rewards_string += ' 🌟'
            if pokemon.shadow:
                pokemon_rewards_string += '🌒'
            pokemon_rewards_string += '\n'
        reward_string = ""
        if item_reward_string:
            reward_string += "*Items:*\n" + item_reward_string
        if pokemon_rewards_string:
            reward_string += "*Pokemon*\n" + pokemon_rewards_string
        if not reward_string:
            reward_string = "・ None"
        return reward_string

    def get_objective_string(self):
        objective = ""
        check_emoji = '✅'
        if self.task == 'defeat_specific_pokemon':
            for pokemon_name, amount_remaining in self.defeat_specific_pokemon.items():
                total = self.defeat_specific_pokemon_original[pokemon_name]
                amount_completed = total - amount_remaining
                objective += "・ Defeat " + pokemon_name + ': ' + str(amount_completed) + '/' + str(total)
                if amount_remaining == 0:
                    objective += " " + check_emoji
                objective += "\n"
        if self.task == 'defeat_specific_trainer':
            for trainer_name in self.defeat_specific_trainer_original:
                objective += "・ Defeat " + trainer_name
                if trainer_name not in self.defeat_specific_trainer:
                    objective += " " + check_emoji
                objective += "\n"
        if self.task == 'catch_specific_pokemon':
            for pokemon_name, amount_remaining in self.catch_specific_pokemon.items():
                total = self.catch_specific_pokemon_original[pokemon_name]
                amount_completed = total - amount_remaining
                objective += "・ Catch " + pokemon_name + ': ' + str(amount_completed) + '/' + str(total)
                if amount_remaining == 0:
                    objective += " " + check_emoji
                objective += "\n"
        if self.task == 'catch_level_pokemon':
            for pokemon_name, amount_remaining in self.catch_level_pokemon.items():
                total = self.catch_level_pokemon_original[pokemon_name]
                amount_completed = total - amount_remaining
                objective += "・ Catch " + pokemon_name + ': ' + str(amount_completed) + '/' + str(total)
                if amount_remaining == 0:
                    objective += " " + check_emoji
                objective += "\n"
        if self.task == 'pokemon_caught':
            total = self.pokemon_caught_original
            amount_completed = total - self.pokemon_caught
            objective += "・ Catch any Pokemon: " + str(amount_completed) + '/' + str(total)
        if self.task == 'trainers_defeated':
            total = self.trainers_defeated_original
            amount_completed = total - self.trainers_defeated
            objective += "・ Defeat any Trainers: " + str(amount_completed) + '/' + str(total)
        if self.task == 'pokemon_defeated':
            total = self.pokemon_defeated_original
            amount_completed = total - self.pokemon_defeated
            objective += "・ Defeat any Pokemon: " + str(amount_completed) + '/' + str(total)
        if self.task == 'raids_defeated':
            total = self.raids_defeated_original
            amount_completed = total - self.raids_defeated
            objective += "・ Defeat Raids: " + str(amount_completed) + '/' + str(total)
        return objective

    def defeat_pokemon(self, pokemon, location=""):
        if self.location_requirement:
            if self.location_requirement != location:
                return
        if self.pokemon_defeated > 0:
            self.pokemon_defeated -= 1
        if pokemon.name in self.defeat_specific_pokemon.keys():
            if self.defeat_specific_pokemon[pokemon.name] > 0:
                self.defeat_specific_pokemon[pokemon.name] -= 1

    def defeat_raid(self):
        if self.raids_defeated > 0:
            self.raids_defeated -= 1

    def defeat_trainer(self, trainer):
        if self.trainers_defeated > 0:
            self.trainers_defeated -= 1
        if trainer.name in self.defeat_specific_trainer:
            self.defeat_specific_trainer.remove(trainer.name)

    def catch_pokemon(self, pokemon, location=""):
        if self.location_requirement:
            if self.location_requirement != location:
                return
        if self.pokemon_caught > 0:
            self.pokemon_caught -= 1
        if pokemon.name in self.catch_specific_pokemon.keys():
            if self.catch_specific_pokemon[pokemon.name] > 0:
                self.catch_specific_pokemon[pokemon.name] -= 1
        for level in list(self.catch_level_pokemon.keys()):
            if pokemon.level >= level:
                if self.catch_level_pokemon[level] > 0:
                    self.catch_level_pokemon[level] -= 1

    def check_complete(self):
        if self.started:
            defeat_specific_pokemon_bool = all(i == 0 for i in list(self.defeat_specific_pokemon.values()))
            defeat_specific_trainer_bool = (len(self.defeat_specific_trainer) == 0)
            catch_specific_pokemon_bool = all(i == 0 for i in list(self.catch_specific_pokemon.values()))
            catch_level_pokemon_bool = all(i == 0 for i in list(self.catch_level_pokemon.values()))
            pokemon_caught_bool = (self.pokemon_caught == 0)
            pokemon_defeated_bool = (self.pokemon_defeated == 0)
            trainers_defeated_bool = (self.trainers_defeated == 0)
            raids_defeated_bool = (self.raids_defeated == 0)
            if defeat_specific_trainer_bool and defeat_specific_pokemon_bool and catch_specific_pokemon_bool and \
                    pokemon_defeated_bool and pokemon_caught_bool and trainers_defeated_bool and raids_defeated_bool \
                    and catch_level_pokemon_bool:
                self.complete = True
        return self.complete

    def to_json(self):
        pokemon_reward_list = []
        for pokemon in self.pokemon_rewards:
            pokemon_reward_list.append(pokemon.toJSON())
        jsonDict = {
            'title': self.title,
            'location_requirement': self.location_requirement,
            'task': self.task,
            'started': self.started,
            'complete': self.complete,
            'pokemon_rewards': pokemon_reward_list,
            'item_rewards_names': list(self.item_rewards.keys()),
            'item_rewards_amounts': list(self.item_rewards.values()),
            'can_abandon': self.can_abandon,

            'defeat_specific_trainer': self.defeat_specific_trainer,

            'defeat_specific_trainer_original': self.defeat_specific_trainer_original,

            'defeat_specific_pokemon_names': list(self.defeat_specific_pokemon.keys()),
            'defeat_specific_pokemon_amounts': list(self.defeat_specific_pokemon.values()),

            'defeat_specific_pokemon_original_names': list(self.defeat_specific_pokemon_original.keys()),
            'defeat_specific_pokemon_original_amounts': list(self.defeat_specific_pokemon_original.values()),

            'catch_specific_pokemon_names': list(self.catch_specific_pokemon.keys()),
            'catch_specific_pokemon_amounts': list(self.catch_specific_pokemon.values()),

            'catch_specific_pokemon_original_names': list(self.catch_specific_pokemon_original.keys()),
            'catch_specific_pokemon_original_amounts': list(self.catch_specific_pokemon_original.values()),

            'catch_level_pokemon_names': list(self.catch_level_pokemon.keys()),
            'catch_level_pokemon_amounts': list(self.catch_level_pokemon.values()),

            'catch_level_pokemon_original_names': list(self.catch_level_pokemon_original.keys()),
            'catch_level_pokemon_original_amounts': list(self.catch_level_pokemon_original.values()),

            'pokemon_caught': self.pokemon_caught,
            'pokemon_caught_original': self.pokemon_caught_original,

            'pokemon_defeated': self.pokemon_defeated,
            'pokemon_defeated_original': self.pokemon_defeated_original,

            'trainers_defeated': self.trainers_defeated,
            'trainers_defeated_original': self.trainers_defeated_original,

            'raids_defeated': self.raids_defeated,
            'raids_defeated_original': self.raids_defeated_original,
        }
        return jsonDict

    def from_json(self, json, data, from_event=False):
        if 'title' in json:
            self.title = json['title']
        if 'task' in json:
            self.task = json['task']
        if 'location_requirement' in json:
            self.location_requirement = json['location_requirement']
        if "can_abandon" in json:
            self.can_abandon = json['can_abandon']

        if from_event:
            if 'pokemon_rewards' in json:
                for pokemon_json in json['pokemon_rewards']:
                    pokemon = Pokemon(data, pokemon_json['name'], pokemon_json['level'])
                    if 'shiny' in pokemon_json:
                        if pokemon_json['shiny']:
                            pokemon.shiny = pokemon_json['shiny']
                    else:
                        pokemon.shiny = False
                    if 'distortion' in pokemon_json:
                        if pokemon_json['distortion']:
                            pokemon.distortion = pokemon_json['distortion']
                    else:
                        pokemon.distortion = False
                    if 'altshiny' in pokemon_json:
                        if pokemon_json['altshiny']:
                            pokemon.altShiny = pokemon_json['altshiny']
                    else:
                        pokemon.altShiny = False
                    if 'shadow' in pokemon_json:
                        if pokemon_json['shadow']:
                            pokemon.shadow = pokemon_json['shadow']
                        if pokemon.shadow:
                            pokemon.setSpritePath()
                    if 'form' in pokemon_json:
                        pokemon.setForm(pokemon_json['form'])
                    self.pokemon_rewards.append(pokemon)

            if 'item_rewards' in json:
                for item_json in json['item_rewards']:
                    self.item_rewards[item_json['name']] = item_json['amount']

            if self.task == 'catch_specific_pokemon':
                task_list = json['list']
                for pair in task_list:
                    pokemon = pair['pokemon']
                    quantity = pair['quantity']
                    self.catch_specific_pokemon[pokemon] = quantity
                    self.catch_specific_pokemon_original[pokemon] = quantity
            elif self.task == 'catch_level_pokemon':
                task_list = json['list']
                for pair in task_list:
                    level = pair['level']
                    quantity = pair['quantity']
                    self.catch_level_pokemon[level] = quantity
                    self.catch_level_pokemon_original[level] = quantity
            elif self.task == 'defeat_specific_pokemon':
                task_list = json['list']
                for pair in task_list:
                    pokemon = pair['pokemon']
                    quantity = pair['quantity']
                    self.defeat_specific_pokemon[pokemon] = quantity
                    self.defeat_specific_pokemon_original[pokemon] = quantity
            elif self.task == "pokemon_caught":
                self.pokemon_caught = int(json['quantity'])
                self.pokemon_caught_original = int(json['quantity'])
            elif self.task == "pokemon_defeated":
                self.pokemon_defeated = int(json['quantity'])
                self.pokemon_defeated_original = int(json['quantity'])
            elif self.task == "trainers_defeated":
                self.trainers_defeated = int(json['quantity'])
                self.trainers_defeated_original = int(json['quantity'])
            elif self.task == "raids_defeated":
                self.raids_defeated = int(json['quantity'])
                self.raids_defeated_original = int(json['quantity'])
            elif self.task == "defeat_specific_trainer":
                task_list = json['list']
                for trainer_name in task_list:
                    self.defeat_specific_trainer.append(trainer_name)
                    self.defeat_specific_trainer_original.append(trainer_name)
            self.started = True
        else:
            if 'started' in json:
                self.started = json['started']
            if 'complete' in json:
                self.complete = json['complete']

            if 'pokemon_caught' in json:
                self.pokemon_caught = json['pokemon_caught']
            if 'pokemon_caught_original' in json:
                self.pokemon_caught_original = json['pokemon_caught_original']

            if 'pokemon_defeated' in json:
                self.pokemon_defeated = json['pokemon_defeated']
            if 'pokemon_defeated_original' in json:
                self.pokemon_defeated_original = json['pokemon_defeated_original']

            if 'trainers_defeated' in json:
                self.trainers_defeated = json['trainers_defeated']
            if 'trainers_defeated_original' in json:
                self.trainers_defeated_original = json['trainers_defeated_original']

            if 'raids_defeated' in json:
                self.raids_defeated = json['raids_defeated']
            if 'raids_defeated_original' in json:
                self.raids_defeated_original = json['raids_defeated_original']

            if 'pokemon_rewards' in json:
                for pokemon_json in json['pokemon_rewards']:
                    pokemon = Pokemon(data, pokemon_json['name'], pokemon_json['level'])
                    pokemon.fromJSON(pokemon_json)
                    self.pokemon_rewards.append(pokemon)

            if 'item_rewards_names' in json and 'item_rewards_amounts' in json:
                for x in range(0, len(json['item_rewards_names'])):
                    self.item_rewards[json['item_rewards_names'][x]] = json['item_rewards_amounts'][x]

            if 'defeat_specific_trainer' in json:
                for trainer_name in json['defeat_specific_trainer']:
                    self.defeat_specific_trainer.append(trainer_name)
            if 'defeat_specific_trainer_original' in json:
                for trainer_name in json['defeat_specific_trainer_original']:
                    self.defeat_specific_trainer_original.append(trainer_name)

            if 'defeat_specific_pokemon_names' in json and 'defeat_specific_pokemon_amounts' in json:
                for x in range(0, len(json['defeat_specific_pokemon_names'])):
                    self.defeat_specific_pokemon[json['defeat_specific_pokemon_names'][x]] = \
                    json['defeat_specific_pokemon_amounts'][x]
            if 'defeat_specific_pokemon_original_names' in json and 'defeat_specific_pokemon_original_amounts' in json:
                for x in range(0, len(json['defeat_specific_pokemon_original_names'])):
                    self.defeat_specific_pokemon_original[json['defeat_specific_pokemon_original_names'][x]] = \
                    json['defeat_specific_pokemon_original_amounts'][x]

            if 'catch_specific_pokemon_names' in json and 'catch_specific_pokemon_amounts' in json:
                for x in range(0, len(json['catch_specific_pokemon_names'])):
                    self.catch_specific_pokemon[json['catch_specific_pokemon_names'][x]] = json['catch_specific_pokemon_amounts'][
                        x]
            if 'catch_specific_pokemon_original_names' in json and 'catch_specific_pokemon_original_amounts' in json:
                for x in range(0, len(json['catch_specific_pokemon_original_names'])):
                    self.catch_specific_pokemon_original[json['catch_specific_pokemon_original_names'][x]] = \
                    json['catch_specific_pokemon_original_amounts'][x]

            if 'catch_level_pokemon_names' in json and 'catch_level_pokemon_amounts' in json:
                for x in range(0, len(json['catch_level_pokemon_names'])):
                    self.catch_level_pokemon[json['catch_level_pokemon_names'][x]] = json['catch_level_pokemon_amounts'][x]
            if 'catch_level_pokemon_original_names' in json and 'catch_level_pokemon_original_amounts' in json:
                for x in range(0, len(json['catch_level_pokemon_original_names'])):
                    self.catch_level_pokemon_original[json['catch_level_pokemon_original_names'][x]] = \
                    json['catch_level_pokemon_original_amounts'][x]


class QuestReadEmbed(disnake.embeds.Embed):
    def __init__(self, bot, user, trainer, quest, page_offset=0):
        super().__init__(title=quest.title, description='\u200b')
        self.user = user
        self.bot = bot
        self.trainer = trainer
        self.quest = quest
        self.page_offset = page_offset
        self.init_footer()
        self.init_thumbnail()
        self.init_fields()
        self.color = disnake.Color.green()

    def init_footer(self):
        self.set_footer(
            text=f"Quest for {self.user}",
            icon_url=self.user.display_avatar,
        )

    def init_thumbnail(self):
        self.set_thumbnail(url="https://i.imgur.com/DjqTo5u.png")

    def init_fields(self):
        self.add_field(
            name="Task: ",
            value='・ ' + self.quest.get_task_string() + '\n'
        )
        if self.quest.location_requirement:
            self.add_field(
                name="\nLocation Requirement: ",
                value='・ ' + self.quest.location_requirement + '\n',
                inline=False
            )
        self.add_field(
            name="\nObjectives:",
            value=self.quest.get_objective_string()[:800]
            + "\n",
            inline=False
        )

        self.add_field(
            name="\nRewards",
            value=self.quest.get_rewards_string()[:800]
                  + "\n----------------------------------------",
            inline=False
        )


class QuestReadView(disnake.ui.View):
    def __init__(self, bot, user, trainer, quest, page_offset=0):
        super().__init__()
        self.trainer = trainer
        self.quest = quest
        self.user = user
        self.page_offset = page_offset
        self.bot = bot
        self.update_buttons()

    def update_buttons(self):
        if self.quest.complete:
            self.children[0].disabled = False
            self.children[1].disabled = True
        else:
            self.children[0].disabled = True
            self.children[1].disabled = False
        if not self.quest.can_abandon:
            self.children[1].disabled = True

    @disnake.ui.button(label="Claim Rewards", style=disnake.ButtonStyle.green, emoji="⭐")
    async def claim_button_press(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        self.quest.redeem_rewards(self.trainer)
        self.trainer.questList.remove(self.quest)
        self.page_offset = 0
        embed = QuestListEmbed(self.bot, self.user, self.trainer, self.page_offset)
        view = QuestListView(self.bot, self.user, self.trainer, self.page_offset)
        await interaction.response.edit_message(embed=embed, view=view)
        rewards_string = self.quest.get_rewards_string()
        embed = disnake.Embed(title="Rewards Received:", description=rewards_string)
        embed.set_footer(
            text=f"Quest Rewards for {self.user}",
            icon_url=self.user.display_avatar,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label="Abandon Quest", style=disnake.ButtonStyle.red, emoji="❌")
    async def abandon_quest_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        embed = ConfirmDeleteEmbed(self.user, self.quest)
        view = ConfirmDeleteView(self.bot, self.user, self.trainer, self.quest, self.page_offset)
        await interaction.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="↩️")
    async def back_button_press(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        embed = QuestListEmbed(self.bot, self.user, self.trainer, self.page_offset)
        view = QuestListView(self.bot, self.user, self.trainer, self.page_offset)
        await interaction.response.edit_message(embed=embed, view=view)


class QuestListEmbed(disnake.embeds.Embed):
    def __init__(self, bot, user, trainer,  page_offset=0):
        super().__init__(
            title="PokéNav Quest List (pg." + str(page_offset + 1) + ")",
            description=(
                ":exclamation:・Unclaimed Quest Rewards: "
                + str(trainer.num_quests_completed())
                + "\n-------------------------------------"
            ),
        )
        self.bot = bot
        self.trainer = trainer
        self.user = user
        self.init_footer()
        self.init_thumbnail()
        self.page_offset = page_offset
        self.color = disnake.Color.green()
        self.init_fields()

    def init_fields(self):
        emoji_list = [":one:", ":two:", ":three:", ":four:", ":five:"]
        for x in range(5):
            index = x + self.page_offset * 5
            if index < len(self.trainer.questList):
                quest = self.trainer.questList[index]
                quest_complete = ""
                if quest.complete:
                    quest_complete = " ❗"
                title_string = quest.title
                value_string = "*Task*: " + quest.get_task_string() + ''
                if quest.location_requirement:
                    value_string += "\n*Location*: " + quest.location_requirement
                value_string += "\n*(Click the numbered button below to view quest details)*"
                value_string += "\n-------------------------------------"
                self.add_field(
                    name=emoji_list[x] + " " + title_string + quest_complete,
                    value=value_string,
                    inline=False
                )
            else:
                self.add_field(
                    name=emoji_list[x]
                    + " - Empty quest slot"
                    + "\n\n----------------------",
                    value="\u200b",
                    inline=False,
                )

    def init_footer(self):
        self.set_footer(
            text=f"Quest List for {self.user}",
            icon_url=self.user.display_avatar,
        )

    def init_thumbnail(self):
        self.set_thumbnail(url="https://i.imgur.com/DjqTo5u.png")


class QuestListView(disnake.ui.View):
    def __init__(self, bot, user, trainer, page_offset):
        super().__init__()
        self.user = user
        self.trainer = trainer
        self.page_offset = page_offset
        self.bot = bot
        self.max_pages = math.ceil(len(self.trainer.questList) / 5)
        self.update_buttons()

    def update_buttons(self):
        for x in range(5):
            index = x + self.page_offset * 5
            if index < len(self.trainer.questList):
                self.children[x].disabled = False
            else:
                self.children[x].disabled = True
        if len(self.trainer.questList) <= 5:
            self.children[5].disabled = True
            self.children[6].disabled = True
        else:
            self.children[5].disabled = False
            self.children[6].disabled = False
        # if self.trainer.ready_for_daily_quest():
        #     self.children[7].disabled = False
        # else:
        #     self.children[7].disabled = True

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="1️⃣")
    async def one_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.view_quest(1, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="2️⃣")
    async def two_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.view_quest(2, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="3️⃣")
    async def three_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.view_quest(3, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="4️⃣")
    async def four_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.view_quest(4, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="5️⃣")
    async def five_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.view_quest(5, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="⬅️")
    async def left_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        self.page_offset -= 1
        if self.page_offset < 0:
            self.page_offset = self.max_pages - 1
        embed = QuestListEmbed(self.bot, self.user, self.trainer, self.page_offset)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="➡️")
    async def right_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        self.page_offset += 1
        if self.page_offset > self.max_pages - 1:
            self.page_offset = 0
        embed = QuestListEmbed(self.bot, self.user, self.trainer, self.page_offset)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    # @disnake.ui.button(label="Claim Daily Quest", style=disnake.ButtonStyle.green)
    # async def daily_quest_button(
    #         self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    # ):
    #     if not await verify_author(interaction, self.user):
    #         return
    #     if self.trainer.ready_for_daily_quest():
    #         self.trainer.claim_daily_quest()
    #     embed = QuestListEmbed(self.bot, self.user, self.trainer, self.page_offset)
    #     self.update_buttons()
    #     await interaction.response.edit_message(embed=embed, view=self)

    async def view_quest(self, button_number, interaction):
        if not await verify_author(interaction, self.user):
            return
        index = button_number - 1 + self.page_offset * 5
        quest = self.trainer.questList[index]
        embed = QuestReadEmbed(self.bot, self.user, self.trainer, quest, self.page_offset)
        view = QuestReadView(self.bot, self.user, self.trainer, quest, self.page_offset)
        await interaction.response.edit_message(embed=embed, view=view)


class ConfirmDeleteEmbed(disnake.embeds.Embed):
    def __init__(self, author, quest):
        super().__init__(title="WARNING: This will PERMANENTLY delete this quest. You cannot get it back.", description="__Title of Quest for Deletion:__\n`" + quest.title + "`\n\nPress `DELETE` below to permanently delete this quest.\nPress `WAIT GO BACK!` to cancel.")
        self.user = author
        self.init_footer()
        self.init_thumbnail()
        self.color = disnake.Color.red()

    def init_footer(self):
        self.set_footer(
            text=f"Quest Deletion for {self.user}",
            icon_url=self.user.display_avatar,
        )

    def init_thumbnail(self):
        self.set_thumbnail(url="https://i.imgur.com/DjqTo5u.png")


class ConfirmDeleteView(disnake.ui.View):
    def __init__(self, bot, author, trainer, quest, page_offset=0):
        super().__init__()
        self.bot = bot
        self.user = author
        self.trainer = trainer
        self.quest = quest
        self.page_offset = page_offset

    @disnake.ui.button(label="DELETE", style=disnake.ButtonStyle.red)
    async def option_yes(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if not await verify_author(interaction, self.user):
            return
        self.trainer.questList.remove(self.quest)
        self.page_offset = 0
        embed = QuestListEmbed(self.bot, self.user, self.trainer, self.page_offset)
        view = QuestListView(self.bot, self.user, self.trainer, self.page_offset)
        await interaction.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(label="WAIT GO BACK!", style=disnake.ButtonStyle.green)
    async def option_no(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        embed = QuestReadEmbed(self.bot, self.user, self.trainer, self.quest, self.page_offset)
        view = QuestReadView(self.bot, self.user, self.trainer, self.quest, self.page_offset)
        await interaction.response.edit_message(embed=embed, view=view)


async def verify_author(interaction, user):
    if interaction.author != user:
        await interaction.response.send_message(
            "Sorry this quest inventory is for: "
            + user.name
            + "\nPlease request your own quest inventory with `/quests`!",
            ephemeral=True,
        )
        return False
    return True