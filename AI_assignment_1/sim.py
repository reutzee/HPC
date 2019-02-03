import argparse
from abc import ABCMeta

from agents.simple_agents import Human, Greedy, Vandal
from agents.smart_agents import SmartGreedy, SmartAStar, SmartRTA
from env import World


class Simulator:
    __metaclass__ = ABCMeta

    def __init__(self,  agents, state=None):
        self.state = state
        self.agents = agents

class HurricaneEvacuationSimulator(Simulator):
    def __init__(self, graph_file, agent_file, f):
        self.graph_file = graph_file
        self.time = 0             # track time of the world
        self.evacuated = 0        # total number of people evacuated
        self.f_constant = f
        self.agents_history = []  # search paths of smart agents
        world = World(graph_file=graph_file, k=self.prompt_k())
        self.deadline = world.get_deadline()
        agents = self.get_agents_data(agent_file=agent_file, world=world)
        super(HurricaneEvacuationSimulator, self).__init__(state=world, agents=agents)
        self.vandal_records = {}  # pairs of <edge>:<time-of-blocking>
    # return num of actions for each agent
    def get_all_actions(self):
        agent_actions = {}
        for agent in self.agents:
            agent_actions[agent.name] = len(agent.get_actions())
        return agent_actions

    # return number of all people evacuated for ALL agents
    def get_total_evacuated(self):
        acc = 0
        for agent in self.agents:
            acc += agent.get_evacuated()
        return acc

    # move agent to the destination
    def move_agent_to(self, agent, dest, edge):
        agent.vertex = dest     # move the agent
        moving_time = self.calculate_price(agent=agent, edge=edge)
        self.time += moving_time                        # add total time of simulator
        # if deadline has passed, return
        if self.time > self.deadline:
            return False
        if agent.observation.is_house(agent.vertex) and not isinstance(agent, Vandal):
            agent.pick_up()
        elif agent.get_people_in_car() > 0:   # if in a Shelter vertex
            agent.drop_off()
        return True

    # time it takes to traverse on 'edge'
    def calculate_price(self, agent, edge):
        w = edge.weight
        k = self.state.get_slow_down()
        p = agent.get_people_in_car()
        return w*(1+k*p)

    # Do a 1step for a Human & Greedy Agent
    def do_agent(self, agent):
        next_move = agent.do()  # do action for Human Agent
        agent.add_action(next_move)
        if next_move == 'NOP':
            self.time += 1
        else:  # Traverse
            if next_move[0].upper() != 'T':
                raise Exception('Unknown action')
            dest = int(next_move[1:])  # number of the destination vertex
            edge_to_traverse = self.state.get_edge(agent.vertex, dest)
            return self.move_agent_to(agent=agent, edge=edge_to_traverse, dest=dest)

    # Do a step for a Vandal Agent
    def do_vandal(self, agent):
        next_move = agent.do()    # do action for Vandal Agent
        agent.add_action(next_move)
        if next_move == 'NOP':
            self.time += 1
        elif str(next_move).startswith('BLOCK'):
            v1 = int(next_move.split()[1])
            v2 = int(next_move.split()[2])
            to_block = self.state.get_edge(v1, v2)
            to_block.blocked = True
            self.time += 1
            self.record_block(v1, v2)
        else:    # Traverse
            if next_move[0].upper() != 'T':
                raise Exception('Unknown action')
            dest = int(next_move[1:])   # number of the destination vertex
            edge_to_traverse = self.state.get_edge(agent.vertex, dest)
            return self.move_agent_to(agent=agent, edge=edge_to_traverse, dest=dest)

    # Do a step for a Vandal Agent
    def simulate_vandal(self, agent):
        while self.time <= self.deadline:
            self.do_vandal(agent=agent)
        # re-create the world
        self.state = World(graph_file=self.graph_file, k=self.state.get_slow_down())
    # input in the format of : H1 V3 G10 H2 ;  <Type|Vertex>

    def get_agents_data(self,  world, agent_file=None):
        num_human = 0
        num_greedy = 0
        num_vandal = 0
        agents = []
        if agent_file is not None:
            with open(agent_file) as agents_file:
                for line in agents_file.readlines():
                    for agent_symbol in line.split():
                        vertex_number = int(agent_symbol[1:])
                        if agent_symbol.upper().startswith('H'):
                            agent = Human(world=world, name='Human-{}'.format(str(num_human)), init_vertex=vertex_number)
                            num_human += 1
                        elif agent_symbol.upper().startswith('G'):
                            agent = Greedy(world=world, name='Greedy-{}'.format(str(num_greedy)), init_vertex=vertex_number)
                            num_greedy += 1
                        else:  # agent_symbol.upper().startswith('V')
                            agent = Vandal(world=world, name='Vandal-{}'.format(str(num_vandal)), init_vertex=vertex_number)
                            num_vandal += 1
                        agents.append(agent)

        return agents

    # prompt the user for the K  -   slow down constant
    def prompt_k(self):
        k = 1#float(input('Enter the slow-down constant: '))
        # 0 < K < 1
        if 0 < k <= 1:
            return k
        raise Exception('K must be in range (0,1)')

    def run_task1(self):
        print('DEADLINE IS {}'.format(self.deadline))
        # First round of pick-ups
        for agent in self.agents:
            if isinstance(agent, Human) or isinstance(agent, Greedy):
                agent.pick_up()
        while self.time < self.deadline:
            for agent in self.agents:
                if isinstance(agent, Human) or isinstance(agent, Greedy):
                    if isinstance(agent, Human):
                        agent.print_agent_status()
                    if self.do_agent(agent=agent) is False:
                        continue
                if isinstance(agent, Vandal):
                    if self.do_vandal(agent=agent) is False:
                        break
                if self.time >= self.deadline:
                    break
                print('Time : {}\n---------'.format(self.time))
                agent.print_agent_status()
                # self.state.print_graph()
                print('----step done, time {}----\n\n'.format(self.time))


    def run_task2(self, expand_limit, agent="greedy"):
        agent_type = agent
        print(agent_type)
        if agent_type.lower() == "greedy":
            smart_agent = SmartGreedy(world=self.state, name='SmartGreedy', init_vertex=1)
        elif agent_type.lower() == "a*":
            smart_agent = SmartAStar(world=self.state, name='SmartAStar', init_vertex=1)
        else: #if agent.upper() is "RTA":
            smart_agent = SmartRTA(world=self.state, name='RTA', init_vertex=1, expand_limit=expand_limit)

        self.agents.append(smart_agent)
        final_node = smart_agent.do()
        self.agents_history.append((agent_type, self.get_state_path(final_node)))
        self.print_run()

    def run_bonus(self, expand_limit, agent="greedy", vandal_init_vertex=1):

        vandal = Vandal(world=self.state, init_vertex=vandal_init_vertex, name='Vandal_Agents')
        self.simulate_vandal(vandal)  # run the vandal
        print('------------\nThe Vandal records are: {}\n------------\n'.format(self.vandal_records))
        agent_type = agent
        print(agent_type)
        if agent_type.lower() == "greedy":
            smart_agent = SmartGreedy(world=self.state, name='SmartGreedy', init_vertex=1, bonus_vandal_records=self.vandal_records)
        elif agent_type.lower() == "a*":
            smart_agent = SmartAStar(world=self.state, name='SmartAStar', init_vertex=1, bonus_vandal_records=self.vandal_records)
        else: #if agent.upper() is "RTA":
            smart_agent = SmartRTA(world=self.state, name='RTA', init_vertex=1, expand_limit=expand_limit, bonus_vandal_records=self.vandal_records)

        self.agents.append(smart_agent)
        final_node = smart_agent.do()
        self.agents_history.append((agent_type, self.get_state_path(final_node)))
        self.print_run()

        # vandal = Vandal(world=self.state, init_vertex=vandal_init_vertex, name='Vandal_Agents')
        #
        # agent_type = agent
        # print(agent_type)
        # if agent_type.lower() == "greedy":
        #     smart_agent = SmartGreedy(world=self.state, name='SmartGreedy', init_vertex=1)
        # elif agent_type.lower() == "a*":
        #     smart_agent = SmartAStar(world=self.state, name='SmartAStar', init_vertex=1)
        # else: #if agent.upper() is "RTA":
        #     smart_agent = SmartRTA(world=self.state, name='RTA', init_vertex=1, expand_limit=expand_limit)
        #
        # self.agents.append(smart_agent)
        # final_node = smart_agent.do()
        # nodes = smart_agent.search_tree.get_visited_vertices(final_node)
        # smart_node = nodes[-1]
        #
        # while smart_node.get_time() <= self.deadline:
        #     # "advance" the smart agent one step
        #     smart_node = smart_agent.search_tree.get_next_node_in_path(smart_node, final_node)
        #     state = smart_node.get_state()
        #     # advance time as the smart agent's step
        #     self.time = smart_node.get_time()
        #     # run one step of the vandal
        #     self.do_vandal(vandal)
        #     # state[]

    # create a path of states from the final node. the path is the agent's actions.
    def get_state_path(self, final_node):
        path = [final_node]
        if final_node == 'FAILURE':
            return ['FAILURE']
        runner_node = final_node.parent

        while runner_node is not None:
            path.insert(0, runner_node)
            runner_node = runner_node.parent
        return path

    # get the number of people saved by the Agent
    def get_score_from_path(self, state_path):
        score = 0
        for i in range(len(state_path))[1:]:
            in_car = state_path[i].get_people_in_car()
            # if 0 people in car, it means last state was a drop-off
            if in_car is 0:
                score += state_path[i - 1].get_people_in_car()
        return score


    # def get_rescue_list_from_path(self, state_path):
    #     rescue_list = []
    #     for i in range(len(state_path)):
    #         rescue_list.append(' ')
    #         in_car = state_path[i].get_people_in_car()
    #         if in_car > state_path[i - 1].get_people_in_car():
    #             rescue_list[i] = 'picked up : {}'.format(in_car)
    #         elif in_car < state_path[i - 1].get_people_in_car():
    #             rescue_list[i] = 'dropped off : {}'.format(state_path[i - 1].get_people_in_car())
    #     return rescue_list

    def print_run(self):

        if len(self.agents_history) is 0:
            print('Nothing to print!')
            return
        for agent, state_path in self.agents_history:
            actions = [node.action for node in state_path]
            score = self.get_score_from_path(state_path)
            expands = self.agents[-1].expands
            p = self.f_constant * score + expands
            print('**********\nShowing steps of {}.\nscore:{}\nExpands:{}'.format(agent, score, expands))
            print('Performance: {} = {} * {} + {}'.format(p, self.f_constant, score, expands))
            print('Final State: {}\n\n'.format(state_path[len(state_path) - 1].state))
            print('Action Trace:\n    {}\n'.format(actions))


    def record_block(self, v1, v2):
        edge1 = '{},{}'.format(str(v1), str(v2))
        edge2 = '{},{}'.format(str(v2), str(v1))
        self.vandal_records[edge1] = self.time
        self.vandal_records[edge2] = self.time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph_file', default='./graph.txt')
    parser.add_argument('-a', '--agent_file', default='./agents.txt') # for task 1
    parser.add_argument('-t', '--task_number', default='1')
    parser.add_argument('-s', '--smart_strategy', type=str, default='GREEDY')  # for task 2
    parser.add_argument('-e', '--expand_limit', default='11') # for task 2 - RTA
    parser.add_argument('-f', '--f_parameter', default='-100') # for performance measure


    args = parser.parse_args()

    sim = HurricaneEvacuationSimulator(graph_file=args.graph_file, agent_file=args.agent_file, f=int(args.f_parameter))
    sim.state.print_adjacency()
    print('\n\n')
    if args.task_number == '2':
        sim.run_task2(agent=args.smart_strategy, expand_limit=int(args.expand_limit))
    elif args.task_number == '1':
        sim.run_task1()
    # run the bonus
    elif args.task_number == '3':
        sim.run_bonus(agent=args.smart_strategy, expand_limit=int(args.expand_limit))



