import logging
import random
import uuid
from asyncio import sleep
from datetime import datetime
import disnake as discord

class Raid(object):

    def __init__(self, data, battleTower):
        self.data = data
        self.battleTower = battleTower
        self.raidBoss = None
        self.isRaidSpecial = False
        self.raidStarted = False
        self.raidEnded = False
        self.isTera = False
        self.teraType = None
        self.inRaidList = []
        self.raidChannelList = []
        self.raidStartTime = None
        self.identifier = uuid.uuid4()
        self.alertMessagesList = []

    async def startRaid(self, override=False, overrideNumRecentUsers=None):
        if self.raidStarted:
            logging.debug('raid - startRaid - Not starting raid, raid already started.')
            return False
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
            logging.debug("raid - New raid starting.")
            self.raidStarted = True
            self.raidEnded = False
            now = datetime.today()
            self.data.lastRaidTime = now
            self.raidStartTime = now
            self.inRaidList.clear()
            pokemon = self.generateRaidBoss(numRecentUsers)
            self.raidBoss = pokemon
            files, embed = self.createRaidInviteEmbed()
            logging.debug("raid - sending to raid channel for startRaid")
            await self.sendToRaidChannel(files, embed)
            for channel_id in channelList:
                try:
                    channel = self.data.getChannelById(channel_id)
                    files, embed = self.createRaidInviteEmbed()
                    alertMessage = await channel.send(files=files, embed=embed)
                    # self.addAlertMessage(alertMessage)
                except:
                    pass
                await sleep(0.1)
            return True
        logging.debug("raid - Raid not started since numRecentUsers < 2.")
        return False

    async def sendToRaidChannel(self, files, embed, addMessage=True):
        try:
            logging.debug("raid - sending message to raid channel")
            channel = self.data.getChannelById(841925516298420244)
            role = self.data.getRoleById(805976403140542476, 893340442572259338)
            await channel.send(role.mention)
            message = await channel.send(files=files, embed=embed)
            await message.publish()
            if addMessage:
                logging.debug("raid - adding alert message")
                self.addAlertMessage(message)
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
            teraInt = random.randint(1, 5)
            if teraInt == 1:
                type_list = ['normal', 'fairy', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost', 'steel',
                                          'fire', 'water', 'grass', 'electric', 'psychic', 'ice', 'dragon', 'dark']
                type_index = random.randint(0, len(type_list)-1)
                pokemon.teraType = type_list[type_index].capitalize()
                self.isTera = True
                self.teraType = pokemon.teraType
        return pokemon

    async def hasRaidExpired(self):
        if self.raidBoss:
            if self.raidStartTime:
                elapsedTime = datetime.today() - self.raidStartTime
                elapsedHours = elapsedTime.total_seconds() / 3600
                if elapsedHours > 3 and not self.raidEnded:
                    logging.debug("raid - Raid has expired, ending with failure - " + str(elapsedTime.total_seconds()) + " seconds elapsed since start")
                    await self.endRaid(False)
                    return True
        return False

    async def endRaid(self, success):
        logging.debug("raid - endRaid called")
        rewardDict = {}
        if self.raidBoss and (self.raidBoss.currentHP <= 0 or not success):
            if self.raidEnded:
                logging.debug("raid - endRaid - returning due to raid already ended")
                return
            self.raidEnded = True
            logging.debug("raid - Raid has ended with success = " + str(success) + ".")
            if success:
                rewardDict = self.generateRaidRewards()
                for user in self.inRaidList:
                    user.raidDefeatedEvent()
                    for item, amount in rewardDict.items():
                        # if item == "BP":
                        #     if not user.checkFlag('elite4'):
                        #         continue
                        user.addItem(item, amount)
            files, embed = self.createEndRaidEmbed(success, rewardDict)
            logging.debug("raid - endRaid - sending raid end message to raid channel")
            await self.sendToRaidChannel(files, embed, False)
            logging.debug("raid - endRaid - sending to messages in raidChannelList with len = " + str(len(self.raidChannelList)))
            for channel_id in self.raidChannelList:
                files, embed = self.createEndRaidEmbed(success, rewardDict)
                try:
                    channel = self.data.getChannelById(channel_id)
                    await channel.send(files=files, embed=embed)
                except:
                    pass
                await sleep(0.1)
            # logging.debug("raid - endRaid - setting self.data.raid to None")
            # self.data.raid = None
        logging.debug("raid - endRaid - function ended")

    def generateRaidRewards(self):
        rewardDict = {}
        if self.isRaidSpecial:
            rewardDict['BP'] = 7
            masterBallRoll = random.randint(1, 30)
            if masterBallRoll == 1:
                rewardDict['Master Ball'] = 1
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
            rewardDict['Ultra Ball'] = ultraBallRoll
        greatBallRoll = random.randint(0, 5)
        if greatBallRoll > 0:
            rewardDict['Great Ball'] = greatBallRoll
        pokeBallRoll = random.randint(0, 10)
        if pokeBallRoll > 0:
            rewardDict['Poke Ball'] = pokeBallRoll

        if 'halloween' in self.data.activeEvent.lower():
            rewardDict['Candy'] = 10

        if self.isTera:
            if self.teraType:
                rewardDict[self.teraType.capitalize() + " Tera Shard"] = 1

        return rewardDict

    def createRaidInviteEmbed(self):
        files = []
        pokemon = self.raidBoss
        strikeThrough = ''
        if pokemon.currentHP <= 0:
            strikeThrough = '~~'
        if self.isTera:
            title = strikeThrough + ':mega: TERA RAID ALERT! (Tera Type: ' + self.raidBoss.teraType + ') :mega:' + strikeThrough + '\n'
        else:
            title = strikeThrough + ':mega: RAID ALERT! :mega:' + strikeThrough + '\n'
        desc = strikeThrough + "`" + pokemon.name + "` raid active now! Use `/raid` to join!\nUse `/raid_info` to get an update on the boss's health." + strikeThrough
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

    def removeUserFromRaidList(self, user):
        if self.isUserInRaidList(user):
            self.inRaidList.remove(user)
            return True
        return False

    def isUserInRaidList(self, user):
        for raidUser in self.inRaidList:
            if user.identifier == raidUser.identifier:
                return True
        return False

    def addChannel(self, channel):
        if channel.id not in self.raidChannelList:
            self.raidChannelList.append(channel.id)

    def addAlertMessage(self, msg):
        logging.debug("raid - addAlertMessage() called")
        self.alertMessagesList.append(msg)

    async def updateAlertMessages(self):
        logging.debug("raid - updatingAlertMessages with len = " + str(len(self.alertMessagesList)))
        count = 0
        for message in self.alertMessagesList:
            logging.debug("raid - updatingAlertMessages message num = " + str(count))
            count += 1
            files, embed = self.createRaidInviteEmbed()
            try:
                await message.edit(embed=embed)
            except:
                pass
            await sleep(0.1)
