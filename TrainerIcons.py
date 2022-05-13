import math
import disnake


class TrainerIcon(object):

    def __init__(self, name, filename, price, category, subcategory):
        self.name = name
        self.filename = filename
        self.price = price
        self.category = category
        self.subcategory = subcategory

    def __str__(self):
        prtString = ''
        prtString += self.name + '\n'
        prtString += self.filename + '\n'
        prtString += str(self.price) + '\n'
        prtString += self.category + '\n'
        prtString += self.subcategory + '\n'
        return prtString


class TrainerIconPurchaseEmbed(disnake.embeds.Embed):
    def __init__(self, data, user, trainer, category=None, subcategory=None, page_offset=0):
        if category and subcategory:
            description = category + ' | ' + subcategory
        elif category:
            description = category
        else:
            description = "Choose category below."
        title = "Trainer Icon Purchase (pg." + str(page_offset + 1) + ")"
        super().__init__(
            title=title,
            description=(
                description
                + "\n-------------------------------------"
            ),
        )
        self.data = data
        self.trainer = trainer
        self.user = user
        self.init_footer()
        self.page_offset = page_offset
        self.color = disnake.Color.green()
        label_list, is_icons = getLabelList(data, category, subcategory, self.trainer)
        self.init_fields(label_list)
        self.current_category = category
        self.current_subcategory = subcategory

    def init_fields(self, label_list):
        emoji_list = [":one:", ":two:", ":three:", ":four:", ":five:"]
        value_string = "\u200b"
        for x in range(5):
            index = x + self.page_offset * 5
            if index < len(label_list):
                label = label_list[index]
                title_string = label
                self.add_field(
                    name=emoji_list[x] + " - " + title_string,
                    value=value_string,
                    inline=False
                )
            else:
                self.add_field(
                    name=emoji_list[x]
                    + " - Empty slot",
                    value=value_string,
                    inline=False,
                )

    def init_footer(self):
        self.set_footer(
            text=f"Trainer Icon Shop for {self.user}",
            icon_url=self.user.display_avatar,
        )


class TrainerIconPurchaseView(disnake.ui.View):
    def __init__(self, data, user, trainer, category=None, subcategory=None, page_offset=0):
        super().__init__()
        self.user = user
        self.trainer = trainer
        self.page_offset = page_offset
        self.data = data
        self.category = category
        self.subcategory = subcategory
        self.label_list = []
        self.is_icons = False
        self.max_pages = 0
        self.chosen = ''
        self.reset()

    def reset(self):
        self.label_list, self.is_icons = getLabelList(self.data, self.category, self.subcategory, self.trainer)
        self.max_pages = math.ceil(len(self.label_list) / 5)
        self.chosen = ''
        self.update_buttons()

    def update_buttons(self):
        for x in range(5):
            index = x + self.page_offset * 5
            if index < len(self.label_list):
                self.children[x].disabled = False
            else:
                self.children[x].disabled = True
        if len(self.label_list) <= 5:
            self.children[5].disabled = True
            self.children[6].disabled = True
        else:
            self.children[5].disabled = False
            self.children[6].disabled = False
        if not self.category and not self.subcategory:
            self.children[7].disabled = True
        else:
            self.children[7].disabled = False

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="1️⃣")
    async def one_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.button_press(1, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="2️⃣")
    async def two_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.button_press(2, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="3️⃣")
    async def three_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.button_press(3, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="4️⃣")
    async def four_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.button_press(4, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="5️⃣")
    async def five_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await self.button_press(5, interaction)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="⬅️")
    async def left_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        self.page_offset -= 1
        if self.page_offset < 0:
            self.page_offset = self.max_pages - 1
        embed = TrainerIconPurchaseEmbed(self.data, self.user, self.trainer, self.category, self.subcategory, self.page_offset)
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
        embed = TrainerIconPurchaseEmbed(self.data, self.user, self.trainer, self.category, self.subcategory, self.page_offset)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="\u200b", style=disnake.ButtonStyle.grey, emoji="↩️")
    async def back_button_press(
            self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if not await verify_author(interaction, self.user):
            return
        if self.is_icons and self.subcategory:
            embed = TrainerIconPurchaseEmbed(self.data, self.user, self.trainer, self.category)
            self.subcategory = None

        else:
            embed = TrainerIconPurchaseEmbed(self.data, self.user, self.trainer)
            self.subcategory = None
            self.category = None
        self.page_offset = 0
        self.reset()
        await interaction.response.edit_message(embed=embed, view=self)

    async def button_press(self, button_number, interaction):
        if not await verify_author(interaction, self.user):
            return
        index = button_number - 1 + self.page_offset * 5
        if self.is_icons:
            icon_name = self.label_list[index].split('\n')[0]
            for icon in self.data.iconList:
                if icon_name == icon.name:
                    self.chosen = icon
            if self.chosen:
                await interaction.response.defer()
                self.stop()
        else:
            if self.category:
                self.subcategory = self.label_list[index]
            else:
                self.category = self.label_list[index]
            embed = TrainerIconPurchaseEmbed(self.data, self.user, self.trainer, self.category, self.subcategory,
                                             0)
            self.page_offset = 0
            self.reset()
            await interaction.response.edit_message(embed=embed, view=self)


def getLabelList(data, category, subcategory=None, trainer=None):
    categories = ['Owned', 'General', 'Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar',
                       'Legends Arceus', 'Orre', 'Anime (Pokemon)', 'Anime']
    is_icons = False
    if category and category in data.icon_subcategory.keys():
        label_list = data.icon_subcategory[category]
    else:
        label_list = categories
    if subcategory or len(label_list) == 0:
        icons = data.getAllTrainerIconsInCategory(category, subcategory, trainer)
        label_list = []
        is_icons = True
        for icon in icons:
            label_list.append(icon.name + '\nPrice: ' + str(icon.price) + 'BP')
            label_list.sort()
    return label_list, is_icons


async def verify_author(interaction, user):
    if interaction.author != user:
        await interaction.response.send_message(
            "Sorry this icon purchase is for: "
            + user.name
            + "\nPlease request your own shop with `/shop`!",
            ephemeral=True,
        )
        return False
    return True
