import re

from enumerator import MultiQuery
from graph import Graph

class World(Graph):
    def __init__(self, graph_file):
        super(World, self).__init__()
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
            # self._d = self.parse_deadline(lines[len(lines) - 1])
            # initial create for n House vertices with 0 People
            self.create_init_vertices()
            # skip first and last
            lines = lines[1:len(lines)-1]
            # get Vertices from file
            v_lines = filter(lambda l: l.startswith('#V'), lines)
            for line in v_lines:
                vertex = self.parse_vertex(line=line)
                self._vertices[vertex.tag-1] = vertex
            # get Edges from file
            e_lines = filter(lambda l: l.startswith('#E'), lines)
            for line in e_lines:
                edge1, edge2 = self.parse_edge_line(line=line)
                self._edges.append(edge1)
                self._edges.append(edge2)
                self.adj_dict[edge1.get_v1().tag].append(edge1.get_v2().tag)  # add adjacency
                self.adj_dict[edge1.get_v2().tag].append(edge1.get_v1().tag)  # to both vertices of the edge

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
        if len(split_line) is 3 and 'F' in new_line:
            # default probability for a flood = 0.0
            return House(tag=int(split_line[0]), prob_flooding=float(split_line[2]))
        else:
            return House(tag=int(split_line[0]), prob_flooding=0)

    # parse an Edge line -: #E 2 4 W5
    # returns 2 edges (bi-directional)
    def parse_edge_line(self, line):
        new_line = self.remove_comments(line)
        if len(new_line.split(' ')) is not 4:
            raise BaseException('bad line: {}'.format(new_line))
        parsed_line = re.sub('W', '', new_line)
        parsed_line = re.sub('#E', '', parsed_line)
        edge_num, a, b, w = map(int, parsed_line.split(' '))
        a_vertex = self._vertices[a - 1]
        b_vertex = self._vertices[b - 1]
        return Graph.Edge(edge_num, a_vertex, b_vertex, w), Graph.Edge(edge_num, b_vertex, a_vertex, w)

    # parse N line
    def parse_num_of_vertices(self, line):
        new_line = self.remove_comments(line)
        new_line = re.sub('#V ', '', new_line)
        return int(new_line.split(' ')[0])

    def create_init_vertices(self):
        for i in range(1, self._num_of_vertices + 1):
            self._vertices.append(House(tag=i))
            self.adj_dict[i] = []  # empty list of adjacents


    # return the slow-down factor
    def get_slow_down(self):
        return self._k

    def get_deadline(self):
        return self._d

    #  ------- Print the world state
    def print_graph(self):
        print('------------------')

        print('file = {}'.format(self._graph_path))
        print('n = {}'.format(self._num_of_vertices))

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
            v1 = World.vertex_tostring_short(e.get_v1())
            v2 = World.vertex_tostring_short(e.get_v2())
            print('( {} , {} ) weight: {}'.format(v1, v2, e.weight))



    #  ------- Aux functions
    # Dijsktra algorithm, return visited & path :=
    # visited   { VERTEX_TAG : distance of VERTEX_TAG from source }
    # path      { VERTEX_TAG : optimal path from source to VERTEX_TAG
    def all_paths(self, source, destination, return_edge_nums=True):
        paths_list = []
        def all_paths_rec(u, visited, path):
            visited[u] = True
            path.append(u)
            if u == destination:
                paths_list.append([v for v in path])
            else:
                for v in self.get_adjacent_to(u):
                    if visited[v] is False:
                        all_paths_rec(v, visited, path)
            path.pop()
            visited[u] = False
        visited = {v: False for v in [vertex.tag for vertex in self.get_vertices()]}
        # paths_list = []
        all_paths_rec(source, visited, [])
        return map(self.vertices_to_edge_nums_path, paths_list)


    def vertices_to_edge_nums_path(self, v_path):
        edges_path = []
        # edges_path = reduce(lambda v1,v2: self.get_edge(v1, v1), v_path)
        for i in range(len(v_path)):
            if i < len(v_path) - 1:
                edges_path.append(self.get_edge(v1=v_path[i], v2=v_path[i+1]))
        return [e.edge_num for e in edges_path]




    def bi_edge_in_list(self, edge, edge_list):
        for e in edge_list:
            if e.is_equal(edge.get_v1().tag, edge.get_v2().tag, bidirectional=True):
                return True
        return False

    # get the edges in the path from vertex to sources
    def get_edges_in_path(self, dijkstra_path, source , vertex):
        current = vertex
        edges = []
        while current != source:
            v = dijkstra_path[current]
            edges.append(self.get_edge(v, current))
            current = v
        return edges


    def get_probability_path_blocked(self, path, bayes_network, reports):
        reported_evidence = reports.copy()
        query_vars = filter(lambda n: n.get_edge().edge_num in path, bayes_network.get_nodes_of_type('blockage'))
        multi_query = MultiQuery(query_vars=query_vars, evidence=reported_evidence, network=bayes_network)
        # vars_true is False - we want blockages to be false.
        p = multi_query.query_to_value(vars_true=True)
        return p


    @staticmethod
    def vertex_tostring(v):
        if isinstance(v, House):
            return '( {} , {} , prob_flood {} )'.format(v.tag, type(v).__name__, v.prob_flooding)
        else:
            return '( {} , {} )'.format(v.tag, type(v).__name__)

    @staticmethod
    def vertex_tostring_short(v):
        return str(v.tag)

    @staticmethod
    def remove_comments(line):
        return ' '.join(line[0:line.find(';')].split())


# A House vertex.
class House(Graph.Vertex):
    def __init__(self, tag, prob_flooding=0.0):
        super(House, self).__init__(tag)
        # probability of this spot to be flooded
        self.prob_flooding = prob_flooding





