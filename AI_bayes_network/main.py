import argparse
from abc import ABCMeta

import os
from bayes_network import BayesNetwork, Evacuees, Blockage, Flooding
from enumerator import Enumerator, MultiQuery

from env import World

class Main(object):
    def __init__(self, graph_file):
        self.graph_file = graph_file
        self.world = World(graph_file=graph_file)
        self.deadline = self.world.get_deadline()
        self.bayes_network = BayesNetwork(world=self.world)
        self.reports = {}

    def clear_screen(self, stupid=False):
        if stupid:
            print('\n') * 100
        else:
            os.system('cls' if os.name == 'nt' else 'clear')

    def get_numbers(self,prompt, smallest, biggest):
        while True:
            choice = raw_input(prompt).split()
            if 'exit' in choice or 'quit' in choice or 'q' in choice:
                exit()

            elif not any(int(x) < smallest or int(x) > biggest for x in choice) and not len(choice) == 0:
                # self.clear_screen(stupid=True)
                return choice

            else:
                # self.clear_screen(stupid=True)
                print('illegal input.')
                return False

    # get query evidence from user
    def prompt_query_evidence(self):
        all_reports = {}
        num_edges = len(self.world.get_edges(one_way=True))
        num_vertices = len(self.world.get_vertices())
        report_prompt = 'What would you like to report? \n 1. Flood\n 2. Blockage\n 3. Evacuees\n-------\n ' \
                        '4. No Flood\n 5. No Blockage\n 6. No Evacuees\n-------\n 7. Non-Blocked Path\n 8. Print Reasoning\n 9. Bonus\n 10. Reset\n choice: '
        short_report_prompt = '\nAnother report?'
        blockage_prompt = 'report Blocking at edges : range-({},{}) '.format(1, num_edges)
        flooding_prompt = 'report Flooding at vertices range-({},{}) : '.format(1, num_vertices)
        evacuees_prompt = 'report Evacuees at vertices range-({},{}): '.format(1, num_vertices)
        non_blockage_prompt = 'report NON Blocking at edges : range-({},{}) '.format(1, num_edges)
        non_flooding_prompt = 'report NON Flooding at vertices range-({},{}) : '.format(1, num_vertices)
        non_evacuees_prompt = 'report NON Evacuees at vertices range-({},{}): '.format(1, num_vertices)
        iteration = 0
        while True:
            iteration += 1
            print('\n----------------\nReported so far :  \n{}\n----------------'.format(all_reports))
            if iteration is 1:
                report_choice = int(self.get_numbers(report_prompt, smallest=1, biggest=10)[0])
            else:
                report_choice = int(self.get_numbers(short_report_prompt, smallest=1, biggest=10)[0])
            if report_choice == 1:
                floodings = set(self.get_numbers(flooding_prompt, smallest=1, biggest=num_vertices))
                floodings = set(['flooding ' + str(num) for num in floodings])
                for report in floodings:
                    all_reports[report] = True

            elif report_choice == 2:
                blockages = set(self.get_numbers(blockage_prompt, smallest=1, biggest=num_edges))
                blockages = set(['blockage ' + str(num) for num in blockages])
                for report in blockages:
                    all_reports[report] = True

            elif report_choice == 3:
                evacuees = set(self.get_numbers(evacuees_prompt, smallest=1, biggest=num_vertices))
                evacuees = set(['evacuees ' + str(num) for num in evacuees])
                for report in evacuees:
                    all_reports[report] = True

            elif report_choice == 4:
                floodings = set(self.get_numbers(non_flooding_prompt, smallest=1, biggest=num_vertices))
                floodings = set(['flooding ' + str(num) for num in floodings])
                for report in floodings:
                    all_reports[report] = False

            elif report_choice == 5:
                blockages = set(self.get_numbers(non_blockage_prompt, smallest=1, biggest=num_edges))
                blockages = set(['blockage ' + str(num) for num in blockages])
                for report in blockages:
                    all_reports[report] = False

            elif report_choice == 6:
                evacuees = set(self.get_numbers(non_evacuees_prompt, smallest=1, biggest=num_vertices))
                evacuees = set(['evacuees ' + str(num) for num in evacuees])
                for report in evacuees:
                    all_reports[report] = False

            elif report_choice == 7:
                print('Overall Reported: {}'.format(all_reports))
                prompt = 'Enter a set of Edges as a path. range-({},{}) '.format(1, num_edges)
                path = set(int(n) for n in self.get_numbers(prompt, smallest=1, biggest=num_edges))
                if len(path) > 1:
                    self.reports = all_reports
                    p = self.get_probability_path_free(path)
                    non_blocked = ', '.join(['not blockage {}'.format(str(e)) for e in path])
                    given = self.evidence_as_string(all_reports)
                    s = 'P({of} | {given} ) = {p}'.format(of=non_blocked, given=given, p=p)
                    print(s)
                else:
                    print('A single edge can computed normally')

            elif report_choice == 8:
                print('Overall Reported: {}'.format(all_reports))
                self.reports = all_reports
                self.perform_reasoning()

            elif report_choice == 9:
                self.reports = all_reports
                print('Overall Reported: {}'.format(all_reports))
                prompt = 'Enter a source Vertex and a Destination Vertex. range-({},{}) '.format(1, num_vertices)
                user_input = [int(n) for n in self.get_numbers(prompt, smallest=1, biggest=num_vertices)]
                if len(user_input) is not 2:
                    print('usage : <source> <destination>')
                else:
                    self.reports = all_reports
                    self.do_bonus(source=user_input[0], destination=user_input[1])

            elif report_choice == 10:
                all_reports = dict()

    # print the network
    def print_network(self):
        self.bayes_network.print_network()

    def perform_reasoning(self):
        self.query_type('evacuees')
        self.query_type('flooding')
        self.query_type('blockage')

    def query_type(self, node_type, for_print=True):
        nodes = self.bayes_network.get_nodes_of_type(node_type)
        vals = []
        for node in nodes:
            # self.enumerate_prob(node)
            if node.node_type != 'blockage':
                vals.append((node.get_vertex().tag, self.enumerate_prob(node)))
            else:
                vals.append((node.get_edge().edge_num, self.enumerate_prob(node)))
        return vals

    def do_bonus(self, source, destination):
        paths = self.world.all_paths(source=source, destination=destination)
        probabilities = [self.get_probability_path_free(p) for p in paths]
        print('Printing the Probability of free from blockages - path from {} to {} :'.format(source, destination))
        min_path = ([], 0.0)
        for (path, prob) in zip(paths, probabilities):
            if prob >= min_path[1]:
                min_path = (path, prob)
            print('Path: {} , Probability(free) = {}'.format(path, prob))
        print('\n===========================\n')
        if min_path[1] == 0.0:
            print('all paths from {} to {} are blocked with probability 1'.format(source, destination))
        else:
            print('Best path is : {} with probability {}'.format(min_path[0], min_path[1]))


    # and print
    def enumerate_prob(self, node):
        enumerator = Enumerator(query_var=node, evidence=self.reports, network=self.bayes_network)
        p = enumerator.pretty_string(query_value=True)
        p_val = enumerator.enumeration_ask()
        s = p + str(p_val[0])
        print(s)
        # print("\n")
        return p_val[0]



    def get_probability_path_free(self, path):
            reported_evidence = self.reports.copy()
            query_vars = filter(lambda n: n.get_edge().edge_num in path, self.bayes_network.get_nodes_of_type('blockage'))
            multi_query = MultiQuery(query_vars=query_vars, evidence=reported_evidence, network=self.bayes_network)
            # vars_true is False - we want blockages to be false.
            p = multi_query.query_to_value(vars_true=False)

            return p

    def evidence_as_string(self, evidence):
        s = ''
        for e in evidence.keys():
            if s != '':
                s += ','
            if evidence[e]:
                s += e
            else:
                s += 'not ' + e
        return s




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph_file', default='./graph.txt')

    args = parser.parse_args()

    main = Main(graph_file=args.graph_file)
    main.print_network()
    print '\n' * 5
    main.prompt_query_evidence()
    print '\n' * 10







