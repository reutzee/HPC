from abc import ABCMeta

# A Simple Generic Agent
class Agent:
    __metaclass__ = ABCMeta

    def __init__(self, world, name='Agent', init_vertex=1):
        self.name = name
        self.observation = world                      # the world
        self.vertex = init_vertex
        self._actions = []

    # get the actions list
    def get_actions(self):
        return self._actions



class PlanningAgent(Agent):
    def __init__(self, world, belief_space, utilities, init_state, blockage, name=None, init_vertex=1):
        super(PlanningAgent, self).__init__(world=world, name=name, init_vertex=init_vertex)
        self.belief_space = belief_space
        self.utilities = utilities
        self.state = init_state
        self.blockage = blockage



    # The agent's only actions are traveling between vertices.
    def do(self):
        states = self.belief_space.states
        successors = self.state.successors.values()
        successors = [item for sublist in successors for item in sublist]

        if len(successors) == 0:
            return self.state
        filtered_successors = filter(lambda s: self.consistent_state(s, self.blockage), successors)

        max = -1
        max_succ = successors[0]
        for succ in filtered_successors:
            utility = self.utilities[succ]#states.index(succ)]
            if utility > max:
                max = utility
                max_succ = succ
        self.state = max_succ
        return max_succ







    def consistent_state (self, belief_state, blockage_instance):
        state_blocked = belief_state.blocked_edges
        for edge_num in state_blocked:
            if blockage_instance[edge_num] != state_blocked[edge_num]:
                return False
        return True

