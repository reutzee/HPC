from abc import abstractmethod
from itertools import product

LEAKAGE = 0.001

class PT(object):
    def __init__(self, node_tag):
        self.node_tag = node_tag

    @abstractmethod
    def get_probability(self, me, given): pass


# Conditional probability table
class CPT(PT):
    def __init__(self, parent_tags, node_tag, network):
        super(CPT, self).__init__(node_tag=node_tag)
        self.parent_tags = parent_tags
        self.probability_table = dict()
        self.initialize_table(network=network)

    # string representation of a certain model of parents
    def model_to_string(self, model):
        s = ''
        for parent_tag, parent_value in zip(self.parent_tags, model):
            value_str = parent_tag if parent_value is True else 'not ' + parent_tag
            value_str += ','
            s += value_str
        s = s[0:-1]     # remove final comma
        return s

    def initialize_table(self, network):
        # an list of possible random variable mappings (?!)
        parent_values = map(list, product([False, True], repeat=len(self.parent_tags)))
        # edges in bayes network
        edges = [network.get_bayes_edge(parent_tag, self.node_tag) for parent_tag in self.parent_tags]
        q_values = [edge.weight for edge in edges]

        # [True ,True,False]
        # [ Q1  , Q2 , Q3    ]
        for bool_array in parent_values:
            # calculate product of qi's
            qval_bool = zip(q_values, bool_array)
            true_qs = map((lambda (q, b): q), filter(lambda (q, b): b is True, qval_bool))
            q_product = reduce(lambda x, y: x*y, true_qs) if len(true_qs) is not 0 else 0
            self.probability_table[tuple(bool_array)] = 1.0 - q_product if len(true_qs) is not 0 else LEAKAGE
            # if len(true_qs) is not 0:
            #     self.probability_table[tuple(bool_array)] = 1.0 - q_product
            # else:
            #     self.probability_table[tuple(bool_array)] = LEAKAGE



    def get_probability(self, me, given):
        given = tuple(given)
        p = self.probability_table[given]
        return p if me is True else 1 - p

    def to_string(self):

        s_true = ''
        s_false = ''

        parent_values = self.probability_table.keys()
        for value in parent_values:
            current_prob = 'P({of}|{given}) = {value}'
            given_str = self.model_to_string(value)
            true_value = self.get_probability(True, value)
            false_value = self.get_probability(False, value)
            s_true += current_prob.format(of=self.node_tag, given=given_str, value=true_value) + '\n'
            s_false += current_prob.format(of='not ' + self.node_tag, given=given_str, value=false_value) + '\n'
        return s_true + s_false






# basic probability table - for Flooding Nodes. (have not parents)
class BasicPT(PT):
    def __init__(self, node_tag, probability=0.0):
        super(BasicPT, self).__init__(node_tag=node_tag)
        self.probability = probability

    def get_probability(self, me, given):
        return self.probability if me is True else (1 - self.probability)


    def to_string(self):
        prob_str = 'P({of}) = {value}'
        str_true = prob_str.format(of=self.node_tag, value=self.get_probability(True, 1))
        str_false = prob_str.format(of='not ' + self.node_tag, value=self.get_probability(False, 1))
        return str_true + '\n' + str_false
