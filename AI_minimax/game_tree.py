from env import Shelter, House
import math
from graph import Graph



def infinity():
    return float('inf')

def minus_infinity():
    return float('-inf')

class GameTree(Graph):
    def __init__(self, init_state, world, agents, mode, cutoff_depth):

        self.mode = mode
        self.cutoff_depth = cutoff_depth
        self.root = Node( parent=None, state=init_state, agent=agents[0])  # initial node
        self.world = world
        self.agents = agents
        self.visited_houses = []

        super(GameTree, self).__init__(self.root)
        if mode == 'adversarial':
            self.alpha_beta_minimax(node=self.root)
        else:
            self.maximax(node=self.root)


    # return the utility value according to task - Adversarial, semi-coop, coop
    def utility_value(self, utility, agent=0):
        # get the index of the playing agent
        if agent is not 0:
            agent = self.agents.index(agent)
        if self.mode == 'adversarial' or isinstance(utility, int) or isinstance(utility, float):
            return utility
        elif self.mode == 'semi-coop':
            return utility[agent]
        else: # if fully coop mode!
            return sum(utility)

    # -------------------task1------------------------
    #           normal alpha beta algorithm
    # alpha beta pruning
    def alpha_beta_minimax(self, node):
        value = self.max_value(node, minus_infinity(), infinity())
        node.set_minimax_value(value)

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
    #       maximize OWN value (disregard adversary)
    def maximax(self, node):
        value = self.maximax_max_value(node)
        node.set_minimax_value(value)

    # for MAX nodes
    def maximax_max_value(self, node):
        value = minus_infinity()
        if self.cutoff_test(node):
            node.terminal = True
            value = self.utility(node)
        else:
            for child in self.expand(node):
                value = self.max_vector(value, self.maximax_max_value(child), agent=node.agent)
        node.set_minimax_value(value)
        return value

    # return the maximal vector according to agent index (0 or 1)
    def max_vector(self, utility1, utility2, agent):
        value1 = self.utility_value(utility1, agent=agent)
        value2 = self.utility_value(utility2, agent=agent)
        if value1 > value2:
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

    # get the utility - only for terminal states
    def utility(self, node):
        # score of agent MAX
        first_score = node.get_people_saved(agent=self.agents[0].name)
        # score of agent MIN
        second_score = node.get_people_saved(agent=self.agents[1].name)
        if self.mode == 'adversarial':
            utility = first_score - second_score
        elif self.mode == 'semi-coop':
            utility = (first_score, second_score)
        else: # full-coop
            utility = first_score + second_score


        return utility





    # isolate the houses out of all vertices of shape : (vertex, [cost, people])
    def isolate_sort_houses(self, vertices, world, visited=None,remove_empty_houses = False):
        def house_filter(house):
            return world.get_vertex_for_tag(house[0]).people > 0 and house[0] not in visited
        isolated = list([key, value] for key, value in vertices.iteritems() if world.is_house(key))
        isolated.sort(key=lambda x: x[1][0])
        if remove_empty_houses and visited is not None:
            isolated = filter(house_filter, isolated)

        return isolated

    # isolate the houses out of all vertices of shape : (vertex, [cost, people])
    def isolate_sort_shelters(self, vertices, world):
        isolated = list([key, value] for key, value in vertices.iteritems() if world.is_shelter(key))
        isolated.sort(key=lambda x: x[1][0])
        return isolated

    def g(self, node):
        return node.get_time()



    # return a list of "visited" vertices for a given node state

    def get_visited_vertices(self, node):
        visited = []
        while node is not None:
            visited.append(node.get_position())
            node = node.parent
        return visited

    # given a node in the search tree, and a "final" node, get the next one for "current"
    def get_next_node_in_path(self, current, last_node):
        current_node = last_node
        while last_node.parent != current:
            current_node = current_node.parent
        return current_node

    # return set of Nodes to expand node
    def expand(self, node):
        pairs = self.successor(node)
        successors_nodes = []
        next_agent = self.agents[(self.agents.index(node.agent) + 1) % len(self.agents)]
        for action, result in pairs:
            # path_cost [s] = path_cost[s] + step_cost(node, action, s) = result.time (already calc it)
            # as a result - just assign state of the new node to be the result

            child = Node(parent=node, action=action, state=result, agent=next_agent, depth=node.get_depth() + 1)
            # add the new node to s children
            node.add_child(child)
            successors_nodes.append(child)
        return successors_nodes

    # Successor function for a state and observation (the world in our case)
    def successor(self, node):
        agent = node.agent
        position = node.get_position(agent=agent.name)
        neighbours = self.world.get_adjacent_to(position)    # neighbours
        pairs = []
        for v in neighbours:
            people_in_car = node.get_people_in_car(agent=agent.name)
            new_people_in_car = people_in_car
            new_people_saved = node.get_people_saved(agent=agent.name)
            new_time = node.get_time() + self.calculate_price(self.world, position, v, people_in_car)
            # if v is House Vertex -> pick up
            if self.world.is_house(v) and not self.house_visited(node, v):
                new_people_in_car += self.world.get_vertex_for_tag(v).people

            # if v is Shelter Vertex -> drop off all of them
            elif self.world.is_shelter(v) and new_time <= self.world.get_deadline():
                new_people_in_car = 0
                new_people_saved += people_in_car
            # creating [action, result]
            action = 'T{}'.format(str(v))
            result_agent = {'position': v,
                      'people_in_car': new_people_in_car,
                      'people_saved' : new_people_saved}
            result = node.get_state().copy()
            result[agent.name] = result_agent
            result['time'] = new_time

            pairs.append((action, result))

        # add a NOP option
        nop_result = node.get_state().copy()
        nop_result['time'] += 1
        pairs.append(('NOP', nop_result))

        return pairs

    # time it takes to traverse on 'edge'
    def calculate_price(self, world, v1, v2, p):
        edge = world.get_edge(v1, v2)
        w = edge.weight
        k = world.get_slow_down()
        return w*(1+k*p)

    def house_visited(self, node, house):
        visited = []
        current = node
        while current is not None:
            for agent in self.agents:
                visited.append(current.get_position(agent=agent.name))
            current = current.parent

        return house in visited


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
    def __init__(self, parent, state, agent, action='NOP', depth=0):

        self.agent = agent
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

    def get_position(self,agent):
        return self.state[agent]['position']


    def get_people_saved(self,agent):
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









