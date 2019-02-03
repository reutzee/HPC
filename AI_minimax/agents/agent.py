
from abc import ABCMeta


# A Simple Generic Agent
class Agent:
    __metaclass__ = ABCMeta

    def __init__(self, world, name='Agent', init_vertex=1):
        self.name = name
        self.observation = world                      # the world
        self.vertex = init_vertex
        self._people_in_car = 0                 # people this agent carries right now
        self._total_evacuated = 0
        self._actions = []           # actions done by this agents

    # get the actions list
    def get_actions(self):
        return self._actions

    def get_people_in_car(self):
            return self._people_in_car

    def get_evacuated(self):
        return self._total_evacuated

    # pick people up from a house
    def pick_up(self):
        self._people_in_car += self.observation.pick_people_up(self.vertex)

    # add an action for this agent
    def add_action(self, action):
        self._actions.append(action)

    # drop people off at shelter
    def drop_off(self):
        self._total_evacuated += self._people_in_car
        self._people_in_car = 0

    # print the state
    def print_agent_status(self):
        print("name: {0}\nin car: {1}\naction: {2}\nevac: {3}\nvertex: {4} ".format(self.name,
                                                                                    self.get_people_in_car(),
                                                                                    self.get_actions(),
                                                                    self.get_evacuated(),
                                                                                    self.vertex))






