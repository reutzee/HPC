from env import *
from agent import Agent

class Human(Agent):
    def __init__(self, world, name=None, init_vertex=1):
        super(Human, self).__init__(world=world, name=name, init_vertex=init_vertex)

    # return (the current position, the next move) for the Simulator
    def do(self):
        return self.get_next_move()

    # get the next move from the user
    def get_next_move(self):
        return raw_input("What is your next move?\n--NOP to no-op\n--T<#Vertex> to traverse to another vertex\nInput: ").upper()


# A greedy agent
# compute the shortest currently unblocked path
# to the next vertex with people to be rescued
# OR to a shelter if it is carrying people
# If there is no such path, do no-op.
class Greedy(Agent):
    def __init__(self, world, name=None, init_vertex=1):
        super(Greedy, self).__init__(world=world, name=name, init_vertex=init_vertex)

    def do(self):
        curr_vertex = self.vertex
        # run Dijsktra
        distance_dict, path = self.observation.dijkstra(curr_vertex)
        # removing its curr_vertex (because distance from v to v is 0 .. )
        distance_dict.pop(curr_vertex, None)

        # if it is carrying people - look for the closet shelter
        if self.get_people_in_car() > 0:
            traverse_to_shelter = self.traverse_to_v(self.observation.shelter_vertices, distance_dict, path)
            if traverse_to_shelter is not False:
                return traverse_to_shelter
        # look for the closet house
        else:
            # filter house tags only with at least one person in it
            self.observation.filter_empty_houses()
            traverse_to_house = self.traverse_to_v(self.observation.house_vertices, distance_dict, path)
            if traverse_to_house is not False:
                return traverse_to_house
                # No such path - do nop
        return 'NOP'

    def traverse_to_v(self, v_tags, distance_dict, path):
        # filter only distances of SHELTER/HOUSE vertices
        filter_distance_dict = {k: distance_dict[k] for k in v_tags if k in distance_dict}
        # if found unblocked shortest path
        if len(filter_distance_dict) > 0:
            min_distance = min(filter_distance_dict.values())
            vertices = filter_distance_dict.keys()
            distances = filter_distance_dict.values()
            # get key by its value(= in our case distance)
            destination_tag = vertices[distances.index(min_distance)]
            backtrack = path[destination_tag]
            if backtrack is self.vertex:
                # traverse straight to the shelter vertex
                return 'T{}'.format(str(destination_tag))
            while path[backtrack] is not self.vertex:
                backtrack = path[backtrack]
            return 'T{}'.format(str(backtrack))

        # No such path - do nop
        else:
            return False

# A Vandal agent
# does V no-ops
# blocks the lowest costing adjacent edge
# traverses lowest cost edge (if more than 1, the lowest index)


class Vandal(Agent):
    def __init__(self, world, name=None, init_vertex=1):
        super(Vandal, self).__init__(world=world, name=name, init_vertex=init_vertex)
        self.v = world.get_num_vertices()       # the time the vandal waits
        self.no_ops = 0
        self.last_action = 'TRAVERSE'

    def do(self):
        # do NoOps
        if self.no_ops < self.v:        # if should keep doing NoOp
            self.no_ops += 1
            return 'NOP'
        # now Block a road
        elif self.no_ops == self.v and self._actions[-1] == 'NOP':
            if self.last_action == 'TRAVERSE':
                cheapest = self.lowest_adjacent()
                if cheapest is not None:
                    self.no_ops = 0
                    self.last_action = 'BLOCK'
                    return 'BLOCK {} {}'.format(self.vertex, cheapest)
                else:
                    return 'NOP'
            elif self.last_action == 'BLOCK':
                cheapest = self.lowest_adjacent()
                if cheapest is not None:
                    self.no_ops = 0
                    self.last_action = 'TRAVERSE'
                    return 'T{}'.format(str(cheapest))
                else:
                    return 'NOP'



    def lowest_adjacent(self):
        def weight(v):
            return self.observation.get_edge(v, self.vertex).weight
        adjacent = self.observation.get_adjacent_to(self.vertex)  # list of adjacent vertices
        if len(adjacent) > 0:
            adjacent.sort(key=weight)
            return adjacent[0]
        return None

