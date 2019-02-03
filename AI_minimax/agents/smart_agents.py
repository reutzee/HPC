from env import *
from agent import Agent
from game_tree import GameTree, infinity, minus_infinity, Node
from ping_pong_game_tree import PingPongGameTree

class SmartAgent(Agent):
    def __init__(self, world, name=None, init_vertex=1):
        super(SmartAgent, self).__init__(world=world, name=name, init_vertex=init_vertex)
        self.world = world






class GameTreeAgent(SmartAgent):
    def __init__(self, world, name, init_vertex=1, choice='MAX'):
        super(GameTreeAgent, self).__init__(world=world, name=name, init_vertex=init_vertex)
        self.choice = choice

    # get the next move according to the MINIMAX value
    def get_move(self, node):
        minimax_value = node.get_minimax_value()
        for child in node.children:
            if child.get_minimax_value() == minimax_value:
                return child.action

    # return an action to be made, and the RESULTING Node (which includes the resulting state)
    def get_move_new_tree(self, state, visited, mode, world, cutoff_depth):

        tree = PingPongGameTree(init_state=state, visited=visited, choice=self.choice, mode=mode,
                                world=world, cutoff_depth=cutoff_depth, agent=self)
        return tree.result_node

