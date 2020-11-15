from transport_graph import Network
from simulation_gui import SimulationGUI

def export_connections_csv(network, outfile):
    out_fd = open(outfile, 'w')
    for stop in network.stops:
        out_fd.write(f'{stop.id}')
        for connection in network.get_connections_for_stop(stop):
            if (connection.stop_1 == stop):
                adjacent_stop = connection.stop_2.id
            else:
                adjacent_stop = connection.stop_1.id
            out_fd.write(f',{adjacent_stop}:{connection.time}')
        out_fd.write('\n')
    out_fd.close()

def export_stops_csv(network, outfile):
    out_fd = open(outfile, 'w')
    for stop in network.stops:
        out_fd.write(f'{stop.id},{stop.name},{stop.lat},{stop.lon}\n')
    out_fd.close()
    

if __name__ == '__main__':
    network = Network()
    # print(network)
    # input('hi')
    gui = SimulationGUI(network)
    input('Press Enter to close...')
    # export_stops_csv(network, 'stops.csv')
    # export_connections_csv(network, 'connections.csv')