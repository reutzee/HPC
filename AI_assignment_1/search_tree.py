from env import Shelter, House
from graph import Graph



class SearchTree(Graph):
    def __init__(self, init_state, strategy='greedy', expand_limit=None, vandal_records=None):
        self.expand_limit = expand_limit
        self.strategy = strategy
        self.root = SmartVertex(None, init_state)  # initial node
        super(SearchTree, self).__init__(self.root)
        self.calculated_h = {}
        self.num_expands = 0
        self.vandal_records = vandal_records

    def tree_search(self, world):
        # initialize the search tree using the init_state of root
        # fringe - queue sorted in decreasing order of desirability
        fringe = [self.root]
        while True:
            # if there are no candidates for expansion -> FAIL
            if len(fringe) is 0:
                return 'FAILURE'
            # choose a leaf node for expansion according to strategy
            node = self.get_best(fringe, world)
            fringe.remove(node)
            # if the node contains a goal state -> SOLUTION
            if self.goal_test(node, world):
                return node
            # else expand the node and add the resulting nodes to the search tree
            if self.strategy.upper() == 'RTA' and self.num_expands >= self.expand_limit:
                    return node
            fringe += self.expand(node, world)

    # get best node according to heuristic evaluation function and strategy
    def get_best(self, fringe, world):
        if self.strategy == 'greedy':
            # Using Greedy Search - by h(n)
            m = min(fringe, key=lambda node: self.h(node, world))
        # Using A* Search - by f(n) = h(n) + g(n)
        elif self.strategy.upper() == 'A*':
            m = min(fringe, key=lambda node: self.h(node, world) + self.g(node))
        else:   # if self.strategy.upper() is 'RTA':
            m = min(fringe, key=lambda node: self.h(node, world) + self.g(node))
        return m

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

    def h(self, node, world):
        if node in self.calculated_h:
            return self.calculated_h[node]
        # print('Calculating H({})'.format(node.state))
        died = 0
        FACTOR = 1#world.get_deadline() * 2
        # get all visited vertices till this state
        visited_h = self.get_visited_vertices(node)
        people_collected = node.get_people_in_car()
        vertices_h, path_h = world.super_dijkstra(source=node.get_position(), people_collected=people_collected, dont_collect=visited_h)
        # print('\n----------------\nSuper dijkstra from vertex: {} to nearest house\ngot vertices {} \npath {}--------------------\n\n'.format(node.get_position() -1,
        #                                                                                                                                       [v-1 for v in vertices_h],
                                                                                                                                              # [v-1 for v in path_h]))
        vertices_h.pop(node.get_position(), None)   # remove self
        houses = self.isolate_sort_houses(vertices=vertices_h, world=world, visited=visited_h, remove_empty_houses=True)       #TODO Check for bug (no houses)
        current_tag = node.get_position()
        if world.is_house(current_tag) and current_tag ==  self.get_visited_vertices(node)[0] and world.get_vertex_for_tag(current_tag).people > 0 :
            house_entry  = [current_tag , (0,world.get_vertex_for_tag(current_tag).people )]
            houses += [house_entry]
            visited_h += [house_entry]
        for house in houses:
            # print('houses --- {}'.format(houses))
            visited = visited_h + [house[0]]# + self.get_vertices_in_path(path_h, house[0])                # update the visited vertices (DONT PICK UP FROM THEM)
            cost_to_house = house[1][0]
            people_collected = house[1][1]  # collected people on the way to the house
            vertices_s, path_s = world.super_dijkstra(source=house[0], people_collected=people_collected, dont_collect=visited)
            shelters = self.isolate_sort_shelters(vertices=vertices_s, world=world)
            closest_shelter = shelters[0]
            cost_to_shelter = closest_shelter[1][0]
            if node.get_time() + cost_to_house + cost_to_shelter > world.get_deadline():
                died += world.get_vertex_for_tag(house[0]).people
        self.calculated_h[node] = (max(died, node.get_people_in_car()))*FACTOR
        print('\nh: {} is : {}\n\n'.format(node.get_state(alter=True), self.calculated_h[node]))
        return self.calculated_h[node]

    # returns list of vertices for given dijkstra path (of predecessors)
    def get_vertices_in_path(self, path, to):
        vertices = [to]
        try:
            while True:
                vertices.append(path[to])
                to = path[to]
        except KeyError:
            return vertices
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






    # goal_test - goal state - saved all people OR time ends up
    def goal_test(self, node, world):
        return ((len(node.get_full_houses()) is 0) and (node.get_people_in_car() is 0)) \
               or (node.get_time() >= world.get_deadline())

    # return set of SmartVertex Nodes to expand s
    def expand(self, s, world):
        pairs = self.successor(s.state, world)
        successors_nodes = []
        for action, result in pairs:
            # path_cost [s] = path_cost[s] + step_cost(node, action, s) = result.time (already calc it)
            # as a result - just assign state of the new node to be the result
            node = SmartVertex(parent=s, action=action, state=result)
            # add the new node to s children
            s.add_child(node)
            # add the new node as a new vertex at the search graph
            self.add_vertex(node)
            # add a new edge (s <-> node)
            # in the *env* graph - we know that s is adjacent of node so get the edge and add it to the *search* graph
            # add the new node to successors
            successors_nodes.append(node)
        print('expanded: {}\n       to {}'.format(s.get_state(alter=True), [node.get_state(alter=True) for node in successors_nodes]))
        self.num_expands += 1
        return successors_nodes

    # Successor function for a state and observation (the world in our case)
    def successor(self, state, world):
        position = state['position']                    # position of the agent in the world
        neighbours = world.get_adjacent_to(position)    # neighbours
        pairs = []
        for v in neighbours:
            new_full_houses = list(state['full_houses'])
            new_people_in_car = state['people_in_car']
            new_time = state['time'] + self.calculate_price(world, position, v, state['people_in_car'])
            # if v is House Vertex -> pick up
            if world.is_house(v) and v in new_full_houses:
                new_full_houses.remove(v)
                new_people_in_car += world.get_vertex_for_tag(v).people
            # if v is Shelter Vertex -> drop off all of them
            if world.is_shelter(v) and new_time <= world.get_deadline():
                new_people_in_car = 0
            # creating [action, result]
            action = 'T{}'.format(str(v))
            result = {'position': v,
                      'full_houses': new_full_houses,
                      'people_in_car': new_people_in_car,
                      'time': new_time
                      }
            # if result['time'] > world.get_deadline():
            #     continue
            # for bonus
            if self.vandal_records is not None:

                try:
                    block_time = self.vandal_records['{},{}'.format(str(v), str(position))]
                    if not (state['time'] <= block_time <= result['time']):

                        continue
                except KeyError:
                    pairs.append((action, result))
                    continue
            pairs.append((action, result))
        return pairs

    # time it takes to traverse on 'edge'
    def calculate_price(self, world, v1, v2, p):
        edge = world.get_edge(v1, v2)
        w = edge.weight
        k = world.get_slow_down()
        return w*(1+k*p)


# tag generator
def tag_gen():
    i = 1
    while True:
        yield i
        i += 1


gen = tag_gen()


class SmartVertex(Graph.Vertex):
        def __init__(self, parent, state, action='NOP'):
            self.action = action
            self.children = []
            self.parent = parent
            self.state = state.copy()
            super(SmartVertex, self).__init__(gen.next())

        def get_state(self, alter=False):
            if alter:
                new_s = dict(self.state)
                new_s['position'] -= 1
                houses  = new_s['full_houses']
                houses = [h - 1 for h in houses]
                new_s['full_houses'] = houses
                return new_s
            return self.state

        def add_child(self, node_to_add):
            self.children.append(node_to_add)

        def get_position(self):
            return self.state['position']

        def get_full_houses(self):
            return self.state['full_houses']

        def get_people_in_car(self):
            return self.state['people_in_car']

        def get_time(self):
            return self.state['time']











