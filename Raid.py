import logging
import random
import uuid
from datetime import datetime
import discord

class Raid(object):

    def __init__(self, data, battleTower):
        self.data = data
        self.battleTower = battleTower
        self.raidBoss = None
        self.isRaidSpecial = False
        self.raidEnded = False
        self.inRaidList = []
        self.raidChannelList = []
        self.raidStartTime = None
        self.identifier = uuid.uuid4()

    async def startRaid(self, override=False, overrideNumRecentUsers=None):
        if override:
            numRecentUsers, channelList = self.data.getNumOfRecentUsersForRaid()
            if overrideNumRecentUsers:
                numRecentUsers = overrideNumRecentUsers
            else:
                numRecentUsers = 1
        else:
            numRecentUsers, channelList = self.data.getNumOfRecentUsersForRaid()
        self.raidChannelList = channelList
        if numRecentUsers > 1 or override:
            logging.debug("New raid starting.")
            self.raidEnded = False
            now = datetime.today()
            self.data.lastRaidTime = now
            self.raidStartTime = now
            self.inRaidList.clear()
            pokemon = self.generateRaidBoss(numRecentUsers)
            self.raidBoss = pokemon
            files, embed = self.createRaidInviteEmbed()
            await self.sendToRaidChannel(files, embed)
            for channel_id in channelList:
                try:
                    channel = self.data.getChannelById(channel_id)
                    files, embed = self.createRaidInviteEmbed()
                    await channel.send(files=files, embed=embed)
                except:
                    pass
            return True
        logging.debug("Raid not started since numRecentUsers < 2.")
        return False

    async def sendToRaidChannel(self, files, embed):
        try:
            channel = self.data.getChannelById(841925516298420244)
            await channel.send(files=files, embed=embed)
        except:
            pass

    def generateRaidBoss(self, numRecentUsers, specified=None):
        pokemon = None
        if not specified:
            isSpecial = False
            specialInt = random.randint(1, 10)
            if specialInt < 3:
                isSpecial = True
            self.isRaidSpecial = isSpecial
            pokemon = self.battleTower.getPokemon(10, isSpecial)
            pokemon.hp = pokemon.hp * numRecentUsers * 4
            # pokemon.hp = 1
            pokemon.currentHP = pokemon.hp
        return pokemon

    async def hasRaidExpired(self):
        if self.raidBoss:
            if self.raidStartTime:
                elapsedTime = datetime.today() - self.raidStartTime
                elapsedHours = elapsedTime.total_seconds() / 3600
                if elapsedHours > 3:
                    await self.endRaid(False)
                    return True
        return False

    async def endRaid(self, success):
        logging.debug("endRaid called")
        if self.raidEnded:
            logging.debug("endRaid - returning due to raid already ended")
            return
        rewardDict = {}
        if self.raidBoss and (self.raidBoss.currentHP <= 0 or not success):
            self.data.raid = None
            self.raidEnded = True
            logging.debug("Raid has ended with success = " + str(success) + ".")
            if success:
                rewardDict = self.generateRaidRewards()
                for user in self.inRaidList:
                    for item, amount in rewardDict.items():
                        # if item == "BP":
                        #     if not user.checkFlag('elite4'):
                        #         continue
                        user.addItem(item, amount)
            files, embed = self.createEndRaidEmbed(success, rewardDict)
            await self.sendToRaidChannel(files, embed)
            for channel_id in self.raidChannelList:
                channel = self.data.getChannelById(channel_id)
                files, embed = self.createEndRaidEmbed(success, rewardDict)
                await channel.send(files=files, embed=embed)
        logging.debug("endRaid - function ended")

    def generateRaidRewards(self):
        rewardDict = {}
        if self.isRaidSpecial:
            rewardDict['BP'] = 7
            masterBallRoll = random.randint(1, 30)
            if masterBallRoll == 1:
                rewardDict['Masterball'] = 1
            shinyCharmRoll = random.randint(1, 5) - 2
        else:
            rewardDict['BP'] = 3
            shinyCharmRoll = random.randint(1, 5)

        if self.raidBoss.shiny:
            shinyCharmRoll = 1
        if shinyCharmRoll <= 1:
            rewardDict['Shiny Charm Fragment'] = 1

        moneyRoll = random.randint(1, 3)
        if moneyRoll == 1:
            moneyRoll = random.randint(3000, 10000)
        elif moneyRoll == 2:
            moneyRoll = random.randint(5000, 12000)
        elif moneyRoll == 3:
            moneyRoll = random.randint(10000, 20000)
        rewardDict["money"] = moneyRoll

        ultraBallRoll = random.randint(0, 3)
        if ultraBallRoll > 0:
            rewardDict['Ultraball'] = ultraBallRoll
        greatBallRoll = random.randint(0, 5)
        if greatBallRoll > 0:
            rewardDict['Greatball'] = greatBallRoll
        pokeBallRoll = random.randint(0, 10)
        if pokeBallRoll > 0:
            rewardDict['Pokeball'] = pokeBallRoll

        return rewardDict

    def createRaidInviteEmbed(self):
        files = []
        pokemon = self.raidBoss
        title = ':mega: RAID ALERT! :mega:\n'
        desc = "`" + pokemon.name + "` raid active now! Use `!raid` to join!\nUse `!raidInfo` to get an update on the boss's health."
        movesStr = ''
        for move in pokemon.moves:
            movesStr += (move['names']['en'] + "\n")
        embed = discord.Embed(title=title,
                              description=desc,
                              color=0x00ff00)
        embed.add_field(name='Level:', value=str(pokemon.level))
        embed.add_field(name='Health:', value=str(pokemon.currentHP) + ' / ' + str(pokemon.hp))
        embed.add_field(name='Moves:', value=movesStr)
        file = discord.File(pokemon.getSpritePath(), filename="image.png")
        files.append(file)
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=(
            'Raid will be active for 3 HOURS from the time of this message or until defeated.\nPlease note, only trainers who have beaten the Elite 4 may participate in raids.\nAlso, items are not allowed during raids.'))
        return files, embed

    def createEndRaidEmbed(self, success, rewardDict):
        files = []
        pokemon = self.raidBoss
        title = ':mega: ' + pokemon.name + " raid has ended! :mega:\n"
        if success:
            desc = "`" + pokemon.name + "` raid has ended in `SUCCESS`!\nThe following rewards have been distributed to ALL participants:"
        else:
            desc = "`" + pokemon.name + "` raid has ended in `FAILURE`!\nRaid expired.\nBetter luck next time trainers."
        embed = discord.Embed(title=title,
                              description=desc,
                              color=0x00ff00)
        rewardStr = ''
        for rewardName, rewardAmount in rewardDict.items():
            name = rewardName
            if rewardName == 'money':
                name = 'PokeDollars'
            rewardStr += name + " x " + str(rewardAmount) + "\n"
        if not rewardStr:
            rewardStr = 'None'
        embed.add_field(name='Rewards:', value=rewardStr)
        file = discord.File(pokemon.getSpritePath(), filename="image.png")
        files.append(file)
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=('Thank you for playing!'))
        return files, embed

    def clearRaidList(self):
        self.inRaidList.clear()

    def isUserInRaidList(self, user):
        for raidUser in self.inRaidList:
            if user.identifier == raidUser.identifier:
                return True
        return False