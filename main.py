from transport_graph import Network
from simulation_gui import SimulationGUI
from controller import NetworkController
from time import sleep

# def export_connections_csv(network, outfile):
#     out_fd = open(outfile, 'w')
#     for stop in network.stops:
#         out_fd.write(f'{stop.id}')
#         for connection in network.get_connections_for_stop(stop):
#             if (connection.stop_1 == stop):
#                 adjacent_stop = connection.stop_2.id
#             else:
#                 adjacent_stop = connection.stop_1.id
#             out_fd.write(f',{adjacent_stop}:{connection.time}')
#         out_fd.write('\n')
#     out_fd.close()

# def export_stops_csv(network, outfile):
#     out_fd = open(outfile, 'w')
#     for stop in network.stops:
#         out_fd.write(f'{stop.id},{stop.name},{stop.lat},{stop.lon}\n')
#     out_fd.close()

def show_walks_for_routes(controller):
    for route in controller.prev_optimal_walks.keys():
        print(f'ROUTE {route.route_num}')
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
    network = Network()
    # print(network)
    # input('hi')
    # show_sorted_elevations(network)
    gui = SimulationGUI(network)
    controller = NetworkController(network, seconds_per_tick=360)
    show_walks_for_routes(controller)
    # input('Press Enter to close...')
    # export_stops_csv(network, 'stops.csv')
    # export_connections_csv(network, 'connections.csv')
    while (not controller.is_complete()):
        controller.update()
        gui.update(controller.current_water_level)
        sleep(0.5)
    input('Press enter to exit')