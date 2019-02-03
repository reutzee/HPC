import argparse
from env import World
from belief import BeliefSpace
from val_iterate import ValueIteration
from itertools import chain, combinations
from itertools import product
from agent import PlanningAgent
import random


class HurricaneEvacuationSimulator(object):
    def __init__(self, graph_file, start_vertex):
        self.graph_file = graph_file
        self.world = World(graph_file=graph_file)
        self.deadline = self.world.get_deadline()
        self.shelter_tag = self.world.get_shelter_tag()
        # create agent
        self.start_vertex = start_vertex
        self.time = 0             # track time of the world
        self.evacuated = 0        # total number of people evacuated
        self.belief_space = self.init_belief_space()

        self.val_iterator = ValueIteration(self.belief_space, self.world)
        self.utilities = self.val_iterator.value_iteration()
        print(self.utilities.values())



    # initialize the belief space for the graph
    def init_belief_space(self):
        bs = BeliefSpace(self.world, init_vertex=int(args.start_vertex))
        bs.create_all_belief_states(self.start_vertex)
        return bs



    # generate all possible blockage combinations
    def all_blockage_instances(self):
        # edge that can be blocked
        maybe_blocked = map(lambda e: e.edge_num, filter(lambda e: e.prob_blockage > 0, self.world.get_edges(one_way=True)))
        blockages = set(product({True, False}, repeat=len(maybe_blocked)))
        return [dict(zip(maybe_blocked, blockage)) for blockage in blockages]

    def random_blockage(self):
        # blockable edges
        blockables = map(lambda e: e.edge_num, filter(lambda e : e.prob_blockage > 0,self.world.get_edges(one_way=True)))
        # NONE at first
        blockage_dict = {key: None for key in blockables}
        for e in blockage_dict:
            prob = self.world.get_edge_for_num(e).prob_blockage
            blockage_dict[e] = self.true_in_prob(prob)

        return blockage_dict

    # return 'True' in probability of 'prob'
    def true_in_prob(self, prob):

        rand = random.random()
        return True if rand <= prob else False


    def run_an_agent(self, times=10000):
        util_acc = 0.0
        init_s = None
        for i in range (times):
            blockage_instance = self.random_blockage()
            init_states = self.belief_space.init_states
            # remove from init state/s
            init_state = filter(lambda d: self.consistent_state(d, blockage_instance), init_states)[0]
            init_s = init_state
            agent = PlanningAgent(world=self.world, belief_space=self.belief_space, utilities=self.utilities, \
                                  init_state=init_state, init_vertex=self.start_vertex, blockage=blockage_instance)
            next_state = agent.state
            while not self.belief_space.goal_state(next_state) and not (len(next_state.successors) == 0):
                next_state = agent.do()
            util_acc += self.utilities[next_state]#self.belief_space.states.index(next_state)]
            print('i: {}\nacc: {}'.format(i, util_acc))
        #print('accumulated: {}'.format(util_acc))
        print('average: {}'.format(util_acc/times))
        print('init value: {}'.format(self.utilities[self.belief_space.states[0]]))









    def consistent_state (self, belief_state, blockage_instance):
        state_blocked = belief_state.blocked_edges
        for edge_num in state_blocked:
            if blockage_instance[edge_num] != state_blocked[edge_num]:
                return False
        return True






if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph_file', default='./graph.txt')
    parser.add_argument('-s', '--start_vertex', default=1)
    args = parser.parse_args()

    simulator = HurricaneEvacuationSimulator(graph_file=args.graph_file, start_vertex=int(args.start_vertex))
    simulator.world.print_graph()

    simulator.run_an_agent()

