from env import *
from agent import Agent
from ping_pong_game_tree import Node
class Human(Agent):
    def __init__(self, world, name=None, init_vertex=1,choice=None):
        super(Human, self).__init__(world=world, name=name, init_vertex=init_vertex)
        if choice is not None:
            self.choice = choice


    # return (the current position, the next move) for the Simulator
    def do(self):
        return self.get_next_move()

    def get_result_state_of_move(self,  move, state, visited, world):
        if move == 'NOP':
            new_state = state.copy()
            new_state['time'] += 1
            return new_state
        else:
            v = int(move[1:])
            position = state[self.name]['position']
            new_people_in_car = state[self.name]['people_in_car']
            new_people_saved = state[self.name]['people_saved']
            new_time = state['time'] + world.calculate_price(position, v, state[self.name]['people_in_car'])

            if world.is_house(v) and v not in visited:
                new_people_in_car += world.get_vertex_for_tag(v).people
            # if v is Shelter Vertex -> drop off all of them
            elif world.is_shelter(v) and new_time <= world.get_deadline():
                new_people_in_car = 0
                new_people_saved += state[self.name]['people_in_car']
            result_agent = {'position': v,
                            'people_in_car': new_people_in_car,
                            'people_saved' : new_people_saved}
            result = state.copy()
            result[self.name] = result_agent
            result['time'] = new_time
            return result

    # (state=state, visited=visited, world=self.world)
    def get_move(self, state, visited, world, node=None):
        move = self.get_next_move()
        new_state = self.get_result_state_of_move(move, state, visited, world)
        next_choice = 'MAX' if self.choice ==  'MIN' else 'MIN'
        return Node(None,state=new_state, choice=next_choice, action=move)

    # get the next move from the user
    def get_next_move(self):
        return raw_input("What is your next move?\n--NOP to no-op\n--T<#Vertex> to traverse to another vertex\nInput: ").upper()



