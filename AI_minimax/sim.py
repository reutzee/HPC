import argparse
from abc import ABCMeta

from agents.simple_agents import Human
from agents.smart_agents import GameTreeAgent

from env import World
from game_tree import GameTree


class Simulator:
    __metaclass__ = ABCMeta

    def __init__(self,  agents, state=None):
        self.state = state
        self.agents = agents


class HurricaneGameSimulator(Simulator):
    def __init__(self, graph_file, agent_file, cutoff_depth, ping_pong, mode='adversarial'):
        self.ping_pong = ping_pong
        self.graph_file = graph_file
        self.time = 0             # track time of the world
        self.evacuated = 0        # total number of people evacuated
        self.agents_history = []  # search paths of smart agents
        self.cutoff_depth = int(cutoff_depth)
        self.world = World(graph_file=graph_file, k=self.prompt_k())
        self.deadline = self.world.get_deadline()
        self.agents = self.get_agents_data(agent_file=agent_file, world=self.world)
        self.init_state = self.create_init_states(self.world, self.agents)
        self.mode = mode
        if not ping_pong:
            self.game_tree = GameTree(self.init_state, self.world, self.agents, mode=mode, cutoff_depth=self.cutoff_depth)
        super(HurricaneGameSimulator, self).__init__(state=self.world, agents=self.agents)

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
        if agent.observation.is_house(agent.vertex):
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



    # input in the format of : H1 G3;  <Type|Vertex>
    def get_agents_data(self,  world, agent_file=None):
        num_human = 0
        num_gamers = 0
        agents = []
        if agent_file is not None:
            with open(agent_file) as agents_file:
                for line in agents_file.readlines():
                    for agent_symbol in line.split():
                        vertex_number = int(agent_symbol[1:])
                        choice = 'MAX' if len(agents) == 0 else 'MIN'
                        if agent_symbol.upper().startswith('H'):
                            name = 'Human-{}'.format(str(num_human))
                            agent = Human(world=world, name=name, init_vertex=vertex_number, choice=choice)
                            agents.append(agent)
                            num_human += 1
                        elif agent_symbol.upper().startswith('G'):

                            choice = 'MAX' if len(agents) == 0 else 'MIN'
                            name = 'Gamer-{}'.format(str(num_gamers))
                            agent = GameTreeAgent(world=world, name=name, init_vertex=vertex_number, choice=choice)
                            agents.append(agent)
                            num_gamers += 1

        return agents

    # prompt the user for the K  -   slow down constant
    def prompt_k(self):
        k = float(input('Enter the slow-down constant: '))
        # 0 < K < 1
        if 0 < k <= 1:
            return k
        raise Exception('K must be in range (0,1)')

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

    # create a state for 2 agent problem
    def create_init_states(self, world, agents):
        state = dict()
        for agent in agents:
            people = world.get_vertex_for_tag(agent.vertex).people if world.is_house(agent.vertex) else 0
            state[agent.name] = {'position': agent.vertex,
                            'people_in_car': people,
                            'people_saved': 0}
        state['time'] = 0
        return state

    # run each agent in turn. in case of human agent, CHANGE the parent according to the human's choice.
    def run(self):
        print('initial state : {}'.format(self.game_tree.root.get_state()))
        node = self.game_tree.root
        i = 0           # first agent to "run"
        while node.type is not 'CUTOFF' and node.type is not 'TERMINAL':
            agent = self.agents[i]
            action = agent.get_move(node)
            # update to next node
            for child in node.children:
                if child.action == action:
                    child.parent = node
                    node = child
            state_path = self.get_state_path(node)
            print('path here : {}'.format([n.action for n in state_path]))
            print('------\nagent:{} action {}\ntime: {}\nminimax value: {}\nstate: {}\n------\n'.format(agent.name, action, node.get_time() ,node.get_minimax_value(), node.get_state()))
            # next agent
            i = (i + 1) % len(self.agents)


    def run_ping_pong(self):
        turn = 0
        actions = []
        visited = []
        state = self.create_init_states(self.world, self.agents)
        visited.append(state[self.agents[0].name]['position'])        # append initial positions
        visited.append(state[self.agents[1].name]['position'])        # append initial positions
        while True:
            current_agent = self.agents[turn]
            if isinstance(current_agent, Human):
                result_node = current_agent.get_move(state=state, visited=visited, world=self.world)
            else:
                result_node = current_agent.get_move_new_tree(state=state, visited=visited,
                                                              world=self.world, cutoff_depth=self.cutoff_depth, mode=self.mode)
            actions.append(result_node.action)
            visited.append(result_node.get_position(current_agent.name))
            visited.append(result_node.get_position(current_agent.name))

            print('path here : {}'.format(actions))
            print('------\nagent:{} action {}\ntime: {}\nminimax value: {}\nstate: {}\n------\n'.format(self.agents[turn].choice, result_node.action,
                                                                                                        result_node.get_time() ,result_node.get_minimax_value(), result_node.get_state()))

            if result_node.type == 'CUTOFF' or result_node.type == 'TERMINAL':
                print("final state: {}".format(result_node.get_state()))
                break
            turn = (turn + 1) % len(self.agents)    # next agent's turn
            state = result_node.get_state()
            result_node = None









if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph_file', default='./graph.txt')
    parser.add_argument('-a', '--agent_file', default='./agents.txt') # for task 1
    parser.add_argument('-p', '--ping_pong', default=False)
    parser.add_argument('-t', '--task_number', default='1')
    parser.add_argument('-c', '--cutoff_depth', default=15)

    args = parser.parse_args()

    # ping pong - each agent creates a new tree every turn
    ping_pong = True if (str(args.ping_pong).lower() == 'y' or str(args.ping_pong).lower() == 'yes') else False
    if int(args.task_number) is 1:
        sim = HurricaneGameSimulator(graph_file=args.graph_file, agent_file=args.agent_file, mode='adversarial', cutoff_depth=args.cutoff_depth, ping_pong=ping_pong)
    elif int(args.task_number) is 2:
        sim = HurricaneGameSimulator(graph_file=args.graph_file, agent_file=args.agent_file, mode='semi-coop', cutoff_depth=args.cutoff_depth, ping_pong=ping_pong)
    else: #if 'full-coop'
        sim = HurricaneGameSimulator(graph_file=args.graph_file, agent_file=args.agent_file, mode='full-coop', cutoff_depth=args.cutoff_depth, ping_pong=ping_pong)
    if ping_pong:
        sim.run_ping_pong()
    else:
        sim.run()


