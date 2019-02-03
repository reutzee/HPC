from env import *
from agent import Agent
from search_tree import SearchTree

# A greedy search agent, by h(n) = #unsaved people no matter what

class SmartAgent(Agent):
    def __init__(self, world, name=None, init_vertex=1, init_state=None, bonus_vandal_records=None):
        super(SmartAgent, self).__init__(world=world, name=name, init_vertex=init_vertex)
        self.expands = None
        self.search_tree = None
        self.world = world
        if init_state is None:
            self.init_state = {'position': init_vertex,
                          'full_houses': world.filter_empty_houses(),
                          'people_in_car': 0,
                          'time': 0}
        else:
            self.init_state=init_state
        self.bonus_vandal_records = bonus_vandal_records

    def do(self):
        result = self.search_tree.tree_search(self.world)
        self.expands = self.search_tree.num_expands
        return result


class SmartGreedy(SmartAgent):
    def __init__(self, world, name=None, init_vertex=1, bonus_vandal_records=None):
        super(SmartGreedy, self).__init__(world=world, name=name, init_vertex=init_vertex, bonus_vandal_records=bonus_vandal_records)
        self.search_tree = SearchTree(init_state=self.init_state, strategy='greedy', vandal_records=bonus_vandal_records)


# An agent using A* search, by f(n) = h(n) + g(n) where g(n) - time passed.
class SmartAStar(SmartAgent):
    def __init__(self, world, name=None, init_vertex=1, bonus_vandal_records=None):
        super(SmartAStar, self).__init__(world=world, name=name, init_vertex=init_vertex, bonus_vandal_records=bonus_vandal_records)
        self.search_tree = SearchTree(init_state=self.init_state, strategy='A*', vandal_records=bonus_vandal_records)




class SmartRTA(SmartAgent):
    def __init__(self, world, expand_limit, name=None, init_vertex=1, bonus_vandal_records=None):
        super(SmartRTA, self).__init__(world=world, name=name, init_vertex=init_vertex, bonus_vandal_records=bonus_vandal_records)
        self.search_tree = SearchTree(init_state=self.init_state, strategy='RTA', expand_limit=expand_limit, vandal_records=bonus_vandal_records)
    #
    # def do(self):
    #     return self.search_tree.tree_sear