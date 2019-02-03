from belief import *
import copy

class ValueIteration(object):
    def __init__(self, belief_space, world):
        self.world = world
        self.space = belief_space
        self.states = belief_space.states
        self.U = {s:0.0 for s in self.states}#[0.0] * len(self.states)
        self.UTAG ={s:0.0 for s in self.states}# [0.0] * len(self.states)


    def pretty_print(self):
        for s in self.states:
            print('------\n')
            print('state:')
            s.print_state(print_succ=False)
            print('U: {}'.format(self.U[s]))

    def value_iteration(self):
        self.states.reverse()

        while True:
            self.U = dict(self.UTAG)
            delta = 0.0
            for s in self.states:
                self.UTAG[s] = self.expected_val(s)
                diff = abs(float(self.UTAG[s]) - float(self.U[s]))
                if diff > delta:
                    print('delta of values {} and {}'.format(self.UTAG[s], self.U[s]))
                    delta = diff
            if delta == 0:
                break
            else:
                print('delta is {}'.format(delta))

        for s in self.states:
            if self.space.goal_state(s):
                self.U[s] = float(s.saved)
        self.states.reverse()
        return self.U

    def expected_val(self, state):
        if self.space.goal_state(state):
            return 0
        return max(map(lambda loc: (sum(map(lambda s: self.prob(state, s), loc))), state.successors.values()))

        # max = -1
        # for loc in state.successors.values():
        #     ls = map(lambda s: self.prob(state, s), loc)
        #     summm = sum(ls)
        #     if summm > max:
        #         max = summm
        # return max

    def prob(self, state, s):
        reward = 0
        if self.space.goal_state(s):
            reward = s.saved
        else:
            reward = 0
        return self.transition(state, s) * (reward + 1 * self.UTAG[s])

    def successor_sum(self, state):
        successor_states = state.successors
        if len(successor_states) == 0:
            return 0.0
        return max(map(lambda s: self.transition(state, s) * float(self.U[s]), successor_states))

    def transition(self, old_state, new_state):
        known = old_state.blocked_edges
        blockages = new_state.blocked_edges
        init_p = 1.0
        for e in blockages:
            if e in known:
                continue
            edge = self.world.get_edge_for_num(e)
            p = edge.prob_blockage
            if blockages[e] is True:
                init_p = init_p * p
            else:
                init_p = init_p * (1.0 - p)
        return init_p





