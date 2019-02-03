MAX_EVACUEES = 5
from itertools import chain, combinations
from itertools import product



class BeliefSpace(object):
    def __init__(self, world, init_vertex=1):
        self.world = world
        self.states = []
        self.init_states = []

    def create_all_belief_states(self, init_vertex):
        # init state
        all_init_states = self.belief_state_list(location=init_vertex, time=0)

        legal = filter(lambda state: state.saved == 0 and state.evacuees == self.get_init_evacs()[0], all_init_states)
        self.init_states += legal

        self.states += legal
        self.expand(legal)

    def goal_state(self, state):
        total_saved = sum([v.evac for v in self.world.get_vertices()])
        deadline = self.world.get_deadline()
        return state.time >= deadline or state.saved == total_saved

    # to_expand is a LIST of belief states to expand
    def expand(self, to_expand):
        q = to_expand
        while q:
            state = q.pop()
            if self.goal_state(state):
                continue
            neighbors = self.world.get_adjacent_to(state.location)

            successors = []
            for n in neighbors:

                edge = self.world.get_edge(n, state.location)
                # if we know already its blocked
                if edge.edge_num in state.blocked_edges.keys() and state.blocked_edges[edge.edge_num] is True:
                    continue

                new_location = n
                new_time = state.time + edge.weight

                new_evacs = dict(state.evacuees)
                new_carrying = int(state.carrying)
                new_saved = int(state.saved)
                # if there are evacuees at the neighbor
                # carry them
                if n in state.evacuees.keys():
                    new_carrying += self.world.get_vertex_for_tag(n).evac
                    # delete from evacuees (in place)
                    new_evacs.pop(n)

                # fix shelter parsing
                if self.world.get_shelter_tag() == n and new_time <= self.world.get_deadline():
                    new_saved += state.carrying
                    new_carrying = 0

                # [ {e1: T e2: F} ... ]
                # OR
                # [ { } ]
                # NEW edges that has prob > 0
                dict_block = self.get_possible_blocked(n, e_nums_to_ignore=state.blocked_edges.keys())
                for blocked_possibility in dict_block:
                    if blocked_possibility == {}:
                        continue

                    new_blocked = dict(blocked_possibility, ** dict(state.blocked_edges))
                    s = BeliefState(new_location, new_blocked, new_carrying, new_evacs, new_saved, new_time)
                    # add successor
                    successors.append(s)

                if len(dict_block) is 0 or dict_block == [{}]:
                    s = BeliefState(new_location, dict(state.blocked_edges), new_carrying, new_evacs, new_saved, new_time)
                    # add successor
                    successors.append(s)
            q += successors
            i = 1
            self.states += successors

            locations = map(lambda s: s.location, successors)
            succ = {loc: [] for loc in locations}
            for s in successors:
                loc = s.location
                succ[loc].append(s)
            state.successors = succ




    def belief_state_list(self, location, time):
        states = []

        blockages = self.get_possible_blocked(location)  # list of all dicts {1: Blocked, 2: Non-Blocked.....} 1,2 are neighbors of 'location'
        total_saved = sum([v.evac for v in self.world.get_vertices()])    # total number of evacuees
        saved_set = range(total_saved + 1)      # all possibilities for 'saved'
        evacs = self.get_possible_evacs()
        carrying = self.world.get_vertex_for_tag(location).evac

        prod = list(product(*[[location], blockages,[carrying], evacs, saved_set, [time]]))
        for (l, bl, c, ev, s, t) in prod:
            belief_state = BeliefState(location=l, blocked_edges=bl, carrying=c, evacs_dict=ev, saved=s, time=t)
            states.append(belief_state)
        return states

    def get_init_evacs(self):
        evacables = map(lambda v : v.tag, filter(lambda v: v.evac > 0, self.world.get_vertices()))
        evac_attrs = set(product({True}, repeat=len(evacables)))
        return [dict(zip(evacables, attr)) for attr in evac_attrs]

    def get_possible_evacs(self):
        evacables = map(lambda v : v.tag, filter(lambda v: v.evac > 0, self.world.get_vertices()))
        evac_attrs = set(product({True, False}, repeat=len(evacables)))
        return [dict(zip(evacables, attr)) for attr in evac_attrs]

    def get_possible_blocked(self, location, e_nums_to_ignore=[]):
        adj = self.world.get_adjacent_to(location)
        adj_edges = [self.world.get_edge(location, v) for v in adj]
        adj_edges_filters = filter(lambda e: e.edge_num not in e_nums_to_ignore, adj_edges)
        blockables = filter(lambda x: x.prob_blockage > 0, adj_edges_filters)

        blockables_tag = map(lambda e: e.edge_num, blockables)
        blockable_attrs = set(product({True, False}, repeat=len(blockables)))
        # filter this from all NON BLOCKED edges
        tag_to_option = [dict(zip(blockables_tag, attr)) for attr in blockable_attrs]
        return tag_to_option

    def get_successor(self, state):
        successors = []
        neighbors = self.world.get_adjacent_to(state.location)


class BeliefState(object):
    def __init__(self, location, blocked_edges, carrying, evacs_dict, saved, time):
        self.location = location
        self.evacuees = evacs_dict    # {v1: 3, v2: 2, v3: 0 .... }
        self.blocked_edges = blocked_edges
        self.carrying = carrying
        self.saved = saved
        self.time = time
        self.successors = None

    def print_state(self, print_succ=True):
        evac_values = (list(self.evacuees.values())) or ['NO_EVACS']
        joint_evac = ",".join(list(map(lambda e: str(e), evac_values)))
        blockage_str = " ,"
        for item in self.blocked_edges.items():
            blockage_str+=  'EDGE_BLOCK '+str(item[0]) + ": "+str(item[1])
        if len(self.blocked_edges.items()) == 0:
            blockage_str += ".."

        print("(V"+str(self.location)+","+str(self.evacuees)+", SAVED:"+str(self.saved)+blockage_str+","+str(self.time)+") "+ "C"+str(self.carrying) )

        if print_succ:
            print("SUCCESSORS :")
            for s in self.successors:
                s.print_state()
            print("--------------------")

    def to_dict(self):
        d = dict()
        d['location'] = self.location
        d['blocked'] = self.blocked_edges
        d['carrying'] = self.carrying
        d['evacuees'] = self.evacuees
        d['saved'] = self.saved
        d['time'] = self.time
        return d

