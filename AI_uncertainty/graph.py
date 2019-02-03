from abc import ABCMeta
import json

class Graph(object):
    def __init__(self, root=None):
        self.root = root
        self._vertices = []
        self._edges = []
        self.adj_dict = {}                      # VERTEX_TAG : VERTEX ADJ'S {"1": [2, 3], "2": [1, 3, 4]}
        self._num_of_vertices = 0
        if root is not None:
            self.add_vertex(root)

    # should be a Vertex object
    def add_vertex(self, to_add):
        self._vertices.append(to_add)
        self.adj_dict.update({to_add.tag:[]})
        self._num_of_vertices += 1

    # should be an Edge object
    def add_edge(self, edge, bi_directional=True):
        self._edges.append(edge)
        self.adj_dict[edge.get_v1().tag].append(edge.get_v2().tag)  # add adjacency
        if bi_directional:
            self.adj_dict[edge.get_v2().tag].append(edge.get_v1().tag)  # to both vertices of the edge

    # print the adjacency dict
    def print_adjacency(self):
        print (json.dumps(self.adj_dict))

    #  ------- Getters
    def get_num_vertices(self):
        return self._num_of_vertices

    def get_adjacency_dict(self):
        return self.adj_dict

    # only for numeric tagged graph
    # TODO: MAYBE A BUG
    def get_vertex_for_tag(self,tag):
        return self._vertices[int(tag)-1]

    # return the edge of (v1, v2) if exists. else, return False
    def get_edge(self, v1, v2):
        for edge in self._edges:
            if edge.is_equal(v1, v2):
                return edge
        return False

    # returns all adjacent vertices that are NOT blocked
    def get_adjacent_to(self, vertex):
        if isinstance(vertex, Graph.Vertex):
            vertex = vertex.tag
        adjacent = self.adj_dict[vertex]
        # adjacent = filter(lambda v: self.get_edge(v, vertex) is not False, adjacent)  # filter out all blocked
        adjacent.sort()
        return adjacent

    # get the parents of 'vertex'. if as_object is True, then Vertex objects. else, as strings (tags)
    def get_parents_of(self, vertex, as_object=True):
        if isinstance(vertex, Graph.Vertex):
            vertex = vertex.tag
        parents = list()
        for edge in self._edges:
            if edge.get_v2().tag == vertex:
                parents.append(edge.get_v1() if as_object else edge.get_v1().tag)
        return parents





    def get_vertices(self):
        return self._vertices

    def get_edges(self, one_way=False):
        if one_way:
            taken = []
            edges = []
            for edge in self._edges:
                if edge.edge_num not in taken:
                    taken.append(edge.edge_num)
                    edges.append(edge)
            return edges
        return self._edges

    def get_edge_for_num(self, num):
        for edge in self._edges:
            if edge.edge_num == num:
                return edge

    # describes an edge on the graph
    class Edge(object):
        def __init__(self, edge_num, v1, v2, w, prob_blockage=0):
            self.edge_num = edge_num
            self._v1 = v1
            self._v2 = v2
            self.weight = w
            self.prob_blockage = prob_blockage

        # if edge v1-v2 equals (by tag) to this edge
        def is_equal(self, v1, v2, bidirectional=False):
            if bidirectional:
                return (v1 == self._v1.tag and v2 == self._v2.tag) or (v2 == self._v1.tag and v1 == self._v2.tag)

            return v1 == self._v1.tag and v2 == self._v2.tag

        def to_string(self, vertices=False):
            if vertices:
                return "({v1},{v2})".format(v1=self._v1, v2=self._v2)
            return "({edge_num})".format(edge_num=self.edge_num)

        def get_v1(self):
            return self._v1

        def get_v2(self):
            return self._v2

    # describes a vertex on the graph
    class Vertex(object):
        __metaclass__ = ABCMeta

        def __init__(self, tag=0):
            self.tag = tag


