import enum
import random


class SlotOptions(enum.Enum):
    red_7 = 'red_7'
    blue_7 = 'blue_7'
    bolt = 'bolt'
    lotad = 'lotad'
    cherry = 'cherry'
    replay = 'replay'
    azurill = 'azurill'


class Slots(object):
    gif = 'https://i.imgur.com/Ti6TJaD.gif'
    payouts = { # does not include 2 cherries or 1 cherry or triple replay
        'red_7,red_7,red_7': 300,
        'blue_7,blue_7,blue_7': 300,
        'blue_7,blue_7,red_7': 90,
        'blue_7,red_7,blue_7': 90,
        'blue_7,red_7,red_7': 90,
        'red_7,red_7,blue_7': 90,
        'red_7,blue_7,red_7': 90,
        'red_7,blue_7,blue_7': 90,
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
        rows = [center_row, top_row, bottom_row, diagonal_bottom_right, diagonal_top_left]
        for row in rows:
            if row in self.payouts.keys():
                payout += self.payouts[row]
            if 'cherry,cherry' in row:
                payout += 4
            elif 'cherry' in row:
                payout += 2
            if 'replay,replay,replay' in row:
                replay = True
        return payout, replay
