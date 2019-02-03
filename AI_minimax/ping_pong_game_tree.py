from env import Shelter, House
import math
from graph import Graph



def infinity():
    return float('inf')

def minus_infinity():
    return float('-inf')

class PingPongGameTree(Graph):
    def __init__(self, init_state, world, mode, cutoff_depth, choice, visited, agent):
        self.agent = agent
        self.choice = choice        # MAX or MIN
        self.mode = mode
        self.cutoff_depth = cutoff_depth
        self.root = Node(parent=None, state=init_state, choice=choice)  # initial node
        self.world = world
        # houses visited until creation of this tree
        self.visited_houses = visited

        super(PingPongGameTree, self).__init__(self.root)
        if mode == 'adversarial':
            self.result_node = self.alpha_beta_minimax(node=self.root)
        else:
            self.result_node = self.maximax(node=self.root)


    # in case of a utility VECTOR, MAX's value is the first, MIN's value is the second.
    def index_for_choice(self, choice):
        if choice == 'MAX':
            return 0
        return 1

    # return the utility value according to task - Adversarial, semi-coop, coop
    def utility_value(self, utility, choice='MAX'):
        # get the index of the playing agent
        # print('utility is {}'.format(utility))
        if self.mode == 'adversarial' or isinstance(utility, int) or isinstance(utility, float):
            return utility
        elif self.mode == 'semi-coop':
            return utility[self.index_for_choice(choice)]
        else: # if fully coop mode!
            return sum(utility)

    # -------------------task1------------------------
    #           normal alpha beta algorithm
    # alpha beta pruning
    def alpha_beta_minimax(self, node):
        if node.choice == 'MAX':
            value = self.max_value(node, minus_infinity(), infinity())
        else: # if node.choice == 'MIN'
            value = self.min_value(node, minus_infinity(), infinity())
        node.set_minimax_value(value)
        for child in node.children:
            if child.get_minimax_value() == value:
                return child    # return the child node

    # for MAX nodes
    def max_value(self, node, a, b):
        value = minus_infinity()
        if self.cutoff_test(node):
            value = self.utility(node)
        else:
            for child in self.expand(node):
                value = max(value, self.min_value(child, a, b))
                if value >= b:
                    node.set_minimax_value(value)
                    return value
                a = max(a, value, 0)
        node.set_minimax_value(value)
        return value

    # for MIN nodes
    def min_value(self, node, a, b):
        value = infinity()
        if self.cutoff_test(node):
            value = self.utility(node)
        else:
            for child in self.expand(node):
                value = min(value, self.max_value(child, a, b))
                if value <= a:
                    node.set_minimax_value(value)
                    return value
                b = min(b, value)
        node.set_minimax_value(value)
        return value

    # -----------------------------------------------
    # -------------------task2------------------------
    #       maximize OWN value or SUM (disregard adversary)
    def maximax(self, node):

        value = self.maximax_max_value(node)

        node.set_minimax_value(value)
        for child in node.children:
            if child.get_minimax_value() == value:
                return child # return the child node
    # for MAX nodes
    def maximax_max_value(self, node):
        value = minus_infinity()
        # value = node.get_minimax_value()
        if self.cutoff_test(node):
            value = self.utility(node)
        else:
            successors = self.expand(node)
            for child in successors:
                value = self.max_vector(value, self.maximax_max_value(child), choice=node.choice)
        node.set_minimax_value(value)
        return value

    # return the maximal vector according to agent index (0 or 1)
    def max_vector(self, utility1, utility2, choice):
        value1 = self.utility_value(utility1, choice=choice)
        value2 = self.utility_value(utility2, choice=choice)
        if value1 >= value2:
            return utility1
        return utility2

    def cutoff_test(self, node):
        if node.get_depth() == self.cutoff_depth:
            node.set_cutoff_node()
            return True
        if self.terminal_test(node):
            node.set_terminal()
            return True


    # terminal - goal state - saved all people OR time ends up
    def terminal_test(self, node):
        return node.get_time() >= self.world.get_deadline()

    # returns the current agent playing opponent's name
    def my_opponent(self, node):
        return [agent for agent in node.get_state().keys() if (agent != 'time') and agent != self.agent.name][0]

    # get the utility - only for terminal states or cutoff
    def utility(self, node):
        # list (pair) of playing agent names
        opponent = self.my_opponent(node)
        if self.choice == 'MAX':
            max_score, min_score = node.get_people_saved(agent=self.agent.name), node.get_people_saved(agent=opponent)
        else:
            max_score, min_score = node.get_people_saved(agent=opponent), node.get_people_saved(agent=self.agent.name)

        if self.mode == 'adversarial':
            utility = max_score - min_score

        elif self.mode == 'semi-coop':
            utility = (max_score, min_score)
        else: # full-coop
            utility = max_score + min_score


        return utility


    # return set of Nodes to expand node
    def expand(self, node):
        pairs = self.successor(node)
        successors_nodes = []
        next_choice = 'MAX' if node.choice == 'MIN' else 'MIN'
        for action, result in pairs:
            # path_cost [s] = path_cost[s] + step_cost(node, action, s) = result.time (already calc it)
            # as a result - just assign state of the new node to be the result

            child = Node(parent=node, action=action, state=result, choice=next_choice, depth=node.get_depth() + 1)
            # add the new node to s children
            node.add_child(child)
            successors_nodes.append(child)
        return successors_nodes

    # Successor function for a state and observation (the world in our case)
    def successor(self, node):

        agent_name = self.agent.name if self.choice == node.choice else self.my_opponent(node)
        position = node.get_position(agent=agent_name)
        neighbours = self.world.get_adjacent_to(position)    # neighbours
        pairs = []
        # add a NOP option
        nop_result = node.get_state().copy()
        nop_result['time'] += 1
        pairs.append(('NOP', nop_result))
        for v in neighbours:
            people_in_car = node.get_people_in_car(agent=agent_name)
            new_people_in_car = people_in_car
            new_people_saved = node.get_people_saved(agent=agent_name)
            new_time = node.get_time() + self.world.calculate_price(position, v, people_in_car)
            # if v is House Vertex -> pick up
            if self.world.is_house(v) and not self.house_visited(v, node):
                new_people_in_car += self.world.get_vertex_for_tag(v).people

            # if v is Shelter Vertex -> drop off all of them
            elif self.world.is_shelter(v) and new_time <= self.world.get_deadline():
                new_people_in_car = 0
                new_people_saved += people_in_car
            # creating [action, result]
            action = 'T{}'.format(str(v))
            result_agent = {'position': v,
                            'people_in_car': new_people_in_car,
                            'people_saved': new_people_saved}
            result = node.get_state().copy()
            result[agent_name] = result_agent
            result['time'] = new_time

            pairs.append((action, result))

        return pairs

    # time it takes to traverse on 'edge'
    def calculate_price(self, world, v1, v2, p):
        edge = world.get_edge(v1, v2)
        w = edge.weight
        k = world.get_slow_down()
        return w*(1+k*p)

    def house_visited(self, house, node):
        visited = []
        current = node
        while current is not None:
            visited.append(current.get_position(agent=self.agent.name))
            visited.append(current.get_position(agent=self.my_opponent(node)))
            current = current.parent
        return house in visited + self.visited_houses



# tag generator
def tag_gen():
    i = 1
    while True:
        yield i
        i += 1


gen = tag_gen()

#   A       AGENT1
# B   C     AGENT2

class Node(Graph.Vertex):
    def __init__(self, parent, state, choice='MAX', action='NOP', depth=0):

        self.choice = choice
        self._minimax_value = float('-inf')
        self.action = action
        self.children = []
        self.parent = parent
        self.depth = depth
        self.state = state.copy()
        self.type = 'INNER_NODE'
        super(Node, self).__init__(gen.next())

    def get_minimax_value(self):
        return self._minimax_value

    def set_minimax_value(self, value):
        self._minimax_value = value

    def get_state(self, agent=None):
        if agent is None:
            return self.state
        return self.state[agent]

    # depth in game tree
    def get_depth(self):
        return self.depth

    def add_child(self, node_to_add):
        self.children.append(node_to_add)

    def get_position(self, agent):
        return self.state[agent]['position']


    def get_people_saved(self, agent):

        return self.state[agent]['people_saved']

    def add_people_saved(self, agent, to_add):
        self.state[agent]['people_saved'] += to_add

    def get_people_in_car(self,agent):
        return self.state[agent]['people_in_car']

    def get_time(self):
        return self.state['time']

    def set_terminal(self):
        self.type = 'TERMINAL'

    def set_cutoff_node(self):
        self.type = 'CUTOFF'









