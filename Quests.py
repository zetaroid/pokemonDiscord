from Pokemon import Pokemon


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

    def start(self):
        self.started = True

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

        if from_event:
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
                    self.catch_level_pokemon[pokemon] = quantity
                    self.catch_level_pokemon_original[pokemon] = quantity
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
                    self.item_rewards[json['defeat_specific_pokemon_names'][x]] = \
                    json['defeat_specific_pokemon_amounts'][x]
            if 'defeat_specific_pokemon_original_names' in json and 'defeat_specific_pokemon_original_amounts' in json:
                for x in range(0, len(json['defeat_specific_pokemon_original_names'])):
                    self.item_rewards[json['defeat_specific_pokemon_original_names'][x]] = \
                    json['defeat_specific_pokemon_original_amounts'][x]

            if 'catch_specific_pokemon_names' in json and 'catch_specific_pokemon_amounts' in json:
                for x in range(0, len(json['catch_specific_pokemon_names'])):
                    self.item_rewards[json['catch_specific_pokemon_names'][x]] = json['catch_specific_pokemon_amounts'][
                        x]
            if 'catch_specific_pokemon_original_names' in json and 'catch_specific_pokemon_original_amounts' in json:
                for x in range(0, len(json['catch_specific_pokemon_original_names'])):
                    self.item_rewards[json['catch_specific_pokemon_original_names'][x]] = \
                    json['catch_specific_pokemon_original_amounts'][x]

            if 'catch_level_pokemon_names' in json and 'catch_level_pokemon_amounts' in json:
                for x in range(0, len(json['catch_level_pokemon_names'])):
                    self.item_rewards[json['catch_level_pokemon_names'][x]] = json['catch_level_pokemon_amounts'][x]
            if 'catch_level_pokemon_original_names' in json and 'catch_level_pokemon_original_amounts' in json:
                for x in range(0, len(json['catch_level_pokemon_original_names'])):
                    self.item_rewards[json['catch_level_pokemon_original_names'][x]] = \
                    json['catch_level_pokemon_original_amounts'][x]
