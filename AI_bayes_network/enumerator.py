# list helper functions
def first(ls):
    if not ls:
        return ls
    return ls[0]


def rest(ls):
    if not ls:
        return None
    return ls[1:]


# copies evidence and returns the extended version
def extend(evidence, var, value):
    new_evidence = evidence.copy()
    new_evidence[var] = value
    return new_evidence


class Enumerator(object):
    # query_var   -   a BNN
    # evidence    -   a mappping {'blockage 1' : True, 'blockage 2' : False.....}
    # network     -   a Bayes Network
    # hidden      -   BNN's with unknown values
    def __init__(self, query_var, evidence, network):
        self.network = network
        self.query_var = query_var
        self.evidence = evidence

    def enumeration_ask(self):
        values = self.query_var.possible_values
        distribution = []
        # in case of conflicting 'given' and query vars
        if self.query_var.tag in self.evidence.keys():
            return (1.0, 0.0) if self.evidence[self.query_var.tag] is True else (0.0, 1.0)
        for value in values:
            extended_evidence = extend(evidence=self.evidence, var=self.query_var.tag, value=value)
            network_vars = self.network.get_nodes_sorted_conditionally()
            distribution.append(self.enumerate_all(variables=network_vars, evidence=extended_evidence))
        distribution = self.normalize(distribution)
        return distribution

    # pre-condition : all evidence variables have values =! None
    # variables - are BayesNetwork Nodes
    def enumerate_all(self, variables, evidence):
        # if empty
        if not variables:
            return 1.0
        # Y in the book
        v = first(variables)
        # meaning v has a value in Evidence
        if v.tag in evidence.keys():
            return self.probability(of=v, value=evidence[v.tag], evidence=evidence) *\
                   self.enumerate_all(rest(variables), evidence=evidence)
        else:
            v_true = self.probability(v, True, evidence) * self.enumerate_all(rest(variables), extend(evidence, v.tag, True))
            v_false = self.probability(v, False, evidence) * self.enumerate_all(rest(variables), extend(evidence, v.tag, False))
            return v_true + v_false

    def probability(self, of, value, evidence):
        # 'of' is a bayes network variable
        # list of parents (e.g. ['blockage 1','blockage 2'...]
        parents = self.network.get_parents_of(of, as_object=False)
        parents_values = []
        # if the query variable is KNOWN in the initial Evidence!

        for parent in parents:
            try:
                # append "known" parent values to list
                parents_values.append(evidence[parent])
            # this should not happen
            except KeyError as e:
                print('parent {} value not found in evidence: {}'.format(parent, evidence))
                exit()
        prob = of.get_probability(value, parents_values)
        return prob

    # normalize a distribution vector
    def normalize(self, pair):
        s = float(sum(pair))
        if s == 0.0:
            return (0.0, 0.0)
        else:
            return pair[0]/s, pair[1]/s

    # returns a P(variable| given) = ... string
    def pretty_string(self, query_value):
        evidence_list = []
        for key in self.evidence.keys():
            evidence_list.append(key if self.evidence[key] is True else 'not ' + key)
        return 'P( {var} |  {given} ) = '.format(var=self.query_var.tag if query_value else 'not ' + self.query_var.tag,
                                                 given=', '.join(evidence_list), )

# supports a query of multi-variables
class MultiQuery(object):
    def __init__(self, query_vars, evidence, network):
        self.network = network
        self.query_vars = query_vars
        self.evidence = evidence

    # turn a query into a product of values, using the Enumerator
    # using the chain rule
    # vars_true - indicates if all vars are queried for True of False
    def query_to_value(self, vars_true=False):
        evidence = self.evidence.copy()
        values = []
        for var in self.query_vars:
            enumerator = Enumerator(query_var=var, evidence=evidence, network=self.network)
            # take [1] the second value - NOT BLOCKED
            if not vars_true:
                values.append(enumerator.enumeration_ask()[1])
            else:
                values.append(enumerator.enumeration_ask()[0])
            # update evidence with var=True for next calculation
            evidence[var.tag] = False
        return reduce(lambda x, y: x*y, values)






