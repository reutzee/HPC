import re
from graph import Graph

class World(Graph):
    def __init__(self, graph_file, k=1):
        super(World, self).__init__()
        self._k = k
        self._d = 0
        self._graph_path = graph_file
        self.shelter_vertices = []              # Shelter vertex tags
        self.parse_file()                       # parsing given ASCII file
        self.house_vertices = list(set(range(1, self._num_of_vertices + 1)) - set(self.shelter_vertices))

    def parse_file(self):
        with open(self._graph_path) as graph_file:
            lines = graph_file.readlines()
            # get n parameter
            self._num_of_vertices = self.parse_num_of_vertices(lines[0])
            # get d parameter
            self._d = self.parse_deadline(lines[len(lines) - 1])
            # initial create for n House vertices with 0 People
            self.create_init_vertices()
            # skip first and last
            lines = lines[1:len(lines)-1]
            # get Vertices from file
            v_lines = filter(lambda l: l.startswith('#V'), lines)
            for line in v_lines:
                vertex = self.parse_vertex(line=line)
                self._vertices[vertex.tag-1] = vertex
                if isinstance(vertex, Shelter):
                    self.shelter_vertices.append(vertex.tag)

            # get Edges from file
            e_lines = filter(lambda l: l.startswith('#E'), lines)
            for line in e_lines:
                edge = self.parse_edge_line(line=line)
                self._edges.append(edge)
                self.adj_dict[edge.v1.tag].append(edge.v2.tag)  # add adjacency
                self.adj_dict[edge.v2.tag].append(edge.v1.tag)  # to both vertices of the edge

    # parse D line
    def parse_deadline(self, line):
        new_line = self.remove_comments(line)
        new_line = re.sub('#D ', '', new_line)
        return int(new_line.split(' ')[0])

    # parse a Vertex line -: #V 2 P 1 *or* #V 1 S
    def parse_vertex(self, line):
        new_line = self.remove_comments(line)
        new_line = re.sub('#V ', '', new_line)
        split_line = new_line.split(' ')

        # if its a SHELTER line
        if len(split_line) is 2 and 's' in new_line.lower():
            return Shelter(tag=int(split_line[0]))
        # HOUSE line
        elif len(split_line) is 3 and 'p' in new_line.lower():
            return House(tag=int(split_line[0]), people=int(split_line[2]))

    # parse an Edge line -: #E 2 4 W5
    def parse_edge_line(self, line):
        new_line = self.remove_comments(line)
        if len(new_line.split(' ')) is not 4:
            raise BaseException('bad line: {}'.format(new_line))
        parsed_line = re.sub('W', '', new_line)
        parsed_line = re.sub('#E ', '', parsed_line)
        a, b, w = map(int, parsed_line.split(' '))
        a_vertex = self._vertices[a - 1]
        b_vertex = self._vertices[b - 1]
        return Graph.Edge(a_vertex, b_vertex, w)

    # parse N line
    def parse_num_of_vertices(self, line):
        new_line = self.remove_comments(line)
        new_line = re.sub('#V ', '', new_line)
        return int(new_line.split(' ')[0])

    # #  ------- Alter the world
    def create_init_vertices(self):
        for i in range(1, self._num_of_vertices + 1):
            self._vertices.append(House(tag=i, people=0))
            self.adj_dict[i] = []  # empty list of adjacents

    def pick_people_up(self, vertex_number):
        vertex = self._vertices[vertex_number - 1]
        if isinstance(vertex, House):
            return vertex.flee()
        return 0

    # return the slow-down factor
    def get_slow_down(self):
        return self._k

    def get_deadline(self):
        return self._d

    def is_shelter(self, vertex_num):
        return not isinstance(self._vertices[vertex_num - 1], House)

    def is_house(self, vertex_num):
        return isinstance(self._vertices[vertex_num - 1], House)
    # Task 1 only
    def filter_empty_houses(self):
        new = list(filter(lambda tag: self._vertices[tag - 1].people != 0, self.house_vertices))
        self.house_vertices = new
        return new

    #  ------- Print the world state
    def print_graph(self):
        print('------------------')

        print('file = {}'.format(self._graph_path))
        print('n = {}'.format(self._num_of_vertices))
        print('k = {}'.format(self._k))
        print('d = {}'.format(self._d))

        self.print_vertices()
        self.print_edges()
        print('------------------')

    # print all vertices
    def print_vertices(self):
        print('Vertices: ')
        for v in self._vertices:
            print(self.vertex_tostring(v))

    # print all edges
    def print_edges(self):
        print('Edges: ')
        for e in self._edges:
            v1 = World.vertex_tostring_short(e.v1)
            v2 = World.vertex_tostring_short(e.v2)
            #print('v1: {}\nv2: {}\nw: {}'.format(v1, v2, e.weight))
            print('( {} , {} ) weight: {}'.format(v1, v2, e.weight))


            #  ------- Aux functions
    @staticmethod
    def vertex_tostring(v):
        if isinstance(v, House):
            return '( {} , {} , {} )'.format(v.tag, type(v).__name__, v.people)
        else:
            return '( {} , {} )'.format(v.tag, type(v).__name__)

    @staticmethod
    def vertex_tostring_short(v):
        return str(v.tag)

    # remove ;                 from a line
    @staticmethod
    def remove_comments(line):
        return ' '.join(line[0:line.find(';')].split())

    # Dijsktra algorithm, return visited & path :=
    # visited   { VERTEX_TAG : distance of VERTEX_TAG from source }
    # path      { VERTEX_TAG : optimal path from source to VERTEX_TAG
    def dijkstra(self, source):
        visited = {source: 0}   # VERTEX_TAG : DISTANCE FROM SOURCE
        path = {}               # V : PREV V Previous node in optimal path from source

        # get all vertices' tags
        nodes = set((lambda v: v.tag)(v) for v in self._vertices)
        while nodes:
            u = None
            for node in nodes:
                if node in visited:
                    if u is None:
                        u = node
                    elif visited[node] < visited[u]:
                        u = node

            if u is None:
                break

            # Node with the least distance will be selected first
            nodes.remove(u)
            # get the distance from source to u
            distance_u = visited[u]

            # for each neighbor v of u
            for v in self.get_adjacent_to(u):
                # get length(u, v)
                edge_u_v = self.get_edge(u, v)
                len_u_v = edge_u_v.weight

                # weight = dist[u] + length(u, v)
                weight = distance_u + len_u_v

                #  A shorter path to v has been found
                if v not in visited or weight < visited[v]:
                    visited[v] = weight
                    path[v] = u    # prev[v] <- u
        return visited, path


    # For task 2
    def super_dijkstra(self, source, people_collected=0, dont_collect=None):
        def add_people(tag, dont_collect):
            if dont_collect is None or tag not in dont_collect:
                return self.get_vertex_for_tag(tag).people
            return 0
        source_vertex = self.get_vertex_for_tag(source)
        if people_collected == 0:
            people_in_source = 0 if isinstance(source_vertex, Shelter) else source_vertex.people
        else:
            people_in_source = people_collected
        visited = {source: (0, people_in_source)}   # VERTEX_TAG : DISTANCE FROM SOURCE
        path = {}               # V : PREV V Previous node in optimal path from source
        # get all vertices' tags
        nodes = set((lambda v: v.tag)(v) for v in self._vertices)
        while nodes:
            u = None
            for node in nodes:
                if node in visited:
                    if u is None:
                        u = node
                    elif visited[node][0] < visited[u][0]:
                        u = node

            if u is None:
                break
            # Node with the least distance will be selected first
            nodes.remove(u)
            # get the distance from source to u
            distance_u = visited[u][0]
            # for each neighbor v of u
            for v in self.get_adjacent_to(u):
                # get length(u, v)
                len_u_v = self.calc_edge_weight(v1=u, v2=v, visited=visited)
                # weight = dist[u] + length(u, v)
                weight = distance_u + len_u_v
                #  A shorter path to v has been found
                if v not in visited or weight < visited[v][0]:
                    people = visited[u][1] + add_people(v, dont_collect=dont_collect) \
                        if isinstance(self.get_vertex_for_tag(v), House)\
                        else 0

                    visited[v] = (weight, people)    # update collected ppl
                    path[v] = u    # prev[v] <- u

                   # print('******\n******\nvisited: {}\npath:{}\n******\n******\n'.format(visited, path))
        return visited, path

    def calc_edge_weight(self, v1, v2, visited):
        edge = self.get_edge(v1, v2)
        v1_collected_people = visited[v1][1]    # num of collected people in v1
        return edge.weight * (1 + self._k * v1_collected_people)






# A Shelter vertex.
class Shelter(Graph.Vertex):
    def __init__(self, tag):
        super(Shelter, self).__init__(tag)


# A House vertex. may contain "people" to evacuate ( >=0 )
class House(Graph.Vertex):
    def __init__(self, tag, people):
        super(House, self).__init__(tag)
        self.people = people

    # empty the house and return number of people that fled from it
    def flee(self):
        fled = self.people
        self.people = 0
        return fled




