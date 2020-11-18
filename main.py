import argparse
from transport_graph import Network
from simulation_gui import SimulationGUI
from controller import NetworkController
from time import sleep

def show_walks_for_routes(controller):
    for route in controller.prev_optimal_walks.keys():
        print(f'ROUTE {route.route_num}')
        if (controller.prev_optimal_walks[route] == None):
            print('\tNONE')
        for connection in controller.prev_optimal_walks[route]:
            print(f'\t{connection.stop_1.id}, {connection.stop_2.id}')

def show_sorted_elevations(network):
    print('STOPS')
    stop_elevations = []
    for stop in network.stops:
        stop_elevations.append(stop.elevation)
    stop_elevations.sort()
    for elevation in stop_elevations:
        print(f'\t{elevation}')
    
    print('CONNECTIONS')
    connection_elevations = []
    for connection in network.connections:
        connection_elevations.append(connection.elevation)
    connection_elevations.sort()
    for elevation in connection_elevations:
        print(f'\t{elevation}')

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--disaster_resistant', help='disaster resistant?', action='store_true')
    args = parser.parse_args()
    network = Network()
    gui = SimulationGUI(network)
    controller = NetworkController(network, disaster_resistant=args.disaster_resistant, seconds_per_tick=120)

    while (not controller.is_complete()):
        controller.update()
        gui.update(controller.current_water_level, controller.current_time)
        sleep(0.05)
    
    input('Press enter to exit')