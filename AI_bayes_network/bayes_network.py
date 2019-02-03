from graph import Graph
from cpt import CPT, BasicPT
UNKNOWN = 'unknown'


class BayesNetwork(Graph):

    def __init__(self, world=None):
        super(BayesNetwork, self).__init__()
        if world is not None:
            self.world = world
            self.create_network(world)

    # add an edge to the bayes network.
    # add child and parent to vertices
    def add_bayes_edge(self, parent, child):

        qi = None
        # flooding -> blockage
        if parent.node_type == 'flooding' and child.node_type == 'blockage':
            w_e = child.get_edge().weight
            qi = 1 - 0.6*(1.0/w_e)

        elif parent.node_type == 'blockage' and child.node_type == 'evacuees':
            w_e = parent.get_edge().weight
            pi = 0.8 if w_e > 4 else 0.4
            qi = 1 - pi

        edge = Graph.Edge(0, parent, child, w=qi)
        super(BayesNetwork, self).add_edge(edge, bi_directional=False)

    # create the bayes nodes and edges
    def create_network(self, world):
        self.create_bayes_nodes(world=world)
        self.create_bayes_edges()
        # now create a CPT for each node in the network
        for node in self._vertices:
            if node.is_conditional():
                parent_tags = self.get_parents_of(node, as_object=False)
                cpt = CPT(parent_tags=parent_tags, node_tag=node.tag, network=self)
                node.set_cpt(cpt)
            else:
                pt = BasicPT(node.tag, probability=node.get_vertex().prob_flooding)
                node.set_cpt(pt)




    # create bayes nodes for Flooding, Evacuees, and Blockage
    def create_bayes_nodes(self, world):
        for vertex in world.get_vertices():
            # create Flood vertex
            self.add_vertex(Flooding(vertex=vertex))
            self.add_vertex(Evacuees(vertex=vertex))
        # world - has bi-directional edges. add Bayes node just for 1 direction
        added_edges = []
        for edge in world.get_edges():
            if edge.edge_num not in added_edges:
                self.add_vertex(Blockage(edge=edge))
                added_edges.append(edge.edge_num)

    # create edges according to dependency
    def create_bayes_edges(self):
        # from flooding nodes to blockage nodes
        flooding_nodes = self.get_nodes_of_type(node_type='flooding')
        blockage_nodes = self.get_nodes_of_type(node_type='blockage')
        evacuees_nodes = self.get_nodes_of_type(node_type='evacuees')
        for blockage in blockage_nodes:
            v1 = blockage.get_edge().get_v1()
            v2 = blockage.get_edge().get_v2()
            flood_v1 = next((f_node for f_node in flooding_nodes if f_node.get_vertex().tag == v1.tag), None)
            flood_v2 = next((f_node for f_node in flooding_nodes if f_node.get_vertex().tag == v2.tag), None)
            self.add_bayes_edge(parent=flood_v1, child=blockage)
            self.add_bayes_edge(parent=flood_v2, child=blockage)
        # from blockage nodes to evacuees nodes
        for evacuees_node in evacuees_nodes:
            def leads_here(blockage_node):
                # True if the Blockage node refers the road HERE (the vertex of evacuees)
                return  evacuees_node.get_vertex().tag in (blockage_node.get_edge().get_v2().tag, blockage_node.get_edge().get_v1().tag)
            relevant_blockages = filter(leads_here, blockage_nodes)
            for blockage in relevant_blockages:
                self.add_bayes_edge(parent=blockage, child=evacuees_node)


    # get nodes of certain type, according to name. (e.g. 'flooding', 'blockage'...)
    def get_nodes_of_type(self, node_type):
        nodes = list()
        for node in self._vertices:
            nodes.append(node) if node.node_type.lower() == node_type.lower() else None
        return nodes

    # return nodes that are related to a world vertex. (e.g. Flooding nodes of vertex 1, etc...)
    def get_nodes_of_world_vertex(self, vertex):
        nodes = list()
        # isolate only vertex-related nodes.
        for node in filter(lambda n: n.node_type.lower() in ('flooding', 'evacuees'), self._vertices):
            if node.get_vertex().tag == vertex.tag:
                nodes.append(node)
        return nodes

    # return nodes that are related to a world vertex. (e.g. Flooding nodes of vertex 1, etc...)
    def get_nodes_of_world_edge(self, edge):
        nodes = list()
        # isolate only vertex-related nodes.
        for node in filter(lambda n: n.node_type.lower() == 'blockage', self._vertices):
            nodes.append(node) if node.get_edge().edge_num == edge.edge_num else None
        return nodes

    # returns a bayes Edge (parent) -> (child)
    def get_bayes_edge(self, parent_tag, child_tag):
        for bayes_edge in self.get_edges():
            if (parent_tag == bayes_edge.get_v1().tag) and (child_tag == bayes_edge.get_v2().tag):
                return bayes_edge
        raise BaseException('did not find bayes edge for ({},{})'.format(parent_tag, child_tag))

    # returns a Bayes node according to it's tag (e.g. ' blockage 1 ')
    def get_node_by_tag(self, tag):
        for node in self._vertices:
            if node.tag.lower() == tag.lower():
                return node

    # return list of all nodes, sorted according to condition - Flooding -> Blockage -> Evacuees
    def get_nodes_sorted_conditionally(self):
        floodings = []
        blockages = []
        evacuees = []
        nodes = self.get_vertices()
        for node in nodes:
            if node.node_type == 'flooding':
                floodings.append(node)
            elif node.node_type == 'blockage':
                blockages.append(node)
            elif node.node_type == 'evacuees':
                evacuees.append(node)
        return sorted(floodings) + sorted(blockages) + sorted(evacuees)




    # print network content for each vertex and edge in the "world" graph
    def print_network(self):
        probability = 'P({of}|{given}) = {value}'
        tab = '\t'

        def print_vertex(v):
            print('VERTEX {}:'.format(v.tag))
            bayes_nodes = self.get_nodes_of_world_vertex(v)
            for n in bayes_nodes:
                print(n.table_as_string())

        def print_edge(e):
            print('EDGE {}:'.format(e.edge_num))
            bayes_nodes = self.get_nodes_of_world_edge(e)
            for n in bayes_nodes:
                print(n.table_as_string())
        for vertex in self.world.get_vertices():
            print_vertex(vertex)
        for edge in self.world.get_edges(one_way=True):
            print_edge(edge)


# A Bayes Network Node
class BNNode(Graph.Vertex):
    def __init__(self, possible_values, short_name, name, node_type):
        super(BNNode, self).__init__(tag=name)
        self.node_type = node_type
        # dict of possible values & their probability
        self.possible_values = possible_values
        self.short_name = short_name
        self.CPT = None

    # set CPT for this node
    def set_cpt(self, cpt):
        self.CPT = cpt

    def table_as_string(self):
        return self.CPT.to_string()

    def to_string(self, short=True):
        if short:
            s = self.short_name
        else:
            #TODO:print more detailed
            s = self.short_name
        return s

    # get the probability for a certain CPT row
    def get_probability(self, node_value, parent_values):
         return self.CPT.get_probability(me=node_value, given=parent_values)
    #
    # # get probability if maybe some parents have unknown values
    # def get_cond_probability(self, node_value, parents, evidence):
    #







# Represents a Flooding at a certain Vertex
class Flooding(BNNode):
    def __init__(self, vertex):
        self._vertex = vertex
        type = 'flooding'
        name = '{} {}'.format(type, vertex.tag)
        short_name = 'Fl({})'.format(vertex.tag)
        values = [True, False]
        super(Flooding, self).__init__(possible_values=values, short_name=short_name, name=name, node_type=type)
        # the edge this Blockage Random Variable Refers to

    def get_vertex(self):
        return self._vertex

    def is_conditional(self):
        return False

# Represents a Blockage of a certain Edge
class Blockage(BNNode):
    def __init__(self, edge):
        # the edge this Blockage Random Variable Refers to
        self._edge = edge
        type = 'blockage'
        name = '{} {}'.format(type, edge.edge_num)
        short_name = 'B({})'.format(edge.to_string(vertices=True))
        values = [True, False]

        super(Blockage, self).__init__(possible_values=values, short_name=short_name, name=name, node_type=type)



    def get_edge(self):
        return self._edge


    def is_conditional(self):
        return True


# Represents a Blockage of a certain Edge
class Evacuees(BNNode):
    def __init__(self, vertex):
        self._vertex = vertex
        type = 'evacuees'
        name = '{} {}'.format(type, vertex.tag)
        short_name = 'Ev({})'.format(vertex.tag)
        values = [True, False]
        # initially, probabilities are unknown
        super(Evacuees, self).__init__(possible_values=values, short_name=short_name, name=name, node_type=type)

    def get_vertex(self):
        return self._vertex


    def is_conditional(self):
        return True












