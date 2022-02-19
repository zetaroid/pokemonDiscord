import disnake


class ConfirmView(disnake.ui.View):
    def __init__(self, author, text_confirm, text_nevermind):
        super().__init__()
        self.author = author
        self.confirmed = False
        self.children[0].label = text_confirm
        self.children[1].label = text_nevermind

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